from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from club.api import auth, content, files, public
from club.api.issues import IssueViewSet

router = DefaultRouter()
router.register('issues', IssueViewSet)
router.register('collections', content.CollectionViewSet)
router.register('events', content.EventViewSet)
router.register('documents', content.DocumentViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/csrf/', public.csrf),
    path('api/auth/session/', auth.session),
    path('api/auth/login/', auth.LoginView.as_view()),
    path('api/auth/logout/', auth.LogoutView.as_view()),
    path('api/auth/account/', auth.AccountView.as_view()),
    path('api/auth/reset-password/', auth.ResetPasswordView.as_view()),
    path('api/site/', public.site_info),
    path('api/join/', public.JoinApplicationView.as_view()),
    path('api/members/', public.members),
    path('api/members/<uuid:pk>/', public.member_detail),
    path('api/dashboard/', public.DashboardView.as_view()),
    path('api/upload/', files.UploadView.as_view()),
    path('api/assets/<uuid:pk>/', files.AssetStatusView.as_view()),
    path('api/assets/<uuid:pk>/<str:variant>/', files.asset_file),
    path('api/health/', public.health),
]
