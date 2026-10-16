# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for dropcheck.py (no network)."""
import unittest
from datetime import date, timedelta

import dropcheck as dc


def days(first, n):
    d0 = date.fromisoformat(first)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


def synthetic():
    """Author 1 posts daily in A and B and stops; author 2 posts twice per window;
    author 3 appears only in C; one post has no author; one falls on a change day."""
    posts = []
    for d in days("2026-08-27", 16) + days("2026-09-12", 16):
        posts.append((1, d, False, ("seo",)))
    for d in ("2026-08-28", "2026-09-05", "2026-09-13", "2026-09-20", "2026-10-01", "2026-10-10"):
        posts.append((2, d, True, ("python",)))
    for d in ("2026-10-02", "2026-10-03", "2026-10-04"):
        posts.append((3, d, True, ("ai",)))
    posts.append((None, "2026-09-15", False, ()))
    posts.append((2, "2026-09-28", True, ("python",)))
    return posts


def transition(gap_placebo, gap_test, heavy, occasional):
    """Minimal analyse() output for predictions(): gaps via ratios, retentions as given."""
    out = []
    for kind, g, (h, o) in (("placebo", gap_placebo, (heavy[0], occasional[0])),
                            ("test", gap_test, (heavy[1], occasional[1]))):
        out.append({"kind": kind, "engaged_ratio": 1.0, "zero_engagement_ratio": 1.0 + g,
                    "classes": {"heavy": {"retention": h}, "regular": {"retention": 1.0},
                                "occasional": {"retention": o}}})
    return {"transitions": out}


class TestWindows(unittest.TestCase):
    def test_days(self):
        self.assertEqual([dc.days_in(w) for w in ("A", "B", "C")], [16, 16, 15])

    def test_window_of(self):
        self.assertIsNone(dc.window_of("2026-08-26"))
        self.assertEqual(dc.window_of("2026-08-27"), "A")
        self.assertEqual(dc.window_of("2026-09-11"), "A")
        self.assertEqual(dc.window_of("2026-09-12"), "B")
        self.assertEqual(dc.window_of("2026-09-27"), "B")
        self.assertIsNone(dc.window_of("2026-09-28"))
        self.assertIsNone(dc.window_of("2026-09-29"))
        self.assertEqual(dc.window_of("2026-09-30"), "C")
        self.assertEqual(dc.window_of("2026-10-14"), "C")
        self.assertIsNone(dc.window_of("2026-10-15"))

    def test_author_class(self):
        self.assertEqual([dc.author_class(n) for n in (40, 16, 15, 4, 3, 1)],
                         ["heavy", "heavy", "regular", "regular", "occasional", "occasional"])
        self.assertIsNone(dc.author_class(0))

    def test_listing_path(self):
        self.assertEqual(dc.listing_path(1000, 3, "tok"), "/articles/latest?per_page=1000&page=3&item=tok")


