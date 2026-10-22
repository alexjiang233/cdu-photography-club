from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from club.models import Collection, Issue, IssueBlock
from club.services import transition


class Command(BaseCommand):
    help = '从现有公开照片编排创刊号；已有第一期时不覆盖。'
    def add_arguments(self, parser):
        parser.add_argument('--collection', required=True)
    @transaction.atomic
    def handle(self, *args, **options):
        if Issue.objects.filter(number=1).exists():
            self.stdout.write('第一期已存在，未作修改。')
            return
        source = Collection.objects.get(pk=options['collection'], status='published', visibility='public')
        photos = list(source.photos.select_related('asset').order_by('position', 'created_at')[:4])
        if len(photos) != 4:
            raise CommandError('创刊号需要已有的四张公开照片。')
        editor = source.owner.__class__.objects.filter(is_superuser=True, is_active=True).first()
        if not editor:
            raise CommandError('请先设置编辑账号。')
        issue = Issue.objects.create(number=1, title='入夜以后', english_title='After dark',
            description='建筑、城市与星空。\n从现有影像中选出四张，作为社刊的第一期。',
            credits='选片与编排：成都大学摄影协会', cover=photos[1].asset, owner=editor)
        for position, (photo, layout) in enumerate([(photos[1], 'wide'), (photos[0], 'inset'), (photos[2], 'pair'), (photos[3], 'pair')]):
            IssueBlock.objects.create(issue=issue, position=position, layout=layout, image=photo.asset, heading=photo.caption)
        transition(editor, issue, 'submit')
        transition(editor, issue, 'publish')
        self.stdout.write(self.style.SUCCESS(f'创刊号已编排：{issue.pk}'))
