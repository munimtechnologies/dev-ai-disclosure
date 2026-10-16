#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Why does DEV's /api/articles/latest listing return fewer posts than it did?

Three whole-platform sweeps of the listing (same code path, same window
2026-08-12 to the snapshot) wrote fewer posts each time: 414,144 on
2026-10-14, 348,461 on 2026-10-15 and 295,145 on 2026-10-16, over about the
same number of 1,000-slot pages. A post absent from the third sweep
(published 2026-08-14) is still served by /api/articles/<id>.

The sweep drops duplicate ids, so two causes fit: pages come back short, or
adjacent pages overlap (and leave gaps) because they are served from an edge
cache at different ages. This probe measures, on the live API and without
storing any username or title:
  1. per page: how many items a 1,000-slot page returns, how many lack
     published_at, duplicates within the page, and the response's cache
     headers (Age, X-Cache, Cache-Control, Date);
  2. adjacent pages: shared ids and whether the time order between them holds
     (a page's newest post should be no newer than the previous page's oldest);
  3. gap sampling: random article ids inside the id range of a fetched page
     that the listing did not return, fetched one by one: 404 (not public)
     or 200 (live). A live post whose published_at falls inside the time
     window of the fetched pages but which the listing did not return is
     "live but absent from the listing";
  4. stability: one page fetched twice, minutes apart.

Uses only DEV's public API (no key). Made by MV2 of Munim, Inc., with AI
agents working in his name.
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

VERSION = "0.1.0"
API = "https://dev.to/api"
UA = f"mv2-dev-listing-gap-probe/{VERSION} (MV2 of Munim, Inc.; mv2@munimtech.com)"
HEADERS_KEPT = ("age", "x-cache", "x-cache-hits", "cache-control", "date", "x-served-by", "via", "surrogate-control")


def log(msg):
    print(msg, flush=True)


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


class Client:
    def __init__(self, pause):
        self.pause = pause
        self.requests = 0
        self.last = 0.0

    def get(self, path):
        """Return (status, json_or_None, headers). Retries 429/5xx with backoff."""
        wait = self.pause - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        for attempt in range(5):
            req = urllib.request.Request(API + path, headers={"User-Agent": UA, "Accept": "application/json"})
            self.requests += 1
            self.last = time.time()
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    hdr = {k: r.headers.get(k) for k in HEADERS_KEPT if r.headers.get(k) is not None}
                    return r.status, json.loads(r.read().decode("utf-8")), hdr
            except urllib.error.HTTPError as e:
                hdr = {k: e.headers.get(k) for k in HEADERS_KEPT if e.headers.get(k) is not None}
                if e.code in (404, 403, 401):
                    return e.code, None, hdr
                if e.code == 429 or e.code >= 500:
                    time.sleep(5 * (attempt + 1))
                    continue
                return e.code, None, hdr
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
                time.sleep(5 * (attempt + 1))
        return 0, None, {}


def page_stats(batch):
    """Pure: summarise one listing page. batch is the JSON list."""
    ids = [a.get("id") for a in batch]
    with_pub = [a for a in batch if a.get("published_at")]
    pubs = [parse_time(a["published_at"]) for a in with_pub]
    return {
        "items": len(batch),
        "without_published_at": len(batch) - len(with_pub),
        "without_id": sum(1 for i in ids if i is None),
        "dup_within_page": len(ids) - len(set(ids)),
        "min_id": min((i for i in ids if i is not None), default=None),
        "max_id": max((i for i in ids if i is not None), default=None),
        "oldest": min(pubs).isoformat() if pubs else None,
        "newest": max(pubs).isoformat() if pubs else None,
        "ids": sorted(set(i for i in ids if i is not None)),
    }


def adjacent_check(prev, cur):
    """Pure: duplicates and time-order violations between page p and p+1."""
    overlap = len(set(prev["ids"]) & set(cur["ids"]))
    order_ok = None
    if prev["oldest"] and cur["newest"]:
        order_ok = parse_time(cur["newest"]) <= parse_time(prev["oldest"])
    return {"overlap_ids": overlap, "time_order_ok": order_ok}


def gap_candidates(lo, hi, seen, n, rng):
    """Pure: up to n random ids in [lo, hi] not in seen."""
    pool = [i for i in range(lo, hi + 1) if i not in seen]
    rng.shuffle(pool)
    return sorted(pool[:n])


