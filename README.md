# Team Performance Tracker

Turn a raw log of task-completion timestamps into a weekly Slack summary:
who hit their quota, who's genuinely behind — both against a flat team
target and against *their own* usual pace — with no false alarms from a
bar that ignores how differently people actually work.

I built and ran a related automation (Make.com, triggered daily, posting
a weekly summary to Slack) that reads a sheet counting completed work per
coordinator against a daily norm. This is an independent Python rebuild
of that underlying logic on fully synthetic data — not an export of that
scenario, and not a claim that this exact codebase ran in production.

## Three decisions that aren't arbitrary

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
3. **Two independent signals, not one.** A flat weekly target (`target:
   100 rows`) answers "did they hit the number." A comparison against
   their own baseline answers "did *they* slow down" — someone whose
   normal pace is naturally below the team target shouldn't get flagged
   every single week for being who they always are; someone whose normal
   pace is comfortably above target can still genuinely slip. The two
   checks catch different things and the report shows both.

## Results — both signals actually firing, not just described

Three synthetic team members, two full weeks. One (`Sam Park`) has a
deliberately slower second week built into the demo data generator —
fewer tasks *and* a slower pace — specifically so both signals can be
shown catching the same real thing, independently:

```
week 1 — establishes the baseline:
  :red_circle: Behind     Sam Park:    96 rows (target: 100,  96.0%)
  :white_check_mark: On Track  Alex Rivera: 112 rows (target: 100, 112.0%)
  :white_check_mark: On Track  Jordan Lee:  128 rows (target: 100, 128.0%)
  Team Total: 336 rows

week 2 — compared against that baseline:
  :red_circle: Behind     Sam Park:     34 rows (target: 100,  34.0%)  ⚠️ down 62% vs own baseline
  :white_check_mark: On Track  Alex Rivera: 108 rows (target: 100, 108.0%)
  :white_check_mark: On Track  Jordan Lee:  131 rows (target: 100, 131.0%)
  Team Total: 273 rows
```

Alex and Jordan — whose pace didn't change — correctly get **no**
baseline alert in either week, even though Alex's count moved around a
little; that's normal variation, not a slowdown. Sam Park gets flagged
by *both* signals in week 2, for the same real reason, independently
computed. That agreement is the actual test of the design: a target-only
report would have called Sam "behind" in week 1 too, which is true but
not new information — the baseline comparison is what tells you
something actually *changed*.

## Architecture

```
tracker/
├── metrics.py    workday boundary, throughput calc, target & baseline comparison
├── alerts.py      formats the real Slack message style + the webhook POST
└── report.py      reads events.csv, runs both, posts, updates the baseline
tests/
└── test_metrics.py   8 tests on hand-built timestamps, no demo-data dependency
make_demo_data.py      generates two synthetic weeks (seeded, reproducible)
```

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m unittest tests.test_metrics -v      # 8 tests, no setup needed

python make_demo_data.py                       # writes two weeks of synthetic events
python -m tracker.report data/events_history.csv --target 100     # establishes the baseline
python -m tracker.report data/events_this_week.csv --target 100   # compares this week against it
```

Add your own `SLACK_WEBHOOK_URL` to `.env` for a real post; without one,
the exact message just prints instead.

## Honest limitations

- `events.csv` has to already exist — this doesn't include a collector;
  in production that was a Make.com scenario reading from wherever the
  team's tasks are actually logged, not something this repo rebuilds.
- A 25% drop threshold and a 100-row weekly target are reasonable demo
  defaults, not universally correct ones — the right numbers depend on
  the specific team and task.
- No notion of task *difficulty* — ten easy tasks and ten hard ones count
  the same. A real deployment would need that nuance; this demo doesn't.

---
Independent re-implementation, built on synthetic data as a portfolio
piece. Not affiliated with, and contains no code or data from, any employer.
