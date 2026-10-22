from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django_otp.plugins.otp_totp.models import TOTPDevice


@override_settings(DEBUG=True)
class OTPTranslationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('translation-admin', password='test-only-password')
        self.client.force_login(self.user)

    def test_navigation_and_add_form_are_translated_and_keep_configuration(self):
        response = self.client.get('/admin/')
        self.assertContains(response, '账号安全')
        self.assertContains(response, '管理员验证器')
        response = self.client.get('/admin/otp_totp/totpdevice/add/')
        for text in ['所属管理员', '设备名称', '验证密钥', '验证码更新间隔', '时钟状态', '失败重试限制', '本地预览无需配置']:
            self.assertContains(response, text)
        self.assertContains(response, 'name="key"')
        self.assertContains(response, 'name="step"')
        self.assertNotContains(response, 'A hex-encoded secret key')

    def test_existing_configuration_and_sensitive_data_setting_are_preserved(self):
        device = TOTPDevice.objects.create(user=self.user, name='我的手机', confirmed=True)
        response = self.client.get(f'/admin/otp_totp/totpdevice/{device.pk}/change/')
        self.assertContains(response, '我的手机')
        self.assertContains(response, 'name="step"')
        device.refresh_from_db()
        self.assertTrue(device.confirmed)
        with override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=True):
            response = self.client.get(f'/admin/otp_totp/totpdevice/{device.pk}/change/')
            self.assertNotContains(response, 'name="key"')
            self.assertEqual(self.client.get(f'/admin/otp_totp/totpdevice/{device.pk}/config/').status_code, 403)

    def test_qr_binding_page_is_chinese(self):
        device = TOTPDevice.objects.create(user=self.user, name='手机')
        response = self.client.get(f'/admin/otp_totp/totpdevice/{device.pk}/config/')
        self.assertContains(response, '使用手机验证器扫描')
        self.assertNotContains(response, 'Install')
