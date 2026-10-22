from django.db import transaction
from django.db.models import Case, IntegerField, Max, Q, Value, When
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from .. import services
from ..models import (
    Asset,
    Collection,
    Comment,
    Document,
    DocumentVersion,
    Event,
    Photo,
    Profile,
    Status,
)
from ..permissions import can_edit, require_member, visible_queryset
from ..serializers import (
    CollectionSerializer,
    CommentSerializer,
    DocumentSerializer,
    EventSerializer,
    PhotoSerializer,
    RegistrationSerializer,
)


class CommentThrottle(SimpleRateThrottle):
    scope = 'comment'

    def get_cache_key(self, request, view):
        if request.method != 'POST':
            return None
        # Use the same IP budget for guests and signed-in administrators.
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


def validated_uuid(value):
    import uuid

    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError('内容编号无效。')


class EditorialViewSet(viewsets.ModelViewSet):
    lookup_value_regex = '[0-9a-fA-F-]{36}'
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = visible_queryset(super().get_queryset(), self.request.user)
        if qs.model is Collection and self.request.query_params.get('placeholder') == '0':
            qs = qs.filter(is_placeholder=False)
        if self.request.query_params.get('mine') == '1':
            if not self.request.user.is_authenticated:
                return qs.none()
            qs = qs.filter(owner=self.request.user)
        term = self.request.query_params.get('q', '')[:100].strip()
        if term:
            qs = qs.filter(
                Q(title__icontains=term)
                | Q(description__icontains=term)
                | Q(tags__name__icontains=term)
            ).distinct()
        tag = self.request.query_params.get('tag', '')
        if tag:
            qs = qs.filter(tags__name=tag)
        event_id = self.request.query_params.get('event', '')
        if event_id and self.queryset.model != Event:
            try:
                import uuid

                qs = qs.filter(event_id=uuid.UUID(event_id))
            except ValueError:
                raise ValidationError('活动编号无效。')
        return qs

    def perform_create(self, serializer):
        require_member(self.request.user)
        extra = {'owner': self.request.user}
        if serializer.Meta.model == Collection:
            profile, _ = Profile.objects.get_or_create(
                user=self.request.user, defaults={'display_name': self.request.user.username}
            )
            extra['author'] = profile
        else:
            if not self.request.user.has_perm(f'club.add_{serializer.Meta.model._meta.model_name}'):
                raise PermissionDenied('需要对应的内容管理权限。')
        obj = serializer.save(**extra)
        services.audit(self.request.user, 'create', obj)

    def perform_update(self, serializer):
        if not can_edit(self.request.user, serializer.instance):
            raise PermissionDenied()
        obj = serializer.save()
        services.audit(self.request.user, 'update', obj)

    @action(detail=True, methods=['post'])
    def workflow(self, request, pk=None):
        obj = services.transition(
            request.user,
            self.get_object(),
            request.data.get('action'),
            str(request.data.get('note', ''))[:2000],
        )
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=['get', 'post'], throttle_classes=[CommentThrottle])
    def comments(self, request, pk=None):
        obj = self.get_object()
        if not isinstance(obj, (Collection, Event)):
            raise Http404()
        target = {'collection': obj} if isinstance(obj, Collection) else {'event': obj}
        if request.method == 'POST':
            serializer = CommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            comment = services.submit_comment(request.user, target, serializer.validated_data)
            return Response(CommentSerializer(comment).data, status=201)
        query = (
            Comment.objects.filter(**target)
            .filter(
                Q(approved=True) | Q(author=request.user)
                if request.user.is_authenticated
                else Q(approved=True)
            )
            .select_related('author__profile')
        )
        page = self.paginate_queryset(query)
        return self.get_paginated_response(CommentSerializer(page, many=True).data)