class TestAnalyse(unittest.TestCase):
    def setUp(self):
        self.an = dc.analyse(synthetic())

    def test_windows(self):
        w = self.an["windows"]
        self.assertEqual([w[k]["posts"] for k in "ABC"], [18, 19, 5])
        self.assertEqual([w[k]["authors"] for k in "ABC"], [2, 2, 2])
        self.assertAlmostEqual(w["B"]["zero_engagement_per_day"], 17 / 16)
        self.assertAlmostEqual(w["C"]["engaged_per_day"], 5 / 15)
        self.assertEqual(self.an["daily"]["2026-09-28"], {"posts": 1, "engaged": 1})

    def test_placebo(self):
        t = self.an["transitions"][0]
        self.assertEqual((t["from"], t["to"], t["kind"]), ("A", "B", "placebo"))
        self.assertEqual(t["classes"]["heavy"]["authors"], 1)
        self.assertAlmostEqual(t["classes"]["heavy"]["retention"], 1.0)
        self.assertAlmostEqual(t["classes"]["occasional"]["retention"], 1.0)
        self.assertEqual(t["classes"]["regular"]["authors"], 0)
        self.assertIsNone(t["classes"]["regular"]["retention"])
        self.assertEqual(t["newcomers"]["authors"], 0)
        self.assertAlmostEqual(t["engaged_ratio"], 1.0)
        self.assertAlmostEqual(t["zero_engagement_ratio"], 17 / 16)

    def test_test_transition(self):
        t = self.an["transitions"][1]
        h, o = t["classes"]["heavy"], t["classes"]["occasional"]
        self.assertAlmostEqual(h["retention"], 0.0)
        self.assertEqual(h["authors_stopped"], 1)
        self.assertAlmostEqual(h["per_day_from_stopped"], 1.0)
        self.assertAlmostEqual(o["retention"], 16 / 15)
        self.assertEqual(t["newcomers"]["authors"], 1)
        self.assertAlmostEqual(t["newcomers"]["per_day_to"], 0.2)
        self.assertAlmostEqual(t["authored_per_day_from"], 18 / 16)
        self.assertAlmostEqual(t["authored_per_day_to"], 5 / 15)
        self.assertAlmostEqual(t["engaged_ratio"], (5 / 15) / (2 / 16))
        self.assertAlmostEqual(t["zero_engagement_ratio"], 0.0)

    def test_predictions_supported(self):
        p = dc.predictions(self.an)
        self.assertTrue(p["P1"]["holds"])
        self.assertTrue(p["P2"]["holds"])
        self.assertEqual(p["verdict"], "SUPPORTED")

    def test_tags(self):
        old = dc.MIN_TAG_POSTS_B
        dc.MIN_TAG_POSTS_B = 2
        try:
            rows = dc.analyse(synthetic())["tags"]
        finally:
            dc.MIN_TAG_POSTS_B = old
        self.assertEqual([r["tag"] for r in rows], ["seo", "python"])
        self.assertAlmostEqual(rows[0]["fall_per_day"], 1.0)
        self.assertAlmostEqual(rows[0]["ratio_C_B"], 0.0)
        self.assertAlmostEqual(rows[1]["per_day_C"], 2 / 15)
        self.assertEqual(self.an["tags"], [])

    def test_report_renders(self):
        meta = {"snapshot_at": "2026-10-17T00:00:00+00:00", "posts": 44, "since": "2026-08-27",
                "stopped": "reached since", "coverage": {"pages": 1, "cached_pages": 0, "duplicate_ids": 0,
                                                         "max_hole_minutes": 0.0}}
        g = dc.gate({"2026-09-01": 100}, {"2026-09-01": 100})
        text = dc.report(self.an, dc.predictions(self.an), g, meta)
        self.assertIn("## Verdict: SUPPORTED", text)
        self.assertIn("Coverage gate", text)
        self.assertIn("PASS", text)
        self.assertNotIn("user_id", text)
        text2 = dc.report(self.an, dc.predictions(self.an), {"pass": None}, meta)
        self.assertIn("not checked", text2)


class TestPredictions(unittest.TestCase):
    def test_not_supported(self):
        an = transition(0.0, 0.0, (0.5, 0.5), (0.8, 0.8))
        p = dc.predictions(an)
        self.assertFalse(p["P1"]["holds"])
        self.assertFalse(p["P2"]["holds"])
        self.assertEqual(p["verdict"], "NOT SUPPORTED")

    def test_mixed(self):
        an = transition(0.0, -0.3, (0.5, 0.5), (0.8, 0.8))
        p = dc.predictions(an)
        self.assertTrue(p["P1"]["holds"])
        self.assertFalse(p["P2"]["holds"])
        self.assertEqual(p["verdict"], "MIXED")

    def test_placebo_gap_blocks_p1(self):
        an = transition(-0.2, -0.5, (0.5, 0.2), (0.8, 0.8))
        p = dc.predictions(an)
        self.assertFalse(p["P1"]["holds"])
        self.assertTrue(p["P2"]["holds"])
        self.assertEqual(p["verdict"], "MIXED")

    def test_occasional_fall_blocks_p2(self):
        an = transition(0.0, -0.3, (0.5, 0.2), (0.8, 0.6))
        self.assertFalse(dc.predictions(an)["P2"]["holds"])

    def test_missing_retention(self):
        an = transition(0.0, -0.3, (None, 0.2), (0.8, 0.8))
        self.assertFalse(dc.predictions(an)["P2"]["holds"])


class TestGate(unittest.TestCase):
    def test_fail(self):
        g = dc.gate({"2026-09-01": 100, "2026-09-02": 200}, {"2026-09-01": 100, "2026-09-02": 203})
        self.assertFalse(g["pass"])
        self.assertEqual(g["worst_day"], "2026-09-02")
        self.assertAlmostEqual(g["worst_diff"], -3 / 203)

    def test_pass_and_range(self):
        g = dc.gate({"2026-09-01": 100, "2026-09-02": 201, "2026-08-20": 1},
                    {"2026-09-01": 100, "2026-09-02": 203, "2026-08-20": 9000, "2026-10-16": 4014})
        self.assertTrue(g["pass"])
        self.assertEqual(g["checked_days"], 2)

    def test_missing_day(self):
        g = dc.gate({}, {"2026-09-01": 100})
        self.assertFalse(g["pass"])
        self.assertAlmostEqual(g["worst_diff"], -1.0)

    def test_parse_reference(self):
        text = "date,posts,not_disclosed\n2026-09-28,8226,7941\n2026-09-29,6136,5882\n"
        self.assertEqual(dc.parse_reference(text), {"2026-09-28": 8226, "2026-09-29": 6136})


if __name__ == "__main__":
    unittest.main()
