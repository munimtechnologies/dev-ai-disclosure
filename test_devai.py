# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for devai.py: no network, DEV's API is replaced by a stub."""
import csv
import gzip
import json
import os
import tempfile
import unittest
import urllib.parse
from argparse import Namespace
from collections import Counter, defaultdict
from datetime import timedelta
from unittest import mock

import devai

LAUNCH = devai.parse_time("2026-08-26T15:00:00Z")
# A few names from Forem's Fastly allowlist (config/fastly/snippets/safe_params_list.vcl);
# any other query parameter is removed before the cache lookup.
ALLOWLIST_SAMPLE = {"page", "per_page", "item", "ut", "i", "token", "p_id"}
# Every parameter ArticleApiIndexService reads.
READ_BY_INDEX = {"page", "tag", "tags", "tags_exclude", "username", "state", "sort", "top", "collection_id",
                 "per_page"}


def article(aid, published, level="some_ai", uid=7, **extra):
    a = {"id": aid, "title": "A post", "published_at": published, "tag_list": ["ai", "Python"],
         "cover_image": "https://x/y.png", "reading_time_minutes": 4, "public_reactions_count": 3,
         "comments_count": 1, "language": "en", "ai_disclosure_level": level,
         "canonical_url": f"https://dev.to/someone/a-post-{aid}", "edited_at": None,
         "user": {"username": "someone", "user_id": uid}}
    a.update(extra)
    return a


