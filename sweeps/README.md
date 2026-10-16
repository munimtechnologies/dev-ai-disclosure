# Sweep evidence

Collect logs and per-day counts of the sweeps behind the cached-listing finding in the main README.
Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0.

| File | Sweep | Snapshot (UTC) | Posts | Note |
|---|---|---|---|---|
| 2026-10-14-v1-collect.log | devai 0.1.0 | 2026-10-14 19:01 | 414,144 | first sweep at per_page=1000; coherent; the published snapshot |
| 2026-10-15-v3-collect.log, -daily.csv, -meta.json | devai 0.2.0 | 2026-10-15 18:31 | 348,461 | incomplete (cached pages) |
| 2026-10-16-v4-collect.log | devai 0.3.0 | 2026-10-16 08:03 | cut off at page 300 | the host stopped the job; log kept for the page comparison |
| 2026-10-16-v5-collect.log, -daily.csv, -meta.json | devai 0.3.0 | 2026-10-16 12:44 | 295,145 | incomplete (cached pages) |

Each log prints, every 25 pages, the number of posts written so far and the oldest post seen. Compare
the "oldest" value on the same page number across sweeps: identical values hours or days apart mean
the page came from a cache. Compare `daily.csv` rows between v3 and v5: days from Oct 5 on agree
within a few posts, earlier days lost 20-70%.

The v3 and v5 per-day counts are not platform counts and must not be quoted as such.