class CollectionViewSet(EditorialViewSet):
    queryset = Collection.objects.select_related('author', 'event').prefetch_related(
        'tags', 'photos__asset'
    )
    serializer_class = CollectionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('featured') == '1':
            qs = qs.filter(featured=True)
        if self.request.query_params.get('author'):
            qs = qs.filter(author_id=validated_uuid(self.request.query_params['author']))
        return qs

    @action(detail=True, methods=['post'])
    def photos(self, request, pk=None):
        with transaction.atomic():
            obj = Collection.objects.select_for_update().get(pk=self.get_object().pk)
            if not can_edit(request.user, obj) or obj.status not in [Status.DRAFT, Status.RETURNED]:
                raise PermissionDenied('只有作者或编辑可以修改草稿照片。')
            asset = get_object_or_404(
                Asset,
                pk=validated_uuid(request.data.get('asset_id')),
                owner=request.user,
                state=Asset.State.READY,
            )
            if not asset.content_type.startswith('image/'):
                raise ValidationError('作品中只能添加图片。')
            if obj.photos.filter(asset=asset).exists():
                raise ValidationError('这张图片已加入作品。')
            data = PhotoSerializer(data=request.data)
            data.is_valid(raise_exception=True)
            photo = Photo.objects.create(
                collection=obj,
                asset=asset,
                caption=data.validated_data['caption'],
                position=data.validated_data.get('position', obj.photos.count()),
                **{name: data.validated_data.get(name, '') for name in ['photographer', 'taken_at', 'camera_body', 'lens', 'shutter_speed', 'aperture', 'iso']},
            )
            services.audit(request.user, 'add_photo', obj)
        return Response(PhotoSerializer(photo).data, status=201)

    @action(detail=True, methods=['post'], url_path='remove-photo')
    def remove_photo(self, request, pk=None):
        obj = self.get_object()
        if not can_edit(request.user, obj) or obj.status not in [Status.DRAFT, Status.RETURNED]:
            raise PermissionDenied()
        photo = get_object_or_404(
            Photo, pk=validated_uuid(request.data.get('photo_id')), collection=obj
        )
        photo.delete()
        services.audit(request.user, 'remove_photo', obj)
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='update-photo')
    def update_photo(self, request, pk=None):
        obj = self.get_object()
        if not can_edit(request.user, obj) or obj.status not in [Status.DRAFT, Status.RETURNED]:
            raise PermissionDenied()
        photo = get_object_or_404(
            Photo, pk=validated_uuid(request.data.get('photo_id')), collection=obj
        )
        caption = str(request.data.get('caption', '')).strip()
        if not caption or len(caption) > 300:
            raise ValidationError('图片说明须为 1 至 300 字。')
        photo.caption = caption
        metadata = PhotoSerializer(photo, data=request.data, partial=True)
        metadata.is_valid(raise_exception=True)
        for name in ['photographer', 'taken_at', 'camera_body', 'lens', 'shutter_speed', 'aperture', 'iso']:
            if name in metadata.validated_data:
                setattr(photo, name, metadata.validated_data[name])
        if 'position' in request.data:
            try:
                photo.position = int(request.data['position'])
            except (ValueError, TypeError):
                raise ValidationError('图片顺序须为非负整数。')
            if photo.position < 0:
                raise ValidationError('图片顺序须为非负整数。')
        photo.save()
        services.audit(request.user, 'update_photo', obj)
        return Response(PhotoSerializer(photo).data)


class EventViewSet(EditorialViewSet):
    queryset = Event.objects.select_related('cover').prefetch_related('tags', 'photos__asset')
    serializer_class = EventSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        now = timezone.now()
        scope = self.request.query_params.get('when', '')
        if scope == 'upcoming':
            return qs.filter(starts_at__gte=now).order_by('starts_at')
        if scope == 'past':
            return qs.filter(starts_at__lt=now).order_by('-starts_at')
        # 默认把尚未开始的活动排在前面，已结束的随后。
        return qs.annotate(
            _past=Case(When(starts_at__lt=now, then=Value(1)), default=Value(0), output_field=IntegerField())
        ).order_by('_past', 'starts_at')

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        obj = self.get_object()
        if obj.is_demo:
            raise ValidationError('这是示例活动，不接受真实报名。')
        contact = str(request.data.get('contact', ''))
        note = str(request.data.get('note', ''))
        if len(contact) > 120 or len(note) > 500:
            raise ValidationError('联系方式或备注过长。')
        record = services.register(request.user, obj.pk, contact, note)
        return Response(RegistrationSerializer(record).data, status=201)

    @action(detail=True, methods=['post'], url_path='cancel-registration')
    def cancel(self, request, pk=None):
        require_member(request.user)
        services.cancel_registration(request.user, self.get_object())
        return Response({'ok': True})

    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        obj = self.get_object()
        if not can_edit(request.user, obj):
            raise PermissionDenied()
        return Response(
            RegistrationSerializer(
                obj.registrations.select_related('user__profile'), many=True
            ).data
        )


class DocumentViewSet(EditorialViewSet):
    queryset = Document.objects.prefetch_related('versions__asset', 'tags')
    serializer_class = DocumentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        year = self.request.query_params.get('year')
        if year:
            if not year.isdigit():
                raise ValidationError('年份无效。')
            qs = qs.filter(year=int(year))
        category = self.request.query_params.get('category')
        return qs.filter(category=category) if category else qs

    @action(detail=True, methods=['post'])
    def versions(self, request, pk=None):
        with transaction.atomic():
            obj = Document.objects.select_for_update().get(pk=self.get_object().pk)
            if not can_edit(request.user, obj) or obj.status not in [Status.DRAFT, Status.RETURNED]:
                raise PermissionDenied('请在草稿状态添加版本。')
            asset = get_object_or_404(
                Asset,
                pk=validated_uuid(request.data.get('asset_id')),
                owner=request.user,
                state=Asset.State.READY,
            )
            version = (obj.versions.aggregate(value=Max('version'))['value'] or 0) + 1
            DocumentVersion.objects.create(
                document=obj,
                asset=asset,
                version=version,
                note=str(request.data.get('note', ''))[:400],
            )
            services.audit(request.user, 'add_version', obj)
        return Response(self.get_serializer(obj).data, status=201)