def stamp(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class RowTests(unittest.TestCase):
    def test_row_fields(self):
        r = devai.row_of(article(5, "2026-09-01T10:00:00Z"), LAUNCH)
        self.assertEqual(r["date"], "2026-09-01")
        self.assertEqual(r["level"], "some_ai")
        self.assertEqual(r["tags"], "ai python")
        self.assertEqual(r["n_tags"], 2)
        self.assertEqual(r["has_cover"], 1)
        self.assertEqual(r["is_org"], 0)
        self.assertEqual(r["crossposted"], 0)
        self.assertEqual(r["edited_after_launch"], 0)
        self.assertEqual(set(r), set(devai.POST_COLS))
        self.assertNotIn("someone", json.dumps(r).replace("https://dev.to/someone", ""))

    def test_row_flags(self):
        a = article(6, "2026-08-01T10:00:00Z", level=None, canonical_url="https://blog.example.com/p",
                    organization={"name": "Org"}, edited_at="2026-09-02T00:00:00Z", tag_list="a, b, c",
                    cover_image=None)
        r = devai.row_of(a, LAUNCH)
        self.assertEqual(r["level"], "not_disclosed")
        self.assertEqual(r["crossposted"], 1)
        self.assertEqual(r["is_org"], 1)
        self.assertEqual(r["edited_after_launch"], 1)
        self.assertEqual(r["n_tags"], 3)
        self.assertEqual(r["has_cover"], 0)


class SweepCheckTests(unittest.TestCase):
    def test_bust_param_survives_the_allowlist_and_is_not_read(self):
        self.assertIn(devai.BUST_PARAM, ALLOWLIST_SAMPLE)
        self.assertNotIn(devai.BUST_PARAM, READ_BY_INDEX)
        self.assertNotIn("sweep", ALLOWLIST_SAMPLE)

    def test_listing_path(self):
        self.assertEqual(devai.listing_path(1000, 3), "/articles/latest?per_page=1000&page=3")
        p = devai.listing_path(1000, 3, "20261016T1300")
        self.assertEqual(p, "/articles/latest?per_page=1000&page=3&item=20261016T1300")
        q = urllib.parse.parse_qs(urllib.parse.urlparse(p).query)
        self.assertEqual(q["page"], ["3"])
        self.assertEqual(q["item"], ["20261016T1300"])
        self.assertNotIn("sweep", q)
        self.assertEqual(devai.listing_path(1000, 3, "x", "ut"), "/articles/latest?per_page=1000&page=3&ut=x")

    def test_page_edges_and_hole(self):
        a = [article(1, "2026-10-01T10:00:00Z"), article(2, "2026-10-01T09:00:00Z"), {"id": 3}]
        oldest, newest = devai.page_edges(a)
        self.assertEqual(oldest, devai.parse_time("2026-10-01T09:00:00Z"))
        self.assertEqual(newest, devai.parse_time("2026-10-01T10:00:00Z"))
        self.assertEqual(devai.page_edges([]), (None, None))
        # Next page starts an hour after the previous one ended: a one-hour hole.
        self.assertEqual(devai.page_hole_seconds(oldest, devai.parse_time("2026-10-01T08:00:00Z")), 3600)
        # Next page starts before the previous one ended: overlap, negative.
        self.assertEqual(devai.page_hole_seconds(oldest, devai.parse_time("2026-10-01T09:30:00Z")), -1800)
        self.assertIsNone(devai.page_hole_seconds(None, newest))

    def test_cached_page(self):
        self.assertFalse(devai.cached_page({}))
        self.assertFalse(devai.cached_page({"Age": "0", "X-Cache": "MISS"}))
        self.assertFalse(devai.cached_page({"Age": "0", "X-Cache": "MISS, MISS"}))
        self.assertTrue(devai.cached_page({"Age": "4311"}))
        self.assertTrue(devai.cached_page({"X-Cache": "HIT, MISS"}))
        self.assertTrue(devai.cached_page({"X-Cache": "MISS, HIT"}))
        self.assertFalse(devai.cached_page({"Age": "junk"}))

    def test_coverage_line(self):
        m = {"cache_bust": True, "bust_param": "item",
             "coverage": {"pages": 400, "cached_pages": 0, "duplicate_ids": 12,
                          "max_hole_minutes": 0.3, "pages_with_hole_over_10min": 0}}
        line = devai.coverage_line(m)
        self.assertIn("per-sweep value in `item`", line)
        self.assertIn("allowlist", line)
        self.assertIn("0 of 400 pages", line)
        self.assertIn("12 ids were listed twice", line)
        self.assertIn("per-sweep value in `item`", devai.coverage_line({"cache_bust": True, "coverage": {"pages": 1}}))
        self.assertEqual(devai.coverage_line({}), "")
        self.assertEqual(devai.coverage_line({"cache_bust": False, "coverage": {}}), "")
        self.assertIn("could come from a cache", devai.coverage_line({"cache_bust": False, "coverage": {"pages": 9}}))


class MathTests(unittest.TestCase):
    def test_pct_in(self):
        vals = [0, 0, 1, 5]
        self.assertAlmostEqual(devai.pct_in(vals, 5, exclude_self=True), 1.0)
        self.assertAlmostEqual(devai.pct_in(vals, 0, exclude_self=True), 1 / 6)
        self.assertAlmostEqual(devai.pct_in([1.0, 2.0, 3.0, 4.0], 2.5), 0.5)

    def test_median(self):
        self.assertIsNone(devai.median([]))
        self.assertEqual(devai.median([3, 1, 2]), 2)
        self.assertEqual(devai.median([4, 1, 2, 3]), 2.5)

    def test_week_start(self):
        self.assertEqual(devai.week_start("2026-08-26", LAUNCH), "2026-08-26")
        self.assertEqual(devai.week_start("2026-09-01", LAUNCH), "2026-08-26")
        self.assertEqual(devai.week_start("2026-09-02", LAUNCH), "2026-09-02")
        self.assertEqual(devai.week_start("2026-08-25", LAUNCH), "2026-08-19")

    def test_shares(self):
        s = devai.shares(Counter({"not_disclosed": 6, "some_ai": 3, "no_ai": 1}))
        self.assertEqual(s["posts"], 10)
        self.assertAlmostEqual(s["some_ai"], 0.3)
        self.assertAlmostEqual(s["any_label"], 0.4)
        self.assertAlmostEqual(s["fully_autonomous"], 0.0)
        self.assertIsNone(devai.shares(Counter())["any_label"])

    def test_engagement_within_day(self):
        ts = LAUNCH.timestamp() + 3600
        eng = [("2026-09-01", ts, 10, 2, "no_ai", 1), ("2026-09-01", ts, 0, 0, "some_ai", 1),
               ("2026-09-02", ts, 50, 1, "no_ai", 0), ("2026-09-02", ts, 40, 0, "some_ai", 1),
               ("2026-09-03", ts + 10 ** 9, 99, 9, "some_ai", 1)]
        e = devai.engagement(eng, ts + 1)
        self.assertEqual(e["no_ai"]["posts"], 2)
        self.assertAlmostEqual(e["no_ai"]["mean_day_percentile"], 1.0)
        self.assertAlmostEqual(e["some_ai"]["mean_day_percentile"], 0.0)
        self.assertEqual(e["some_ai"]["posts"], 2)
        self.assertAlmostEqual(e["some_ai"]["share_zero_reactions"], 0.5)
        en = devai.engagement(eng, ts + 1, en_only=True)
        self.assertEqual(en["no_ai"]["posts"], 1)

    def test_author_summary(self):
        authors = {1: Counter({"fully_autonomous": 8}), 2: Counter({"fully_autonomous": 1, "not_disclosed": 2}),
                   3: Counter({"some_ai": 1, "no_ai": 1}), 4: Counter({"not_disclosed": 5})}
        s = devai.author_summary(authors)
        self.assertEqual(s["authors"], 4)
        self.assertEqual(s["by_level"]["fully_autonomous"]["authors"], 2)
        self.assertEqual(s["by_level"]["fully_autonomous"]["authors_for_half_of_posts"], 1)
        self.assertEqual(s["authors_with_any_label"], 3)
        self.assertEqual(s["authors_with_two_or_more_labels"], 1)
        self.assertEqual(s["authors_mixing_labelled_and_undisclosed"], 1)

    def test_weekly_author_summary(self):
        weekly = {"2026-09-02": {1: {"some_ai"}, 2: {"not_disclosed"}, 3: {"no_ai", "some_ai"}},
                  "2026-08-26": {1: {"fully_autonomous", "not_disclosed"}}}
        w = devai.weekly_author_summary(weekly)
        self.assertEqual([r["week"] for r in w], ["2026-08-26", "2026-09-02"])
        self.assertEqual(w[0], {"week": "2026-08-26", "authors": 1, "no_ai": 0, "some_ai": 0,
                                "fully_autonomous": 1, "any_label": 1})
        self.assertEqual(w[1]["authors"], 3)
        self.assertEqual(w[1]["some_ai"], 2)
        self.assertEqual(w[1]["no_ai"], 1)
        self.assertEqual(w[1]["any_label"], 2)


def write_posts(path, arts):
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=devai.POST_COLS)
        wr.writeheader()
        for a in arts:
            wr.writerow(devai.row_of(a, LAUNCH))


