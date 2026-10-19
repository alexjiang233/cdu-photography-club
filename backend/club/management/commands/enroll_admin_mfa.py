from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_totp.models import TOTPDevice


class Command(BaseCommand):
    help = 'Interactively enroll a staff TOTP authenticator. Do not save terminal output.'

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['username'], is_staff=True, is_active=True)
        except User.DoesNotExist:
            raise CommandError('未找到有效管理员账号。')
        device, created = TOTPDevice.objects.get_or_create(
            user=user, name='primary', defaults={'confirmed': False}
        )
        if device.confirmed:
            raise CommandError('该账号已绑定验证器；恢复与更换请由服务器管理员人工处理。')
        self.stdout.write('请在可信的验证器中添加下方 URI，不要分享或保存输出：')
        self.stdout.write(device.config_url)
        token = input('请输入验证器当前的六位验证码：').strip()
        if not device.verify_token(token):
            raise CommandError('验证码无效，未完成绑定。')
        device.confirmed = True
        device.save(update_fields=['confirmed'])
        self.stdout.write(self.style.SUCCESS('验证器已绑定。'))
