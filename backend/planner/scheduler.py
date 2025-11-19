from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from ortools.sat.python import cp_model
import math

from django.utils import timezone


# ======= Dataclasses làm lớp trao đổi nội bộ =======

@dataclass
class Slot:
    id: int
    start: datetime
    end: datetime
    day_idx: int  # 0..6 (Mon..Sun)
    is_focus: bool


@dataclass
class Task:
    id: int
    subject_id: int
    difficulty: int  # 1..5
    estimate_min: int
    due_at: Optional[datetime]
    kind: str = "study"  # study/review/...
    # allowed_slots: nếu None => mọi slot hợp lệ theo availability; nếu có => chỉ cho phép danh sách này
    allowed_slot_ids: Optional[List[int]] = None


@dataclass
class Prefs:
    week_start: date
    horizon_days: int = 7
    session_len_min: int = 50
    break_min: int = 10
    max_daily_min: int = 240
    max_consecutive_sessions: int = 3
    easy_first_week: bool = True
    hard_first_day: bool = True
    focus_windows: Optional[List[dict]] = None  # [{"weekday": 0|1|..|"any", "start":"07:00","end":"11:00"}]


# ======= Helpers =======

def parse_time_str(s: str) -> time:
    hh, mm = s.split(":")
    return time(int(hh), int(mm))


def in_time_window(t: time, start: time, end: time) -> bool:
    return start <= t < end


def mark_focus(slot: Slot, focus_windows: Optional[List[dict]]) -> bool:
    if not focus_windows:
        return False
    st, en = slot.start.time(), slot.end.time()
    for w in focus_windows:
        wd = w["weekday"]
        s = parse_time_str(w["start"])
        e = parse_time_str(w["end"])
        if wd == "any" or wd is None or int(wd) == slot.day_idx:
            # slot là focus nếu phần lớn thời gian nằm trong cửa sổ
            mid = (datetime.combine(date.min, st) + (datetime.combine(date.min, en) - datetime.combine(date.min, st)) / 2).time()
            if in_time_window(mid, s, e):
                return True
    return False


def overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


# ======= Build slots từ availability weekly + exceptions =======

def build_slots(availability_weekly: List[dict], week_start: date, prefs: Prefs,
                busy_exceptions: Optional[List[dict]] = None) -> List[Slot]:
    tz = timezone.get_current_timezone()
    slots: List[Slot] = []
    sid = 0
    busy = []
    for ex in (busy_exceptions or []):
        bs = timezone.make_aware(datetime.fromisoformat(ex["from"])) if isinstance(ex["from"], str) else ex["from"]
        be = timezone.make_aware(datetime.fromisoformat(ex["to"])) if isinstance(ex["to"], str) else ex["to"]
        busy.append((bs, be))

    for d in range(prefs.horizon_days):
        day = week_start + timedelta(days=d)
        wd = day.weekday()  # 0..6 Mon..Sun
        day_avails = [a for a in availability_weekly if int(a["weekday"]) == wd]

        for a in day_avails:
            start_t = parse_time_str(a["start"])
            end_t = parse_time_str(a["end"])
            # cắt thành các phiên session_len_min
            cur = timezone.make_aware(datetime.combine(day, start_t), tz)
            end_dt = timezone.make_aware(datetime.combine(day, end_t), tz)
            while cur + timedelta(minutes=prefs.session_len_min) <= end_dt:
                nxt = cur + timedelta(minutes=prefs.session_len_min)
                # loại các phiên trùng busy_exceptions
                skip = any(overlap(cur, nxt, bs, be) for (bs, be) in busy)
                if not skip:
                    slot = Slot(
                        id=sid,
                        start=cur,
                        end=nxt,
                        day_idx=wd,
                        is_focus=False,  # cập nhật sau
                    )
                    slots.append(slot)
                    sid += 1
                # chèn break ảo: để solver không phải xếp liên tiếp quá dài, đã có ràng buộc consecutive; break_min chỉ là tham số UI
                cur = nxt

    # Đánh dấu focus
    for i, s in enumerate(slots):
        s.is_focus = mark_focus(s, prefs.focus_windows or [])

    return slots