def burst_fixture():
    """150 AI-Assisted posts 5 minutes apart with one tag set (a burst); 150 posts with
    another tag set a day apart (not a burst); 50 more at burst pace (too few); one
    burst-paced group before launch (ignored); 40 ordinary undisclosed posts."""
    arts, aid = [], 0
    t0 = devai.parse_time("2026-09-24T00:00:00Z")
    for i in range(150):
        aid += 1
        arts.append(article(aid, stamp(t0 + timedelta(minutes=5 * i)), "some_ai", 9,
                            tag_list=["massage", "training", "brussels"], public_reactions_count=0))
    for i in range(150):
        aid += 1
        arts.append(article(aid, stamp(devai.parse_time("2026-08-27T08:00:00Z") + timedelta(hours=10 * i)),
                            "some_ai", 10, tag_list=["python", "tutorial"]))
    for i in range(50):
        aid += 1
        arts.append(article(aid, stamp(t0 + timedelta(minutes=2 * i)), "fully_autonomous", 11,
                            tag_list=["short"]))
    for i in range(120):
        aid += 1
        arts.append(article(aid, stamp(devai.parse_time("2026-08-13T00:00:00Z") + timedelta(minutes=i)),
                            "not_disclosed", 12, tag_list=["old", "spam"]))
    for i in range(40):
        aid += 1
        arts.append(article(aid, stamp(devai.parse_time("2026-09-10T00:00:00Z") + timedelta(hours=7 * i)),
                            "not_disclosed", 100 + i, tag_list=["webdev"]))
    return arts


