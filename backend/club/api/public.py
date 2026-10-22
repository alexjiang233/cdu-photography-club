from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from ..models import (
    Collection,
    Document,
    Event,
    JoinApplication,
    Notice,
    Photo,
    Profile,
    Registration,
    SiteSettings,
    Tag,
)
from ..serializers import CollectionSerializer, JoinApplicationSerializer, ProfileSerializer
from .auth import identity


@api_view(['GET'])
@permission_classes([AllowAny])
def csrf(request):
    from django.middleware.csrf import get_token

    return Response({'csrf_token': get_token(request)})


def public_stats():
    published = {'status': 'published', 'visibility': 'public'}
    return {
        'collections': Collection.objects.filter(**published).count(),
        'photos': Photo.objects.filter(Q(collection__status='published', collection__visibility='public') | Q(event__status='published', event__visibility='public')).count(),
        'events': Event.objects.filter(**published).count(),
        'documents': Document.objects.filter(**published).count(),
        'members': Profile.objects.filter(is_public=True).count(),
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def site_info(request):
    site, _ = SiteSettings.objects.get_or_create(pk=1)
    return Response(
        {
            'name': site.name,
            'introduction': site.introduction,
            'join_instructions': site.join_instructions,
            'contact_email': site.contact_email,
            'contact_qr_url': f'/api/assets/{site.contact_qr_id}/display/?v={site.contact_qr.checksum[:12]}' if site.contact_qr_id else None,
            'logo_url': f'/api/assets/{site.logo_id}/display/?v={site.logo.checksum[:12]}'
            if site.logo_id
            else None,
            'tags': list(Tag.objects.values_list('name', flat=True)),
            'stats': public_stats(),
            'has_demo': any(
                model.objects.filter(is_demo=True, status='published', visibility='public').exists()
                for model in [Collection, Event, Document]
            ),
        }
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def members(request):
    return Response(
        ProfileSerializer(
            Profile.objects.filter(is_public=True).order_by('display_name')[:200], many=True
        ).data
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def member_detail(request, pk):
    profile = get_object_or_404(Profile, pk=pk, is_public=True)
    return Response(ProfileSerializer(profile).data)


class DashboardView(APIView):
    def get(self, request):
        user = request.user
        data = {
            'identity': identity(user),
            'registrations': [],
            'notices': list(
                Notice.objects.filter(recipient=user).values(
                    'id', 'text', 'href', 'read', 'created_at'
                )[:30]
            ),
            'collections': [],
        }
        data['registrations'] = [
            {
                'id': str(item.pk),
                'event_id': str(item.event_id),
                'title': item.event.title,
                'starts_at': item.event.starts_at,
                'cancelled': item.cancelled,
            }
            for item in Registration.objects.filter(user=user)
            .select_related('event')
            .order_by('-created_at')[:50]
        ]
        data['collections'] = CollectionSerializer(
            Collection.objects.filter(owner=user)
            .select_related('author')
            .prefetch_related('photos__asset', 'tags'),
            many=True,
            context={'request': request},
        ).data
        return Response(data)

    def post(self, request):
        Notice.objects.filter(recipient=request.user, read=False).update(read=True)
        return Response({'ok': True})


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    return Response({'status': 'ok'})


class JoinThrottle(ScopedRateThrottle):
    scope = 'join'


class JoinApplicationView(APIView):
    """公开招新报名；联系方式只进入后台，不对外返回。"""

    permission_classes = [AllowAny]
    throttle_classes = [JoinThrottle]

    def post(self, request):
        # 隐藏字段用于挡机器人：填了就当成功，但不入库。
        if str(request.data.get('website', '')).strip():
            return Response({'detail': '已收到。'}, status=status.HTTP_201_CREATED)
        serializer = JoinApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        return Response(
            {
                'detail': '已收到。负责人会在一周内联系你。',
                'id': str(application.pk),
            },
            status=status.HTTP_201_CREATED,
        )