def classify(status, article, window_oldest, window_newest, seen):
    """Pure: label one probed id."""
    if status == 404:
        return "not_public"
    if status != 200 or not isinstance(article, dict):
        return f"http_{status}"
    pub = article.get("published_at")
    if not pub:
        return "live_no_published_at"
    t = parse_time(pub)
    if article.get("id") in seen:
        return "live_listed"
    if window_oldest <= t <= window_newest:
        return "live_absent_in_window"
    return "live_outside_window"


def slim(article):
    """Fields kept for a probed article: no username, no title, no body."""
    tags = article.get("tag_list")
    if isinstance(tags, list):
        n_tags = len(tags)
    else:
        n_tags = len([t for t in (tags or "").split(",") if t.strip()])
    return {
        "id": article.get("id"),
        "published_at": article.get("published_at"),
        "type_of": article.get("type_of"),
        "reactions": article.get("public_reactions_count"),
        "comments": article.get("comments_count"),
        "n_tags": n_tags,
        "language": article.get("language"),
        "reading_time": article.get("reading_time_minutes"),
        "has_org": bool(article.get("organization")),
        "subforem_id": article.get("subforem_id"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="1,2,3,40,41,42,80,81,82,120,121,122,200,201,202,300,301,302,400,401,402")
    ap.add_argument("--per-page", type=int, default=1000)
    ap.add_argument("--sample-per-group", type=int, default=20)
    ap.add_argument("--ids", default="4392326,4847820")
    ap.add_argument("--restability-page", type=int, default=300)
    ap.add_argument("--pause", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=20261016)
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    rng = random.Random(args.seed)
    client = Client(args.pause)
    t0 = time.time()
    started = datetime.now(timezone.utc).isoformat()

    pages = [int(p) for p in args.pages.split(",") if p.strip()]
    stats = {}
    first_fetch = {}
    for p in pages:
        status, batch, hdr = client.get(f"/articles/latest?per_page={args.per_page}&page={p}")
        if status != 200 or not isinstance(batch, list):
            log(f"page {p}: HTTP {status} {hdr}")
            stats[p] = {"http": status, "headers": hdr}
            continue
        s = page_stats(batch)
        s["http"] = 200
        s["headers"] = hdr
        stats[p] = s
        first_fetch[p] = time.time()
        log(f"page {p}: {s['items']} items, {s['without_published_at']} without published_at, "
            f"ids {s['min_id']}..{s['max_id']}, {s['oldest']} .. {s['newest']}, headers {hdr}")

    adjacent = {}
    for a, b in zip(pages, pages[1:]):
        if b == a + 1 and stats.get(a, {}).get("http") == 200 and stats.get(b, {}).get("http") == 200:
            adjacent[f"{a}-{b}"] = adjacent_check(stats[a], stats[b])
            log(f"pages {a}-{b}: {adjacent[f'{a}-{b}']}")

    groups = []
    cur = []
    for p in pages:
        if cur and p != cur[-1] + 1:
            groups.append(cur)
            cur = []
        cur.append(p)
    if cur:
        groups.append(cur)

    probes = []
    seen_all = set()
    for s in stats.values():
        seen_all.update(s.get("ids", []))
    for g in groups:
        ok = [p for p in g if stats.get(p, {}).get("http") == 200]
        if len(ok) < 2:
            continue
        mid = ok[len(ok) // 2]
        lo, hi = stats[mid]["min_id"], stats[mid]["max_id"]
        w_old = min(parse_time(stats[p]["oldest"]) for p in ok)
        w_new = max(parse_time(stats[p]["newest"]) for p in ok)
        cands = gap_candidates(lo, hi, seen_all, args.sample_per_group, rng)
        listed_in_range = sum(1 for i in range(lo, hi + 1) if i in seen_all)
        log(f"group {ok}: id range {lo}..{hi} ({hi - lo + 1} ids, {listed_in_range} listed), "
            f"window {w_old.isoformat()} .. {w_new.isoformat()}, probing {len(cands)}")
        for i in cands:
            status, art, hdr = client.get(f"/articles/{i}")
            label = classify(status, art, w_old, w_new, seen_all)
            rec = {"group": ok, "id": i, "http": status, "class": label}
            if isinstance(art, dict):
                rec.update(slim(art))
            probes.append(rec)

    specific = []
    for i in [int(x) for x in args.ids.split(",") if x.strip()]:
        status, art, hdr = client.get(f"/articles/{i}")
        rec = {"id": i, "http": status, "listed_in_probe_pages": i in seen_all}
        if isinstance(art, dict):
            rec.update(slim(art))
        specific.append(rec)
        log(f"id {i}: HTTP {status}")

    restab = None
    p = args.restability_page
    if stats.get(p, {}).get("http") == 200:
        status, batch, hdr = client.get(f"/articles/latest?per_page={args.per_page}&page={p}")
        if status == 200 and isinstance(batch, list):
            s2 = page_stats(batch)
            restab = {"page": p, "first_items": stats[p]["items"], "second_items": s2["items"],
                      "same_ids": len(set(s2["ids"]) & set(stats[p]["ids"])),
                      "minutes_apart": round((time.time() - first_fetch[p]) / 60, 1),
                      "first_headers": stats[p]["headers"], "second_headers": hdr}
            log(f"page {p} again: {restab}")

    classes = {}
    for r in probes:
        classes[r["class"]] = classes.get(r["class"], 0) + 1
    live_in_window = classes.get("live_absent_in_window", 0) + classes.get("live_listed", 0)
    summary = {
        "version": VERSION, "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
        "requests": client.requests, "minutes": round((time.time() - t0) / 60, 1),
        "per_page": args.per_page, "pages": pages,
        "items_per_page": {p: stats[p].get("items") for p in pages},
        "page_headers": {p: stats[p].get("headers") for p in pages},
        "without_published_at_total": sum(stats[p].get("without_published_at", 0) for p in pages),
        "adjacent": adjacent,
        "probe_classes": classes,
        "probed": len(probes),
        "live_absent_in_window": classes.get("live_absent_in_window", 0),
        "live_in_window": live_in_window,
        "specific": specific,
        "restability": restab,
    }
    slim_stats = {p: {k: v for k, v in s.items() if k != "ids"} for p, s in stats.items()}
    with open(os.path.join(args.out_dir, "pages.json"), "w", encoding="utf-8") as f:
        json.dump(slim_stats, f, indent=1)
    with open(os.path.join(args.out_dir, "probes.json"), "w", encoding="utf-8") as f:
        json.dump(probes, f, indent=1)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(args.out_dir, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("# DEV /articles/latest listing probe\n\n")
        f.write(f"Probe {VERSION}, started {started}, {client.requests} requests. Made by MV2 of Munim, Inc., "
                "with AI agents working in his name. No username or title is stored.\n\n")
        f.write("## Items returned per 1,000-slot page\n\n| Page | Items | No published_at | Oldest | Newest | Age | X-Cache |\n|---|---|---|---|---|---|---|\n")
        for p in pages:
            s = stats[p]
            h = s.get("headers") or {}
            if s.get("http") != 200:
                f.write(f"| {p} | HTTP {s.get('http')} | | | | {h.get('age', '')} | {h.get('x-cache', '')} |\n")
            else:
                f.write(f"| {p} | {s['items']} | {s['without_published_at']} | {s['oldest']} | {s['newest']} | {h.get('age', '')} | {h.get('x-cache', '')} |\n")
        f.write("\n## Adjacent pages\n\n| Pages | Shared ids | Time order holds |\n|---|---|---|\n")
        for k, v in adjacent.items():
            f.write(f"| {k} | {v['overlap_ids']} | {v['time_order_ok']} |\n")
        f.write("\n## Random ids inside a page's id range that the listing did not return\n\n")
        f.write("| Class | Count |\n|---|---|\n")
        for k, v in sorted(classes.items()):
            f.write(f"| {k} | {v} |\n")
        f.write(f"\nLive posts whose published_at lies inside the fetched window: {live_in_window}; "
                f"of those, absent from the listing: {classes.get('live_absent_in_window', 0)}.\n\n")
        f.write("## Specific ids\n\n")
        for r in specific:
            f.write(f"- {r['id']}: HTTP {r['http']}, published_at {r.get('published_at')}, listed in probe pages: {r['listed_in_probe_pages']}\n")
        if restab:
            f.write(f"\n## Same page twice\n\n{json.dumps(restab)}\n")
    log("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
