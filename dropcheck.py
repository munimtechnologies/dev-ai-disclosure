#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Did DEV's post volume fall because of Forem's late-September anti-spam changes?

DEV's public listing shows 6,600-9,200 posts on most weekdays through 2026-09-28 and
3,300-4,900 a day from 2026-09-30 (devai.py 0.4.1 snapshot of 2026-10-16). In the same
days Forem merged three changes to its automatic spam handling:
  #23883 (2026-09-28)  low-badge authors with repeated spam flags get the `spam` role,
                       which blocks posting ("693 accounts over the last 2 days" on DEV);
  #23904 (2026-09-29)  only when flags are at least 75% of their recent posts
                       ("~1,650 accounts marked so far");
  #23925 (2026-10-02)  any mascot flag counts; a third same-title copy within 24 hours
                       is clear spam.
Issue #23931 reports that a spam-marked author's posts stay `published` in the public
API, so posts from before the change are still listed. If the fall is these changes,
it should sit in posts nobody reacted to or commented on, and in authors who posted
heavily, not in occasional authors. This script tests that with predictions written
down before the data (sweeps/dropcheck-2026-10-16/PREREG.md), using a placebo pair
of windows with no known change to separate it from ordinary regression to the mean.

Windows (UTC dates, inclusive): A 2026-08-27..09-11 (16 days), B 09-12..09-27
(16 days), C 09-30..10-14 (15 days). 09-28 and 09-29 are the change days and are left
out; 10-15 on are too young for reactions. Placebo transition A->B, test B->C.

