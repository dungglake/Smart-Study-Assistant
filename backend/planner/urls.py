from django.urls import path
from .views import (
    health_check,
    get_busy_week,
    goals_week,
    preview_plan_week,
    apply_plan_week,
    generate_plan_week,
    get_plan_week,
    delete_plan_week,
    autosave_week,
    week_status,
    week_summary,
)

urlpatterns = [
    path("health", health_check, name="health-check"),

    path("busyblocks/week", get_busy_week, name="busy-week-get"),
    path("goals/week", goals_week, name="goals-week"),

    path("plan/preview-week", preview_plan_week, name="plan-preview-week"),
    path("plan/apply-week", apply_plan_week, name="plan-apply-week"),
    path("plan/generate-week", generate_plan_week, name="plan-generate-week"),
    path("plan/week", get_plan_week, name="plan-week-get"),
    path("plan/week/delete", delete_plan_week, name="plan-week-delete"),

    path("week/autosave", autosave_week, name="week-autosave"),
    path("week/status", week_status, name="week-status"),
    path("week/summary", week_summary, name="week-summary"),
]
