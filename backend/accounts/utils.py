from typing import Optional
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings

from .tokens import password_reset_token

User = get_user_model()


def make_password_reset_link(user: User) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token.make_token(user)
    # Frontend sẽ có route /reset-password để nhận hai query này
    return f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"


def get_user_from_uid(uid: str) -> Optional[User]:
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=pk)
    except Exception:
        return None
