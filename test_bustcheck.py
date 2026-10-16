# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for bustcheck.py: no network."""
import unittest

import bustcheck


def art(i, pub):
    return {"id": i, "published_at": pub, "user": {"username": "someone"}, "title": "T"}


def fetched(ids, age=None, xcache=None, status=200):
    hdr = {}
    if age is not None:
        hdr["age"] = str(age)
    if xcache is not None:
        hdr["x-cache"] = xcache
    batch = [art(i, f"2026-10-01T{10 + n % 10:02d}:00:00Z") for n, i in enumerate(ids)]
    return bustcheck.summarise(status, batch if status == 200 else None, hdr)


class CachedTests(unittest.TestCase):
    def test_cached(self):
        self.assertIsNone(bustcheck.cached({}))
        self.assertFalse(bustcheck.cached({"age": "0", "x-cache": "MISS, MISS"}))
        self.assertTrue(bustcheck.cached({"Age": "51200"}))
        self.assertTrue(bustcheck.cached({"x-cache": "MISS, HIT"}))
        self.assertFalse(bustcheck.cached({"age": "junk"}))


class SummariseTests(unittest.TestCase):
    def test_summarise_keeps_ids_and_times_only(self):
        s = fetched([3, 1, 2, 2], age=0, xcache="MISS")
        self.assertEqual(s["items"], 4)
        self.assertEqual(s["ids"], [1, 2, 3])
        self.assertEqual(s["oldest"], "2026-10-01T10:00:00+00:00")
        self.assertEqual(s["newest"], "2026-10-01T13:00:00+00:00")
        self.assertFalse(s["cached"])
        self.assertNotIn("someone", str(s))
        e = fetched([], status=503)
        self.assertEqual(e["http"], 503)
        self.assertNotIn("ids", e)


class VerdictTests(unittest.TestCase):
    def test_kept_when_new_value_misses_then_hits(self):
        plain = fetched([1, 2], age=40000, xcache="HIT")
        first, second = fetched([5, 6], age=0, xcache="MISS"), fetched([5, 6], age=2, xcache="HIT")
        self.assertEqual(bustcheck.verdict(plain, first, second), "kept")

    def test_stripped_when_new_value_comes_from_cache(self):
        plain = fetched([1, 2], age=40000, xcache="HIT")
        first, second = fetched([1, 2], age=40001, xcache="HIT"), fetched([1, 2], age=40002, xcache="HIT")
        self.assertEqual(bustcheck.verdict(plain, first, second), "stripped")

    def test_without_headers_content_decides(self):
        plain = fetched([1, 2])
        same = fetched([1, 2])
        fresh = fetched([5, 6])
        self.assertEqual(bustcheck.verdict(plain, same, same, other_first=fresh), "stripped")
        self.assertEqual(bustcheck.verdict(plain, fresh, fresh, other_first=same), "kept")
        # Both variants match the plain page (it was fresh too): nothing can be told.
        self.assertEqual(bustcheck.verdict(plain, same, same, other_first=same), "unclear")
        self.assertEqual(bustcheck.verdict(plain, same, same), "unclear")

    def test_unclear_on_errors_or_uncached_repeat(self):
        plain = fetched([1, 2], age=0, xcache="MISS")
        self.assertEqual(bustcheck.verdict(plain, fetched([], status=503), fetched([1, 2])), "unclear")
        miss = fetched([5], age=0, xcache="MISS")
        self.assertEqual(bustcheck.verdict(plain, miss, miss), "unclear")


if __name__ == "__main__":
    unittest.main()
