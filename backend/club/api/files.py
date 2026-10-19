from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from .. import services, storage
from ..models import Asset, Collection, Document, Event, SiteSettings
from ..permissions import can_edit, require_member, visible_queryset
from ..serializers import AssetSerializer
from ..uploads import ingest


class UploadView(APIView):
    def get(self, request):
        assets = Asset.objects.filter(
            owner=request.user, content_type__startswith='image/'
        ).order_by('-created_at')
        collection = request.query_params.get('collection')
        if collection:
            from .content import validated_uuid

            obj = get_object_or_404(Collection, pk=validated_uuid(collection))
            if not can_edit(request.user, obj):
                raise Http404()
            assets = assets.exclude(photos__collection_id=obj.pk)
        pagination = PageNumberPagination()
        page = pagination.paginate_queryset(assets, request)
        return pagination.get_paginated_response(AssetSerializer(page, many=True).data)

    def post(self, request):
        require_member(request.user)
        if 'file' not in request.FILES:
            raise ValidationError('请选择文件。')
        asset = ingest(request.user, request.FILES['file'])
        services.audit(request.user, 'upload', asset)
        return Response(AssetSerializer(asset).data, status=201)


class AssetStatusView(APIView):
    def get(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        if asset.owner_id != request.user.id and not request.user.has_perm('club.view_asset'):
            raise Http404()
        return Response(AssetSerializer(asset).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def asset_file(request, pk, variant):
    asset = get_object_or_404(Asset, pk=pk, state=Asset.State.READY)
    owned = request.user.is_authenticated and (
        asset.owner_id == request.user.id or request.user.has_perm('club.view_asset')
    )
    collections = visible_queryset(Collection.objects.filter(photos__asset=asset), request.user)
    events = visible_queryset(Event.objects.filter(cover=asset), request.user)
    documents = visible_queryset(Document.objects.filter(versions__asset=asset), request.user)
    logo = SiteSettings.objects.filter(logo=asset).exists()
    if variant in ['display', 'thumbnail']:
        if not (owned or collections.exists() or events.exists() or logo):
            raise Http404()
        key = asset.display_key if variant == 'display' else asset.thumbnail_key
        if not key:
            raise Http404()
        content_type = 'image/webp'
    elif variant == 'download':
        if not (owned or documents.exists()):
            raise Http404()
        key = asset.original_key
        content_type = asset.content_type
        services.audit(request.user, 'download', asset)
    else:
        raise Http404()
    try:
        response = FileResponse(
            storage.stream(key),
            content_type=content_type,
            as_attachment=variant == 'download',
            filename=asset.original_name if variant == 'download' else f'{asset.pk}.webp',
        )
    except FileNotFoundError:
        raise Http404()
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    if variant == 'download':
        response['Content-Security-Policy'] = "sandbox; default-src 'none'"
    return response
