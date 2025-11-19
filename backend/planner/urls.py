from django.urls import path
from .views import health_check, generate_plan

urlpatterns = [
    path("health/", health_check, name="planner-health"),
    path("plan/generate/", generate_plan, name="planner-generate"),
]
