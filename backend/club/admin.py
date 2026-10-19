from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.html import format_html
from rest_framework.exceptions import APIException
from .models import (
    Asset,
    AuditLog,
    Collection,
    Comment,
    Document,
    DocumentVersion,
    Event,
    Notice,
    Photo,
    Profile,
    Registration,
    SiteSettings,
    Status,
    Tag,
)
from . import services
from .uploads import ingest

admin.site.site_header = '摄影协会 · 管理后台'
admin.site.site_title = '摄影协会'
admin.site.index_title = '内容、成员与档案'


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    autocomplete_fields = ['asset']


class VersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    autocomplete_fields = ['asset']


class EditorialAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'visibility', 'owner', 'updated_at']
    list_filter = ['status', 'visibility', 'is_demo']
    search_fields = ['title', 'description']
    filter_horizontal = ['tags']
    readonly_fields = ['owner', 'status', 'published_at', 'review_note']
    actions = ['submit', 'publish', 'return_content', 'archive', 'revise']

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in [Status.PENDING, Status.PUBLISHED, Status.ARCHIVED]:
            return [f.name for f in self.model._meta.fields] + ['tags']
        return super().get_readonly_fields(request, obj)

    def get_inline_instances(self, request, obj=None):
        if obj and obj.status in [Status.PENDING, Status.PUBLISHED, Status.ARCHIVED]:
            return []
        return super().get_inline_instances(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
        services.audit(request.user, 'admin_update' if change else 'admin_create', obj)

    def run_workflow(self, request, queryset, action, note=''):
        count = 0
        for obj in queryset:
            try:
                services.transition(request.user, obj, action, note)
                count += 1
            except APIException as exc:
                self.message_user(request, f'{obj.title}：{exc.detail}', messages.ERROR)
        if count:
            self.message_user(request, f'已处理 {count} 条内容。', messages.SUCCESS)

    @admin.action(description='提交审核')
    def submit(self, request, queryset):
        self.run_workflow(request, queryset, 'submit')

    @admin.action(description='审核通过并发布')
    def publish(self, request, queryset):
        self.run_workflow(request, queryset, 'publish')

    @admin.action(description='退回修改')
    def return_content(self, request, queryset):
        self.run_workflow(request, queryset, 'return', '请联系编辑确认修改意见，修改后再次提交。')

    @admin.action(description='归档并撤下公开内容')
    def archive(self, request, queryset):
        self.run_workflow(request, queryset, 'archive')

    @admin.action(description='撤回为草稿，准备修订')
    def revise(self, request, queryset):
        self.run_workflow(request, queryset, 'revise')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Collection)
class CollectionAdmin(EditorialAdmin):
    inlines = [PhotoInline]
    autocomplete_fields = ['author', 'event']


@admin.register(Event)
class EventAdmin(EditorialAdmin):
    autocomplete_fields = ['cover']


@admin.register(Document)
class DocumentAdmin(EditorialAdmin):
    inlines = [VersionInline]
    list_filter = EditorialAdmin.list_filter + ['year', 'category']
    autocomplete_fields = ['event']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'cohort', 'is_member', 'is_public', 'is_demo']
    list_filter = ['is_member', 'is_public', 'cohort']
    search_fields = ['display_name', 'user__username']


class UploadForm(forms.ModelForm):
    upload = forms.FileField(
        label='上传图片或资料', help_text='支持 JPG、PNG、WebP、PDF、UTF-8 文本。单文件最大 25 MB。'
    )

    class Meta:
        model = Asset
        fields = []

    def clean_upload(self):
        uploaded = self.cleaned_data['upload']
        if uploaded.size > 25 * 1024 * 1024:
            raise forms.ValidationError('文件超过 25 MB。')
        return uploaded


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'owner', 'content_type', 'size', 'state', 'created_at']
    search_fields = ['original_name']
    list_filter = ['state', 'content_type']
    form = UploadForm

    def get_fields(self, request, obj=None):
        return (
            [
                'original_name',
                'owner',
                'content_type',
                'size',
                'state',
                'error',
                'width',
                'height',
                'checksum',
            ]
            if obj
            else ['upload']
        )

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj) if obj else []

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            return super().get_form(request, obj, **kwargs)

        class RequestUploadForm(UploadForm):
            def clean(self):
                data = super().clean()
                if data.get('upload'):
                    try:
                        self.ingested = ingest(request.user, data['upload'])
                    except APIException as exc:
                        raise forms.ValidationError(str(exc.detail))
                return data

        kwargs['form'] = RequestUploadForm
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            created = form.ingested
            for field in Asset._meta.concrete_fields:
                setattr(obj, field.attname, getattr(created, field.attname))
            obj._state = created._state
            services.audit(request.user, 'admin_upload', obj)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'cancelled', 'created_at']
    list_filter = ['event', 'cancelled']
    search_fields = ['event__title', 'user__username']
    readonly_fields = [f.name for f in Registration._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['text', 'author', 'approved', 'created_at']
    list_filter = ['approved']
    readonly_fields = ['author', 'collection', 'event', 'text']
    actions = ['approve', 'hide']

    def has_add_permission(self, request):
        return False

    @admin.action(description='通过选中讨论')
    def approve(self, request, queryset):
        for obj in queryset:
            obj.approved = True
            obj.save(update_fields=['approved', 'updated_at'])
            services.audit(request.user, 'approve_comment', obj)

    @admin.action(description='隐藏选中讨论')
    def hide(self, request, queryset):
        for obj in queryset:
            obj.approved = False
            obj.save(update_fields=['approved', 'updated_at'])
            services.audit(request.user, 'hide_comment', obj)


@admin.register(AuditLog)
class AuditAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'actor', 'action', 'target_type', 'target_id']
    list_filter = ['action', 'target_type']
    search_fields = ['target_id', 'detail']
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('club.view_auditlog')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteSettings)
class SettingsAdmin(admin.ModelAdmin):
    autocomplete_fields = ['logo']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Tag)
