"""Idempotent illustrative content; creates no usable credentials."""

import hashlib
from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from club.models import (
    Asset,
    Collection,
    Document,
    DocumentVersion,
    Event,
    Photo,
    Profile,
    SiteSettings,
    Status,
    Tag,
)
from club import storage
from club.tasks import process_image


class Command(BaseCommand):
    help = 'Load explicitly labelled demo material; no real association claims.'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username='demo-content', defaults={'is_active': False}
        )
        if created:
            user.set_unusable_password()
            user.save()
        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={
                'display_name': '示例作者',
                'bio': '用于展示作品排版的示例档案，等待摄影协会替换为真实作品。',
                'is_public': True,
                'is_demo': True,
            },
        )
        SiteSettings.objects.get_or_create(pk=1)
        tags = {
            name: Tag.objects.get_or_create(name=name)[0]
            for name in ['自然', '城市', '日常', '人像', '摄影基础']
        }
        samples = [
            ('山色之间', 'nature', '自然'),
            ('城市的呼吸', 'city', '城市'),
            ('缓慢的日常', 'daily', '日常'),
            ('光经过的地方', 'light', '日常'),
            ('远处与此刻', 'water', '自然'),
            ('留白的练习', 'architecture', '城市'),
        ]
        assets = []
        for title, key, tag in samples:
            path = settings.BASE_DIR.parent / 'demo-assets' / f'{key}.jpg'
            if not path.exists():
                self.stdout.write(f'跳过缺失图片：{path.name}')
                continue
            data = path.read_bytes()
            checksum = hashlib.sha256(data).hexdigest()
            asset = Asset.objects.filter(owner=user, checksum=checksum).first()
            if not asset:
                stored = f'originals/demo-{key}.jpg'
                storage.put(stored, data, 'image/jpeg')
                asset = Asset.objects.create(
                    owner=user,
                    original_name=f'{key}.jpg',
                    original_key=stored,
                    content_type='image/jpeg',
                    size=len(data),
                    checksum=checksum,
                )
                process_image(str(asset.pk))
            assets.append(asset)
            collection, _ = Collection.objects.get_or_create(
                title=title,
                is_demo=True,
                defaults={
                    'owner': user,
                    'author': profile,
                    'description': '示例作品系列。图片仅用于演示网站排版，不代表摄影协会或成员的实际创作。正式使用前请替换为获得授权的作品。',
                    'status': Status.PUBLISHED,
                    'published_at': timezone.now(),
                    'featured': True,
                },
            )
            collection.tags.add(tags[tag])
            Photo.objects.get_or_create(
                collection=collection, asset=asset, defaults={'caption': f'{title} · 排版示例图片'}
            )
        now = timezone.now()
        for i, title in enumerate(
            ['周末走走：校园光影外拍', '一起看照片：作品交流会', '从曝光开始：摄影入门']
        ):
            Event.objects.get_or_create(
                title=title,
                is_demo=True,
                defaults={
                    'owner': user,
                    'description': '示例活动，用于展示活动详情和报名界面，不接受真实报名。时间、地点均为演示内容。',
                    'status': Status.PUBLISHED,
                    'published_at': now,
                    'starts_at': now + timedelta(days=7 + i * 7),
                    'ends_at': now + timedelta(days=7 + i * 7, hours=2),
                    'registration_deadline': now + timedelta(days=6 + i * 7),
                    'location': '地点待协会发布',
                    'capacity': 20,
                    'registration_open': False,
                    'cover': assets[i % len(assets)] if assets else None,
                },
            )
        document, _ = Document.objects.get_or_create(
            title='摄影入门与资料归档说明',
            is_demo=True,
            defaults={
                'owner': user,
                'description': '示例资料，展示分类、年份、文件版本与下载。',
                'status': Status.PUBLISHED,
                'published_at': now,
                'year': now.year,
                'category': 'tutorial',
            },
        )
        if not document.versions.exists():
            data = '摄影协会网站示例资料\n\n这里用于存放摄影教程、活动策划、刊物与换届交接文件。\n正式资料请由管理员上传。\n'.encode()
            key = 'originals/demo-guide.txt'
            storage.put(key, data, 'text/plain')
            asset = Asset.objects.create(
                owner=user,
                original_name='示例资料说明.txt',
                original_key=key,
                content_type='text/plain',
                size=len(data),
                checksum=hashlib.sha256(data).hexdigest(),
                state=Asset.State.READY,
            )
            DocumentVersion.objects.create(
                document=document, asset=asset, version=1, note='初始示例版本'
            )
        self.stdout.write(self.style.SUCCESS('示例内容已载入。未创建任何可登录的示例账号。'))
