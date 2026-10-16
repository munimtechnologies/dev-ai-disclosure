#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Compare four whole-platform sweeps of DEV's /articles/latest listing, day by day.

v1 (2026-10-14) and v7 (2026-10-16) were read with every page fresh; v3 and v5 reused
plain page URLs, so many of their pages came from DEV's edge cache at mixed ages. Each
sweep's published daily.csv is fetched from munimtechnologies/dev-ai-disclosure, and
the per-day post counts are compared with v7 over the full days every sweep covers.

  python compare.py --out-dir out          fetch, compare, write COMPARE.md + compare.json
  python compare.py --local DIR --out-dir out   read <name>-daily.csv files from DIR instead

Made by MV2 of Munim, Inc., with AI agents working in his name.
"""
import argparse
import csv
import io
import json
import os
import sys
import urllib.request
from datetime import date, timedelta

VERSION = "0.1.0"
RAW = "https://raw.githubusercontent.com/munimtechnologies/dev-ai-disclosure/main/"
UA = f"mv2-dev-ai-disclosure-compare/{VERSION} (MV2 of Munim, Inc.; mv2@munimtech.com)"
BASE = "v7"
# name, snapshot (UTC), how its pages were requested, path in the repo
SWEEPS = [
    ("v1", "2026-10-14 19:01", "plain URLs, first sweep at per_page=1000", "data/daily.csv"),
    ("v3", "2026-10-15 18:31", "plain URLs", "sweeps/2026-10-15-v3-daily.csv"),
    ("v5", "2026-10-16 12:44", "plain URLs", "sweeps/2026-10-16-v5-daily.csv"),
    ("v7", "2026-10-16 16:32", "per-sweep token in `item`", "data/2026-10-16/daily.csv"),
]


def parse_daily(text):
    """{date string: posts} from a daily.csv body."""
    return {r["date"]: int(r["posts"]) for r in csv.DictReader(io.StringIO(text)) if r.get("date")}


def fetch(path):
    req = urllib.request.Request(RAW + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def common_window(series):
    """(first, last) dates covered by every series, leaving out each series' last day,
    which a sweep only covers up to its snapshot time."""
    firsts, lasts = [], []
    for days in series.values():
        ds = sorted(days)
        firsts.append(ds[0])
        lasts.append((date.fromisoformat(ds[-1]) - timedelta(days=1)).isoformat())
    return max(firsts), min(lasts)


def days_between(first, last):
    d, end, out = date.fromisoformat(first), date.fromisoformat(last), []
    while d <= end:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def compare(base, other, days):
    """Per-day comparison of other against base over days (both {date: posts})."""
    tb = sum(base.get(d, 0) for d in days)
    to = sum(other.get(d, 0) for d in days)
    worst_abs, worst_abs_day = 0, None
    worst_loss, worst_loss_day = 0.0, None
    within_1pct = over_5pct_loss = 0
    for d in days:
        b, o = base.get(d, 0), other.get(d, 0)
        if abs(o - b) > worst_abs:
            worst_abs, worst_abs_day = abs(o - b), d
        loss = (b - o) / b if b else 0.0
        if loss > worst_loss:
            worst_loss, worst_loss_day = loss, d
        if b and abs(o - b) / b <= 0.01:
            within_1pct += 1
        if loss > 0.05:
            over_5pct_loss += 1
    return {"days": len(days), "posts_base": tb, "posts": to,
            "ratio": round(to / tb, 4) if tb else None,
            "max_abs_day_diff": worst_abs, "max_abs_day": worst_abs_day,
            "max_day_loss": round(worst_loss, 4), "max_day_loss_day": worst_loss_day,
            "days_within_1pct": within_1pct, "days_losing_over_5pct": over_5pct_loss}


def report(window, rows, series, days):
    out = ["# Four sweeps of DEV's /articles/latest, compared day by day", "",
           f"compare.py {VERSION}. Made by MV2 of Munim, Inc., with AI agents working in his name. "
           "Data CC BY 4.0.", "",
           f"Window: {window[0]} to {window[1]} ({len(days)} full days that every sweep covers). "
           f"Base: {BASE}, whose page URLs were all new to the cache.", "",
           "| Sweep | Snapshot (UTC) | Page URLs | Posts in window | vs v7 | Days within 1% of v7 | "
           "Days losing over 5% | Largest one-day loss | Largest one-day difference (posts) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for name, snap, how, _ in SWEEPS:
        c = rows[name]
        loss = f"{100 * c['max_day_loss']:.1f}% ({c['max_day_loss_day']})" if c["max_day_loss_day"] else "none"
        diff = f"{c['max_abs_day_diff']} ({c['max_abs_day']})" if c["max_abs_day"] else "0"
        out.append(f"| {name} | {snap} | {how} | {c['posts']:,} | {100 * c['ratio']:.2f}% | "
                   f"{c['days_within_1pct']} of {c['days']} | {c['days_losing_over_5pct']} | {loss} | {diff} |")
    out += ["", "## Per day", "", "| Date | " + " | ".join(n for n, *_ in SWEEPS) + " |",
            "|---|" + "---|" * len(SWEEPS)]
    for d in days:
        out.append(f"| {d} | " + " | ".join(str(series[n].get(d, 0)) for n, *_ in SWEEPS) + " |")
    out += ["", "## Limits", "",
            "- Counts are posts listed per UTC day at each snapshot. Posts deleted or unpublished between "
            "snapshots lower a later sweep slightly; posts published later with an earlier date raise it.",
            "- v1 used plain URLs too, but it was the first sweep at per_page=1000, so no page of that size "
            "was cached yet; its agreement with v7 in the first table is what shows it was coherent.", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--local", default="", help="folder with <name>-daily.csv files (no network)")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    series = {}
    for name, _, _, path in SWEEPS:
        try:
            if args.local:
                with open(os.path.join(args.local, f"{name}-daily.csv"), encoding="utf-8") as f:
                    text = f.read()
            else:
                text = fetch(path)
        except Exception as exc:  # a missing sweep would make every comparison wrong
            print(f"FAILED {name} {path}: {exc}")
            return 1
        series[name] = parse_daily(text)
        print(f"ok {name}: {len(series[name])} days")
    window = common_window(series)
    days = days_between(*window)
    rows = {name: compare(series[BASE], series[name], days) for name, *_ in SWEEPS}
    with open(os.path.join(args.out_dir, "compare.json"), "w", encoding="utf-8") as f:
        json.dump({"version": VERSION, "base": BASE, "window": window, "sweeps": rows}, f, indent=2)
    with open(os.path.join(args.out_dir, "COMPARE.md"), "w", encoding="utf-8") as f:
        f.write(report(window, rows, series, days))
    print(json.dumps({"window": window, "sweeps": rows}))
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
