from django.urls import path
from .views import (
    health_check,
    get_busy_week,
    goals_week,
    generate_plan_week,
    get_plan_week,
    delete_plan_week,
    autosave_week,
    week_status,
)

urlpatterns = [
    path("health/", health_check, name="planner-health"),

    # Busy timetable (auto-copy)
    path("busyblocks/week", get_busy_week, name="busy-week-get"),

    # Weekly subjects goals
    path("goals/week", goals_week, name="goals-week"),

    # Generate plan (persist)
    path("plan/generate-week", generate_plan_week, name="plan-generate-week"),
    path("plan/week", get_plan_week, name="plan-week-get"),
    path("plan/week/delete", delete_plan_week, name="plan-week-delete"),
    
    path("week/autosave", autosave_week, name="week-autosave"),
    
    path("week/status", week_status, name="week-status"),

]
