"""
alerts.py — post a plain-text summary to Slack. Deliberately simple: a
single webhook POST, no SDK, no formatting library — the real version
this generalizes is exactly this, because a manager-facing alert needs to
be readable in a phone notification, not a dashboard.

No webhook configured -> prints instead of posting, and never raises.
A broken or missing alert channel should never take down the metrics run
that's feeding it.
"""
import json
import os
import urllib.request


def send(message, webhook_url=None):
    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("[no SLACK_WEBHOOK_URL configured — would have posted:]")
        print(message)
        return False
    try:
        data = json.dumps({"text": message}).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print("slack post failed: %s" % e)
        return False


def format_daily_summary(team_metrics, drops):
    """team_metrics: {person: metrics dict}. drops: {person: pct_drop}
    for anyone flagged against their own baseline."""
    lines = ["*Daily throughput summary*"]
    for person, m in sorted(team_metrics.items()):
        if not m:
            lines.append("• %s: no activity today" % person)
            continue
        flag = " ⚠️ down %.0f%% vs baseline" % drops[person] if person in drops else ""
        lines.append("• %s: %.0f/hr, %.0f items, %.1fh active%s"
                     % (person, m["items_per_hour"], m["items"], m["active_hours"], flag))
    if drops:
        lines.append("\n_%d team member(s) below their usual pace — may be worth a check-in,"
                     " not a problem on its own (meetings, a hard task, a bad day)._"
                     % len(drops))
    return "\n".join(lines)
