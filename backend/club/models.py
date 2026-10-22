import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q


class Visibility(models.TextChoices):
    PUBLIC = 'public', '公开'
    MEMBERS = 'members', '协会成员'
    PRIVATE = 'private', '仅负责人'


class Status(models.TextChoices):
    DRAFT = 'draft', '草稿'
    PENDING = 'pending', '待审核'
    PUBLISHED = 'published', '已发布'
    RETURNED = 'returned', '退回修改'
    ARCHIVED = 'archived', '已归档'


class Timestamped(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Profile(Timestamped):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='profile',
    )
    display_name = models.CharField('署名', max_length=60)
    bio = models.TextField('简介', blank=True, max_length=2000)
    cohort = models.CharField('届别', max_length=20, blank=True)
    is_member = models.BooleanField('有效成员', default=False)
    is_public = models.BooleanField('公开主页', default=False)
    is_demo = models.BooleanField('示例资料', default=False)

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name = '成员档案'
        verbose_name_plural = verbose_name


class Tag(models.Model):
    name = models.CharField('标签', max_length=40, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = verbose_name


class Asset(Timestamped):
    class State(models.TextChoices):
        PROCESSING = 'processing', '处理中'
        READY = 'ready', '可用'
        REJECTED = 'rejected', '检查失败'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    original_name = models.CharField(max_length=240)
    original_key = models.CharField(max_length=300)
    display_key = models.CharField(max_length=300, blank=True)
    thumbnail_key = models.CharField(max_length=300, blank=True)
    content_type = models.CharField(max_length=80)
    size = models.PositiveBigIntegerField()
    checksum = models.CharField(max_length=64)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    state = models.CharField(max_length=20, choices=State.choices, default=State.PROCESSING)
    error = models.CharField(max_length=300, blank=True)
    photo_metadata = models.JSONField('可公开的拍摄参数', default=dict, blank=True)

    def __str__(self):
        return self.original_name

    class Meta:
        verbose_name = '文件'
        verbose_name_plural = verbose_name


class Editorial(Timestamped):
    title = models.CharField('标题', max_length=140)
    description = models.TextField('正文', blank=True, max_length=16000)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField('状态', max_length=20, choices=Status.choices, default=Status.DRAFT)
    visibility = models.CharField(
        '可见范围', max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    review_note = models.TextField('审核说明', blank=True, max_length=2000)
    is_demo = models.BooleanField('示例内容', default=False)
    tags = models.ManyToManyField(Tag, blank=True)
    published_at = models.DateTimeField('发布时间', null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        abstract = True


class Event(Editorial):
    starts_at = models.DateTimeField('开始时间')
    ends_at = models.DateTimeField('结束时间')
    registration_deadline = models.DateTimeField('报名截止时间')
    location = models.CharField('地点', max_length=160)
    capacity = models.PositiveIntegerField('人数上限', default=20)
    registration_open = models.BooleanField('开放报名', default=False)
    cover = models.ForeignKey(
        Asset, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.starts_at
            and self.registration_deadline
            and self.registration_deadline > self.starts_at
        ):
            raise ValidationError({'registration_deadline': '报名截止时间不能晚于活动开始。'})
        if self.cover_id and (
            self.cover.state != Asset.State.READY
            or not self.cover.content_type.startswith('image/')
        ):
            raise ValidationError({'cover': '请选择已处理完成的图片。'})

    class Meta:
        verbose_name = '活动'
        verbose_name_plural = verbose_name
        ordering = ['-starts_at']
        indexes = [models.Index(fields=['status', 'visibility', 'starts_at'])]
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__gt=models.F('starts_at')), name='event_end_after_start'
            ),
            models.CheckConstraint(condition=Q(capacity__gt=0), name='event_positive_capacity'),
        ]