Reads DEV's public /articles/latest listing once, with a per-sweep token in the
allowlisted `item` parameter (as devai.py 0.4.1). Author ids are held in memory only
to count posts per author; nothing that names or identifies an author is written.
Made by MV2 of Munim, Inc., with AI agents working in his name.
"""
import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timezone

VERSION = "0.1.0"
API = "https://dev.to/api"
UA = f"mv2-dev-ai-disclosure-dropcheck/{VERSION} (MV2 of Munim, Inc.; mv2@munimtech.com)"
PAUSE = 1.0
BUST_PARAM = "item"
WINDOWS = {"A": ("2026-08-27", "2026-09-11"),
           "B": ("2026-09-12", "2026-09-27"),
           "C": ("2026-09-30", "2026-10-14")}
TRANSITIONS = (("A", "B", "placebo"), ("B", "C", "test"))
# Classes by an author's posts in the earlier window of a transition (A and B are 16 days).
HEAVY, REGULAR = 16, 4
CLASSES = ("heavy", "regular", "occasional")
# Pre-registered thresholds (PREREG.md).
P1_MARGIN = 0.15
P2_HEAVY_MARGIN = 0.20
P2_OCCASIONAL_MARGIN = 0.10
GATE_MAX_DAY_DIFF = 0.01
MIN_TAG_POSTS_B = 320
REFERENCE_URL = ("https://raw.githubusercontent.com/munimtechnologies/dev-ai-disclosure/main/"
                 "data/2026-10-16/daily.csv")


def log(msg):
    print(msg, flush=True)


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def days_in(w):
    first, last = (date.fromisoformat(d) for d in WINDOWS[w])
    return (last - first).days + 1


def window_of(day):
    """Window key holding an ISO date string, or None."""
    for w, (first, last) in WINDOWS.items():
        if first <= day <= last:
            return w
    return None


def author_class(n):
    if n >= HEAVY:
        return "heavy"
    if n >= REGULAR:
        return "regular"
    if n >= 1:
        return "occasional"
    return None


def ratio(a, b):
    return None if not b else a / b


def listing_path(per_page, page, token):
    return f"/articles/latest?per_page={per_page}&page={page}&{BUST_PARAM}={token}"


# ---------------------------------------------------------------- analysis

def analyse(posts):
    """posts: iterable of (author, day, engaged, tags). Returns aggregate counts only."""
    counts = {w: Counter() for w in WINDOWS}
    totals = {w: Counter() for w in WINDOWS}
    tag_counts = {w: Counter() for w in WINDOWS}
    daily = defaultdict(Counter)
    for author, day, engaged, tags in posts:
        kind = "engaged" if engaged else "zero_engagement"
        daily[day]["posts"] += 1
        daily[day][kind] += 1
        w = window_of(day)
        if w is None:
            continue
        totals[w]["posts"] += 1
        totals[w][kind] += 1
        for t in tags or ("(no tags)",):
            tag_counts[w][t] += 1
        if author is not None:
            counts[w][author] += 1
    windows = {}
    for w in WINDOWS:
        d = days_in(w)
        windows[w] = {"first": WINDOWS[w][0], "last": WINDOWS[w][1], "days": d,
                      "posts": totals[w]["posts"], "authors": len(counts[w]),
                      "posts_per_day": totals[w]["posts"] / d,
                      "engaged_per_day": totals[w]["engaged"] / d,
                      "zero_engagement_per_day": totals[w]["zero_engagement"] / d}
    transitions = []
    for x, y, kind in TRANSITIONS:
        dx, dy = days_in(x), days_in(y)
        t = {"from": x, "to": y, "kind": kind, "classes": {}}
        for k in CLASSES:
            members = [a for a, n in counts[x].items() if author_class(n) == k]
            base = sum(counts[x][a] for a in members)
            nxt = sum(counts[y][a] for a in members)
            stopped = [a for a in members if counts[y][a] == 0]
            t["classes"][k] = {"authors": len(members), "posts_from": base, "posts_to": nxt,
                               "per_day_from": base / dx, "per_day_to": nxt / dy,
                               "retention": ratio(nxt / dy, base / dx),
                               "authors_stopped": len(stopped),
                               "per_day_from_stopped": sum(counts[x][a] for a in stopped) / dx}
        new = [a for a in counts[y] if a not in counts[x]]
        t["newcomers"] = {"authors": len(new), "posts": sum(counts[y][a] for a in new),
                          "per_day_to": sum(counts[y][a] for a in new) / dy}
        t["authored_per_day_from"] = sum(counts[x].values()) / dx
        t["authored_per_day_to"] = sum(counts[y].values()) / dy
        t["engaged_ratio"] = ratio(windows[y]["engaged_per_day"], windows[x]["engaged_per_day"])
        t["zero_engagement_ratio"] = ratio(windows[y]["zero_engagement_per_day"],
                                           windows[x]["zero_engagement_per_day"])
        transitions.append(t)
    tags = []
    for tag, nb in tag_counts["B"].items():
        if nb < MIN_TAG_POSTS_B:
            continue
        ra, rb, rc = (tag_counts[w][tag] / days_in(w) for w in ("A", "B", "C"))
        tags.append({"tag": tag, "per_day_A": ra, "per_day_B": rb, "per_day_C": rc,
                     "fall_per_day": rb - rc, "ratio_C_B": ratio(rc, rb), "ratio_B_A": ratio(rb, ra)})
    tags.sort(key=lambda r: (-r["fall_per_day"], r["tag"]))
    return {"windows": windows, "transitions": transitions, "tags": tags,
            "daily": {d: dict(c) for d, c in sorted(daily.items())}}


def predictions(an):
    """The two pre-registered predictions and the verdict they give."""
    placebo, test = an["transitions"][0], an["transitions"][1]

    def gap(t):
        if t["engaged_ratio"] is None or t["zero_engagement_ratio"] is None:
            return None
        return t["zero_engagement_ratio"] - t["engaged_ratio"]

    g_test, g_placebo = gap(test), gap(placebo)
    p1 = (g_test is not None and g_placebo is not None
          and g_test <= -P1_MARGIN and abs(g_placebo) < P1_MARGIN)
    h_test = test["classes"]["heavy"]["retention"]
    h_placebo = placebo["classes"]["heavy"]["retention"]
    o_test = test["classes"]["occasional"]["retention"]
    o_placebo = placebo["classes"]["occasional"]["retention"]
    p2 = (None not in (h_test, h_placebo, o_test, o_placebo)
          and h_test <= h_placebo - P2_HEAVY_MARGIN
          and o_test >= o_placebo - P2_OCCASIONAL_MARGIN)
    if p1 and p2:
        verdict = "SUPPORTED"
    elif not p1 and not p2:
        verdict = "NOT SUPPORTED"
    else:
        verdict = "MIXED"
    return {"P1": {"holds": p1, "gap_test": g_test, "gap_placebo": g_placebo},
            "P2": {"holds": p2, "heavy_test": h_test, "heavy_placebo": h_placebo,
                   "occasional_test": o_test, "occasional_placebo": o_placebo},
            "verdict": verdict}


def gate(mine, ref, first=WINDOWS["A"][0], last=WINDOWS["C"][1]):
    """Compare per-day post counts with an earlier sweep. mine, ref: {day: posts}."""
    worst, n = None, 0
    for day, r in sorted(ref.items()):
        if not (first <= day <= last) or not r:
            continue
        n += 1
        d = (mine.get(day, 0) - r) / r
        if worst is None or abs(d) > abs(worst[1]):
            worst = (day, d)
    return {"checked_days": n, "worst_day": worst[0] if worst else None,
            "worst_diff": worst[1] if worst else None,
            "pass": worst is not None and abs(worst[1]) <= GATE_MAX_DAY_DIFF}


def parse_reference(text):
    return {r["date"]: int(r["posts"]) for r in csv.DictReader(io.StringIO(text))}


# ---------------------------------------------------------------- sweep

def fetch(url, pause, tries=6):
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                headers = {k: r.headers.get(k) for k in ("Age", "X-Cache") if r.headers.get(k)}
                body = r.read()
            time.sleep(pause)
            return body, headers
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(120, 5 * (i + 1)))
                continue
            log(f"HTTP {e.code} for {url}")
            return None, {}
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            log(f"retry {i + 1} for {url}: {e}")
            time.sleep(5 * (i + 1))
    return None, {}


def sweep(per_page, budget_minutes, pause):
    t0 = time.time()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    token = started.replace("-", "").replace(":", "").replace("+", "")
    since = WINDOWS["A"][0]
    posts, seen = [], set()
    cov = {"pages": 0, "cached_pages": 0, "duplicate_ids": 0, "max_hole_minutes": 0.0}
    prev_oldest = None
    old_pages = failures = 0
    stopped = "max pages"
    for page in range(1, 1001):
        if (time.time() - t0) / 60 > budget_minutes:
            stopped = "time budget"
            break
        body, headers = fetch(API + listing_path(per_page, page, token), pause)
        try:
            batch = json.loads(body) if body is not None else None
        except json.JSONDecodeError:
            batch = None
        if batch is None:
            failures += 1
            if failures >= 3:
                stopped = f"page {page} unreadable"
                break
            continue
        failures = 0
        if not isinstance(batch, list) or not batch:
            stopped = "end of listing"
            break
        cov["pages"] += 1
        try:
            cached = int(headers.get("Age") or 0) > 0
        except ValueError:
            cached = False
        if cached or "HIT" in str(headers.get("X-Cache") or "").upper():
            cov["cached_pages"] += 1
        dated = [a for a in batch if a.get("published_at")]
        if dated:
            pubs = [parse_time(a["published_at"]) for a in dated]
            if prev_oldest is not None:
                hole = (prev_oldest - max(pubs)).total_seconds() / 60
                cov["max_hole_minutes"] = round(max(cov["max_hole_minutes"], hole), 1)
            prev_oldest = min(pubs)
        for a in dated:
            if a.get("id") in seen:
                cov["duplicate_ids"] += 1
                continue
            day = a["published_at"][:10]
            if day < since:
                continue
            seen.add(a.get("id"))
            engaged = int(a.get("public_reactions_count") or 0) + int(a.get("comments_count") or 0) > 0
            tl = a.get("tag_list")
            tags = tuple(x.strip().lower() for x in (tl.split(",") if isinstance(tl, str) else (tl or [])) if x.strip())
            posts.append(((a.get("user") or {}).get("user_id"), day, engaged, tags))
        if dated and all(a["published_at"][:10] < since for a in dated):
            old_pages += 1
            if old_pages >= 2:
                stopped = "reached since"
                break
        else:
            old_pages = 0
        if page % 25 == 0:
            log(f"  page {page}: {len(posts)} posts, {(time.time() - t0) / 60:.1f} min, coverage {cov}")
    meta = {"version": VERSION, "snapshot_at": started, "since": since, "posts": len(posts),
            "stopped": stopped, "minutes": round((time.time() - t0) / 60, 1), "bust_param": BUST_PARAM,
            "per_page": per_page, "coverage": cov}
    return posts, meta


# ---------------------------------------------------------------- report

def f2(x):
    return "n/a" if x is None else f"{x:.2f}"


def f0(x):
    return f"{x:,.0f}"


def report(an, pred, g, meta):
    w = an["windows"]
    out = ["# Did DEV's post volume fall because of the late-September anti-spam changes?", "",
           f"dropcheck.py {VERSION}, sweep started {meta['snapshot_at']}. Predictions and thresholds were "
           "committed before this sweep ran (PREREG.md). Made by MV2 of Munim, Inc., with AI agents working "
           "in his name; code Apache-2.0, data CC BY 4.0.", "",
           f"Sweep: {meta['posts']} posts since {meta['since']} over {meta['coverage']['pages']} pages; stopped at: "
           f"{meta['stopped']}; {meta['coverage']['cached_pages']} pages had cache headers; "
           f"{meta['coverage']['duplicate_ids']} ids listed twice; largest time hole between pages "
           f"{meta['coverage']['max_hole_minutes']} min.", ""]
    if g.get("pass") is None or g.get("worst_day") is None:
        out += ["Coverage gate: not checked (reference file unreadable or no overlapping days).", ""]
    else:
        out += [f"Coverage gate (per-day posts within {GATE_MAX_DAY_DIFF:.0%} of the 2026-10-16 snapshot on every "
                f"day {WINDOWS['A'][0]}..{WINDOWS['C'][1]}): {'PASS' if g['pass'] else 'FAIL'}; "
                f"{g['checked_days']} days, largest difference {g['worst_diff']:+.2%} on {g['worst_day']}.", ""]
    out += [f"## Verdict: {pred['verdict']}", "",
            f"- P1 (the fall is in posts with no reactions or comments): {'holds' if pred['P1']['holds'] else 'fails'}. "
            f"Zero-engagement ratio minus engaged ratio: test {f2(pred['P1']['gap_test'])} (needed <= "
            f"-{P1_MARGIN}), placebo {f2(pred['P1']['gap_placebo'])} (needed within +/-{P1_MARGIN}).",
            f"- P2 (heavy authors fall, occasional authors do not): {'holds' if pred['P2']['holds'] else 'fails'}. "
            f"Heavy retention test {f2(pred['P2']['heavy_test'])} vs placebo {f2(pred['P2']['heavy_placebo'])} "
            f"(needed at least {P2_HEAVY_MARGIN} lower); occasional test {f2(pred['P2']['occasional_test'])} vs "
            f"placebo {f2(pred['P2']['occasional_placebo'])} (needed no more than {P2_OCCASIONAL_MARGIN} lower).", "",
            "## Windows", "",
            "| Window | Dates | Days | Posts | Posts/day | With a reaction or comment /day | With neither /day | Authors |",
            "|---|---|---|---|---|---|---|---|"]
    for k, v in w.items():
        out.append(f"| {k} | {v['first']}..{v['last']} | {v['days']} | {v['posts']} | {f0(v['posts_per_day'])} | "
                   f"{f0(v['engaged_per_day'])} | {f0(v['zero_engagement_per_day'])} | {v['authors']} |")
    for t in an["transitions"]:
        out += ["", f"## {t['from']} -> {t['to']} ({t['kind']})", "",
                f"Engaged posts/day ratio {f2(t['engaged_ratio'])}; zero-engagement posts/day ratio "
                f"{f2(t['zero_engagement_ratio'])}. Authors are classed by their posts in {t['from']}: heavy >= "
                f"{HEAVY}, regular {REGULAR}-{HEAVY - 1}, occasional 1-{REGULAR - 1}.", "",
                f"| Class (by posts in {t['from']}) | Authors | Posts/day in {t['from']} | Their posts/day in {t['to']} | "
                f"Retention | Authors with no post in {t['to']} | Their posts/day in {t['from']} |",
                "|---|---|---|---|---|---|---|"]
        for k in CLASSES:
            c = t["classes"][k]
            out.append(f"| {k} | {c['authors']} | {f0(c['per_day_from'])} | {f0(c['per_day_to'])} | "
                       f"{f2(c['retention'])} | {c['authors_stopped']} | {f0(c['per_day_from_stopped'])} |")
        n = t["newcomers"]
        out.append(f"| no post in {t['from']} | {n['authors']} | 0 | {f0(n['per_day_to'])} | | | |")
        out.append(f"| **all** | | **{f0(t['authored_per_day_from'])}** | **{f0(t['authored_per_day_to'])}** | | | |")
    out += ["", f"## Tags with at least {MIN_TAG_POSTS_B} posts in B, largest fall in posts/day from B to C", "",
            "| Tag | A /day | B /day | C /day | C/B |", "|---|---|---|---|---|"]
    for r in an["tags"][:25]:
        out.append(f"| {r['tag']} | {f0(r['per_day_A'])} | {f0(r['per_day_B'])} | {f0(r['per_day_C'])} | "
                   f"{f2(r['ratio_C_B'])} |")
    out += ["", "## Limits", "",
            "- This tests whether the fall looks like what the anti-spam changes would do; it cannot see which "
            "accounts DEV marked, and other changes in the same days could act the same way.",
            "- Reactions and comments are counted at the sweep; window C posts are younger, which lowers C's "
            "engaged count and works against P1.",
            "- Posts deleted or unpublished before the sweep are missing from every window.",
            "- Classes come from one window's post count, so heavy authors fall back somewhat in any later window; "
            "the placebo transition measures that baseline.", ""]
    return "\n".join(out)


def rounded(x):
    if isinstance(x, float):
        return round(x, 4)
    if isinstance(x, dict):
        return {k: rounded(v) for k, v in x.items()}
    if isinstance(x, list):
        return [rounded(v) for v in x]
    return x


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--per-page", type=int, default=1000)
    ap.add_argument("--budget-minutes", type=float, default=150)
    ap.add_argument("--pause", type=float, default=PAUSE)
    ap.add_argument("--reference", default=REFERENCE_URL)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    posts, meta = sweep(args.per_page, args.budget_minutes, args.pause)
    log(json.dumps(meta))
    an = analyse(posts)
    body, _ = fetch(args.reference, 0)
    ref = parse_reference(body.decode("utf-8")) if body else {}
    g = gate({d: c.get("posts", 0) for d, c in an["daily"].items()}, ref) if ref else {"pass": None}
    pred = predictions(an)
    if meta["stopped"] != "reached since":
        pred["verdict"] = "INCOMPLETE SWEEP (" + meta["stopped"] + "); not a test"
    with open(os.path.join(args.out_dir, "daily.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["date", "posts", "engaged", "zero_engagement"])
        for d, c in an["daily"].items():
            wr.writerow([d, c.get("posts", 0), c.get("engaged", 0), c.get("zero_engagement", 0)])
    with open(os.path.join(args.out_dir, "tags_drop.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["tag", "per_day_A", "per_day_B", "per_day_C", "fall_per_day",
                                           "ratio_C_B", "ratio_B_A"])
        wr.writeheader()
        wr.writerows(rounded(an["tags"]))
    result = {"meta": meta, "gate": g, "predictions": pred, "windows": an["windows"],
              "transitions": an["transitions"]}
    with open(os.path.join(args.out_dir, "dropcheck.json"), "w", encoding="utf-8") as f:
        json.dump(rounded(result), f, indent=2)
    with open(os.path.join(args.out_dir, "DROPCHECK.md"), "w", encoding="utf-8") as f:
        f.write(report(an, pred, g, meta))
    log(f"DONE verdict={pred['verdict']} gate={g.get('pass')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
