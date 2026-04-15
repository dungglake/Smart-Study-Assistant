from datetime import timedelta, date as date_type, datetime, time
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from .models import BusyBlock, WeeklySubjectGoal, Subject, PlanSlot, WeekDayConfig
from .serializers import SaveGoalsWeekSer, GenerateWeekSer, WeekAutoSaveSer


PRIORITY_ORDER = {
    "urgent": 4,
    "high": 3,
    "normal": 2,
    "low": 1,
}

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"}, status=200)


def _week_range(week_start: date_type, horizon_days: int = 7):
    return week_start, week_start + timedelta(days=horizon_days)


def _study_time_to_hours(value):
    if value is None or value == "":
        return 1.0
    value = str(value).strip()
    if ":" in value:
        hour, minute = value.split(":")[:2]
        return round(int(hour or 0) + int(minute or 0) / 60, 2)
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
    return last_busy.date - timedelta(days=last_busy.date.weekday())


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

    BusyBlock.objects.bulk_create([
        BusyBlock(
            user=user,
            date=b.date + timedelta(days=shift_days),
            start=b.start,
            end=b.end,
            type=b.type,
        )
        for b in prev_blocks
    ])

    new_qs = BusyBlock.objects.filter(user=user, date__gte=ws, date__lt=we).order_by("date", "start")
    busy_items = [{"date": b.date, "start": b.start, "end": b.end, "type": b.type} for b in new_qs]
    return busy_items, {"auto_copied": True, "source_week_start": prev_ws.isoformat()}


