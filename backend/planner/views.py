from datetime import timedelta, date as date_type
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .models import BusyBlock, WeeklySubjectGoal, Subject, PlanSlot, WeekDayConfig
from .serializers import SaveGoalsWeekSer, GenerateWeekSer, WeekAutoSaveSer
from .scheduler import Prefs, Task, solve_schedule, build_slots_from_busy_daily

@api_view(["GET"])

def _week_range(week_start: date_type, horizon_days: int = 7):
    return week_start, week_start + timedelta(days=horizon_days)

def _has_sleep(busy_items) -> bool:
    return any((b.get("type") == "sleep") for b in (busy_items or []))
PRIORITY_ORDER = {
    "urgent": 4,
    "high": 3,
    "normal": 2,
    "low": 1,
}


def _study_time_to_hours(value):
    """
    Convert studyTime từ frontend sang required_hours.
    Hỗ trợ:
    - "02:30" => 2.5
    - "2" => 2.0
    - None/empty => 1.0
    """
    if value is None or value == "":
        return 1.0

    value = str(value).strip()

    if ":" in value:
        parts = value.split(":")
        hour = int(parts[0] or 0)
        minute = int(parts[1] or 0)
        return round(hour + minute / 60, 2)

    return float(value)

def _find_prev_week_with_busy(user, week_start: date_type):
    last_busy = (
        BusyBlock.objects
        .filter(user=user, date__lt=week_start)
        .order_by("-date")
        .first()
    )
    if not last_busy:
        return None
    d = last_busy.date
    prev_week_start = d - timedelta(days=d.weekday())
    return prev_week_start


def _auto_copy_busy_if_empty(user, week_start: date_type, horizon_days: int = 7):
    ws, we = _week_range(week_start, horizon_days)
    qs = BusyBlock.objects.filter(user=user, date__gte=ws, date__lt=we).order_by("date", "start")
    if qs.exists():
        busy_items = [{"date": b.date, "start": b.start, "end": b.end, "type": b.type} for b in qs]
        return busy_items, {"auto_copied": False, "source_week_start": None}

    prev_ws = _find_prev_week_with_busy(user, week_start)
    if not prev_ws:
        return [], {"auto_copied": False, "source_week_start": None}

    prev_ws2, prev_we2 = _week_range(prev_ws, horizon_days)
    prev_blocks = BusyBlock.objects.filter(user=user, date__gte=prev_ws2, date__lt=prev_we2).order_by("date", "start")

    shift_days = (week_start - prev_ws).days

    new_objs = []
    for b in prev_blocks:
        new_objs.append(BusyBlock(
            user=user,
            date=b.date + timedelta(days=shift_days),
            start=b.start,
            end=b.end,
            type=b.type,
        ))
    BusyBlock.objects.bulk_create(new_objs)

    new_qs = BusyBlock.objects.filter(user=user, date__gte=ws, date__lt=we).order_by("date", "start")
    busy_items = [{"date": b.date, "start": b.start, "end": b.end, "type": b.type} for b in new_qs]
    return busy_items, {"auto_copied": True, "source_week_start": prev_ws.isoformat()}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_busy_week(request):
    week_start_str = request.query_params.get("week_start")
    if not week_start_str:
        return Response({"detail": "week_start is required"}, status=400)

    week_start = date_type.fromisoformat(week_start_str)

    busy_items, meta = _auto_copy_busy_if_empty(request.user, week_start, 7)

    def _fmt_time(t):
        return t.strftime("%H:%M") if hasattr(t, "strftime") else str(t)[:5]

    out = [{
        "date": b["date"].isoformat(),
        "start": _fmt_time(b["start"]),
        "end": _fmt_time(b["end"]),
        "type": b.get("type", "other"),
    } for b in busy_items]
    sleep_missing = not _has_sleep(busy_items)

    return Response({
        "week_start": week_start.isoformat(),
        **meta,
        "count": len(out),
        "busy": out,
        "sleep_missing": sleep_missing,
    })



