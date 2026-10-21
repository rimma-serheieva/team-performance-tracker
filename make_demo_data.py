"""
make_demo_data.py — generate synthetic task-completion events for the demo.

Fully synthetic: fictional names, no real team's data. Three people, four
days each, each with their own realistic pace (gaps drawn from a normal
distribution around a per-person mean). On the final day, one person's
gaps are deliberately widened — that's the case the baseline-drop alert
in tracker/metrics.py is supposed to catch, so the demo can show it
actually firing rather than describe it in the abstract.
"""
import csv
import datetime
import os
import random

random.seed(42)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "events.csv")

PEOPLE = {
    "Jordan Lee": 90,      # mean seconds between tasks
    "Sam Park": 140,
    "Alex Rivera": 110,
}
DAYS = 4
TASKS_PER_DAY = 35
SLOWDOWN_PERSON = "Sam Park"
SLOWDOWN_DAY = DAYS - 1          # 0-indexed: the final day
SLOWDOWN_FACTOR = 2.6


def gen_day(mean_gap, start, n, slow=False):
    stamps, t = [], start
    for _ in range(n):
        gap = max(10, random.gauss(mean_gap * (SLOWDOWN_FACTOR if slow else 1),
                                   mean_gap * 0.25))
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
    base = datetime.datetime(2026, 10, 19, 9, 0)
    history, today = [], []
    for day in range(DAYS):
        for person, mean_gap in PEOPLE.items():
            start = base + datetime.timedelta(days=day, minutes=random.randint(-20, 20))
            slow = (person == SLOWDOWN_PERSON and day == SLOWDOWN_DAY)
            bucket = today if day == SLOWDOWN_DAY else history
            for ts in gen_day(mean_gap, start, TASKS_PER_DAY, slow=slow):
                bucket.append({"person": person, "timestamp": ts.isoformat()})

    hist_path = os.path.join(HERE, "data", "events_history.csv")
    today_path = os.path.join(HERE, "data", "events_today.csv")
    n1 = write_csv(hist_path, history)
    n2 = write_csv(today_path, today)
    print("%d historical events -> %s (establishes the baseline)" % (n1, hist_path))
    print("%d today's events    -> %s (run against that baseline)" % (n2, today_path))


if __name__ == "__main__":
    main()
