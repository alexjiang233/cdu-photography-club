from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from .. import services
from ..models import Profile
from ..permissions import is_member
from ..serializers import ProfileSerializer, ProfileUpdateSerializer


class LoginThrottle(AnonRateThrottle):
    scope = 'login'


def identity(user):
    if not user.is_authenticated:
        return {'authenticated': False}
    profile = getattr(user, 'profile', None)
    return {
        'authenticated': True,
        'username': user.username,
        'member': is_member(user),
        'staff': user.is_staff,
        'profile': ProfileSerializer(profile).data if profile else None,
        'can_edit_events': user.has_perm('club.change_event'),
        'can_edit_documents': user.has_perm('club.change_document'),
        'can_review': user.has_perm('club.change_collection'),
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def session(request):
    return Response({**identity(request.user), 'csrf_token': get_token(request)})


@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        user = authenticate(
            request,
            username=str(request.data.get('username', ''))[:150],
            password=request.data.get('password', ''),
        )
        if not user:
            raise ValidationError('账号或密码不正确。')
        verified_device = None
        if user.is_staff and not settings.DEBUG:
            from django_otp.plugins.otp_totp.models import TOTPDevice

            with transaction.atomic():
                devices = TOTPDevice.objects.select_for_update().filter(user=user, confirmed=True)
                verified_device = next(
                    (
                        device
                        for device in devices
                        if device.verify_token(str(request.data.get('otp', '')))
                    ),
                    None,
                )
                if verified_device is None:
                    raise ValidationError('请输入有效的管理员动态验证码。')
        login(request, user)
        if verified_device:
            from django_otp import login as otp_login

            otp_login(request, device=verified_device)
        return Response(identity(user))


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'ok': True})


class AccountView(APIView):
    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(
            user=request.user, defaults={'display_name': request.user.username}
        )
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        services.audit(request.user, 'update_profile', profile)
        return Response(identity(request.user))

    def post(self, request):
        if not request.user.check_password(request.data.get('current_password', '')):
            raise ValidationError('原密码不正确。')
        try:
            validate_password(request.data.get('new_password', ''), request.user)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        request.user.set_password(request.data['new_password'])
        request.user.save(update_fields=['password'])
        update_session_auth_hash(request, request.user)
        return Response({'ok': True})


@method_decorator(csrf_protect, name='dispatch')
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        if request.data.get('token'):
            try:
                uid = force_str(urlsafe_base64_decode(request.data.get('uid', '')))
                user = User.objects.get(pk=uid, is_active=True)
            except (ValueError, User.DoesNotExist, OverflowError):
                raise ValidationError('重置链接无效或已过期。')
            if not default_token_generator.check_token(user, request.data['token']):
                raise ValidationError('重置链接无效或已过期。')
            try:
                validate_password(request.data.get('password', ''), user)
            except DjangoValidationError as exc:
                raise ValidationError(exc.messages)
            user.set_password(request.data['password'])
            user.save(update_fields=['password'])
            return Response({'detail': '密码已重置，请重新登录。'})
        email = str(request.data.get('email', ''))[:254]
        if not settings.DEBUG and settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
            return Response({'detail': '邮件服务尚未开放，请联系协会管理员重置密码。'}, status=503)
        for user in User.objects.filter(email__iexact=email, is_active=True).exclude(email='')[:5]:
            if not user.has_usable_password():
                continue
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            base = settings.CSRF_TRUSTED_ORIGINS[0]
            send_mail(
                '摄影协会密码重置',
                f'请访问 {base}/reset-password?uid={uid}&token={token} 重置密码。如非本人操作请忽略。',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        return Response({'detail': '如果邮箱已关联账号，我们会发送重置邮件。'})
