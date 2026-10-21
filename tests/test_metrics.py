"""Unit tests for the core metrics logic — small, hand-built timestamp
lists, no demo-data generation involved, so each test is obviously
checking one specific behaviour."""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from tracker import metrics


def dt(h, m=0):
    return datetime.datetime(2026, 10, 20, h, m)


class TestWorkday(unittest.TestCase):
    def test_a_late_session_belongs_to_the_day_it_started(self):
        """01:30 after a 21:00 start is the SAME working day, not the
        next one — the whole reason the 4am boundary exists."""
        start_of_session = metrics.workday(dt(21, 0))
        end_of_session = metrics.workday(datetime.datetime(2026, 10, 21, 1, 30))
        self.assertEqual(start_of_session, end_of_session)

    def test_a_normal_daytime_timestamp_is_unaffected(self):
        self.assertEqual(metrics.workday(dt(14, 0)).day, 20)


class TestThroughput(unittest.TestCase):
    def test_empty_input_returns_none(self):
        self.assertIsNone(metrics.throughput([]))

    def test_steady_pace_gives_a_sensible_items_per_hour(self):
        # 10 tasks, exactly 2 minutes apart -> 30/hour
        stamps = [dt(9, 0) + datetime.timedelta(minutes=2 * i) for i in range(10)]
        m = metrics.throughput(stamps)
        self.assertAlmostEqual(m["items_per_hour"], 30, delta=0.5)
        self.assertEqual(m["items"], 10)

    def test_a_long_gap_is_excluded_as_a_break_not_counted_as_slow_work(self):
        """A 2-hour lunch gap must not drag the pace number down — it's
        excluded from the gap calculation entirely, matching the real
        production logic this generalizes."""
        fast_pace = [dt(9, 0) + datetime.timedelta(minutes=2 * i) for i in range(5)]
        after_lunch = [dt(13, 0) + datetime.timedelta(minutes=2 * i) for i in range(5)]
        m = metrics.throughput(fast_pace + after_lunch)
        self.assertAlmostEqual(m["items_per_hour"], 30, delta=0.5)


class TestBaselineComparison(unittest.TestCase):
    def test_a_real_slowdown_is_flagged(self):
        baseline = {"items_per_hour": 30}
        today = {"items_per_hour": 15}        # 50% slower
        flagged, pct = metrics.compare_to_baseline(today, baseline, drop_threshold=0.25)
        self.assertTrue(flagged)
        self.assertAlmostEqual(pct, 50.0, delta=0.5)

    def test_normal_day_to_day_variation_is_not_flagged(self):
        baseline = {"items_per_hour": 30}
        today = {"items_per_hour": 27}        # 10% slower — just noise
        flagged, _ = metrics.compare_to_baseline(today, baseline, drop_threshold=0.25)
        self.assertFalse(flagged)

    def test_no_baseline_yet_never_flags(self):
        """The first day anyone's tracked, there's nothing to compare
        against — this must not crash or false-positive."""
        flagged, pct = metrics.compare_to_baseline({"items_per_hour": 10}, None)
        self.assertFalse(flagged)
        self.assertEqual(pct, 0.0)


if __name__ == "__main__":
    unittest.main()
