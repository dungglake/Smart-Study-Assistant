import pytest
from urllib.parse import urlparse, parse_qs
from django.urls import reverse
from django.core import mail
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken, OutstandingToken
)

REGISTER_URL = "auth-register"
LOGIN_URL = "auth-login"
LOGOUT_URL = "auth-logout"
PWD_RESET_REQ_URL = "auth-password-reset"
PWD_RESET_CONFIRM_URL = "auth-password-reset-confirm"
pytestmark = pytest.mark.django_db

@pytest.fixture
def register_payload():
    return {
        "username": "alice",
        "email": "alice@example.com",
        "password": "StrongP@ss123",
        "first_name": "Alice",
        "last_name": "Nguyen",
    }

# -----------------------------
# ĐĂNG KÝ
# -----------------------------
def test_register_success_returns_tokens(api_client, register_payload, django_user_model):
    res = api_client.post(reverse(REGISTER_URL), register_payload, format="json")
    assert res.status_code == status.HTTP_201_CREATED, res.data
    assert "access" in res.data and "refresh" in res.data
    assert django_user_model.objects.filter(username="alice").exists()

def test_register_rejects_duplicate_email(api_client, register_payload, create_user):
    create_user(username="bob", email=register_payload["email"])
    res = api_client.post(reverse(REGISTER_URL), register_payload, format="json")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in res.data

def test_register_rejects_weak_password(api_client, register_payload):
    payload = {**register_payload, "username": "weakuser", "password": "123"}
    res = api_client.post(reverse(REGISTER_URL), payload, format="json")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in res.data

# -----------------------------
# ĐĂNG NHẬP
# -----------------------------
def test_login_with_username(api_client, create_user):
    create_user(username="john", email="john@example.com")
    res = api_client.post(reverse(LOGIN_URL),
                          {"username": "john", "password": "StrongP@ss123"},
                          format="json")
    assert res.status_code == status.HTTP_200_OK, res.data
    assert "access" in res.data and "refresh" in res.data

def test_login_with_email(api_client, create_user):
    create_user(username="john2", email="john2@example.com")
    res = api_client.post(reverse(LOGIN_URL),
                          {"username": "john2@example.com", "password": "StrongP@ss123"},
                          format="json")
    assert res.status_code == status.HTTP_200_OK, res.data
    assert "access" in res.data and "refresh" in res.data

def test_login_wrong_password(api_client, create_user):
    create_user(username="john3", email="john3@example.com")
    res = api_client.post(reverse(LOGIN_URL),
                          {"username": "john3", "password": "WrongPass!"},
                          format="json")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

# -----------------------------
# LOGOUT (blacklist refresh)
# -----------------------------
def test_logout_blacklists_refresh(api_client, register_payload):
    reg = api_client.post(reverse(REGISTER_URL), register_payload, format="json")
    access, refresh = reg.data["access"], reg.data["refresh"]

    # Logout
    res = api_client.post(
        reverse(LOGOUT_URL),
        {"refresh": refresh},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )
    assert res.status_code == status.HTTP_200_OK

    # Refresh lại bằng refresh cũ → phải FAIL vì đã blacklist
    r = api_client.post(reverse("auth-refresh"), {"refresh": refresh}, format="json")
    assert r.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST)

# -----------------------------
# RESET PASSWORD
# -----------------------------
def test_password_reset_flow(api_client, create_user):
    create_user(username="resetuser", email="reset@example.com", password="OldPass!123")

    # request
    res_req = api_client.post(reverse(PWD_RESET_REQ_URL),
                              {"email": "reset@example.com"},
                              format="json")
    assert res_req.status_code == status.HTTP_200_OK

    assert len(mail.outbox) == 1
    body = mail.outbox[0].body

    link = next((ln.strip() for ln in body.splitlines()
                 if "reset-password" in ln and "uid=" in ln and "token=" in ln), None)
    assert link, f"Không tìm thấy link trong email.\n{body}"

    qs = parse_qs(urlparse(link).query)
    uid = qs.get("uid", [""])[0]
    token = qs.get("token", [""])[0]
    assert uid and token

    # confirm
    res_confirm = api_client.post(
        reverse(PWD_RESET_CONFIRM_URL),
        {"uid": uid, "token": token, "new_password": "NewPass!456"},
        format="json",
    )
    assert res_confirm.status_code == status.HTTP_200_OK, res_confirm.data

    # login với mật khẩu mới OK
    res_login_new = api_client.post(
        reverse(LOGIN_URL),
        {"username": "resetuser", "password": "NewPass!456"},
        format="json",
    )
    assert res_login_new.status_code == status.HTTP_200_OK

    # mật khẩu cũ FAIL
    res_login_old = api_client.post(
        reverse(LOGIN_URL),
        {"username": "resetuser", "password": "OldPass!123"},
        format="json",
    )
    assert res_login_old.status_code == status.HTTP_401_UNAUTHORIZED

def test_password_reset_confirm_invalid_token(api_client, create_user):
    create_user(username="resetbad", email="resetbad@example.com", password="OldPass!123")
    res = api_client.post(
        reverse(PWD_RESET_CONFIRM_URL),
        {"uid": "abc", "token": "invalid-token", "new_password": "NewPass!456"},
        format="json",
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