# ======= Expand exams -> review tasks (tuỳ chọn) =======

def expand_exams_to_review_tasks(exams: List[dict], subjects_by_id: Dict[int, dict],
                                 session_len_min: int, default_pattern: List[int] = [1, 2, 4, 7]) -> List[Task]:
    """Tạo các review task 20' cho mỗi ngày trước kỳ thi theo pattern (1/2/4/7 ngày)."""
    tasks: List[Task] = []
    for ex in exams or []:
        subj_id = int(ex["subject_id"])
        diff = int(subjects_by_id[subj_id]["difficulty"])
        exam_at = datetime.fromisoformat(ex["at"])
        exam_at = timezone.make_aware(exam_at)
        pattern = ex.get("review_pattern", default_pattern)
        for k in pattern:
            day = (exam_at.date() - timedelta(days=int(k)))
            # review 20 phút (hoặc làm tròn lên 1 phiên nếu session_len_min > 20)
            est = max(20, session_len_min)
            tasks.append(Task(
                id=int(f"9{subj_id}{k}"),  # id tạm
                subject_id=subj_id,
                difficulty=diff,
                estimate_min=est,
                due_at=exam_at,  # để cost ưu tiên gần thi
                kind="review",
            ))
    return tasks


# ======= Cost function (chi phí thấp = tốt; mục tiêu: minimize) =======

def build_cost(task: Task, slot: Slot, prefs: Prefs) -> int:
    cost = 0.0

    # 1) Deadline – phạt mạnh nếu sau hạn; thưởng nhẹ nếu trước hạn
    if task.due_at:
        delta_h = (slot.start - task.due_at).total_seconds() / 3600.0
        if delta_h > 0:
            cost += 2000 + 10 * delta_h
        else:
            cost += 500 - min(500, 5 * abs(delta_h))

    # 2) Dễ/nhỏ đầu tuần
    if prefs.easy_first_week:
        week_pos = slot.day_idx  # 0..6
        easy_bonus = (1.0 / max(1, task.difficulty)) + (1.0 / max(0.5, task.estimate_min / 60.0))
        cost -= 10.0 * (7 - week_pos) * easy_bonus

    # 3) Khó trong giờ vàng
    if prefs.hard_first_day and slot.is_focus:
        cost -= 8.0 * task.difficulty

    # 4) Review nhẹ hơn
    if task.kind == "review":
        cost -= 15.0

    return int(round(cost * 100))


# ======= Solver chính =======

