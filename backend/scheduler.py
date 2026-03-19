from datetime import date, timedelta
from typing import List, Dict, Set
from backend.plan_data import PLAN, END_DATE, START_DATE


def date_key(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def days_apart(a: date, b: date) -> int:
    return (b - a).days


def get_end_date() -> date:
    return date.fromisoformat(END_DATE)


def get_today() -> date:
    return date.today()


def build_day_snapshot(done_indices: Set[int], today: date) -> List[int]:
    """
    Calculate which readings should be assigned to `today`.
    Uses floor+remainder distribution so the plan always ends on Dec 31.
    """
    end = get_end_date()
    if today > end:
        return []

    pending = [i for i in range(len(PLAN)) if i not in done_indices]
    total_days = days_apart(today, end) + 1  # inclusive

    if not pending:
        return []

    base = len(pending) // total_days
    extras = len(pending) % total_days  # first `extras` days get base+1

    # today is always "day 0" of the remaining schedule
    count = base + 1 if extras > 0 else base
    count = max(1, count)
    return pending[:count]


def build_future_schedule(
    done_indices: Set[int],
    today_snap: List[int],
    today: date,
) -> Dict[str, List[dict]]:
    """
    Build a preview of future days' readings for the full plan view.
    Redistributes remaining pending readings (not done, not today) across future days.
    """
    end = get_end_date()
    days_after = days_apart(today, end)  # excludes today

    today_set = set(today_snap)
    future_pending = [
        i for i in range(len(PLAN))
        if i not in done_indices and i not in today_set
    ]

    sched: Dict[str, List[dict]] = {}

    if not future_pending or days_after <= 0:
        return sched

    base = len(future_pending) // days_after
    extras = len(future_pending) % days_after

    p = 0
    for d in range(1, days_after + 1):
        if p >= len(future_pending):
            break
        future_date = today + timedelta(days=d)
        key = date_key(future_date)

        if d == days_after:
            cnt = len(future_pending) - p
        else:
            cnt = base + 1 if (d - 1) < extras else base
            cnt = max(1, cnt)

        if cnt > 0:
            indices = future_pending[p:p + cnt]
            sched[key] = [
                {"index": i, "reading": PLAN[i][0], "category": PLAN[i][1]}
                for i in indices
            ]
            p += cnt

    return sched


def get_streak(streak_log: List) -> int:
    """Calculate current streak from StreakLog records."""
    completed_dates = {log.date for log in streak_log if log.completed}
    streak = 0
    check = get_today()
    while date_key(check) in completed_dates:
        streak += 1
        check -= timedelta(days=1)
    return streak
