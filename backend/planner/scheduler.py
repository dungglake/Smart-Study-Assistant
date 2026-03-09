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

    # NEW defaults (dev-controlled)
    study_window_start: time = time(6, 0)
    study_window_end: time = time(23, 0)
    max_practice_min_per_day: int = 90


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

def _merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0]]
    for s, e in intervals[1:]:
        ps, pe = merged[-1]
        if s <= pe:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def _clip_interval(s: datetime, e: datetime, ws: datetime, we: datetime) -> Optional[Tuple[datetime, datetime]]:
    s2 = max(s, ws)
    e2 = min(e, we)
    if s2 >= e2:
        return None
    return (s2, e2)


def _subtract_intervals(window: Tuple[datetime, datetime], busies: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    ws, we = window
    free = []
    cur = ws
    for bs, be in busies:
        if be <= cur:
            continue
        if bs > cur:
            free.append((cur, min(bs, we)))
        cur = max(cur, be)
        if cur >= we:
            break
    if cur < we:
        free.append((cur, we))
    return [(s, e) for s, e in free if s < e]


def normalize_busy_blocks(busy_items: List[dict]) -> List[Tuple[datetime, datetime]]:
    """
    busy item: {date, start, end, type}
    Nếu end <= start => bận qua đêm (vd 23:00->06:00), tự kéo end sang ngày hôm sau.
    Trả về list (start_dt, end_dt) timezone-aware theo current timezone.
    """
    tz = timezone.get_current_timezone()
    blocks: List[Tuple[datetime, datetime]] = []
    for b in busy_items:
        d: date = b["date"]
        st: time = b["start"]
        en: time = b["end"]

        sdt = timezone.make_aware(datetime.combine(d, st), tz)
        if en <= st:
            edt = timezone.make_aware(datetime.combine(d + timedelta(days=1), en), tz)
        else:
            edt = timezone.make_aware(datetime.combine(d, en), tz)

        blocks.append((sdt, edt))
    return blocks


def build_slots_from_busy_daily(busy_items: List[dict], week_start: date, prefs: Prefs) -> List[Slot]:
    """
    Tạo slot trong study window (default 06:00-23:00) rồi trừ busy blocks theo từng date.
    week_start = min(date busy) (do views quyết định).
    """
    tz = timezone.get_current_timezone()
    busy_blocks = normalize_busy_blocks(busy_items)

    slots: List[Slot] = []
    sid = 0

    for d in range(prefs.horizon_days):
        day = week_start + timedelta(days=d)
        wd = day.weekday()  # 0..6 Mon..Sun

        sw_start = timezone.make_aware(datetime.combine(day, prefs.study_window_start), tz)
        sw_end = timezone.make_aware(datetime.combine(day, prefs.study_window_end), tz)

        # collect busy blocks overlapping study window
        day_busy: List[Tuple[datetime, datetime]] = []
        for (bs, be) in busy_blocks:
            clipped = _clip_interval(bs, be, sw_start, sw_end)
            if clipped:
                day_busy.append(clipped)

        day_busy = _merge_intervals(day_busy)
        free_blocks = _subtract_intervals((sw_start, sw_end), day_busy)

        # cut into fixed sessions
        for fs, fe in free_blocks:
            cur = fs
            while cur + timedelta(minutes=prefs.session_len_min) <= fe:
                nxt = cur + timedelta(minutes=prefs.session_len_min)
                slots.append(Slot(
                    id=sid,
                    start=cur,
                    end=nxt,
                    day_idx=wd,
                    is_focus=False,
                ))
                sid += 1
                cur = nxt

    # mark focus (nếu bạn vẫn dùng)
    for s in slots:
        s.is_focus = mark_focus(s, prefs.focus_windows or [])

    return slots

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
        diff = getattr(task, "difficulty", 3)  # default difficulty = 3
        easy_bonus = (1.0 / max(1, diff)) + (1.0 / max(0.5, task.estimate_min / 60.0))
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

    # (2) đủ slot cho mỗi task (mềm – thiếu giờ được đưa vào Y, nhưng không được dư)
    for t in tasks:
        xs = [X[(t.id, sid)] for sid in allowed[t.id]]
        # sum(xs): số slot thực sự được gán
        # Y[t.id]: số slot thiếu (0..req_slots)
        # => tổng = req_slots => không thể gán dư
        model.Add(sum(xs) + Y[t.id] == req_slots[t.id])


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
            
    # (6) cap practice per day để "rải đều" (dev default)
    # task.kind == "practice" chỉ nên chiếm tối đa prefs.max_practice_min_per_day mỗi ngày
    for d, sids in day_slots.items():
        practice_vars = []
        for t in tasks:
            if t.kind != "practice":
                continue
            for sid in sids:
                if (t.id, sid) in X:
                    practice_vars.append(X[(t.id, sid)])
        if practice_vars:
            model.Add(sum(practice_vars) * slot_min <= prefs.max_practice_min_per_day)

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

    frag_terms = list(START.values())

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
