# apps/planner/services.py (ví dụ)

from datetime import date, timedelta
from django.utils import timezone

from .models import Subject, StudyTask, Availability, PlanSlot
from .scheduler import Prefs, Task, build_slots, solve_schedule

def generate_plan_for_user(user, week_start: date, prefs_override: dict | None = None):
    """
    Wrapper: lấy dữ liệu từ DB -> gọi OR-Tools -> lưu PlanSlot.
    """

    # 1) Load dữ liệu từ DB
    subjects = list(Subject.objects.filter(user=user))
    tasks_db = list(StudyTask.objects.filter(user=user))
    avails = list(Availability.objects.filter(user=user))

    if not subjects or not tasks_db or not avails:
        # Tuỳ bạn: có thể raise exception hoặc trả rỗng
        return [], {
            "hours_available": 0.0,
            "hours_required": 0.0,
            "hours_assigned": 0.0,
            "hours_missing": 0.0,
            "utilization_percent": 0.0,
            "by_task": [],
        }

    # 2) Map subject -> difficulty
    subjects_by_id = {s.id: s.difficulty for s in subjects}

    # 3) Build Task list cho solver
    tasks_in = []
    for t in tasks_db:
        diff = subjects_by_id.get(t.subject_id, 3)
        tasks_in.append(Task(
            id=t.id,
            subject_id=t.subject_id,
            difficulty=diff,
            estimate_min=t.estimate_minutes,
            due_at=t.due_at,
            kind=t.type,   # "study" / "review" / "practice" / "notes"
        ))

    # 4) Availability weekly cho solver
    availability_weekly = [
        {
            "weekday": a.weekday,
            "start": a.start.strftime("%H:%M"),
            "end": a.end.strftime("%H:%M"),
        }
        for a in avails
    ]

    # 5) Prefs (dùng default hoặc override)
    prefs_kwargs = {
        "week_start": week_start,
    }
    if prefs_override:
        prefs_kwargs.update(prefs_override)

    prefs = Prefs(**prefs_kwargs)

    # 6) Build slots
    slots = build_slots(
        availability_weekly=availability_weekly,
        week_start=week_start,
        prefs=prefs,
        busy_exceptions=[],  # có thể truyền bận riêng nếu bạn lưu DB
    )

    # 7) Gọi solver
    plan, report, _ = solve_schedule(tasks_in, slots, prefs)

    # 8) Xoá plan cũ trong tuần này
    start_date = week_start
    end_date = week_start + timedelta(days=prefs.horizon_days)

    PlanSlot.objects.filter(
        user=user,
        start__date__gte=start_date,
        start__date__lt=end_date,
    ).delete()

    # 9) Lưu PlanSlot mới
    created = []
    for p in plan:
        slot = PlanSlot.objects.create(
            user=user,
            subject_id=p["subject_id"],
            task_id=p["task_id"],
            start=p["start"],   # đã timezone-aware từ build_slots
            end=p["end"],
            kind=p["kind"],
            locked=False,
        )
        created.append(slot)

    return created, report
