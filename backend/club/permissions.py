from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from .models import Status, Visibility


def is_member(user):
    return bool(
        user.is_authenticated
        and user.is_active
        and (user.is_staff or (hasattr(user, 'profile') and user.profile.is_member))
    )


def can_edit(user, obj):
    return bool(
        user.is_authenticated
        and (
            user.is_superuser
            or (is_member(user) and obj.owner_id == user.id)
            or user.has_perm(f'club.change_{obj._meta.model_name}')
        )
    )


def can_moderate(user, model):
    return bool(user.is_authenticated and user.has_perm(f'club.change_{model._meta.model_name}'))


def visible_queryset(queryset, user):
    readable = Q(status=Status.PUBLISHED, visibility=Visibility.PUBLIC)
    if is_member(user):
        readable |= Q(status=Status.PUBLISHED, visibility=Visibility.MEMBERS)
    if user.is_authenticated:
        readable |= Q(owner=user)
        if can_moderate(user, queryset.model):
            return queryset
    return queryset.filter(readable)


def require_member(user):
    if not is_member(user):
        raise PermissionDenied('该操作需要有效的协会成员身份。')
