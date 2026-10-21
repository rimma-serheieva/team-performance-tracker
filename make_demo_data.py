"""
make_demo_data.py — generate synthetic task-completion events for the demo.

Fully synthetic: fictional names, no real team's data. Two WEEKS, each
person with a real weekly total — because the actual report this
generalizes compares a weekly count against a flat weekly target
("100 rows, target 100"), not a single day against it. An earlier version
of this generator produced a partial-week baseline and a single-day
"today," which made every "behind target" comparison meaningless — fixed
by generating two full, comparable weeks.

Week 1 establishes each person's baseline. In week 2, one person's week
is deliberately low — both fewer tasks AND a slower pace — so the demo
can show two independent, CONSISTENT signals catching it: the weekly
total falls behind the flat target, and the pace-based baseline
comparison flags the same person for the same reason.
"""
import csv
import datetime
import os
import random

random.seed(42)
HERE = os.path.dirname(os.path.abspath(__file__))
WORK_DAYS_PER_WEEK = 5

# weekly total, mean seconds between tasks (pace)
BASELINE = {
    "Alex Rivera": (112, 95),
    "Jordan Lee": (128, 80),
    "Sam Park": (96, 115),
}
THIS_WEEK = {
    "Alex Rivera": (108, 97),     # normal week — small natural variance
    "Jordan Lee": (131, 78),      # normal week
    "Sam Park": (34, 300),        # the deliberate slowdown: fewer tasks, much slower pace
}


def gen_week(weekly_total, mean_gap, start_date):
    """Spread `weekly_total` tasks across WORK_DAYS_PER_WEEK days, with
    gaps drawn from `mean_gap` — not perfectly even per day, real days
    vary, but close enough for a demo."""
    per_day = [weekly_total // WORK_DAYS_PER_WEEK] * WORK_DAYS_PER_WEEK
    for i in range(weekly_total - sum(per_day)):
        per_day[i % WORK_DAYS_PER_WEEK] += 1
    random.shuffle(per_day)

    stamps = []
    for day_offset, n in enumerate(per_day):
        t = (start_date + datetime.timedelta(days=day_offset, hours=9,
                                             minutes=random.randint(-20, 20)))
        for _ in range(n):
            gap = max(10, random.gauss(mean_gap, mean_gap * 0.25))
            t += datetime.timedelta(seconds=gap)
            stamps.append(t)
    return stamps


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = sorted(rows, key=lambda r: r["timestamp"])
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["person", "timestamp"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main():
    week1_start = datetime.datetime(2026, 10, 12)
    week2_start = datetime.datetime(2026, 10, 19)

    history, this_week = [], []
    for person, (total, mean_gap) in BASELINE.items():
        for ts in gen_week(total, mean_gap, week1_start):
            history.append({"person": person, "timestamp": ts.isoformat()})
    for person, (total, mean_gap) in THIS_WEEK.items():
        for ts in gen_week(total, mean_gap, week2_start):
            this_week.append({"person": person, "timestamp": ts.isoformat()})

    hist_path = os.path.join(HERE, "data", "events_history.csv")
    week_path = os.path.join(HERE, "data", "events_this_week.csv")
    n1 = write_csv(hist_path, history)
    n2 = write_csv(week_path, this_week)
    print("%d events, week of %s -> %s (baseline)"
          % (n1, week1_start.date(), hist_path))
    print("%d events, week of %s -> %s (compare against baseline)"
          % (n2, week2_start.date(), week_path))


if __name__ == "__main__":
    main()
