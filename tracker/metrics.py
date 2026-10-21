"""
metrics.py — turn a raw stream of task-completion timestamps into an
honest per-person throughput number.

Two decisions here come directly from a real operations problem, not
from guessing at what a metrics script should look like:

1. THE WORKDAY BOUNDARY ISN'T MIDNIGHT. A team member who starts at 21:00
   and finishes at 01:30 is having one session, not two separate half-days
   either side of midnight — counting it as two makes their pace look
   half of what it really is. The fix: a timestamp belongs to the day it
   STARTED, using a configurable cutoff hour (default 4am) rather than 0.

2. PACE IS MEASURED FROM THE MEDIAN GAP BETWEEN CONSECUTIVE TASKS, NOT A
   SIMPLE COUNT/DAY. A simple average silently includes idle time, lunch,
   meetings — none of which reflect how fast someone works. Gaps longer
   than a chosen "this must be a break" threshold are excluded before
   taking the median, so the number reflects active pace. This also makes
   the result directly useful: multiply it out and you get "this many per
   a full productive day," a number a manager can actually act on.
"""
import collections
import datetime
import statistics

DAY_START_HOUR = 4
BREAK_SECONDS = 600       # a gap longer than this is a break, not work


def workday(ts, day_start_hour=DAY_START_HOUR):
    """Which working day does this timestamp belong to?"""
    return (ts - datetime.timedelta(hours=day_start_hour)).date()


def throughput(timestamps, day_start_hour=DAY_START_HOUR, break_seconds=BREAK_SECONDS,
              productive_hours=6.5):
    """-> dict of real pace metrics for one person, or None with no data.

    `productive_hours` is deliberately not 8 — a full workday includes
    breaks, meetings, and context-switching that aren't captured in the
    gaps between task completions, so projecting against the realistic
    productive fraction of a day gives a usable, defensible number rather
    than an inflated one.
    """
    stamps = sorted(timestamps)
    if not stamps:
        return None
    by_day = collections.defaultdict(list)
    for s in stamps:
        by_day[workday(s, day_start_hour)].append(s)

    gaps, active_hours = [], 0.0
    for day_stamps in by_day.values():
        day_stamps.sort()
        day_gaps = [(day_stamps[i + 1] - day_stamps[i]).total_seconds()
                   for i in range(len(day_stamps) - 1)]
        real_gaps = [g for g in day_gaps if 0 < g <= break_seconds]
        gaps += real_gaps
        active_hours += sum(real_gaps) / 3600

    median_gap = statistics.median(gaps) if gaps else 0
    per_hour = 3600 / median_gap if median_gap else 0
    return {
        "items": len(stamps),
        "days_worked": len(by_day),
        "mean_per_day": len(stamps) / len(by_day),
        "active_hours": round(active_hours, 1),
        "median_gap_seconds": round(median_gap, 1),
        "items_per_hour": round(per_hour, 1),
        "projected_full_day": round(per_hour * productive_hours, 1),
    }


def status_vs_target(count, target):
    """The simpler, real-world-facing metric: raw completed count against
    a flat daily/weekly quota, not a rate. This is deliberately a
    SEPARATE, coarser signal from throughput() above — a manager-facing
    weekly report wants "did they hit the number," which a pace
    calculation doesn't directly answer (someone can work fast in short
    bursts and still miss a volume target)."""
    pct = round(100 * count / target, 1) if target else 0.0
    return ("on_track" if count >= target else "behind"), pct


def compare_to_baseline(current, baseline, drop_threshold=0.25):
    """Has this person's pace dropped meaningfully versus their own past
    baseline? Comparing someone to their OWN history, not to a team
    average, matters: people genuinely work at different speeds, and a
    flat team-wide bar would either nag the naturally slower person every
    day or never catch the naturally fast person slipping."""
    if not current or not baseline or not baseline["items_per_hour"]:
        return False, 0.0
    drop = 1 - (current["items_per_hour"] / baseline["items_per_hour"])
    return drop >= drop_threshold, round(drop * 100, 1)