class Collection(Editorial):
    code = models.CharField('档案编号', max_length=16, blank=True, default='', db_index=True)
    author = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name='collections', verbose_name='作者档案'
    )
    event = models.ForeignKey(
        Event,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='collections',
        verbose_name='关联活动',
    )
    featured = models.BooleanField('首页精选', default=False)
    is_placeholder = models.BooleanField('仅作排版占位', default=False)

    class Meta:
        verbose_name = '作品系列'
        verbose_name_plural = verbose_name
        ordering = ['-published_at', '-created_at']
        indexes = [models.Index(fields=['status', 'visibility', 'published_at'])]
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=~Q(code=''),
                name='unique_collection_code',
            )
        ]


class Photo(Timestamped):
    collection = models.ForeignKey(Collection, null=True, blank=True, on_delete=models.CASCADE, related_name='photos')
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE, related_name='photos', verbose_name='活动')
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='photos')
    caption = models.CharField('图片说明', max_length=300)
    position = models.PositiveIntegerField('排序', default=0)
    photographer = models.CharField('摄影署名', max_length=100, blank=True)
    taken_at = models.CharField('拍摄时间', max_length=50, blank=True, help_text='可手动补充；留空时读取相机原始时间，不推测时区。')
    camera_body = models.CharField('机身', max_length=120, blank=True)
    lens = models.CharField('镜头', max_length=160, blank=True)
    shutter_speed = models.CharField('快门', max_length=30, blank=True)
    aperture = models.CharField('光圈', max_length=30, blank=True)
    iso = models.CharField('ISO', max_length=30, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.asset_id and (
            self.asset.state != Asset.State.READY
            or not self.asset.content_type.startswith('image/')
        ):
            raise ValidationError({'asset': '作品只能关联已处理完成的图片。'})

    class Meta:
        ordering = ['position', 'created_at']
        constraints = [
            models.UniqueConstraint(fields=['collection', 'asset'], name='unique_collection_asset'),
            models.UniqueConstraint(fields=['event', 'asset'], name='unique_event_asset'),
            models.CheckConstraint(condition=(Q(collection__isnull=False, event__isnull=True) | Q(collection__isnull=True, event__isnull=False)), name='photo_one_target'),
        ]
        verbose_name = '照片'
        verbose_name_plural = verbose_name


class Registration(Timestamped):
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    contact = models.CharField('联系方式', max_length=120)
    note = models.CharField('备注', max_length=500, blank=True)
    cancelled = models.BooleanField('已取消', default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'user'], name='unique_event_registration')
        ]
        ordering = ['created_at']
        verbose_name = '报名记录'
        verbose_name_plural = verbose_name


class Document(Editorial):
    year = models.PositiveIntegerField('归档年份')
    category = models.CharField(
        '类别',
        max_length=40,
        choices=[
            ('tutorial', '摄影教程'),
            ('publication', '刊物与展览'),
            ('planning', '活动策划'),
            ('handover', '换届交接'),
            ('other', '其他资料'),
        ],
    )
    event = models.ForeignKey(
        Event, null=True, blank=True, on_delete=models.SET_NULL, related_name='documents'
    )

    class Meta:
        ordering = ['-year', '-updated_at']
        indexes = [
            models.Index(fields=['status', 'visibility', 'year']),
            models.Index(fields=['category', 'year']),
        ]
        verbose_name = '资料条目'
        verbose_name_plural = verbose_name


class DocumentVersion(Timestamped):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    version = models.PositiveIntegerField('版本号')
    note = models.CharField('版本说明', max_length=400, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.asset_id and self.asset.state != Asset.State.READY:
            raise ValidationError({'asset': '文件尚未通过处理。'})

    class Meta:
        ordering = ['-version']
        constraints = [
            models.UniqueConstraint(fields=['document', 'version'], name='unique_document_version')
        ]
        verbose_name = '文件版本'
        verbose_name_plural = verbose_name


class Comment(Timestamped):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    guest_name = models.CharField('访客昵称', max_length=40, blank=True)
    collection = models.ForeignKey(
        Collection, null=True, blank=True, on_delete=models.CASCADE, related_name='comments'
    )
    event = models.ForeignKey(
        Event, null=True, blank=True, on_delete=models.CASCADE, related_name='comments'
    )
    text = models.TextField('内容', max_length=2000)
    approved = models.BooleanField('审核通过', default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(collection__isnull=False, event__isnull=True)
                    | Q(collection__isnull=True, event__isnull=False)
                ),
                name='comment_one_target',
            )
        ]
        ordering = ['created_at']
        verbose_name = '讨论与提问'
        verbose_name_plural = verbose_name