def solve_schedule(tasks: List[Task], slots: List[Slot], prefs: Prefs):
    model = cp_model.CpModel()
    slot_min = prefs.session_len_min

    # allowed slots cho mỗi task
    allowed: Dict[int, List[int]] = {}
    for t in tasks:
        allowed[t.id] = t.allowed_slot_ids if t.allowed_slot_ids is not None else [s.id for s in slots]

    # số phiên (slot) cần cho mỗi task
    req_slots = {t.id: math.ceil(t.estimate_min / slot_min) for t in tasks}

    # Biến X_{t,s}
    X: Dict[Tuple[int, int], cp_model.IntVar] = {}
    for t in tasks:
        for sid in allowed[t.id]:
            X[(t.id, sid)] = model.NewBoolVar(f"x_t{t.id}_s{sid}")

    # Biến slack y_t (thiếu phiên)
    Y = {t.id: model.NewIntVar(0, req_slots[t.id], f"y_t{t.id}") for t in tasks}

    # A_s: slot có người học hay không
    A = {s.id: model.NewBoolVar(f"a_s{s.id}") for s in slots}

    # START_{t,s}: bắt đầu một đoạn mới (để phạt phân mảnh)
    START: Dict[Tuple[int, int], cp_model.IntVar] = {}
    sid_to_index = {s.id: i for i, s in enumerate(slots)}

    for t in tasks:
        for sid in allowed[t.id]:
            START[(t.id, sid)] = model.NewBoolVar(f"start_t{t.id}_s{sid}")

    # (1) mỗi slot ≤ 1 task; link A_s
    for s in slots:
        xs = [X[(t.id, s.id)] for t in tasks if (t.id, s.id) in X]
        if xs:
            model.Add(sum(xs) <= 1)
            model.Add(sum(xs) == A[s.id])

    # (2) đủ slot cho mỗi task (mềm)
    for t in tasks:
        xs = [X[(t.id, sid)] for sid in allowed[t.id]]
        model.Add(sum(xs) + Y[t.id] >= req_slots[t.id])

    # (4) giới hạn theo ngày
    day_slots = defaultdict(list)
    for s in slots:
        day_slots[s.day_idx].append(s.id)
    for d, sids in day_slots.items():
        model.Add(sum(A[sid] for sid in sids) * slot_min <= prefs.max_daily_min)

    # (5) giới hạn consecutive: trong bất kỳ cửa sổ (K+1) slot của 1 ngày, tổng A ≤ K
    K = prefs.max_consecutive_sessions
    for d, sids in day_slots.items():
        if len(sids) <= K:
            continue
        for i in range(0, len(sids) - K):
            window = sids[i : i + K + 1]
            model.Add(sum(A[sid] for sid in window) <= K)

    # (START) phát hiện bắt đầu một chuỗi task t
    for t in tasks:
        # sắp theo index thời gian
        allowed_ids_sorted = sorted(allowed[t.id], key=lambda sid: sid_to_index[sid])
        for j, sid in enumerate(allowed_ids_sorted):
            x_cur = X[(t.id, sid)]
            if j == 0:
                model.Add(START[(t.id, sid)] >= x_cur)
            else:
                sid_prev = allowed_ids_sorted[j - 1]
                x_prev = X[(t.id, sid_prev)]
                model.Add(START[(t.id, sid)] >= x_cur - x_prev)
            model.Add(START[(t.id, sid)] <= x_cur)

    # Mục tiêu
    LAMBDA_SLACK = 10_000  # phạt thiếu giờ cực lớn
    LAMBDA_FRAG = 200      # phạt phân mảnh

    costs = []
    for t in tasks:
        for sid in allowed[t.id]:
            slot = slots[sid_to_index[sid]]
            c = build_cost(t, slot, prefs)
            costs.append(c * X[(t.id, sid)])

    frag_terms = [START[(t.id, sid)] for (t, sid) in START]

    model.Minimize(sum(costs) + LAMBDA_SLACK * sum(Y.values()) + LAMBDA_FRAG * sum(frag_terms))

    # Giải
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    # Đọc nghiệm
    plan = []
    assigned_minutes = defaultdict(int)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for t in tasks:
            for sid in allowed[t.id]:
                if solver.Value(X[(t.id, sid)]) == 1:
                    slot = slots[sid_to_index[sid]]
                    plan.append({"task_id": t.id, "subject_id": t.subject_id, "kind": t.kind,
                                 "start": slot.start, "end": slot.end})
                    assigned_minutes[t.id] += slot_min

    # Báo cáo overload
    report = {
        "hours_available": round(sum(1 for s in slots) * slot_min / 60.0, 2),
        "hours_required": round(sum(t.estimate_min for t in tasks) / 60.0, 2),
        "hours_assigned": round(sum(assigned_minutes.values()) * slot_min / 60.0, 2),
        "by_task": [
            {"task_id": t.id,
             "required_min": t.estimate_min,
             "assigned_min": assigned_minutes.get(t.id, 0)}
            for t in tasks
        ],
    }
    report["hours_missing"] = round(max(0.0, report["hours_required"] - report["hours_assigned"]), 2)
    if report["hours_required"]:
        report["utilization_percent"] = round(100.0 * report["hours_assigned"] / report["hours_required"], 1)
    else:
        report["utilization_percent"] = 0.0

    return plan, report, status
