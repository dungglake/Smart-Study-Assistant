from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    EmailOrUsernameTokenObtainPairSerializer,
    RequestPasswordResetSerializer,
    PasswordResetConfirmSerializer,
)
from .utils import make_password_reset_link, get_user_from_uid
from .tokens import password_reset_token

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "detail": "Đăng ký thành công. Vui lòng đăng nhập."
            },
            status=status.HTTP_201_CREATED
        )

class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailOrUsernameTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "Missing refresh token."}, status=400)
        try:
            token = RefreshToken(refresh)
            token.blacklist()  
        except Exception:
            return Response({"detail": "Refresh token is invalid."}, status=400)
        return Response({"detail": "Logout successful."})
        

class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email).first()
        if user:
            link = make_password_reset_link(user)
            subject = "Reset your SmartStudyAssistant password"
            message = (
                f"Hello {user.first_name or user.username},\n\n"
                f"You have requested to reset your password. Please click the link below:\n{link}\n\n"
                "If you did not request this, please ignore this email."
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        return Response({"detail": "If the email exists, we have sent password reset instructions."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        user = get_user_from_uid(uid)
        if not user:
            return Response({"detail": "The link is invalid."}, status=400)

        if not password_reset_token.check_token(user, token):
            return Response({"detail": "Token is invalid or has expired."}, status=400)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"detail": "Password reset successfully."})
    
