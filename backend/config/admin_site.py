from django.conf import settings
from django.contrib.admin import AdminSite
from django_otp.admin import OTPAdminSite


class SecureAdminSite(AdminSite if settings.DEBUG else OTPAdminSite):
    site_header = '摄影协会 · 管理后台'
