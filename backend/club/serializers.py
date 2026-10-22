from django.db.models import Max
from rest_framework import serializers
from .models import (
    Asset,
    Collection,
    Comment,
    Document,
    DocumentVersion,
    Event,
    JoinApplication,
    Photo,
    Profile,
    Registration,
    Tag,
)
from .permissions import can_edit, is_member


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'display_name', 'bio', 'cohort', 'is_public', 'is_demo']


class ProfileUpdateSerializer(ProfileSerializer):
    class Meta(ProfileSerializer.Meta):
        read_only_fields = ['id', 'is_demo']


class AssetSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    def get_thumbnail_url(self, obj):
        return (
            f'/api/assets/{obj.pk}/thumbnail/?v={obj.checksum[:12]}' if obj.thumbnail_key else None
        )

    class Meta:
        model = Asset
        fields = [
            'id',
            'original_name',
            'content_type',
            'size',
            'width',
            'height',
            'state',
            'error',
            'thumbnail_url',
        ]
        read_only_fields = fields


class PhotoSerializer(serializers.ModelSerializer):
    shooting = serializers.SerializerMethodField()
    asset_id = serializers.UUIDField()
    display_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    width = serializers.IntegerField(source='asset.width', read_only=True)
    height = serializers.IntegerField(source='asset.height', read_only=True)

    class Meta:
        model = Photo
        fields = [
            'id',
            'asset_id',
            'caption',
            'position',
            'display_url',
            'thumbnail_url',
            'width',
            'height',
            'photographer', 'taken_at', 'camera_body', 'lens', 'shutter_speed', 'aperture', 'iso', 'shooting',
        ]
        read_only_fields = ['id']

    def get_shooting(self, obj):
        fields = ['taken_at', 'camera_body', 'lens', 'shutter_speed', 'aperture', 'iso', 'focal_length']
        data = {k: obj.asset.photo_metadata[k] for k in fields if obj.asset.photo_metadata.get(k)}
        for name in fields:
            manual = getattr(obj, name, '')
            if manual:
                data[name] = manual
        data['photographer'] = obj.photographer
        data['time_source'] = 'manual' if obj.taken_at else 'exif'
        return data

    def get_display_url(self, obj):
        return (
            f'/api/assets/{obj.asset_id}/display/?v={obj.asset.checksum[:12]}'
            if obj.asset.display_key
            else None
        )

    def get_thumbnail_url(self, obj):
        return (
            f'/api/assets/{obj.asset_id}/thumbnail/?v={obj.asset.checksum[:12]}'
            if obj.asset.thumbnail_key
            else None
        )


class EditorialSerializer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(
        slug_field='name', queryset=Tag.objects.all(), many=True, required=False
    )
    editable = serializers.SerializerMethodField()
    review_note = serializers.SerializerMethodField()

    def get_editable(self, obj):
        return can_edit(self.context['request'].user, obj)

    def get_review_note(self, obj):
        return obj.review_note if self.get_editable(obj) else ''

    def validate(self, data):
        if self.instance and self.instance.status in ['published', 'archived', 'pending']:
            raise serializers.ValidationError(
                '当前内容已进入审核或发布流程，请先由编辑退回草稿再修改。'
            )
        return data


class CollectionSerializer(EditorialSerializer):
    author = serializers.SerializerMethodField()
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = [
            'id',
            'code',
            'title',
            'description',
            'author',
            'event',
            'photos',
            'tags',
            'status',
            'visibility',
            'featured',
            'is_placeholder',
            'is_demo',
            'published_at',
            'created_at',
            'editable',
            'review_note',
        ]
        read_only_fields = ['code', 'status', 'featured', 'is_demo', 'published_at', 'created_at']

    def get_author(self, obj):
        data = ProfileSerializer(obj.author).data
        if not obj.author.is_public and not can_edit(self.context['request'].user, obj):
            data['bio'] = ''
            data['cohort'] = ''
        return data

    def validate_event(self, event):
        if event:
            from .permissions import visible_queryset

            if (
                not visible_queryset(Event.objects.all(), self.context['request'].user)
                .filter(pk=event.pk)
                .exists()
            ):
                raise serializers.ValidationError('无法关联该活动。')
        return event