def cross_author_fixture():
    """burst_fixture plus 160 challenge entries by 160 different authors, 3 minutes apart:
    one tag set and one label at machine pace, but no author posts more than once."""
    arts = burst_fixture()
    t0 = devai.parse_time("2026-10-02T00:00:00Z")
    for i in range(160):
        arts.append(article(5000 + i, stamp(t0 + timedelta(minutes=3 * i)), "not_disclosed", 1000 + i,
                            tag_list=["devchallenge", "hf26challenge"], public_reactions_count=2))
    return arts


def keyed_of(arts):
    """What collect holds in memory for find_author_bursts."""
    keyed = defaultdict(list)
    for a in arts:
        r = devai.row_of(a, LAUNCH)
        pub = devai.parse_time(r["published_at"])
        if r["tags"] and pub >= LAUNCH:
            keyed[(a["user"]["user_id"], r["tags"], r["level"])].append((pub.timestamp(), r["article_id"]))
    return keyed


class BurstTests(unittest.TestCase):
    def test_find_bursts(self):
        with tempfile.TemporaryDirectory() as out:
            path = os.path.join(out, "posts.csv")
            write_posts(path, burst_fixture())
            groups, keys = devai.find_bursts(path, LAUNCH, 100, 15)
            self.assertEqual(len(groups), 1)
            g = groups[0]
            self.assertEqual(g["tags"], "massage training brussels")
            self.assertEqual(g["level"], "some_ai")
            self.assertEqual(g["posts"], 150)
            self.assertAlmostEqual(g["median_gap_minutes"], 5.0)
            self.assertEqual(g["reactions"], 0)
            self.assertEqual(g["first"], "2026-09-24T00:00:00+00:00")
            self.assertEqual(keys, {("massage training brussels", "some_ai")})
            groups, _ = devai.find_bursts(path, LAUNCH, 40, 15)
            self.assertEqual(sorted(g["posts"] for g in groups), [50, 150])

    def test_find_author_bursts(self):
        t0 = LAUNCH.timestamp() + 86400
        keyed = {
            (1, "massage training brussels", "some_ai"): [(t0 + 180 * i, 1000 + i) for i in range(120)],
            # Two authors share a tag set at a combined 5-minute pace, but each has only 80 posts.
            (2, "devchallenge hf26challenge", "not_disclosed"): [(t0 + 600 * i, 2000 + i) for i in range(80)],
            (3, "devchallenge hf26challenge", "not_disclosed"): [(t0 + 300 + 600 * i, 3000 + i) for i in range(80)],
            (4, "python", "no_ai"): [(t0 + 86400 * i, 4000 + i) for i in range(150)],
            (1, "seo", "not_disclosed"): [(t0 + 60 * i, 5000 + i) for i in range(100)],
        }
        groups, n_authors = devai.find_author_bursts(keyed, 100, 15)
        self.assertEqual([len(g) for g in groups], [120, 100])
        self.assertEqual(groups[0][0], 1000)
        self.assertEqual(groups[1][0], 5000)
        self.assertEqual(n_authors, 1)
        self.assertEqual(devai.find_author_bursts({}, 100, 15), ([], 0))

    def test_analyse_without_bursts(self):
        with tempfile.TemporaryDirectory() as out:
            path = os.path.join(out, "posts.csv")
            write_posts(path, burst_fixture())
            meta = os.path.join(out, "meta.json")
            with open(meta, "w", encoding="utf-8") as f:
                json.dump({"launch": LAUNCH.isoformat(), "snapshot_at": "2026-10-14T00:00:00+00:00"}, f)
            a = Namespace(posts=path, meta=meta, authors="", min_tag_posts=1, min_rank_tag_posts=1,
                          burst_min_posts=100, burst_max_gap_minutes=15, out_dir=out)
            self.assertEqual(devai.analyse(a), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["since_launch"]["posts"], 390)
            self.assertEqual(s["since_launch"]["counts"]["some_ai"], 300)
            x = s["since_launch_excluding_bursts"]
            self.assertEqual(x["posts"], 240)
            self.assertEqual(x["counts"]["some_ai"], 150)
            self.assertAlmostEqual(x["some_ai"], 0.625)
            self.assertEqual(len(s["bursts"]), 1)
            self.assertFalse(s["burst_rule"]["one_author"])
            self.assertIsNone(s["tagset_rule_comparison"])
            # The pre-launch group is not a burst, so it stays in the before-launch count.
            self.assertEqual(s["before_launch"]["posts"], 120)
            wk = {w["week"]: w for w in s["weekly"]}
            wx = {w["week"]: w for w in s["weekly_excluding_bursts"]}
            self.assertEqual(wk["2026-09-23"]["posts"] - wx["2026-09-23"]["posts"], 150)
            self.assertEqual(s["engagement_all"]["some_ai"]["posts"] -
                             s["engagement_all_excluding_bursts"]["some_ai"]["posts"], 150)
            with open(os.path.join(out, "daily.csv"), newline="", encoding="utf-8") as f:
                daily = {d["date"]: d for d in csv.DictReader(f)}
            self.assertEqual(sum(int(d["burst_posts"]) for d in daily.values()), 150)
            with open(os.path.join(out, "bursts.csv"), newline="", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 1)
            with open(os.path.join(out, "REPORT.md"), encoding="utf-8") as f:
                rep = f.read()
            self.assertIn("## Bursts: one tag set, one label, machine pace", rep)
            self.assertIn("| massage training brussels | AI-Assisted | 150 |", rep)
            self.assertIn("Since launch without bursts: 240 posts.", rep)
            self.assertIn("bursts left out", rep)
            # No coverage block in this meta: no sweep-check line.
            self.assertNotIn("Sweep check:", rep)

    def test_analyse_with_author_bursts(self):
        with tempfile.TemporaryDirectory() as out:
            arts = cross_author_fixture()
            path = os.path.join(out, "posts.csv")
            write_posts(path, arts)
            groups, n_authors = devai.find_author_bursts(keyed_of(arts), 100, 15)
            self.assertEqual(n_authors, 1)
            bp = os.path.join(out, "burst_posts.csv")
            devai.write_burst_posts(bp, groups)
            self.assertEqual(devai.read_burst_posts(bp), {i: 1 for i in range(1, 151)})
            meta = os.path.join(out, "meta.json")
            with open(meta, "w", encoding="utf-8") as f:
                json.dump({"launch": LAUNCH.isoformat(), "snapshot_at": "2026-10-14T00:00:00+00:00"}, f)
            a = Namespace(posts=path, meta=meta, authors="", burst_posts=bp, min_tag_posts=1,
                          min_rank_tag_posts=1, burst_min_posts=100, burst_max_gap_minutes=15, out_dir=out)
            self.assertEqual(devai.analyse(a), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["since_launch"]["posts"], 550)
            self.assertTrue(s["burst_rule"]["one_author"])
            self.assertEqual(len(s["bursts"]), 1)
            g = s["bursts"][0]
            self.assertEqual((g["tags"], g["level"], g["posts"]), ("massage training brussels", "some_ai", 150))
            self.assertAlmostEqual(g["median_gap_minutes"], 5.0)
            self.assertEqual(g["first"], "2026-09-24T00:00:00+00:00")
            self.assertEqual(g["reactions"], 0)
            x = s["since_launch_excluding_bursts"]
            self.assertEqual(x["posts"], 400)
            self.assertEqual(x["counts"]["not_disclosed"], 200)
            c = s["tagset_rule_comparison"]
            self.assertEqual((c["groups"], c["posts"], c["posts_also_in_author_bursts"]), (2, 310, 150))
            with open(os.path.join(out, "REPORT.md"), encoding="utf-8") as f:
                rep = f.read()
            self.assertIn("## Bursts: one author, one tag set, one label, machine pace", rep)
            self.assertIn("| massage training brussels | AI-Assisted | 150 |", rep)
            self.assertNotIn("| devchallenge hf26challenge |", rep)
            self.assertIn("Since launch without bursts: 400 posts.", rep)
            self.assertIn("finds 2 groups with 310 posts, of which 150 are in a one-author burst", rep)
            self.assertIn("spreads over many accounts is missed", rep)


