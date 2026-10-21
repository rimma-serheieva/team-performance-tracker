"""
report.py — orchestrates metrics.py + alerts.py into one daily run.

    python -m tracker.report events.csv

Reads a CSV of {person, timestamp} task-completion events, computes real
per-person throughput, compares each person against their OWN stored
baseline (not a flat team-wide bar — see metrics.compare_to_baseline for
why), posts a Slack summary, and updates the baseline file for next time.

Resumable in the sense that matters here: baselines persist in
`results/baseline.json` between runs, so each day's comparison is against
real history, not recomputed from scratch.
"""
import argparse
import collections
import csv
import datetime
import json
import os
import sys

from tracker import alerts, metrics

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, os.pardir, "results")
BASELINE_PATH = os.path.join(RESULTS, "baseline.json")


def load_events(path):
    by_person = collections.defaultdict(list)
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ts = datetime.datetime.fromisoformat(row["timestamp"])
            by_person[row["person"]].append(ts)
    return by_person


def load_baseline():
    if os.path.exists(BASELINE_PATH):
        return json.load(open(BASELINE_PATH, encoding="utf-8"))
    return {}


def save_baseline(current_metrics):
    os.makedirs(RESULTS, exist_ok=True)
    existing = load_baseline()
    for person, m in current_metrics.items():
        if m:
            existing[person] = m    # today becomes tomorrow's comparison point
    json.dump(existing, open(BASELINE_PATH, "w", encoding="utf-8"), indent=2)


def run(events_path, drop_threshold=0.25, webhook_url=None, update_baseline=True):
    events = load_events(events_path)
    baseline = load_baseline()

    team_metrics, drops = {}, {}
    for person, timestamps in events.items():
        m = metrics.throughput(timestamps)
        team_metrics[person] = m
        flagged, pct = metrics.compare_to_baseline(m, baseline.get(person), drop_threshold)
        if flagged:
            drops[person] = pct

    message = alerts.format_daily_summary(team_metrics, drops)
    alerts.send(message, webhook_url)
    if update_baseline:
        save_baseline(team_metrics)
    return team_metrics, drops


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("events_csv")
    ap.add_argument("--drop-threshold", type=float, default=0.25)
    ap.add_argument("--no-baseline-update", action="store_true")
    args = ap.parse_args()
    team_metrics, drops = run(args.events_csv, args.drop_threshold,
                              update_baseline=not args.no_baseline_update)
    print("\n%d team members, %d flagged below baseline" % (len(team_metrics), len(drops)))
