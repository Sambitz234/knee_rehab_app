import json
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Exercise, ExerciseSession

# Convention: 0=Sun, 1=Mon, ... 6=Sat
def _dow(d: date) -> int:
    # Python: Monday=0..Sunday=6; convert to 0=Sun
    py = d.weekday()  # 0 Mon .. 6 Sun
    return (py + 1) % 7

def current_week_range(today: date | None = None):
    today = today or date.today()
    # make week Mon..Sun for summary while still using 0=Sun storage
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

def weekly_adherence(db: Session, today: date | None = None):
    monday, sunday = current_week_range(today)
    # Gather all exercises & sum scheduled occurrences this week
    exercises = db.query(Exercise).all()
    scheduled_total = 0
    for ex in exercises:
        sched = json.loads(ex.schedule_dow or "[]")
        # count days in Mon..Sun with dow in sched
        for i in range(7):
            d = monday + timedelta(days=i)
            if _dow(d) in sched:
                scheduled_total += 1

    # Completed = sessions within week
    completed_total = db.query(func.count(ExerciseSession.id))\
        .filter(ExerciseSession.date >= monday, ExerciseSession.date <= sunday)\
        .scalar()

    adherence_pct = 0.0
    if scheduled_total > 0:
        adherence_pct = round(100.0 * float(completed_total) / float(scheduled_total), 2)

    return {
        "week_start": monday,
        "week_end": sunday,
        "scheduled_count": int(scheduled_total),
        "completed_count": int(completed_total),
        "adherence_pct": adherence_pct
    }

def progress_series(db: Session, metric: str, days: int = 30):
    assert metric in {"rom_deg", "pain_0_10"}
    end = date.today()
    start = end - timedelta(days=days-1)

    # Build a dict of date -> aggregated value (avg by day)
    rows = db.query(ExerciseSession.date,
                    func.avg(getattr(ExerciseSession, metric)))\
             .filter(ExerciseSession.date >= start,
                     ExerciseSession.date <= end,
                     getattr(ExerciseSession, metric).isnot(None))\
             .group_by(ExerciseSession.date)\
             .order_by(ExerciseSession.date)\
             .all()

    by_date = {r[0]: float(r[1]) for r in rows}

    points = []
    d = start
    while d <= end:
        points.append({"date": d, "value": by_date.get(d)})
        d += timedelta(days=1)

    return {"metric": metric, "points": points}