@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def goals_week(request):
    if request.method == "GET":
        week_start_str = request.query_params.get("week_start")
        if not week_start_str:
            return Response({"detail": "week_start is required"}, status=400)
        week_start = date_type.fromisoformat(week_start_str)

        qs = WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).select_related("subject")
        out = []
        for g in qs:
            out.append({
                "name": g.subject.name,
                "required_hours": g.required_hours,
                "deadline": g.deadline.isoformat() if g.deadline else None
            })
        return Response({"week_start": week_start.isoformat(), "count": len(out), "subjects": out})

    ser = SaveGoalsWeekSer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    week_start = data["week_start"]
    subjects = data["subjects"]

    WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).delete()

    objs = []
    for s in subjects:
        subj, _ = Subject.objects.get_or_create(user=request.user, name=s["name"])
        objs.append(WeeklySubjectGoal(
            user=request.user,
            week_start=week_start,
            subject=subj,
            required_hours=float(s["required_hours"]),
            deadline=s.get("deadline"),
        ))

    WeeklySubjectGoal.objects.bulk_create(objs)
    return Response({"saved": len(objs), "week_start": week_start.isoformat()})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_plan_week(request):
    ser = GenerateWeekSer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    week_start = data["week_start"]
    ws, we = _week_range(week_start, 7)

    with transaction.atomic():
        if "subjects" in data:
            WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).delete()

            subjects_in = data["subjects"]  
            names = [s["name"] for s in subjects_in]

            existing = Subject.objects.filter(user=request.user, name__in=names)
            subj_by_name = {x.name: x for x in existing}

            missing_names = [n for n in names if n not in subj_by_name]
            if missing_names:
                Subject.objects.bulk_create([Subject(user=request.user, name=n) for n in missing_names])
                created = Subject.objects.filter(user=request.user, name__in=missing_names)
                subj_by_name.update({x.name: x for x in created})

            goals = []
            for s in subjects_in:
                subj = subj_by_name[s["name"]]
                goals.append(WeeklySubjectGoal(
                    user=request.user,
                    week_start=week_start,
                    subject=subj,
                    required_hours=float(s["required_hours"]),
                    deadline=s.get("deadline"),
                ))
            WeeklySubjectGoal.objects.bulk_create(goals)

        goals_qs = (
            WeeklySubjectGoal.objects
            .filter(user=request.user, week_start=week_start)
            .select_related("subject")
        )
        if not goals_qs.exists():
            return Response({
                "detail": "No subjects saved for this week.",
                "code": "NO_SUBJECTS",
                "hint": "Please add at least one subject (required_hours, optional deadline) before generating a plan."
            }, status=400)

        if "busy" in data:
            busy_items = data["busy"]

            BusyBlock.objects.filter(
                user=request.user,
                date__gte=ws,
                date__lt=we,
            ).delete()

            BusyBlock.objects.bulk_create([
                BusyBlock(
                    user=request.user,
                    date=b["date"],
                    start=b["start"],
                    end=b["end"],
                    type=b.get("type") or "other",
                )
                for b in busy_items
            ])

            meta = {
                "auto_saved_busy": True,
                "auto_copied": False,
                "source_week_start": None
            }
        else:
            busy_items, meta0 = _auto_copy_busy_if_empty(request.user, week_start, 7)
            meta = {"auto_saved_busy": False, **meta0}

        sleep_missing = not _has_sleep(busy_items)
        if sleep_missing:
            return Response({
                "detail": "Missing sleep blocks for this week.",
                "code": "NO_SLEEP",
                "hint": "Please add at least one busy block with type='sleep' before generating.",
                "sleep_missing": True,
                "warnings": ["Missing sleep block"],
            }, status=400)

        prefs = Prefs(
            week_start=week_start,
            horizon_days=7,
            session_len_min=60,
            break_min=10,
            max_daily_min=240,
            max_consecutive_sessions=3,
            easy_first_week=True,
            hard_first_day=True,
            focus_windows=[],
        )
        prefs.max_practice_min_per_day = 90

        slots = build_slots_from_busy_daily(busy_items, week_start, prefs)

        tasks_in = []
        subjects_out = []
        for idx, g in enumerate(goals_qs, start=1):
            required_min = int(round(float(g.required_hours) * 60))
            due = g.deadline
            kind = "study" if due else "practice"

            tasks_in.append(Task(
                id=idx,
                subject_id=g.subject_id,
                estimate_min=required_min,
                due_at=due,
                kind=kind,
            ))
            subjects_out.append({
                "id": g.subject_id,
                "name": g.subject.name,
            })

        plan, report, solver_status = solve_schedule(tasks_in, slots, prefs)

        PlanSlot.objects.filter(
            user=request.user,
            start__date__gte=ws,
            start__date__lt=we
        ).delete()

        subj_map = {s.id: s for s in Subject.objects.filter(user=request.user)}

        PlanSlot.objects.bulk_create([
            PlanSlot(
                user=request.user,
                subject=subj_map.get(p["subject_id"]),
                task=None,
                start=p["start"],
                end=p["end"],
                kind=p["kind"],
                locked=False,
            )
            for p in plan
        ])

    name_map = {s["id"]: s["name"] for s in subjects_out}
    out_plan = []
    for p in sorted(plan, key=lambda x: x["start"]):
        out_plan.append({
            "start": p["start"].isoformat(),
            "end": p["end"].isoformat(),
            "subject_id": p["subject_id"],
            "subject_name": name_map.get(p["subject_id"], ""),
            "type": p["kind"],
            "locked": False,
        })

    return Response({
        "week_start": week_start.isoformat(),
        **meta,
        "subjects": subjects_out,
        "plan": out_plan,
        "report": report,
        "solver_status": str(solver_status),
        "sleep_missing": False,
    }, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_plan_week(request):
    week_start_str = request.query_params.get("week_start")
    if not week_start_str:
        return Response({"detail": "week_start is required"}, status=400)

    week_start = date_type.fromisoformat(week_start_str)
    ws, we = _week_range(week_start, 7)

    qs = (
        PlanSlot.objects
        .filter(user=request.user, start__date__gte=ws, start__date__lt=we)
        .select_related("subject")
        .order_by("start")
    )

    out = []
    for p in qs:
        out.append({
            "id": p.id,
            "start": p.start.isoformat(),
            "end": p.end.isoformat(),
            "subject_id": p.subject_id,
            "subject_name": p.subject.name if p.subject else "",
            "kind": p.kind,
            "locked": p.locked,
        })

    return Response({
        "week_start": week_start.isoformat(),
        "count": len(out),
        "plan": out
    }, status=200)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_plan_week(request):
    week_start_str = request.query_params.get("week_start")
    if not week_start_str:
        return Response({"detail": "week_start is required"}, status=400)

    force = request.query_params.get("force", "0") == "1"

    week_start = date_type.fromisoformat(week_start_str)
    ws, we = _week_range(week_start, 7)

    qs = PlanSlot.objects.filter(user=request.user, start__date__gte=ws, start__date__lt=we)
    if not force:
        qs = qs.filter(locked=False)

    deleted, _ = qs.delete()
    return Response({"week_start": week_start.isoformat(), "deleted": deleted, "force": force}, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def autosave_week(request):
    ser = WeekAutoSaveSer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    week_start = data["week_start"]
    ws, we = _week_range(week_start, 7)

    saved = {
        "busy": False,
        "subjects": False,
        "day_configs": False,
    }

    now = timezone.now()
    sleep_missing = None

    with transaction.atomic():
        # 1. Save busy time
        if "busy" in data:
            busy_items = data["busy"]
            sleep_missing = not _has_sleep(busy_items)

            BusyBlock.objects.filter(
                user=request.user,
                date__gte=ws,
                date__lt=we,
            ).delete()

            BusyBlock.objects.bulk_create([
                BusyBlock(
                    user=request.user,
                    date=b["date"],
                    start=b["start"],
                    end=b["end"],
                    type=b.get("type") or "other",
                )
                for b in busy_items
            ])

            saved["busy"] = True

        # 2. Save number of subjects per day
        if "day_configs" in data:
            day_configs = data["day_configs"]

            WeekDayConfig.objects.filter(
                user=request.user,
                week_start=week_start,
            ).delete()

            WeekDayConfig.objects.bulk_create([
                WeekDayConfig(
                    user=request.user,
                    week_start=week_start,
                    date=item["date"],
                    number_of_subjects=item.get("number_of_subjects", 0),
                )
                for item in day_configs
            ])

            saved["day_configs"] = True

        # 3. Save subject list
        if "subjects" in data:
            subjects = data["subjects"]

            subjects = sorted(
                subjects,
                key=lambda s: PRIORITY_ORDER.get(s.get("priority", "normal"), 2),
                reverse=True,
            )

            WeeklySubjectGoal.objects.filter(
                user=request.user,
                week_start=week_start,
            ).delete()

            goals_to_create = []

            for s in subjects:
                subject_name = s["name"].strip()

                if not subject_name:
                    continue

                subj, _ = Subject.objects.get_or_create(
                    user=request.user,
                    name=subject_name,
                )

                required_hours = s.get("required_hours")

                if required_hours is None:
                    required_hours = _study_time_to_hours(s.get("studyTime"))

                goals_to_create.append(WeeklySubjectGoal(
                    user=request.user,
                    week_start=week_start,
                    subject=subj,
                    required_hours=float(required_hours),
                    deadline=s.get("deadline"),
                    priority=s.get("priority", "normal"),
                ))

            WeeklySubjectGoal.objects.bulk_create(goals_to_create)
            saved["subjects"] = True

    return Response({
        "week_start": week_start.isoformat(),
        "saved": saved,
        "saved_at": now.isoformat(),
        "sleep_missing": sleep_missing,
        "warnings": ["Missing sleep block"] if sleep_missing else [],
    }, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def week_status(request):
    week_start_str = request.query_params.get("week_start")
    if not week_start_str:
        return Response({"detail": "week_start is required"}, status=400)

    week_start = date_type.fromisoformat(week_start_str)
    ws, we = _week_range(week_start, 7)

    busy_items, meta = _auto_copy_busy_if_empty(request.user, week_start, 7)
    sleep_missing = not _has_sleep(busy_items)
    sleep_count = BusyBlock.objects.filter(
        user=request.user,
        date__gte=ws,
        date__lt=we,
        type="sleep"
    ).count()


    busy_count = BusyBlock.objects.filter(user=request.user, date__gte=ws, date__lt=we).count()
    subjects_count = WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).count()
    plan_count = PlanSlot.objects.filter(user=request.user, start__date__gte=ws, start__date__lt=we).count()

    return Response({
        "week_start": week_start.isoformat(),
        **meta,  # auto_copied, source_week_start
        "server_counts": {
            "busy": busy_count,
            "subjects": subjects_count,
            "plan": plan_count,
            "sleep": sleep_count,
        },
        "sleep_missing": sleep_missing,
        "has_goals": subjects_count > 0,
        "has_plan": plan_count > 0,
    }, status=200)