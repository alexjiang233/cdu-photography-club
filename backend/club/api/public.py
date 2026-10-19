from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import Collection, Document, Event, Notice, Profile, Registration, SiteSettings, Tag
from ..serializers import CollectionSerializer, ProfileSerializer
from .auth import identity


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
            'logo_url': f'/api/assets/{site.logo_id}/display/?v={site.logo.checksum[:12]}'
            if site.logo_id
            else None,
            'tags': list(Tag.objects.values_list('name', flat=True)),
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
