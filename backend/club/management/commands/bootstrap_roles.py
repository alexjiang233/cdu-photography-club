from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Create repeatable least-privilege staff roles without creating users.'

    def handle(self, *args, **options):
        roles = {
            '作品编辑': {
                'collection': ['add', 'view', 'change'],
                'photo': ['add', 'view', 'change', 'delete'],
                'asset': ['add', 'view'],
                'profile': ['view'],
                'event': ['view'],
                'tag': ['add', 'view', 'change'],
                'comment': ['view', 'change'],
            },
            '活动负责人': {
                'event': ['add', 'view', 'change'],
                'registration': ['view'],
                'asset': ['add', 'view'],
                'tag': ['add', 'view'],
            },
            '资料管理员': {
                'document': ['add', 'view', 'change'],
                'documentversion': ['add', 'view', 'change'],
                'asset': ['add', 'view'],
                'tag': ['add', 'view'],
                'event': ['view'],
            },
        }
        for name, rules in roles.items():
            group, _ = Group.objects.get_or_create(name=name)
            permissions = []
            for model, actions in rules.items():
                permissions.extend(
                    Permission.objects.filter(
                        content_type__app_label='club',
                        codename__in=[f'{action}_{model}' for action in actions],
                    )
                )
            group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS('管理角色已配置；有效成员身份请在成员档案中设置。'))
