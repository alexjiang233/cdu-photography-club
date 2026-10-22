"""Transactional domain operations shared by API and administration."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import AuditLog, Collection, Comment, Document, Event, Notice, Registration, Status, Asset, Issue
from .permissions import can_edit, can_moderate, require_member


def submit_comment(user, target, validated_data):
    """Visitors can submit comments; only moderation makes them public."""
    return Comment.objects.create(
        author=user if user.is_authenticated else None,
        guest_name=validated_data.get('guest_name', '').strip(),
        text=validated_data['text'],
        approved=False,
        **target,
    )


def assign_code(obj):
    """给已发布的作品分配年度档案编号，例如 2026-001。"""
    if isinstance(obj, Collection) and not obj.code and obj.published_at:
        prefix = f'{obj.published_at.year}-'
        last = (
            Collection.objects.filter(code__startswith=prefix)
            .order_by('-code')
            .values_list('code', flat=True)
            .first()
        )
        try:
            sequence = int(last.split('-')[-1]) + 1 if last else 1
        except (ValueError, AttributeError):
            sequence = 1
        obj.code = f'{prefix}{sequence:03d}'
    return obj


def audit(user, action, obj, detail=''):
    AuditLog.objects.create(
        actor=user if user.is_authenticated else None,
        action=action,
        target_type=obj._meta.model_name,
        target_id=str(obj.pk),
        detail=detail[:500],
    )


@transaction.atomic
def delete_collections(user, queryset):
    """Delete series and their dependent rows, preserving uploaded assets and audit history."""
    if not (user.is_active and user.is_staff and user.has_perm('club.delete_collection')):
        raise PermissionDenied('需要作品删除权限。')
    if queryset.model is not Collection:
        raise ValidationError('只能删除作品系列。')
    objects = list(queryset.select_for_update())
    for obj in objects:
        audit(user, 'delete_collection', obj, obj.title)
    Collection.objects.filter(pk__in=[obj.pk for obj in objects]).delete()


@transaction.atomic
def transition(user, obj, action, note=''):
    obj = type(obj).objects.select_for_update().get(pk=obj.pk)
    if isinstance(obj, Issue) and action in ['submit', 'publish']:
        from django.core.exceptions import ValidationError as ModelValidationError
        try:
            obj.full_clean()
            if not obj.blocks.exists():
                raise ValidationError('请先编排本期内容。')
            for block in obj.blocks.select_related('image'):
                block.full_clean()
        except ModelValidationError as exc:
            raise ValidationError(exc.messages)
    if action == 'submit':
        if not can_edit(user, obj):
            raise PermissionDenied()
        if obj.status not in [Status.DRAFT, Status.RETURNED]:
            raise ValidationError('只有草稿或退回的内容可以提交。')
        if (
            isinstance(obj, Collection)
            and not obj.photos.filter(asset__state=Asset.State.READY).exists()
        ):
            raise ValidationError('请先添加至少一张已处理完成的照片。')
        if (
            isinstance(obj, Document)
            and not obj.versions.filter(asset__state=Asset.State.READY).exists()
        ):
            raise ValidationError('请先上传可用的资料文件。')
        obj.status = Status.PENDING
    elif action == 'revise':
        if not can_edit(user, obj):
            raise PermissionDenied()
        if obj.status not in [Status.PUBLISHED, Status.ARCHIVED, Status.PENDING]:
            raise ValidationError('当前内容无需撤回。')
        obj.status = Status.DRAFT
    elif action in ['publish', 'return', 'archive']:
        if not can_moderate(user, type(obj)):
            raise PermissionDenied('需要编辑权限。')
        if action == 'publish':
            if obj.status != Status.PENDING:
                raise ValidationError('请先提交审核。')
            if isinstance(obj, Collection) and (
                not obj.photos.exists()
                or obj.photos.exclude(asset__state=Asset.State.READY).exists()
            ):
                raise ValidationError('作品的照片必须全部处理完成。')
            if (
                isinstance(obj, Document)
                and not obj.versions.filter(asset__state=Asset.State.READY).exists()
            ):
                raise ValidationError('没有可发布的文件版本。')
            obj.status = Status.PUBLISHED
            obj.published_at = timezone.now()
            assign_code(obj)
        elif action == 'return':
            if obj.status != Status.PENDING or not note.strip():
                raise ValidationError('退回待审核内容时请填写修改建议。')
            obj.status = Status.RETURNED
        else:
            obj.status = Status.ARCHIVED
    else:
        raise ValidationError('未知操作。')
    obj.review_note = note
    fields = ['status', 'review_note', 'published_at', 'updated_at']
    if isinstance(obj, Collection):
        fields.append('code')
    obj.save(update_fields=fields)
    audit(user, action, obj, note)
    paths = {'collection': 'works', 'event': 'events', 'document': 'archive', 'issue': 'field-journal/issues'}
    Notice.objects.create(
        recipient=obj.owner,
        text=f'「{obj.title}」：{obj.get_status_display()}',
        href=f'/{paths[obj._meta.model_name]}/{obj.pk}',
    )
    return obj


@transaction.atomic
def register(user, event_id, contact, note=''):
    require_member(user)
    event = Event.objects.select_for_update().get(pk=event_id)
    now = timezone.now()
    if (
        event.status != Status.PUBLISHED
        or not event.registration_open
        or event.registration_deadline <= now
        or event.starts_at <= now
    ):
        raise ValidationError('当前活动未开放报名或已截止。')
    previous = Registration.objects.filter(event=event, user=user).first()
    if previous and not previous.cancelled:
        raise ValidationError('你已报名该活动。')
    if event.registrations.filter(cancelled=False).count() >= event.capacity:
        raise ValidationError('报名人数已满。')
    if not contact.strip():
        raise ValidationError('请填写联系方式。')
    registration, _ = Registration.objects.update_or_create(
        event=event,
        user=user,
        defaults={'contact': contact.strip(), 'note': note, 'cancelled': False},
    )
    audit(user, 'register', event)
    Notice.objects.create(
        recipient=user, text=f'已报名「{event.title}」', href=f'/events/{event.pk}'
    )
    return registration


@transaction.atomic
def cancel_registration(user, event):
    Event.objects.select_for_update().get(pk=event.pk)
    if timezone.now() >= event.starts_at:
        raise ValidationError('活动开始后请联系负责人调整报名。')
    record = Registration.objects.filter(event=event, user=user, cancelled=False).first()
    if not record:
        raise ValidationError('没有有效报名记录。')
    record.cancelled = True
    record.save(update_fields=['cancelled', 'updated_at'])
    audit(user, 'cancel_registration', event)
