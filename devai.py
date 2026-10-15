#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""How DEV authors use its AI-disclosure labels, measured on every public post.

On 2026-08-26 DEV added three disclosure tiers that an author picks per post:
Hand Written (no_ai), AI-Assisted (some_ai) and Fully Autonomous
(fully_autonomous). Posts where the author picks nothing show not_disclosed.
DEV's public API returns the tier with every article, so the whole platform
can be counted, not sampled.

  collect   pages through DEV's public /articles/latest listing back to
            --since and writes one row per post: id, time, tier, language,
            reading time, reactions, comments, tags, cover image, organisation,
            cross-post. Author ids are held in memory only, to count distinct
            authors per tier and per week; usernames and ids are never written.
  analyse   tier shares per day and week, tiers by tag, reactions and comments
            by tier compared within the same publishing day, post traits by
            tier, author concentration, and machine-paced bursts (one exact tag
            set and one tier posted minutes apart) with every headline number
            recomputed without them; writes REPORT.md and CSV/JSON tables.

Uses only DEV's public API (no key). Made by MV2 of Munim, Inc., with AI agents
working in his name.
"""
import argparse
import bisect
import csv
import gzip
import json
import math
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

VERSION = "0.2.0"
API = "https://dev.to/api"
UA = f"mv2-dev-ai-disclosure-study/{VERSION} (MV2 of Munim, Inc.; munimversion2@gmail.com)"
PAUSE = 1.0
# Day of DEV's announcement; replaced by the announcement's exact time when readable.
LAUNCH = "2026-08-26T00:00:00Z"
LAUNCH_POST = "/articles/devteam/introducing-ai-disclosure-on-dev-tools-for-nuance-clarity-and-better-feeds-34mk"
LEVELS = ["not_disclosed", "no_ai", "some_ai", "fully_autonomous"]
LABELLED = LEVELS[1:]
NAMES = {"not_disclosed": "Not disclosed", "no_ai": "Hand Written (no AI)",
         "some_ai": "AI-Assisted", "fully_autonomous": "Fully Autonomous"}
MIN_AGE_DAYS = 7
# A burst: at least this many posts since launch with one exact non-empty tag set and one
# tier, with a median gap between consecutive posts of at most this many minutes.
BURST_MIN_POSTS = 100
BURST_MAX_GAP_MINUTES = 15.0
POST_COLS = ["article_id", "published_at", "date", "level", "language", "reading_time",
             "reactions", "comments", "n_tags", "tags", "has_cover", "is_org",
             "crossposted", "edited_after_launch"]


def log(msg):
    print(msg, flush=True)


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def tags_of(article):
    t = article.get("tag_list")
    if isinstance(t, str):
        return [x.strip() for x in t.split(",") if x.strip()]
    return [str(x) for x in (t or [])]


def level_of(article):
    return str(article.get("ai_disclosure_level") or "not_disclosed").strip().lower()


def row_of(a, launch):
    """One output row for a listed article. Holds no username or author id."""
    pub = parse_time(a["published_at"])
    edited = a.get("edited_at")
    canon = urllib.parse.urlparse(a.get("canonical_url") or "").netloc.lower()
    tags = [t.lower() for t in tags_of(a)]
    return {
        "article_id": int(a["id"]),
        "published_at": a["published_at"],
        "date": pub.strftime("%Y-%m-%d"),
        "level": level_of(a),
        "language": a.get("language") or "",
        "reading_time": int(a.get("reading_time_minutes") or 0),
        "reactions": int(a.get("public_reactions_count") or 0),
        "comments": int(a.get("comments_count") or 0),
        "n_tags": len(tags),
        "tags": " ".join(tags),
        "has_cover": int(bool(a.get("cover_image"))),
        "is_org": int(bool(a.get("organization"))),
        "crossposted": int(bool(canon) and canon != "dev.to" and not canon.endswith(".dev.to")),
        "edited_after_launch": int(bool(edited) and parse_time(edited) >= launch),
    }


class Client:
    def __init__(self, pause=PAUSE):
        self.pause = pause
        self.requests = 0

    def get(self, path, tries=6):
        url = API + path
        for i in range(tries):
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = json.load(r)
                self.requests += 1
                time.sleep(self.pause)
                return data
            except urllib.error.HTTPError as e:
                self.requests += 1
                if e.code == 404:
                    time.sleep(self.pause)
                    return None
                if e.code in (429, 500, 502, 503, 504):
                    wait = 5 * (i + 1)
                    try:
                        wait = max(wait, int(e.headers.get("Retry-After") or 0))
                    except ValueError:
                        pass
                    time.sleep(min(wait, 120))
                    continue
                log(f"HTTP {e.code} for {url}")
                return None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as e:
                log(f"retry {i + 1} for {url}: {e}")
                time.sleep(5 * (i + 1))
        return None


def author_summary(authors):
    """Aggregate counts only: authors is {author: Counter(level -> posts)}."""
    out = {"authors": len(authors), "by_level": {}}
    levels = sorted({lvl for c in authors.values() for lvl in c if c[lvl]})
    for lvl in levels:
        counts = sorted((c[lvl] for c in authors.values() if c[lvl]), reverse=True)
        total = sum(counts)
        need, acc = 0, 0
        for n in counts:
            acc += n
            need += 1
            if acc >= total / 2:
                break
        out["by_level"][lvl] = {"authors": len(counts), "posts": total,
                                "top10_authors_share": round(sum(counts[:10]) / total, 3) if total else None,
                                "authors_for_half_of_posts": need}
    kinds = [sum(1 for lvl in LABELLED if c[lvl]) for c in authors.values()]
    out["authors_with_any_label"] = sum(1 for k in kinds if k >= 1)
    out["authors_with_two_or_more_labels"] = sum(1 for k in kinds if k >= 2)
    out["authors_mixing_labelled_and_undisclosed"] = sum(
        1 for c in authors.values() if c["not_disclosed"] and any(c[lvl] for lvl in LABELLED))
    return out


def weekly_author_summary(weekly):
    """Counts only: weekly is {week: {author: set of levels used that week}}.

    Each author counts once per week however much they post, so a single prolific
    account cannot move these shares the way it moves post shares."""
    out = []
    for w in sorted(weekly):
        used = list(weekly[w].values())
        row = {"week": w, "authors": len(used)}
        for lvl in LABELLED:
            row[lvl] = sum(1 for s in used if lvl in s)
        row["any_label"] = sum(1 for s in used if s & set(LABELLED))
        out.append(row)
    return out


def collect(args):
    os.makedirs(args.out_dir, exist_ok=True)
    t0 = time.time()
    client = Client(args.pause)
    started = now_iso()
    since = parse_time(args.since + "T00:00:00Z")
    launch = parse_time(LAUNCH)
    post = client.get(LAUNCH_POST)
    launch_source = "default"
    if isinstance(post, dict) and post.get("published_at"):
        launch = parse_time(post["published_at"])
        launch_source = f"article {post.get('id')}"
    log(f"launch: {launch.isoformat()} ({launch_source})")
    seen = set()
    authors = defaultdict(Counter)
    weekly_authors = defaultdict(dict)
    pages = written = old_pages = failures = 0
    oldest = newest = None
    stopped = "max pages"
    with open(os.path.join(args.out_dir, "posts.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=POST_COLS)
        wr.writeheader()
        for page in range(1, args.max_pages + 1):
            if (time.time() - t0) / 60 > args.budget_minutes:
                stopped = "time budget"
                break
            batch = client.get(f"/articles/latest?per_page={args.per_page}&page={page}")
            if batch is None:
                failures += 1
                log(f"page {page} unreadable ({failures} in a row)")
                if failures >= 3:
                    stopped = f"page {page} unreadable"
                    break
                continue
            failures = 0
            if not isinstance(batch, list) or not batch:
                stopped = "end of listing"
                break
            pages += 1
            dated = [a for a in batch if a.get("published_at")]
            for a in dated:
                if a.get("id") in seen:
                    continue
                pub = parse_time(a["published_at"])
                if pub < since:
                    continue
                seen.add(a["id"])
                row = row_of(a, launch)
                wr.writerow(row)
                written += 1
                oldest = pub if oldest is None else min(oldest, pub)
                newest = pub if newest is None else max(newest, pub)
                uid = (a.get("user") or {}).get("user_id")
                if uid is not None and pub >= launch:
                    authors[uid][row["level"]] += 1
                    weekly_authors[week_start(row["date"], launch)].setdefault(uid, set()).add(row["level"])
            if dated and all(parse_time(a["published_at"]) < since for a in dated):
                old_pages += 1
                if old_pages >= 2:
                    stopped = "reached --since"
                    break
            else:
                old_pages = 0
            if page % 25 == 0:
                log(f"  page {page}: {written} posts, oldest {oldest}, {(time.time() - t0) / 60:.1f} min")
    with open(os.path.join(args.out_dir, "posts.csv"), "rb") as src, \
            gzip.open(os.path.join(args.out_dir, "posts.csv.gz"), "wb") as dst:
        shutil.copyfileobj(src, dst)
    summary = author_summary(authors)
    summary["weekly"] = weekly_author_summary(weekly_authors)
    with open(os.path.join(args.out_dir, "authors.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    meta = {"version": VERSION, "snapshot_at": started, "finished_at": now_iso(), "since": args.since,
            "launch": launch.isoformat(), "launch_source": launch_source,
            "pages": pages, "per_page": args.per_page, "posts": written,
            "oldest": oldest.isoformat() if oldest else None,
            "newest": newest.isoformat() if newest else None,
            "stopped": stopped, "requests": client.requests,
            "minutes": round((time.time() - t0) / 60, 1)}
    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    log(json.dumps(meta))
    return 0


# ---------------------------------------------------------------- analysis

def pct_in(sorted_vals, x, exclude_self=False):
    """Share of sorted_vals below x, ties counted half. 0.5 = typical."""
    n = len(sorted_vals) - (1 if exclude_self else 0)
    if n <= 0:
        return 0.5
    lt = bisect.bisect_left(sorted_vals, x)
    eq = bisect.bisect_right(sorted_vals, x) - lt - (1 if exclude_self else 0)
    return (lt + 0.5 * eq) / n


def median(vals):
    if not vals:
        return None
    s = sorted(vals)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def week_start(date_str, launch):
    """Start date of the 7-day bucket holding date_str, buckets aligned to launch day."""
    d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    ld = launch.replace(hour=0, minute=0, second=0, microsecond=0)
    k = (d - ld).days // 7
    return (ld + timedelta(days=7 * k)).strftime("%Y-%m-%d")


def shares(counter):
    n = sum(counter.values())
    out = {"posts": n}
    for lvl in LEVELS:
        out[lvl] = round(counter[lvl] / n, 4) if n else None
    out["any_label"] = round(sum(counter[lvl] for lvl in LABELLED) / n, 4) if n else None
    return out


def weekly_shares(daily, launch):
    weekly = defaultdict(Counter)
    week_days = defaultdict(set)
    for d, c in daily.items():
        w = week_start(d, launch)
        weekly[w].update(c)
        week_days[w].add(d)
    return [dict(week=w, days=len(week_days[w]), **shares(weekly[w])) for w in sorted(weekly)]


def engagement(eng, cutoff_ts, en_only=False):
    """Reactions and comments by tier, each post ranked against its own publishing day."""
    days = defaultdict(list)
    for d, ts, rx, cm, lvl, en in eng:
        if ts > cutoff_ts or (en_only and not en):
            continue
        days[d].append((rx, cm, lvl))
    acc = {}
    for posts in days.values():
        srt = sorted(p[0] for p in posts)
        for rx, cm, lvl in posts:
            a = acc.setdefault(lvl, {"n": 0, "pct": 0.0, "rx": [], "cm": 0, "zero_rx": 0, "zero_cm": 0})
            a["n"] += 1
            a["pct"] += pct_in(srt, rx, exclude_self=True)
            a["rx"].append(rx)
            a["cm"] += cm
            a["zero_rx"] += int(rx == 0)
            a["zero_cm"] += int(cm == 0)
    out = {}
    for lvl, a in acc.items():
        n = a["n"]
        mean = a["pct"] / n
        se = math.sqrt(1 / (12 * n))
        out[lvl] = {"posts": n, "mean_day_percentile": round(mean, 3), "z": round((mean - 0.5) / se, 2),
                    "mean_reactions": round(sum(a["rx"]) / n, 2), "median_reactions": median(a["rx"]),
                    "share_zero_reactions": round(a["zero_rx"] / n, 3),
                    "mean_comments": round(a["cm"] / n, 2), "share_zero_comments": round(a["zero_cm"] / n, 3)}
    return out


def find_bursts(path, launch, min_posts=BURST_MIN_POSTS, max_gap_minutes=BURST_MAX_GAP_MINUTES):
    """Machine-paced groups among posts since launch: one exact non-empty tag set and one
    tier, at least min_posts posts, median gap between consecutive posts at most
    max_gap_minutes. Returns (groups, set of (tags, level) keys)."""
    times = defaultdict(list)
    reacts = Counter()
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["tags"]:
                continue
            pub = parse_time(r["published_at"])
            if pub < launch:
                continue
            key = (r["tags"], r["level"])
            times[key].append(pub.timestamp())
            reacts[key] += int(r["reactions"])
    groups = []
    for key, ts in times.items():
        if len(ts) < max(min_posts, 2):
            continue
        ts.sort()
        gap = median([b - a for a, b in zip(ts, ts[1:])]) / 60
        if gap <= max_gap_minutes:
            groups.append({"tags": key[0], "level": key[1], "posts": len(ts),
                           "first": datetime.fromtimestamp(ts[0], timezone.utc).isoformat(timespec="seconds"),
                           "last": datetime.fromtimestamp(ts[-1], timezone.utc).isoformat(timespec="seconds"),
                           "median_gap_minutes": round(gap, 2), "reactions": reacts[key]})
    groups.sort(key=lambda g: -g["posts"])
    return groups, {(g["tags"], g["level"]) for g in groups}


def analyse(args):
    os.makedirs(args.out_dir, exist_ok=True)
    meta = {}
    if args.meta and os.path.exists(args.meta):
        with open(args.meta, encoding="utf-8") as f:
            meta = json.load(f)
    launch = parse_time(meta.get("launch") or LAUNCH)
    min_posts = getattr(args, "burst_min_posts", BURST_MIN_POSTS)
    max_gap = getattr(args, "burst_max_gap_minutes", BURST_MAX_GAP_MINUTES)
    bursts, burst_keys = find_bursts(args.posts, launch, min_posts, max_gap)
    daily, daily_x = defaultdict(Counter), defaultdict(Counter)
    tags = defaultdict(Counter)
    overall, overall_x, pre, challenge = Counter(), Counter(), Counter(), Counter()
    pre_labelled_edited = 0
    traits = {}
    eng, eng_x = [], []
    latest = None
    with open(args.posts, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pub = parse_time(r["published_at"])
            lvl = r["level"]
            in_burst = pub >= launch and (r["tags"], lvl) in burst_keys
            daily[r["date"]][lvl] += 1
            if not in_burst:
                daily_x[r["date"]][lvl] += 1
            latest = pub if latest is None else max(latest, pub)
            if pub < launch:
                pre[lvl] += 1
                if lvl in LABELLED and r["edited_after_launch"] == "1":
                    pre_labelled_edited += 1
                continue
            overall[lvl] += 1
            if not in_burst:
                overall_x[lvl] += 1
            post_tags = r["tags"].split()
            for t in post_tags:
                tags[t][lvl] += 1
            if "hf26challenge" in post_tags:
                challenge[lvl] += 1
            en = int((r["language"] or "en") == "en")
            t = traits.setdefault(lvl, {"n": 0, "reading": [], "en": 0, "cover": 0, "org": 0,
                                        "cross": 0, "no_tags": 0})
            t["n"] += 1
            t["reading"].append(int(r["reading_time"]))
            t["en"] += en
            t["cover"] += int(r["has_cover"])
            t["org"] += int(r["is_org"])
            t["cross"] += int(r["crossposted"])
            t["no_tags"] += int(r["n_tags"] == "0")
            e = (r["date"], pub.timestamp(), int(r["reactions"]), int(r["comments"]), lvl, en)
            eng.append(e)
            if not in_burst:
                eng_x.append(e)
    snap = parse_time(meta["snapshot_at"]) if meta.get("snapshot_at") else latest
    cutoff = (snap - timedelta(days=MIN_AGE_DAYS)) if snap else launch

    with open(os.path.join(args.out_dir, "daily.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["date", "posts"] + LEVELS + ["other", "share_any_label", "burst_posts"])
        for d in sorted(daily):
            c = daily[d]
            n = sum(c.values())
            other = n - sum(c[lvl] for lvl in LEVELS)
            wr.writerow([d, n] + [c[lvl] for lvl in LEVELS] + [other,
                        round(sum(c[lvl] for lvl in LABELLED) / n, 4) if n else "",
                        n - sum(daily_x[d].values())])
    with open(os.path.join(args.out_dir, "bursts.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["tags", "level", "posts", "first", "last", "median_gap_minutes",
                                           "reactions"])
        wr.writeheader()
        wr.writerows(bursts)

    tag_rows = []
    for t, c in tags.items():
        n = sum(c.values())
        if n >= args.min_tag_posts:
            tag_rows.append(dict(tag=t, **shares(c)))
    tag_rows.sort(key=lambda r: -r["posts"])
    with open(os.path.join(args.out_dir, "tags.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["tag", "posts"] + LEVELS + ["any_label"])
        wr.writeheader()
        wr.writerows(tag_rows)

    trait_out = {}
    for lvl, t in traits.items():
        n = t["n"]
        trait_out[lvl] = {"posts": n, "median_reading_minutes": median(t["reading"]),
                          "share_english": round(t["en"] / n, 3), "share_cover_image": round(t["cover"] / n, 3),
                          "share_organisation": round(t["org"] / n, 3),
                          "share_crossposted": round(t["cross"] / n, 3),
                          "share_no_tags": round(t["no_tags"] / n, 3)}
    authors = {}
    if args.authors and os.path.exists(args.authors):
        with open(args.authors, encoding="utf-8") as f:
            authors = json.load(f)
    summary = {
        "meta": meta, "version": VERSION, "launch": launch.isoformat(),
        "engagement_cutoff": cutoff.isoformat(),
        "before_launch": dict(shares(pre), labelled_and_edited_after_launch=pre_labelled_edited,
                              labelled=sum(pre[lvl] for lvl in LABELLED)),
        "since_launch": dict(shares(overall), counts={k: overall[k] for k in sorted(overall)}),
        "weekly": weekly_shares(daily, launch),
        "burst_rule": {"min_posts": min_posts, "max_median_gap_minutes": max_gap},
        "bursts": bursts,
        "since_launch_excluding_bursts": dict(shares(overall_x), counts={k: overall_x[k] for k in sorted(overall_x)}),
        "weekly_excluding_bursts": weekly_shares(daily_x, launch),
        "engagement_all": engagement(eng, cutoff.timestamp()),
        "engagement_english": engagement(eng, cutoff.timestamp(), en_only=True),
        "engagement_all_excluding_bursts": engagement(eng_x, cutoff.timestamp()),
        "traits": trait_out,
        "hf26challenge": shares(challenge),
        "authors": authors,
        "top_tags": tag_rows[:30],
        "most_labelled_tags": sorted((r for r in tag_rows if r["posts"] >= args.min_rank_tag_posts),
                                     key=lambda r: -(r["any_label"] or 0))[:15],
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(args.out_dir, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write(report(summary))
    log(json.dumps({k: summary[k] for k in ("before_launch", "since_launch", "since_launch_excluding_bursts")}))
    log(f"bursts: {len(bursts)} groups, {sum(g['posts'] for g in bursts)} posts")
    return 0


def pc(x):
    return "" if x is None else f"{100 * x:.1f}%"


def engagement_table(e):
    out = ["| Label | Posts | Mean day percentile | z | Mean reactions | Median | No reactions | Mean comments | No comments |",
           "|---|---|---|---|---|---|---|---|---|"]
    for lvl in LEVELS:
        if lvl in e:
            r = e[lvl]
            out.append(f"| {NAMES[lvl]} | {r['posts']} | {r['mean_day_percentile']:.2f} | {r['z']:+.1f} | "
                       f"{r['mean_reactions']} | {r['median_reactions']} | {pc(r['share_zero_reactions'])} | "
                       f"{r['mean_comments']} | {pc(r['share_zero_comments'])} |")
    return out


def report(s):
    m = s.get("meta") or {}
    sl = s["since_launch"]
    out = ["# How DEV authors use AI-disclosure labels", "",
           "Every public post in DEV's /articles/latest listing"
           + (f" from {m.get('since')} to the snapshot at {m.get('snapshot_at')}" if m else "")
           + f". DEV announced the labels at {s['launch']}. "
           f"devai.py {s.get('version', '')}. "
           "Made by MV2 of Munim, Inc., with AI agents working in his name; code Apache-2.0, data CC BY 4.0.", ""]
    if m:
        out += [f"Coverage: {m.get('posts')} posts over {m.get('pages')} listing pages "
                f"(oldest {m.get('oldest')}, newest {m.get('newest')}); stopped at: {m.get('stopped')}.", ""]
    out += ["## Since launch: which label posts carry", "",
            f"{sl['posts']} posts published after the announcement.", "",
            "| Label | Posts | Share |", "|---|---|---|"]
    for lvl in LEVELS:
        out.append(f"| {NAMES[lvl]} | {sl['counts'].get(lvl, 0)} | {pc(sl[lvl])} |")
    other = {k: v for k, v in sl["counts"].items() if k not in LEVELS}
    if other:
        out.append(f"| other values {sorted(other)} | {sum(other.values())} | |")
    out.append(f"| **Any label** | | **{pc(sl['any_label'])}** |")
    b = s["before_launch"]
    out += ["", f"Before the announcement: {b['posts']} posts, {b['labelled']} of them carry a label now "
            f"({b['labelled_and_edited_after_launch']} of those were edited after the announcement).", "",
            "## Week by week (weeks start on launch day; first and last may be partial)", "",
            "| Week from | Days | Posts | Hand Written | AI-Assisted | Fully Autonomous | Any label |",
            "|---|---|---|---|---|---|---|"]
    for w in s["weekly"]:
        out.append(f"| {w['week']} | {w['days']} | {w['posts']} | {pc(w['no_ai'])} | {pc(w['some_ai'])} | "
                   f"{pc(w['fully_autonomous'])} | {pc(w['any_label'])} |")
    rule = s.get("burst_rule") or {}
    bursts = s.get("bursts") or []
    if "since_launch_excluding_bursts" in s:
        x = s["since_launch_excluding_bursts"]
        out += ["", "## Bursts: one tag set, one label, machine pace", "",
                f"A burst is a group of at least {rule.get('min_posts')} posts since launch that share one exact, "
                f"non-empty tag set and one label, with a median gap of at most {rule.get('max_median_gap_minutes')} "
                "minutes between consecutive posts. Rule set after the first snapshot showed one such group; "
                "every group it finds is listed, so a reader can judge what was left out.", ""]
        if bursts:
            out += [f"{len(bursts)} groups, {sum(g['posts'] for g in bursts)} posts.", "",
                    "| Tags | Label | Posts | First | Last | Median gap (min) | Reactions |", "|---|---|---|---|---|---|---|"]
            for g in bursts[:25]:
                out.append(f"| {g['tags']} | {NAMES.get(g['level'], g['level'])} | {g['posts']} | {g['first']} | "
                           f"{g['last']} | {g['median_gap_minutes']} | {g['reactions']} |")
        else:
            out.append("No group meets the rule.")
        out += ["", f"Since launch without bursts: {x['posts']} posts.", "",
                "| Label | Posts | Share |", "|---|---|---|"]
        for lvl in LEVELS:
            out.append(f"| {NAMES[lvl]} | {x['counts'].get(lvl, 0)} | {pc(x[lvl])} |")
        out += [f"| **Any label** | | **{pc(x['any_label'])}** |", "",
                "Week by week without bursts:", "",
                "| Week from | Days | Posts | Hand Written | AI-Assisted | Fully Autonomous | Any label |",
                "|---|---|---|---|---|---|---|"]
        for w in s["weekly_excluding_bursts"]:
            out.append(f"| {w['week']} | {w['days']} | {w['posts']} | {pc(w['no_ai'])} | {pc(w['some_ai'])} | "
                       f"{pc(w['fully_autonomous'])} | {pc(w['any_label'])} |")
    a = s.get("authors") or {}
    if a.get("weekly"):
        out += ["", "## Authors week by week", "",
                "Share of the week's active authors (since launch) who used each label at least once that week. "
                "Each author counts once per week, so one prolific account cannot move these shares.", "",
                "| Week from | Authors | Hand Written | AI-Assisted | Fully Autonomous | Any label |",
                "|---|---|---|---|---|---|"]
        for w in a["weekly"]:
            n = w["authors"]
            out.append(f"| {w['week']} | {n} | " + " | ".join(
                pc(w[k] / n if n else None) for k in ("no_ai", "some_ai", "fully_autonomous", "any_label")) + " |")
    for title, key in (("all posts", "engagement_all"), ("English posts only", "engagement_english"),
                       ("all posts, bursts left out", "engagement_all_excluding_bursts")):
        if key not in s:
            continue
        out += ["", f"## Reactions and comments by label ({title})", "",
                f"Posts published after the announcement and at least {MIN_AGE_DAYS} days before the snapshot "
                f"(cutoff {s['engagement_cutoff']}). Each post's reactions are ranked against every other post "
                "published the same UTC day: 0.50 is typical for that day. z compares the mean with 0.50; "
                "this is a correlation, not an effect of the label.", ""]
        out += engagement_table(s[key])
    out += ["", "## What labelled posts look like", "",
            "| Label | Posts | Median reading minutes | English | Cover image | Organisation | Cross-posted | No tags |",
            "|---|---|---|---|---|---|---|---|"]
    for lvl in LEVELS:
        t = s["traits"].get(lvl)
        if t:
            out.append(f"| {NAMES[lvl]} | {t['posts']} | {t['median_reading_minutes']} | {pc(t['share_english'])} | "
                       f"{pc(t['share_cover_image'])} | {pc(t['share_organisation'])} | "
                       f"{pc(t['share_crossposted'])} | {pc(t['share_no_tags'])} |")
    if a.get("by_level"):
        out += ["", "## Authors", "",
                f"{a['authors']} distinct authors posted after the announcement; {a['authors_with_any_label']} used "
                f"a label at least once, {a['authors_with_two_or_more_labels']} used two or more different labels, "
                f"and {a['authors_mixing_labelled_and_undisclosed']} have both labelled and unlabelled posts. "
                "Counts only; no author is named or stored.", "",
                "| Label | Authors | Posts | Top 10 authors' share | Authors behind half the posts |",
                "|---|---|---|---|---|"]
        for lvl in LEVELS:
            r = a["by_level"].get(lvl)
            if r:
                out.append(f"| {NAMES[lvl]} | {r['authors']} | {r['posts']} | {pc(r['top10_authors_share'])} | "
                           f"{r['authors_for_half_of_posts']} |")
    out += ["", "## Tags", "", "Largest tags since the announcement:", "",
            "| Tag | Posts | Hand Written | AI-Assisted | Fully Autonomous | Any label |", "|---|---|---|---|---|---|"]
    for r in s["top_tags"][:20]:
        out.append(f"| {r['tag']} | {r['posts']} | {pc(r['no_ai'])} | {pc(r['some_ai'])} | "
                   f"{pc(r['fully_autonomous'])} | {pc(r['any_label'])} |")
    if s["most_labelled_tags"]:
        out += ["", "Tags with the highest share of labelled posts (large tags only):", "",
                "| Tag | Posts | Hand Written | AI-Assisted | Fully Autonomous | Any label |",
                "|---|---|---|---|---|---|"]
        for r in s["most_labelled_tags"]:
            out.append(f"| {r['tag']} | {r['posts']} | {pc(r['no_ai'])} | {pc(r['some_ai'])} | "
                       f"{pc(r['fully_autonomous'])} | {pc(r['any_label'])} |")
    h = s["hf26challenge"]
    if h["posts"]:
        out += ["", f"Hacktoberfest challenge entries (tag hf26challenge): {h['posts']} posts, "
                f"{pc(h['any_label'])} labelled (Hand Written {pc(h['no_ai'])}, AI-Assisted {pc(h['some_ai'])}, "
                f"Fully Autonomous {pc(h['fully_autonomous'])})."]
    out += ["", "## Limits", "",
            "- A label is what the author chose, not a measurement of how a post was written. "
            "Not disclosed does not mean no AI.",
            "- The API gives each post's label as it is now; a label added or changed later looks the same as one "
            "set at publishing time.",
            "- Reactions and comments are counted at the snapshot; posts younger than "
            f"{MIN_AGE_DAYS} days are left out of that comparison, and the day percentile removes the effect of age.",
            "- Labels go with other differences (topic, language, author habits, spam), so differences in "
            "reactions are correlations, not effects of the label.",
            "- The burst rule catches only exact repeats of one tag set; a campaign that varies its tags is missed.",
            "- Posts deleted or unpublished before the snapshot are missing.", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--since", default="2026-08-12")
    c.add_argument("--per-page", type=int, default=1000)
    c.add_argument("--max-pages", type=int, default=1000)
    c.add_argument("--budget-minutes", type=float, default=150)
    c.add_argument("--pause", type=float, default=PAUSE)
    c.add_argument("--out-dir", default="out")
    c.set_defaults(func=collect)
    a = sub.add_parser("analyse")
    a.add_argument("--posts", required=True)
    a.add_argument("--meta", default="")
    a.add_argument("--authors", default="")
    a.add_argument("--min-tag-posts", type=int, default=100)
    a.add_argument("--min-rank-tag-posts", type=int, default=1000)
    a.add_argument("--burst-min-posts", type=int, default=BURST_MIN_POSTS)
    a.add_argument("--burst-max-gap-minutes", type=float, default=BURST_MAX_GAP_MINUTES)
    a.add_argument("--out-dir", default="out")
    a.set_defaults(func=analyse)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
