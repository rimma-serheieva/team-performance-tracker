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

from tracker.metrics import status_vs_target


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


DIVIDER = "━" * 24


def format_weekly_report(team_metrics, week_label, target=100, drops=None):
    """Matches the real Slack message this generalizes: a status emoji
    and "behind/on track" label per person, each against a flat weekly
    quota, then a team total. Deliberately simple and scannable in a
    phone notification — a manager reading this on their phone needs the
    answer in the first two words of each line, not in a table.
    """
    drops = drops or {}
    lines = [":bar_chart: *Weekly Performance Report*",
            ":date: %s" % week_label, DIVIDER]

    behind, on_track, total = [], [], 0
    for person, m in sorted(team_metrics.items()):
        count = m["items"] if m else 0
        total += count
        status, pct = status_vs_target(count, target)
        line = "%s %s %s: %d rows (target: %d, %.1f%%)" % (
            ":red_circle:" if status == "behind" else ":white_check_mark:",
            "Behind" if status == "behind" else "On Track", person, count, target, pct)
        if person in drops:
            line += "  ⚠️ down %.0f%% vs own baseline" % drops[person]
        (behind if status == "behind" else on_track).append(line)
    lines += behind + on_track
    lines.append(DIVIDER)
    lines.append(":checkered_flag: *Team Total:* %d rows where coordinators worked" % total)
    return "\n".join(lines)
