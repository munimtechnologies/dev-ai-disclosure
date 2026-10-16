# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import random
import unittest
from datetime import datetime, timezone

import probe


def art(i, pub, **kw):
    a = {"id": i, "published_at": pub, "tag_list": ["a", "b"], "public_reactions_count": 1, "comments_count": 0}
    a.update(kw)
    return a


class PageStatsTests(unittest.TestCase):
    def test_counts_items_missing_fields_and_duplicates(self):
        batch = [art(10, "2026-10-01T10:00:00Z"), art(9, "2026-10-01T09:00:00Z"), art(9, "2026-10-01T09:00:00Z"),
                 {"id": 8}, {"published_at": "2026-10-01T08:00:00Z"}]
        s = probe.page_stats(batch)
        self.assertEqual(s["items"], 5)
        self.assertEqual(s["without_published_at"], 1)
        self.assertEqual(s["without_id"], 1)
        self.assertEqual(s["dup_within_page"], 1)
        self.assertEqual((s["min_id"], s["max_id"]), (8, 10))
        self.assertEqual(s["oldest"], "2026-10-01T08:00:00+00:00")
        self.assertEqual(s["newest"], "2026-10-01T10:00:00+00:00")
        self.assertEqual(s["ids"], [8, 9, 10])

    def test_empty_page(self):
        s = probe.page_stats([])
        self.assertEqual(s["items"], 0)
        self.assertIsNone(s["min_id"])
        self.assertIsNone(s["oldest"])


class AdjacentTests(unittest.TestCase):
    def test_disjoint_and_ordered(self):
        prev = probe.page_stats([art(10, "2026-10-01T10:00:00Z"), art(9, "2026-10-01T09:00:00Z")])
        cur = probe.page_stats([art(8, "2026-10-01T08:00:00Z"), art(7, "2026-10-01T07:00:00Z")])
        self.assertEqual(probe.adjacent_check(prev, cur), {"overlap_ids": 0, "time_order_ok": True})

    def test_overlap_from_shifted_page(self):
        prev = probe.page_stats([art(10, "2026-10-01T10:00:00Z"), art(9, "2026-10-01T09:00:00Z")])
        cur = probe.page_stats([art(9, "2026-10-01T09:00:00Z"), art(8, "2026-10-01T08:00:00Z")])
        self.assertEqual(probe.adjacent_check(prev, cur), {"overlap_ids": 1, "time_order_ok": True})

    def test_order_violation_from_stale_page(self):
        prev = probe.page_stats([art(10, "2026-10-01T10:00:00Z"), art(9, "2026-10-01T09:00:00Z")])
        cur = probe.page_stats([art(12, "2026-10-01T12:00:00Z"), art(11, "2026-10-01T11:00:00Z")])
        self.assertEqual(probe.adjacent_check(prev, cur)["time_order_ok"], False)


class GapAndClassifyTests(unittest.TestCase):
    def test_gap_candidates_excludes_seen_and_caps(self):
        rng = random.Random(1)
        c = probe.gap_candidates(1, 10, {2, 4, 6, 8, 10}, 3, rng)
        self.assertEqual(len(c), 3)
        self.assertTrue(all(i in {1, 3, 5, 7, 9} for i in c))
        self.assertEqual(probe.gap_candidates(1, 3, {1, 2, 3}, 5, rng), [])

    def test_classify(self):
        w0 = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)
        w1 = datetime(2026, 10, 2, 0, 0, tzinfo=timezone.utc)
        seen = {5}
        self.assertEqual(probe.classify(404, None, w0, w1, seen), "not_public")
        self.assertEqual(probe.classify(500, None, w0, w1, seen), "http_500")
        self.assertEqual(probe.classify(200, art(5, "2026-10-01T12:00:00Z"), w0, w1, seen), "live_listed")
        self.assertEqual(probe.classify(200, art(6, "2026-10-01T12:00:00Z"), w0, w1, seen), "live_absent_in_window")
        self.assertEqual(probe.classify(200, art(7, "2026-09-01T12:00:00Z"), w0, w1, seen), "live_outside_window")
        self.assertEqual(probe.classify(200, {"id": 8}, w0, w1, seen), "live_no_published_at")

    def test_slim_keeps_no_identity(self):
        a = art(5, "2026-10-01T12:00:00Z", title="T", user={"username": "u"}, body_markdown="x", tag_list="a, b, c")
        s = probe.slim(a)
        self.assertEqual(s["n_tags"], 3)
        for k in ("title", "user", "body_markdown", "username"):
            self.assertNotIn(k, s)
        self.assertNotIn("'u'", str(s))
        self.assertNotIn("T", s.values())


if __name__ == "__main__":
    unittest.main()
