# Team Performance Tracker

Turn a raw log of task-completion timestamps into a daily Slack summary:
who's on pace, who's genuinely slower than *their own* usual rate — and
no false alarms from a flat team-wide bar that ignores how differently
people actually work.

I built and ran a related automation (Make.com, with Slack alerts) for
tracking my own team's throughput. This is an independent Python rebuild
of the underlying logic on fully synthetic data — not an export of that
scenario, and not a claim that this exact codebase ran in production.

## Two decisions that aren't arbitrary

1. **The workday boundary isn't midnight.** Someone who starts at 21:00
   and finishes at 01:30 is having one session, not two half-days split
   either side of midnight — counting it that way makes their pace look
   half of what it is. A timestamp belongs to the day it *started*
   (configurable cutoff, default 4am).
2. **Pace comes from the median gap between tasks, not count ÷ day.** A
   simple average quietly includes lunch, meetings, idle time. Gaps
   longer than a break-length threshold are excluded before taking the
   median — which is also what makes the number useful: multiply it out
   and you get "this many on a full productive day," not just a count.

## Why compare each person to their OWN history, not a team average

A flat team-wide bar either nags the naturally slower person every
single day, or never notices the naturally fast person actually
slipping. Comparing someone to their own baseline catches a real
slowdown regardless of where their normal pace sits.

## Results — the alert actually firing, not just described

Three synthetic team members, four days of activity. One (`Sam Park`)
has a deliberately slower final day built into the demo data generator,
specifically so the alert can be shown catching something real:

```
stage 1 — establish baseline from days 1-3:
  Alex Rivera: 32/hr
  Jordan Lee:  37/hr
  Sam Park:    26/hr
  (0 flagged — nothing to compare against yet)

stage 2 — run day 4 against that baseline:
  Alex Rivera: 32/hr   (unchanged)
  Jordan Lee:  38/hr   (unchanged)
  Sam Park:    10/hr   ⚠️ down 61% vs baseline
```

Alex and Jordan — whose pace didn't change — correctly get **no** alert.
Only the person who actually slowed down does. That's the real test of
a "compare to your own baseline" design: it has to stay quiet for normal
day-to-day variation and only speak up for an actual drop.

## Architecture

```
tracker/
├── metrics.py    workday boundary, throughput calculation, baseline comparison
├── alerts.py      the Slack webhook — a single POST, no SDK
└── report.py      reads events.csv, runs both, posts, updates the baseline
tests/
└── test_metrics.py   8 tests on hand-built timestamps, no demo-data dependency
make_demo_data.py      generates the synthetic events (seeded, reproducible)
```

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m unittest tests.test_metrics -v      # 8 tests, no setup needed

python make_demo_data.py                       # writes data/events_history.csv + events_today.csv
python -m tracker.report data/events_history.csv   # establishes the baseline
python -m tracker.report data/events_today.csv     # compares today against it
```

Add your own `SLACK_WEBHOOK_URL` to `.env` for a real post; without one,
the exact message just prints instead.

## Honest limitations

- `events.csv` has to already exist — this doesn't include a collector;
  in production that was a Make.com scenario reading from wherever the
  team's tasks are actually logged, not something this repo rebuilds.
- A 25% drop threshold is a reasonable starting default, not a
  universally correct one — the right number depends on how noisy a
  given team's day-to-day pace naturally is.
- No notion of task *difficulty* — ten easy tasks and ten hard ones count
  the same. A real deployment would need that nuance; this demo doesn't.

---
Independent re-implementation, built on synthetic data as a portfolio
piece. Not affiliated with, and contains no code or data from, any employer.