class Notice(Timestamped):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    href = models.CharField(max_length=300, blank=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


class AuditLog(Timestamped):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=60)
    target_type = models.CharField(max_length=60)
    target_id = models.CharField(max_length=80)
    detail = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '操作审计'
        verbose_name_plural = verbose_name


class JoinApplication(Timestamped):
    """公开招新报名。只有管理员能查看联系方式。"""

    name = models.CharField('姓名', max_length=40)
    college = models.CharField('学院与专业', max_length=120)
    grade = models.CharField('年级', max_length=20)
    contact = models.CharField('联系方式', max_length=120)
    gear = models.CharField('常用器材', max_length=120, blank=True)
    portfolio = models.CharField('作品链接', max_length=300, blank=True)
    message = models.TextField('想拍什么', max_length=600, blank=True)
    handled = models.BooleanField('已处理', default=False)
    note = models.CharField('处理备注', max_length=300, blank=True)

    def __str__(self):
        return f'{self.name} · {self.college}'

    class Meta:
        ordering = ['-created_at']
        verbose_name = '入会申请'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['handled', '-created_at'])]


class Issue(Editorial):
    number = models.PositiveIntegerField('编排编号', unique=True)
    english_title = models.CharField('英文标题', max_length=140, blank=True)
    cover = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='+', verbose_name='封面照片')
    credits = models.CharField('编排署名', max_length=300, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.cover_id and (self.cover.state != Asset.State.READY or not self.cover.content_type.startswith('image/')):
            raise ValidationError({'cover': '请选择已处理完成的图片。'})

    def get_absolute_url(self):
        return f'/field-journal/issues/{self.pk}'

    class Meta:
        verbose_name = '展览编排'
        verbose_name_plural = verbose_name
        ordering = ['-number']


class IssueBlock(Timestamped):
    class Layout(models.TextChoices):
        WIDE = 'wide', '大幅照片'
        PAIR = 'pair', '并列照片（连续两项组成一组）'
        INSET = 'inset', '留白照片'
        TEXT = 'text', '文字段落'
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='blocks')
    position = models.PositiveIntegerField('顺序', default=0)
    layout = models.CharField('版式', max_length=10, choices=Layout.choices, default=Layout.WIDE)
    image = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='照片')
    heading = models.CharField('标题或照片名', max_length=140, blank=True)
    text = models.TextField('文字或图注', max_length=6000, blank=True)
    credit = models.CharField('摄影署名', max_length=100, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.layout != self.Layout.TEXT and not self.image_id:
            raise ValidationError({'image': '照片版式需要选择图片。'})
        if self.layout == self.Layout.TEXT and not self.text.strip():
            raise ValidationError({'text': '文字段落不能为空。'})
        if self.image_id and (self.image.state != Asset.State.READY or not self.image.content_type.startswith('image/')):
            raise ValidationError({'image': '请选择已处理完成的图片。'})

    class Meta:
        verbose_name = '展览内容'
        verbose_name_plural = verbose_name
        ordering = ['position', 'created_at']


class SiteSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    name = models.CharField('协会名称', max_length=80, default='摄影协会')
    introduction = models.TextField('协会介绍', default='用影像记录日常，在交流中发现新的视角。')
    join_instructions = models.TextField('加入方式', blank=True)
    contact_email = models.EmailField('联系邮箱', blank=True)
    logo = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL)
    contact_qr = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name='联系二维码')

    class Meta:
        verbose_name = '网站设置'
        verbose_name_plural = verbose_name
