from django.conf import settings
from django.contrib.admin import AdminSite
from django_otp.admin import OTPAdminSite


class SecureAdminSite(AdminSite if settings.DEBUG else OTPAdminSite):
    site_header = '摄影协会 · 管理后台'

    def get_app_list(self, request, app_label=None):
        apps = super().get_app_list(request, app_label)
        for app in apps:
            if app['app_label'] == 'otp_totp':
                app['name'] = '账号安全'
                for model in app['models']:
                    if model['object_name'] == 'TOTPDevice':
                        model['name'] = '管理员验证器'
        return apps
