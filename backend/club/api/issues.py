from rest_framework import serializers, viewsets
from rest_framework.permissions import AllowAny
from ..models import Issue, IssueBlock, Status, Visibility
from ..permissions import can_edit


def image_data(asset):
    if not asset:
        return None
    return {
        'id': str(asset.pk),
        'display_url': f'/api/assets/{asset.pk}/display/?v={asset.checksum[:12]}',
        'width': asset.width, 'height': asset.height,
    }


class IssueBlockSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    def get_image(self, obj):
        return image_data(obj.image)
    class Meta:
        model = IssueBlock
        fields = ['id', 'position', 'layout', 'heading', 'text', 'credit', 'image']


class IssueSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    blocks = IssueBlockSerializer(many=True, read_only=True)
    def get_cover(self, obj):
        return image_data(obj.cover)
    class Meta:
        model = Issue
        fields = ['id', 'number', 'title', 'english_title', 'description', 'credits', 'cover', 'blocks', 'published_at', 'status']


class IssueViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = IssueSerializer
    lookup_value_regex = '[0-9a-fA-F-]{36}'
    queryset = Issue.objects.select_related('cover').prefetch_related('blocks__image')
    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'retrieve' and self.request.query_params.get('preview') == '1':
            if self.request.user.is_staff and self.request.user.has_perm('club.change_issue'):
                return qs
        return qs.filter(status=Status.PUBLISHED, visibility=Visibility.PUBLIC)
