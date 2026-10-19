from django.conf import settings
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed


class StrictSessionAuthentication(SessionAuthentication):
    """Staff sessions must remain OTP-verified when using privileged API paths."""

    recovery_paths = {
        '/api/auth/session/',
        '/api/auth/login/',
        '/api/auth/logout/',
        '/api/auth/reset-password/',
    }

    def authenticate(self, request):
        result = super().authenticate(request)
        if result:
            user, _ = result
            if (
                not settings.DEBUG
                and user.is_staff
                and request.path not in self.recovery_paths
                and not user.is_verified()
            ):
                raise AuthenticationFailed('管理员会话需要动态验证码，请重新登录。')
        return result