class StubClient:
    pages = {
        1: [article(10, "2026-10-14T10:00:00Z", "some_ai", 1),
            article(11, "2026-10-14T09:00:00Z", "not_disclosed", 2),
            article(12, "2026-08-20T09:00:00Z", "no_ai", 3, edited_at="2026-09-01T00:00:00Z")],
        2: [article(11, "2026-10-14T09:00:00Z", "not_disclosed", 2),
            article(13, "2026-08-10T09:00:00Z", "some_ai", 4)],
        3: [article(14, "2026-08-01T09:00:00Z", "some_ai", 4)],
        4: [article(15, "2026-07-01T09:00:00Z", "some_ai", 4)],
        5: [article(16, "2026-10-14T09:00:00Z", "some_ai", 4)],
    }
    headers = {}
    seen_paths = []

    def __init__(self, pause=1.0):
        self.requests = 0
        self.paths = []
        self.last_headers = {}
        type(self).seen_paths = self.paths

    def get(self, path, tries=6):
        self.requests += 1
        self.paths.append(path)
        self.last_headers = dict(self.headers)
        if path == devai.LAUNCH_POST:
            return {"id": 1, "published_at": "2026-08-26T15:00:00Z"}
        if path.startswith("/articles/latest"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
            return self.pages.get(int(q["page"][0]), [])
        return None


class CachedStubClient(StubClient):
    """Every listing page answers with cache headers saying it was served from a cache."""
    headers = {"Age": "4311", "X-Cache": "HIT"}


class BurstStubClient(StubClient):
    """One author posting 110 Fully Autonomous posts two minutes apart with one tag set."""
    pages = {
        1: [article(100 + i, stamp(devai.parse_time("2026-10-01T00:00:00Z") + timedelta(minutes=2 * i)),
                    "fully_autonomous", 77, tag_list=["seo", "backlinks"]) for i in range(110)],
        2: [article(1, "2026-08-01T09:00:00Z", "some_ai", 4)],
        3: [article(2, "2026-07-01T09:00:00Z", "some_ai", 4)],
    }


class PipelineTests(unittest.TestCase):
    def test_collect_then_analyse(self):
        with tempfile.TemporaryDirectory() as out:
            args = Namespace(since="2026-08-12", per_page=1000, max_pages=50, budget_minutes=5, pause=0,
                             out_dir=out)
            with mock.patch.object(devai, "Client", StubClient):
                self.assertEqual(devai.collect(args), 0)
            listing = [p for p in StubClient.seen_paths if p.startswith("/articles/latest")]
            self.assertEqual(len(listing), 4)
            self.assertTrue(all("&item=" in p for p in listing))
            self.assertTrue(all("sweep" not in p for p in listing))
            self.assertEqual(len({p.rsplit("&item=", 1)[1] for p in listing}), 1)
            with open(os.path.join(out, "posts.csv"), newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            # 13, 14 and 15 are older than --since; 11 is listed twice; the listing stops after
            # two pages that are entirely too old, so page 5 is never read.
            self.assertEqual(sorted(int(r["article_id"]) for r in rows), [10, 11, 12])
            self.assertNotIn("username", rows[0])
            with gzip.open(os.path.join(out, "posts.csv.gz"), "rt", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 3)
            with open(os.path.join(out, "meta.json"), encoding="utf-8") as f:
                meta = json.load(f)
            self.assertEqual(meta["stopped"], "reached --since")
            self.assertEqual(meta["posts"], 3)
            self.assertEqual(meta["version"], devai.VERSION)
            self.assertTrue(meta["launch"].startswith("2026-08-26T15:00"))
            self.assertTrue(meta["burst_rule"]["one_author"])
            self.assertTrue(meta["cache_bust"])
            self.assertEqual(meta["bust_param"], "item")
            cov = meta["coverage"]
            self.assertEqual(cov["pages"], 4)
            self.assertEqual(cov["cached_pages"], 0)
            self.assertEqual(cov["duplicate_ids"], 1)
            self.assertEqual(cov["header_samples"], [{"page": 1, "headers": {}}])
            # Page 2 overlaps page 1 (no hole); pages 3 and 4 each start days after the previous
            # page ended, so two holes over 10 minutes; the largest is page 4's 31 days.
            self.assertEqual(cov["pages_with_hole_over_10min"], 2)
            self.assertEqual([h["page"] for h in cov["holes"]], [3, 4])
            self.assertEqual(cov["max_hole_seconds"], 31 * 86400)
            self.assertEqual(cov["max_hole_minutes"], 31 * 1440.0)
            with open(os.path.join(out, "authors.json"), encoding="utf-8") as f:
                authors = json.load(f)
            # Author 3's post is from before the launch, so only authors 1 and 2 count.
            self.assertEqual(authors["authors"], 2)
            self.assertEqual(authors["weekly"], [{"week": "2026-10-14", "authors": 2, "no_ai": 0, "some_ai": 1,
                                                  "fully_autonomous": 0, "any_label": 1}])
            self.assertNotIn('"1"', json.dumps(authors["weekly"]))
            self.assertEqual((authors["burst_groups"], authors["burst_authors"]), (0, 0))
            self.assertEqual(devai.read_burst_posts(os.path.join(out, "burst_posts.csv")), {})

            a = Namespace(posts=os.path.join(out, "posts.csv"), meta=os.path.join(out, "meta.json"),
                          authors=os.path.join(out, "authors.json"), min_tag_posts=1, min_rank_tag_posts=1,
                          out_dir=out)
            self.assertEqual(devai.analyse(a), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["since_launch"]["posts"], 2)
            self.assertAlmostEqual(s["since_launch"]["some_ai"], 0.5)
            self.assertEqual(s["before_launch"]["labelled"], 1)
            self.assertEqual(s["before_launch"]["labelled_and_edited_after_launch"], 1)
            self.assertEqual(s["bursts"], [])
            self.assertEqual(s["since_launch_excluding_bursts"]["posts"], 2)
            with open(os.path.join(out, "daily.csv"), newline="", encoding="utf-8") as f:
                daily = list(csv.DictReader(f))
            self.assertEqual([d["date"] for d in daily], ["2026-08-20", "2026-10-14"])
            with open(os.path.join(out, "tags.csv"), newline="", encoding="utf-8") as f:
                tags = {r["tag"]: r for r in csv.DictReader(f)}
            self.assertEqual(tags["python"]["posts"], "2")
            with open(os.path.join(out, "REPORT.md"), encoding="utf-8") as f:
                rep = f.read()
            for heading in ("## Since launch", "## Week by week", "## Reactions and comments by label",
                            "## What labelled posts look like", "## Authors", "## Authors week by week",
                            "## Bursts", "## Tags", "## Limits"):
                self.assertIn(heading, rep)
            self.assertIn("AI-Assisted", rep)
            self.assertIn("No group meets the rule.", rep)
            self.assertIn("Sweep check: every page URL carried a per-sweep value in `item`", rep)
            self.assertIn("0 of 4 pages came back with headers", rep)
            self.assertIn("1 ids were listed twice", rep)
            self.assertIn("over 10 minutes on 2 pages", rep)
            self.assertIn("Pages served from a cache of different ages", rep)

    def test_collect_with_other_bust_param(self):
        with tempfile.TemporaryDirectory() as out:
            args = Namespace(since="2026-08-12", per_page=1000, max_pages=50, budget_minutes=5, pause=0,
                             out_dir=out, bust_param="ut")
            with mock.patch.object(devai, "Client", StubClient):
                self.assertEqual(devai.collect(args), 0)
            listing = [p for p in StubClient.seen_paths if p.startswith("/articles/latest")]
            self.assertTrue(all("&ut=" in p and "&item=" not in p for p in listing))
            with open(os.path.join(out, "meta.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f)["bust_param"], "ut")

    def test_collect_without_cache_bust_counts_cached_pages(self):
        with tempfile.TemporaryDirectory() as out:
            args = Namespace(since="2026-08-12", per_page=1000, max_pages=50, budget_minutes=5, pause=0,
                             out_dir=out, cache_bust=False)
            with mock.patch.object(devai, "Client", CachedStubClient):
                self.assertEqual(devai.collect(args), 0)
            listing = [p for p in CachedStubClient.seen_paths if p.startswith("/articles/latest")]
            self.assertEqual(listing[0], "/articles/latest?per_page=1000&page=1")
            self.assertTrue(all("item=" not in p for p in listing))
            with open(os.path.join(out, "meta.json"), encoding="utf-8") as f:
                meta = json.load(f)
            self.assertFalse(meta["cache_bust"])
            self.assertIsNone(meta["bust_param"])
            self.assertEqual(meta["coverage"]["cached_pages"], 4)
            self.assertEqual(meta["coverage"]["header_samples"][0]["headers"]["Age"], "4311")
            self.assertIn("could come from a cache", devai.coverage_line(meta))

    def test_collect_writes_author_bursts(self):
        with tempfile.TemporaryDirectory() as out:
            args = Namespace(since="2026-08-12", per_page=1000, max_pages=50, budget_minutes=5, pause=0,
                             out_dir=out)
            with mock.patch.object(devai, "Client", BurstStubClient):
                self.assertEqual(devai.collect(args), 0)
            bp = os.path.join(out, "burst_posts.csv")
            with open(bp, encoding="utf-8") as f:
                self.assertEqual(f.readline().strip(), "article_id,group")
            self.assertEqual(devai.read_burst_posts(bp), {100 + i: 1 for i in range(110)})
            with open(os.path.join(out, "authors.json"), encoding="utf-8") as f:
                authors = json.load(f)
            self.assertEqual((authors["burst_groups"], authors["burst_authors"]), (1, 1))
            a = Namespace(posts=os.path.join(out, "posts.csv"), meta=os.path.join(out, "meta.json"),
                          authors=os.path.join(out, "authors.json"), burst_posts=bp, min_tag_posts=1,
                          min_rank_tag_posts=1, out_dir=out)
            self.assertEqual(devai.analyse(a), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual([g["posts"] for g in s["bursts"]], [110])
            self.assertAlmostEqual(s["bursts"][0]["median_gap_minutes"], 2.0)
            self.assertEqual(s["since_launch_excluding_bursts"]["posts"], 0)
            with open(os.path.join(out, "REPORT.md"), encoding="utf-8") as f:
                rep = f.read()
            self.assertIn("Distinct authors behind these groups: 1.", rep)

    def test_report_without_meta(self):
        with tempfile.TemporaryDirectory() as out:
            path = os.path.join(out, "posts.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                wr = csv.DictWriter(f, fieldnames=devai.POST_COLS)
                wr.writeheader()
                for i, lvl in enumerate(["some_ai", "fully_autonomous", "not_disclosed", "mystery_level"]):
                    wr.writerow(devai.row_of(article(i, "2026-09-0%dT12:00:00Z" % (i + 1), lvl), LAUNCH))
            a = Namespace(posts=path, meta="", authors="", min_tag_posts=1, min_rank_tag_posts=1, out_dir=out)
            self.assertEqual(devai.analyse(a), 0)
            with open(os.path.join(out, "REPORT.md"), encoding="utf-8") as f:
                rep = f.read()
            self.assertIn("other values ['mystery_level']", rep)
            self.assertNotIn("## Authors", rep)


if __name__ == "__main__":
    unittest.main()
