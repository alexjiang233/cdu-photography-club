"""Chinese labels for the existing OTP plugin, without changing verification rules."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django_otp.plugins.otp_totp.models import TOTPDevice


class ChineseTOTPAdmin(TOTPDeviceAdmin):
    change_form_template = 'admin/totp_change_form.html'
    readonly_fields = ['created_time', 'last_used_time', 'qrcode_link']
    list_display = ['account', 'device_name', 'created_time', 'last_used_time', 'enabled']
    search_help_text = '按管理员账号或邮箱搜索。'

    labels = {
        'user': ('所属管理员', '选择要绑定手机验证器的账号。'),
        'name': ('设备名称', '用于辨认设备，例如“我的手机”。'),
        'confirmed': ('设备已启用', '表示设备已准备好用于登录验证；请在完成验证器绑定后启用。'),
        'key': ('验证密钥', '系统已随机生成。用于与手机验证器配对，请妥善保管，通常无需修改。'),
        'step': ('验证码更新间隔（秒）', '默认30秒，需与手机验证器一致，通常无需修改。'),
        't0': ('计时起点', '默认0，表示标准计时起点，通常无需修改。'),
        'digits': ('验证码位数', '通常为6位，需与手机验证器一致。'),
        'tolerance': ('允许的时间误差', '单位为更新周期；默认1，允许前后各一个周期的误差。'),
        'drift': ('时钟偏移', '系统记录的设备时钟偏差，单位为更新周期，通常无需手动修改。'),
        'throttling_failure_timestamp': ('最近验证失败时间', '用于控制连续输错验证码后的重试频率。'),
        'throttling_failure_count': ('连续验证失败次数', '系统维护的失败计数，通常无需手动修改。'),
    }

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for name, (label, help_text) in self.labels.items():
            if name in form.base_fields:
                form.base_fields[name].label = label
                form.base_fields[name].help_text = help_text
        return form

    def get_fieldsets(self, request, obj=None):
        titles = {'Identity': '绑定账号与设备', 'Timestamps': '使用记录',
                  'Configuration': '验证码配置', 'State': '时钟状态', 'Throttling': '失败重试限制'}
        result = []
        for title, options in super().get_fieldsets(request, obj):
            options = dict(options)
            options['fields'] = [
                {'created_at': 'created_time', 'last_used_at': 'last_used_time'}.get(f, f)
                for f in options['fields']
            ]
            if title == 'Configuration':
                options['description'] = '以下参数已有默认值。普通绑定通常无需调整；错误配置可能导致验证码无法使用。'
            result.append((titles.get(title, title), options))
        return result

    @admin.display(description='创建时间', ordering='created_at')
    def created_time(self, obj):
        return obj.created_at

    @admin.display(description='所属管理员', ordering='user__username')
    def account(self, obj):
        return obj.user

    @admin.display(description='设备名称', ordering='name')
    def device_name(self, obj):
        return obj.name

    @admin.display(description='已启用', boolean=True, ordering='confirmed')
    def enabled(self, obj):
        return obj.confirmed

    @admin.display(description='最近使用时间', ordering='last_used_at')
    def last_used_time(self, obj):
        return obj.last_used_at

    @admin.display(description='绑定二维码')
    def qrcode_link(self, device):
        return format_html('<a href="{}">查看绑定二维码</a>', reverse(
            'admin:otp_totp_totpdevice_config', kwargs={'pk': device.pk}
        ))

    def add_view(self, request, form_url='', extra_context=None):
        return super().add_view(request, form_url, {**(extra_context or {}), 'title': '添加管理员验证器'})

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, {**(extra_context or {}), 'title': '管理员验证器'})

    def config_view(self, request, pk):
        response = super().config_view(request, pk)
        response.template_name = 'admin/totp_config.html'
        response.context_data['title'] = '绑定手机验证器'
        return response

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super().change_view(request, object_id, form_url, {
            **(extra_context or {}), 'title': '修改管理员验证器'
        })


if admin.site.is_registered(TOTPDevice):
    admin.site.unregister(TOTPDevice)
admin.site.register(TOTPDevice, ChineseTOTPAdmin)