class EventSerializer(EditorialSerializer):
    photos = PhotoSerializer(many=True, read_only=True)
    registration_count = serializers.SerializerMethodField()
    my_registration = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'description',
            'starts_at',
            'ends_at',
            'registration_deadline',
            'location',
            'capacity',
            'registration_open',
            'registration_count',
            'my_registration',
            'cover_url',
            'photos',
            'tags',
            'status',
            'visibility',
            'is_demo',
            'editable',
            'review_note',
        ]
        read_only_fields = ['status', 'is_demo']

    def get_registration_count(self, obj):
        return obj.registrations.filter(cancelled=False).count()

    def get_my_registration(self, obj):
        user = self.context['request'].user
        return (
            obj.registrations.filter(user=user, cancelled=False).exists()
            if user.is_authenticated
            else False
        )

    def get_cover_url(self, obj):
        return (
            f'/api/assets/{obj.cover_id}/display/?v={obj.cover.checksum[:12]}'
            if obj.cover_id
            else None
        )

    def validate(self, data):
        data = super().validate(data)
        start = data.get('starts_at', getattr(self.instance, 'starts_at', None))
        end = data.get('ends_at', getattr(self.instance, 'ends_at', None))
        deadline = data.get(
            'registration_deadline', getattr(self.instance, 'registration_deadline', None)
        )
        if start and end and end <= start:
            raise serializers.ValidationError({'ends_at': '结束时间须晚于开始时间。'})
        if deadline and start and deadline > start:
            raise serializers.ValidationError(
                {'registration_deadline': '报名截止时间不能晚于活动开始。'}
            )
        if data.get('capacity', getattr(self.instance, 'capacity', 1)) < 1:
            raise serializers.ValidationError({'capacity': '人数须大于 0。'})
        return data


class DocumentVersionSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(source='asset.original_name', read_only=True)
    size = serializers.IntegerField(source='asset.size', read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVersion
        fields = ['id', 'version', 'note', 'filename', 'size', 'download_url', 'created_at']

    def get_download_url(self, obj):
        return f'/api/assets/{obj.asset_id}/download/'


class DocumentSerializer(EditorialSerializer):
    versions = DocumentVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'description',
            'year',
            'category',
            'event',
            'tags',
            'status',
            'visibility',
            'is_demo',
            'versions',
            'editable',
            'review_note',
            'updated_at',
        ]
        read_only_fields = ['status', 'is_demo', 'updated_at']

    def validate_year(self, value):
        if value < 1900 or value > 2200:
            raise serializers.ValidationError('请填写有效年份。')
        return value

    def validate_event(self, value):
        if value:
            from .permissions import visible_queryset

            if (
                not visible_queryset(Event.objects.all(), self.context['request'].user)
                .filter(pk=value.pk)
                .exists()
            ):
                raise serializers.ValidationError('无法关联该活动。')
        return value


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'text', 'guest_name', 'author_name', 'approved', 'created_at']
        read_only_fields = ['id', 'author_name', 'approved', 'created_at']

    def get_author_name(self, obj):
        if not obj.author_id:
            return obj.guest_name or '访客'
        return obj.author.profile.display_name if hasattr(obj.author, 'profile') else '协会成员'


class RegistrationSerializer(serializers.ModelSerializer):
    member = serializers.SerializerMethodField()

    class Meta:
        model = Registration
        fields = ['id', 'event', 'contact', 'note', 'cancelled', 'member', 'created_at']

    def get_member(self, obj):
        return obj.user.profile.display_name if hasattr(obj.user, 'profile') else obj.user.username


class JoinApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JoinApplication
        fields = ['name', 'college', 'grade', 'contact', 'gear', 'portfolio', 'message']
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False, 'max_length': 40},
            'college': {'required': True, 'allow_blank': False, 'max_length': 120},
            'grade': {'required': True, 'allow_blank': False, 'max_length': 20},
            'contact': {'required': True, 'allow_blank': False, 'max_length': 120},
            'gear': {'required': False, 'allow_blank': True, 'max_length': 120},
            'portfolio': {'required': False, 'allow_blank': True, 'max_length': 300},
            'message': {'required': False, 'allow_blank': True, 'max_length': 600},
        }

    def validate(self, data):
        for field in ['name', 'college', 'grade', 'contact']:
            if not str(data.get(field, '')).strip():
                raise serializers.ValidationError({field: '这一项需要填写。'})
        data['name'] = data['name'].strip()
        data['college'] = data['college'].strip()
        data['grade'] = data['grade'].strip()
        data['contact'] = data['contact'].strip()
        return data
