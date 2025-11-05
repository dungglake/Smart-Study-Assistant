import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user(django_user_model):
    def _create(username="u1", email="u1@example.com", password="StrongP@ss123"):
        return django_user_model.objects.create_user(username=username, email=email, password=password)
    return _create

@pytest.fixture(autouse=True)
def _email_settings(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@smartstudyassistant.app"
    settings.FRONTEND_URL = "http://localhost:5173"
