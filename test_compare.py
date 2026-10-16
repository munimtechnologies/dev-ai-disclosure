# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for compare.py (no network)."""
import json
import os
import tempfile
import unittest

import compare

HEADER = "date,posts,not_disclosed,no_ai,some_ai,fully_autonomous,other,share_any_label\n"


def daily(rows):
    return HEADER + "".join(f"{d},{n},{n},0,0,0,0,0.0\n" for d, n in rows)


class TestParse(unittest.TestCase):
    def test_parse_daily_reads_posts_per_date(self):
        self.assertEqual(compare.parse_daily(daily([("2026-08-12", 8985), ("2026-08-13", 7924)])),
                         {"2026-08-12": 8985, "2026-08-13": 7924})

    def test_parse_daily_ignores_extra_columns(self):
        text = "date,posts,burst_posts\n2026-08-12,10,3\n"
        self.assertEqual(compare.parse_daily(text), {"2026-08-12": 10})


class TestWindow(unittest.TestCase):
    def test_common_window_drops_each_last_day(self):
        a = {d: 1 for d in ("2026-08-12", "2026-08-13", "2026-08-14", "2026-08-15")}
        b = {d: 1 for d in ("2026-08-13", "2026-08-14", "2026-08-15", "2026-08-16")}
        self.assertEqual(compare.common_window({"a": a, "b": b}), ("2026-08-13", "2026-08-14"))

    def test_days_between_is_inclusive_and_crosses_months(self):
        self.assertEqual(compare.days_between("2026-09-29", "2026-10-02"),
                         ["2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02"])


class TestCompare(unittest.TestCase):
    def test_loss(self):
        c = compare.compare({"d1": 100, "d2": 200}, {"d1": 100, "d2": 150}, ["d1", "d2"])
        self.assertEqual((c["posts_base"], c["posts"], c["ratio"]), (300, 250, 0.8333))
        self.assertEqual((c["max_abs_day_diff"], c["max_abs_day"]), (50, "d2"))
        self.assertEqual((c["max_day_loss"], c["max_day_loss_day"]), (0.25, "d2"))
        self.assertEqual((c["days_within_1pct"], c["days_losing_over_5pct"]), (1, 1))

    def test_gain_is_not_a_loss(self):
        c = compare.compare({"d1": 100}, {"d1": 103}, ["d1"])
        self.assertEqual((c["max_day_loss"], c["max_day_loss_day"]), (0.0, None))
        self.assertEqual((c["max_abs_day_diff"], c["days_within_1pct"]), (3, 0))

    def test_identical(self):
        c = compare.compare({"d1": 5, "d2": 7}, {"d1": 5, "d2": 7}, ["d1", "d2"])
        self.assertEqual((c["ratio"], c["max_abs_day_diff"], c["max_abs_day"]), (1.0, 0, None))
        self.assertEqual(c["days_within_1pct"], 2)


class TestMain(unittest.TestCase):
    def test_local_run_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = {"v1": [("2026-08-12", 100), ("2026-08-13", 90), ("2026-08-14", 50)],
                    "v3": [("2026-08-12", 60), ("2026-08-13", 90), ("2026-08-14", 80), ("2026-08-15", 9)],
                    "v5": [("2026-08-12", 40), ("2026-08-13", 88), ("2026-08-14", 80), ("2026-08-15", 9)],
                    "v7": [("2026-08-12", 99), ("2026-08-13", 90), ("2026-08-14", 80), ("2026-08-15", 9)]}
            for name, rows in data.items():
                with open(os.path.join(tmp, f"{name}-daily.csv"), "w", encoding="utf-8") as f:
                    f.write(daily(rows))
            out = os.path.join(tmp, "out")
            self.assertEqual(compare.main(["--local", tmp, "--out-dir", out]), 0)
            with open(os.path.join(out, "compare.json"), encoding="utf-8") as f:
                res = json.load(f)
            # v1's last day (08-14) is partial, so the window ends on 08-13
            self.assertEqual(res["window"], ["2026-08-12", "2026-08-13"])
            self.assertEqual(res["sweeps"]["v1"]["posts"], 190)
            self.assertEqual(res["sweeps"]["v7"]["posts"], 189)
            self.assertEqual(res["sweeps"]["v5"]["max_day_loss_day"], "2026-08-12")
            with open(os.path.join(out, "COMPARE.md"), encoding="utf-8") as f:
                text = f.read()
            self.assertIn("| v7 | 2026-10-16 16:32 |", text)
            self.assertIn("100.00%", text)

    def test_missing_sweep_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(compare.main(["--local", tmp, "--out-dir", os.path.join(tmp, "out")]), 1)


if __name__ == "__main__":
    unittest.main()