def _time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def _minutes_to_aware_dt(day: date_type, minutes: int):
    tz = timezone.get_current_timezone()
    hour = min(23, max(0, minutes // 60))
    minute = min(59, max(0, minutes % 60))
    return timezone.make_aware(datetime.combine(day, time(hour=hour, minute=minute)), tz)


def _is_all_day_busy(block: BusyBlock) -> bool:
    start = block.start.strftime("%H:%M")
    end = block.end.strftime("%H:%M")
    return start == "00:00" and end in ("23:59", "00:00")


def _free_intervals_for_day(day: date_type, busy_blocks):
    # Study window: 06:00 -> 23:00
    study_start = 6 * 60
    study_end = 23 * 60
    busy_intervals = []

    for b in busy_blocks:
        start = _time_to_minutes(b.start)
        end = _time_to_minutes(b.end)
        if end <= start:
            end = 24 * 60
        start = max(start, study_start)
        end = min(end, study_end)
        if start < end:
            busy_intervals.append((start, end))

    busy_intervals.sort()
    merged = []
    for start, end in busy_intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    free = []
    cursor = study_start
    for start, end in merged:
        if cursor < start:
            free.append([cursor, start])
        cursor = max(cursor, end)
    if cursor < study_end:
        free.append([cursor, study_end])

    return free


def _available_minutes(intervals):
    return sum(max(0, end - start) for start, end in intervals)


def _allocate_from_intervals(day: date_type, intervals, required_min: int):
    ranges = []
    remaining = required_min

    for interval in intervals:
        if remaining <= 0:
            break
        start, end = interval
        available = end - start
        if available <= 0:
            continue
        take = min(available, remaining)
        slot_start = start
        slot_end = start + take
        ranges.append({
            "start": _minutes_to_aware_dt(day, slot_start),
            "end": _minutes_to_aware_dt(day, slot_end),
        })
        interval[0] = slot_end
        remaining -= take

    return ranges


def _make_summary_from_plan_rows(week_start: date_type, goals, busy_by_date, day_configs, plan_rows):
    rows_by_date = {}
    unique_subject_ids = set()

    for row in plan_rows:
        key = row["start"].date().isoformat()
        rows_by_date.setdefault(key, []).append(row)
        if row.get("subject_id"):
            unique_subject_ids.add(row["subject_id"])

    daily = []
    for i in range(7):
        cur = week_start + timedelta(days=i)
        key = cur.isoformat()
        subject_map = {}

        for row in rows_by_date.get(key, []):
            sid = row.get("subject_id")
            if sid and sid not in subject_map:
                subject_map[sid] = {"id": sid, "name": row.get("subject_name", "")}

        daily.append({
            "date": key,
            "weekday": WEEKDAY_NAMES[i],
            "assigned_subjects": list(subject_map.values()),
            "scheduled_count": len(subject_map),
            "target_count": day_configs.get(cur, 0),
            "busy_all_day": any(_is_all_day_busy(b) for b in busy_by_date.get(cur, [])),
        })

    return {
        "week_start": week_start.isoformat(),
        "total_scheduled_subjects": len(unique_subject_ids),
        "total_subjects_in_list": len(goals),
        "daily": daily,
    }


def _build_schedule_preview(user, week_start: date_type):
    ws, we = _week_range(week_start, 7)
    _auto_copy_busy_if_empty(user, week_start, 7)

    goals = list(
        WeeklySubjectGoal.objects
        .filter(user=user, week_start=week_start)
        .select_related("subject")
    )
    goals.sort(key=lambda g: (-PRIORITY_ORDER.get(g.priority, 2), g.created_at, g.id))

    day_configs = {
        cfg.date: cfg.number_of_subjects
        for cfg in WeekDayConfig.objects.filter(user=user, week_start=week_start)
    }

    busy_by_date = {}
    for busy in BusyBlock.objects.filter(user=user, date__gte=ws, date__lt=we).order_by("date", "start"):
        busy_by_date.setdefault(busy.date, []).append(busy)

    warnings = []
    unassigned = goals[:]
    preview_rows = []
    assigned_subject_ids = set()

    for offset in range(7):
        day = week_start + timedelta(days=offset)
        target_count = day_configs.get(day, 0)
        if target_count <= 0:
            continue

        day_busy = busy_by_date.get(day, [])
        if any(_is_all_day_busy(b) for b in day_busy):
            warnings.append({
                "type": "busy_all_day",
                "date": day.isoformat(),
                "message": f"{WEEKDAY_NAMES[offset]} is busy all day, so no subjects were scheduled on this day.",
            })
            continue

        free_intervals = _free_intervals_for_day(day, day_busy)
        scheduled_today = 0
        tried_moved_subjects = set()

        while scheduled_today < target_count and unassigned:
            assigned_one = False

            for goal in list(unassigned):
                required_min = int(round(float(goal.required_hours) * 60))
                available = _available_minutes(free_intervals)

                if available < required_min:
                    key = (day.isoformat(), goal.subject_id)
                    if key not in tried_moved_subjects:
                        tried_moved_subjects.add(key)
                        warnings.append({
                            "type": "moved_due_to_insufficient_time",
                            "date": day.isoformat(),
                            "subject_id": goal.subject_id,
                            "subject_name": goal.subject.name,
                            "required_minutes": required_min,
                            "available_minutes": available,
                            "message": (
                                f"{goal.subject.name} needs {round(required_min / 60, 2)} hour(s), "
                                f"but {WEEKDAY_NAMES[offset]} only has {round(available / 60, 2)} free hour(s). "
                                "It was moved to another available day."
                            ),
                        })
                    continue

                ranges = _allocate_from_intervals(day, free_intervals, required_min)
                if not ranges:
                    continue

                for r in ranges:
                    preview_rows.append({
                        "subject_id": goal.subject_id,
                        "subject_name": goal.subject.name,
                        "kind": "study" if goal.deadline else "practice",
                        "start": r["start"],
                        "end": r["end"],
                    })

                assigned_subject_ids.add(goal.subject_id)
                unassigned.remove(goal)
                scheduled_today += 1
                assigned_one = True
                break

            if not assigned_one:
                break

    for goal in unassigned:
        warnings.append({
            "type": "unscheduled_subject",
            "subject_id": goal.subject_id,
            "subject_name": goal.subject.name,
            "message": f"{goal.subject.name} could not be scheduled this week because there was not enough available time.",
        })

    summary = _make_summary_from_plan_rows(week_start, goals, busy_by_date, day_configs, preview_rows)

    return {
        "week_start": week_start.isoformat(),
        "scheduled_subjects": len(assigned_subject_ids),
        "unscheduled_subjects": len(unassigned),
        "warnings": warnings,
        "summary": summary,
        "plan": preview_rows,
    }


def _save_preview_to_plan_slots(user, week_start: date_type, preview_plan):
    ws, we = _week_range(week_start, 7)
    PlanSlot.objects.filter(user=user, start__date__gte=ws, start__date__lt=we).delete()

    subject_map = {s.id: s for s in Subject.objects.filter(user=user)}
    PlanSlot.objects.bulk_create([
        PlanSlot(
            user=user,
            subject=subject_map.get(row["subject_id"]),
            task=None,
            start=row["start"],
            end=row["end"],
            kind=row.get("kind") or "study",
            locked=False,
        )
        for row in preview_plan
    ])


def _serialize_plan_rows(rows):
    return [
        {
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
            "kind": row.get("kind", "study"),
            "start": row["start"].isoformat(),
            "end": row["end"].isoformat(),
        }
        for row in rows
    ]


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

    return Response({
        "week_start": week_start.isoformat(),
        **meta,
        "count": len(out),
        "busy": out,
        "sleep_missing": False,
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
        out = [{
            "id": g.subject_id,
            "name": g.subject.name,
            "required_hours": g.required_hours,
            "studyTime": f"{int(g.required_hours):02d}:{int(round((g.required_hours % 1) * 60)):02d}",
            "priority": g.priority,
            "deadline": g.deadline.isoformat() if g.deadline else None,
        } for g in qs]
        return Response({"week_start": week_start.isoformat(), "count": len(out), "subjects": out})

    ser = SaveGoalsWeekSer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    week_start = data["week_start"]

    WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).delete()
    objs = []
    for s in sorted(data["subjects"], key=lambda x: PRIORITY_ORDER.get(x.get("priority", "normal"), 2), reverse=True):
        subj, _ = Subject.objects.get_or_create(user=request.user, name=s["name"].strip())
        required_hours = s.get("required_hours") or _study_time_to_hours(s.get("studyTime"))
        objs.append(WeeklySubjectGoal(
            user=request.user,
            week_start=week_start,
            subject=subj,
            required_hours=float(required_hours),
            deadline=s.get("deadline"),
            priority=s.get("priority", "normal"),
        ))
    WeeklySubjectGoal.objects.bulk_create(objs)
    return Response({"saved": len(objs), "week_start": week_start.isoformat()})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def preview_plan_week(request):
    ser = GenerateWeekSer(data=request.data)
    ser.is_valid(raise_exception=True)
    week_start = ser.validated_data["week_start"]

    if not WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).exists():
        return Response({
            "detail": "No subjects saved for this week.",
            "code": "NO_SUBJECTS",
            "hint": "Please add at least one subject before generating a plan.",
        }, status=400)

    result = _build_schedule_preview(request.user, week_start)
    result["plan"] = _serialize_plan_rows(result["plan"])
    result["applied"] = False
    return Response(result, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apply_plan_week(request):
    ser = GenerateWeekSer(data=request.data)
    ser.is_valid(raise_exception=True)
    week_start = ser.validated_data["week_start"]

    if not WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).exists():
        return Response({
            "detail": "No subjects saved for this week.",
            "code": "NO_SUBJECTS",
            "hint": "Please add at least one subject before applying a plan.",
        }, status=400)

    with transaction.atomic():
        result = _build_schedule_preview(request.user, week_start)
        _save_preview_to_plan_slots(request.user, week_start, result["plan"])

    result["plan"] = _serialize_plan_rows(result["plan"])
    result["applied"] = True
    return Response(result, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_plan_week(request):
    # Backward-compatible endpoint: generate and save immediately.
    return apply_plan_week(request)


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

    out = [{
        "id": p.id,
        "start": p.start.isoformat(),
        "end": p.end.isoformat(),
        "subject_id": p.subject_id,
        "subject_name": p.subject.name if p.subject else "",
        "kind": p.kind,
        "locked": p.locked,
    } for p in qs]
    return Response({"week_start": week_start.isoformat(), "count": len(out), "plan": out}, status=200)


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
    saved = {"busy": False, "subjects": False, "day_configs": False}
    now = timezone.now()

    with transaction.atomic():
        if "busy" in data:
            BusyBlock.objects.filter(user=request.user, date__gte=ws, date__lt=we).delete()
            BusyBlock.objects.bulk_create([
                BusyBlock(
                    user=request.user,
                    date=b["date"],
                    start=b["start"],
                    end=b["end"],
                    type=b.get("type") or "other",
                )
                for b in data["busy"]
            ])
            saved["busy"] = True

        if "day_configs" in data:
            WeekDayConfig.objects.filter(user=request.user, week_start=week_start).delete()
            WeekDayConfig.objects.bulk_create([
                WeekDayConfig(
                    user=request.user,
                    week_start=week_start,
                    date=item["date"],
                    number_of_subjects=item.get("number_of_subjects", 0),
                )
                for item in data["day_configs"]
            ])
            saved["day_configs"] = True

        if "subjects" in data:
            WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).delete()
            goals_to_create = []
            subjects = sorted(data["subjects"], key=lambda s: PRIORITY_ORDER.get(s.get("priority", "normal"), 2), reverse=True)
            for s in subjects:
                subject_name = s["name"].strip()
                if not subject_name:
                    continue
                subj, _ = Subject.objects.get_or_create(user=request.user, name=subject_name)
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
        "sleep_missing": False,
        "warnings": [],
    }, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def week_status(request):
    week_start_str = request.query_params.get("week_start")
    if not week_start_str:
        return Response({"detail": "week_start is required"}, status=400)
    week_start = date_type.fromisoformat(week_start_str)
    ws, we = _week_range(week_start, 7)
    _auto_copy_busy_if_empty(request.user, week_start, 7)

    busy_count = BusyBlock.objects.filter(user=request.user, date__gte=ws, date__lt=we).count()
    subjects_count = WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).count()
    plan_count = PlanSlot.objects.filter(user=request.user, start__date__gte=ws, start__date__lt=we).count()

    return Response({
        "week_start": week_start.isoformat(),
        "auto_copied": False,
        "source_week_start": None,
        "server_counts": {
            "busy": busy_count,
            "subjects": subjects_count,
            "plan": plan_count,
            "sleep": 0,
        },
        "sleep_missing": False,
        "has_goals": subjects_count > 0,
        "has_plan": plan_count > 0,
    }, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def week_summary(request):
    week_start_str = request.query_params.get("week_start")
    if not week_start_str:
        return Response({"detail": "week_start is required"}, status=400)

    week_start = date_type.fromisoformat(week_start_str)
    ws, we = _week_range(week_start, 7)
    goals = list(WeeklySubjectGoal.objects.filter(user=request.user, week_start=week_start).select_related("subject"))
    day_configs = {cfg.date: cfg.number_of_subjects for cfg in WeekDayConfig.objects.filter(user=request.user, week_start=week_start)}

    busy_by_date = {}
    for b in BusyBlock.objects.filter(user=request.user, date__gte=ws, date__lt=we).order_by("date", "start"):
        busy_by_date.setdefault(b.date, []).append(b)

    plan_rows = []
    for p in PlanSlot.objects.filter(user=request.user, start__date__gte=ws, start__date__lt=we).select_related("subject").order_by("start"):
        plan_rows.append({
            "subject_id": p.subject_id,
            "subject_name": p.subject.name if p.subject else "",
            "kind": p.kind,
            "start": p.start,
            "end": p.end,
        })

    return Response(_make_summary_from_plan_rows(week_start, goals, busy_by_date, day_configs, plan_rows), status=200)
