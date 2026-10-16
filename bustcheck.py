#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Which query parameters reach the cache key of DEV's /api/articles/latest?

Forem's Fastly config (config/fastly/snippets/safe_params_list.vcl) keeps only
allowlisted query parameters before the cache lookup. So a per-sweep token in an
unlisted parameter (devai 0.4.0 used `sweep`) cannot stop a page coming from the
edge cache, while one in an allowlisted parameter that the endpoint ignores
(`item`) should. For a few listing pages this fetches:

  plain     /articles/latest?per_page=1000&page=N
  sweep x2  the same with &sweep=<new token>, twice
  item x2   the same with &item=<new token>, twice

and records the cache headers and which ids came back. A parameter is in the
cache key when its first request is a miss and the identical second one a hit;
it is stripped when a never-used value still comes back from the cache or, when
the headers say nothing, when it returns exactly the plain page while the item
variant does not.

Uses only DEV's public API (no key); stores ids and times only, no usernames or
titles. Made by MV2 of Munim, Inc., with AI agents working in his name.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

VERSION = "0.1.0"
API = "https://dev.to/api"
UA = f"mv2-dev-cache-bust-check/{VERSION} (MV2 of Munim, Inc.; mv2@munimtech.com)"
HEADERS_KEPT = ("age", "x-cache", "x-cache-hits", "x-served-by", "cache-control", "date", "vary")
VARIANTS = ("sweep", "item")


def log(msg):
    print(msg, flush=True)


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def fetch(path, pause):
    """(status, json or None, headers with lower-case names)."""
    for attempt in range(4):
        req = urllib.request.Request(API + path, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                hdr = {k: r.headers.get(k) for k in HEADERS_KEPT if r.headers.get(k) is not None}
                data = json.loads(r.read().decode("utf-8"))
            time.sleep(pause)
            return r.status, data, hdr
        except urllib.error.HTTPError as e:
            hdr = {k: e.headers.get(k) for k in HEADERS_KEPT if e.headers.get(k) is not None}
            if e.code == 429 or e.code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            time.sleep(pause)
            return e.code, None, hdr
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            time.sleep(10 * (attempt + 1))
    return 0, None, {}


def cached(headers):
    """True / False from Age and X-Cache; None when the response carries neither."""
    h = {k.lower(): v for k, v in (headers or {}).items()}
    if "age" not in h and "x-cache" not in h:
        return None
    try:
        if int(h.get("age") or 0) > 0:
            return True
    except ValueError:
        pass
    return "HIT" in str(h.get("x-cache") or "").upper()


def summarise(status, batch, headers):
    """One fetch, reduced to what the comparison needs."""
    out = {"http": status, "headers": headers, "cached": cached(headers)}
    if status == 200 and isinstance(batch, list):
        ids = sorted({a.get("id") for a in batch if a.get("id") is not None})
        pubs = [parse_time(a["published_at"]) for a in batch if a.get("published_at")]
        out.update({"items": len(batch), "ids": ids,
                    "oldest": min(pubs).isoformat() if pubs else None,
                    "newest": max(pubs).isoformat() if pubs else None})
    return out


def verdict(plain, first, second, other_first=None):
    """Is the parameter part of the cache key? 'kept', 'stripped' or 'unclear'.

    first and second are two fetches of one URL carrying a value never used before.
    other_first is the first fetch of the other parameter, used only when the headers
    say nothing."""
    if not all(x and x.get("http") == 200 for x in (plain, first, second)):
        return "unclear"
    c1, c2 = first["cached"], second["cached"]
    if c1 is True:
        return "stripped"
    if c1 is False and c2 is True:
        return "kept"
    if c1 is None and c2 is None and other_first and other_first.get("http") == 200:
        same_as_plain = first["ids"] == plain["ids"]
        other_differs = other_first["ids"] != plain["ids"]
        if same_as_plain and other_differs:
            return "stripped"
        if not same_as_plain:
            return "kept"
    return "unclear"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="2,150,300")
    ap.add_argument("--per-page", type=int, default=1000)
    ap.add_argument("--pause", type=float, default=1.0)
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    started = datetime.now(timezone.utc)
    token = started.strftime("%Y%m%dT%H%M%S")
    rows = []
    for page in [int(p) for p in args.pages.split(",") if p.strip()]:
        base = f"/articles/latest?per_page={args.per_page}&page={page}"
        res = {"page": page, "plain": summarise(*fetch(base, args.pause))}
        for v in VARIANTS:
            url = f"{base}&{v}=bc{token}"
            res[v] = [summarise(*fetch(url, args.pause)), summarise(*fetch(url, args.pause))]
        res["verdict"] = {v: verdict(res["plain"], res[v][0], res[v][1],
                                     res[[o for o in VARIANTS if o != v][0]][0]) for v in VARIANTS}
        res["same_ids_as_plain"] = {v: res[v][0].get("ids") == res["plain"].get("ids") for v in VARIANTS}
        log(f"page {page}: plain {res['plain']['headers']} newest {res['plain'].get('newest')}; "
            + "; ".join(f"{v} {res[v][0]['headers']} then {res[v][1]['headers']} newest {res[v][0].get('newest')} "
                        f"-> {res['verdict'][v]}" for v in VARIANTS))
        rows.append(res)

    summary = {"version": VERSION, "started_at": started.isoformat(timespec="seconds"),
               "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "per_page": args.per_page,
               "verdicts": {v: [r["verdict"][v] for r in rows] for v in VARIANTS}}
    slim = [{**r, **{k: ({kk: vv for kk, vv in r[k].items() if kk != "ids"} if k == "plain" else
                         [{kk: vv for kk, vv in x.items() if kk != "ids"} for x in r[k]])
                     for k in ("plain",) + VARIANTS}} for r in rows]
    with open(os.path.join(args.out_dir, "bustcheck.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "pages": slim}, f, indent=1)
    with open(os.path.join(args.out_dir, "BUSTCHECK.md"), "w", encoding="utf-8") as f:
        f.write("# Which query parameters reach the cache key of DEV's /api/articles/latest\n\n")
        f.write(f"bustcheck {VERSION}, {summary['started_at']}. Made by MV2 of Munim, Inc., with AI agents "
                "working in his name.\n\n")
        f.write("| Page | Request | Age | X-Cache | Items | Newest post | Same ids as plain | Verdict |\n"
                "|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            p = r["plain"]
            f.write(f"| {r['page']} | plain | {p['headers'].get('age', '')} | {p['headers'].get('x-cache', '')} | "
                    f"{p.get('items', p['http'])} | {p.get('newest')} | | |\n")
            for v in VARIANTS:
                for n, x in enumerate(r[v], 1):
                    same = (x.get("ids") == p.get("ids")) if x.get("ids") is not None else ""
                    f.write(f"| {r['page']} | {v} #{n} | {x['headers'].get('age', '')} | "
                            f"{x['headers'].get('x-cache', '')} | {x.get('items', x['http'])} | {x.get('newest')} | "
                            f"{same} | {r['verdict'][v] if n == 1 else ''} |\n")
        f.write(f"\nVerdicts: {json.dumps(summary['verdicts'])}\n")
    log(json.dumps(summary))
    log("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
