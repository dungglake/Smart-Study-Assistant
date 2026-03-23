from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    RequestPasswordResetView,
    PasswordResetConfirmView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("password-reset/", RequestPasswordResetView.as_view(), name="auth-password-reset"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
]