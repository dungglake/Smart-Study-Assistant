from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .serializers import GeneratePlanSer
from .scheduler import (
    Prefs, Task, Slot,
    build_slots, expand_exams_to_review_tasks, solve_schedule
)

# giữ health_check cũ
from django.http import JsonResponse
def health_check(request):
    return JsonResponse({"status": "ok", "app": "planner"})

@api_view(["POST"])
@permission_classes([AllowAny])
def generate_plan(request):
    ser = GeneratePlanSer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    prefs_in = data["prefs"]
    prefs = Prefs(
        week_start=prefs_in["week_start"],
        horizon_days=prefs_in.get("horizon_days", 7),
        session_len_min=prefs_in.get("session_len_min", 50),
        break_min=prefs_in.get("break_min", 10),
        max_daily_min=prefs_in.get("max_daily_min", 240),
        max_consecutive_sessions=prefs_in.get("max_consecutive_sessions", 3),
        easy_first_week=prefs_in.get("easy_first_week", True),
        hard_first_day=prefs_in.get("hard_first_day", True),
        focus_windows=prefs_in.get("focus_windows", []),
    )

    # 1) Build slots
    slots = build_slots(
        availability_weekly=data["availability_weekly"],
        week_start=prefs.week_start,
        prefs=prefs,
        busy_exceptions=data.get("busy_exceptions", []),
    )

    # 2) Build tasks
    subjects_by_id = {int(s["id"]): s for s in data["subjects"]}
    tasks_in = []
    for t in data.get("tasks", []):
        subj_id = int(t["subject_id"])
        diff = int(subjects_by_id[subj_id]["difficulty"])
        due = t.get("due_at", None)
        if due is not None:
            # DRF đã parse timezone-aware
            pass
        tasks_in.append(Task(
            id=int(t["id"]),
            subject_id=subj_id,
            difficulty=diff,
            estimate_min=int(t["estimate_minutes"]),
            due_at=due,
            kind=t.get("type", "study"),
        ))

    # 3) Expand exams -> review tasks (optional)
    if data.get("exams") and prefs_in.get("spaced_repetition", True):
        review_tasks = expand_exams_to_review_tasks(
            data.get("exams", []),
            subjects_by_id=subjects_by_id,
            session_len_min=prefs.session_len_min,
        )
        tasks_in.extend(review_tasks)

    # 4) Solve
    plan, report, status_code = solve_schedule(tasks_in, slots, prefs)

    # 5) Format output
    out_plan = []
    for i, p in enumerate(sorted(plan, key=lambda x: x["start"])):
        out_plan.append({
            "slot_id": f"s_{p['start'].isoformat()}",
            "start": p["start"].isoformat(),
            "end": p["end"].isoformat(),
            "subject_id": p["subject_id"],
            "task_id": p["task_id"],
            "type": p["kind"],
            "locked": False,
        })

    return Response({"plan": out_plan, "report": report}, status=status.HTTP_200_OK)
