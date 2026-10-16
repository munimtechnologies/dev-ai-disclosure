# Which query parameters reach the cache key of DEV's /api/articles/latest

bustcheck 0.1.0, 2026-10-16T16:31:47+00:00. Made by MV2 of Munim, Inc., with AI agents working in his name.

| Page | Request | Age | X-Cache | Items | Newest post | Same ids as plain | Verdict |
|---|---|---|---|---|---|---|---|
| 2 | plain | 0 | MISS, MISS | 1000 | 2026-10-16T12:28:52+00:00 | | |
| 2 | sweep #1 | 1 | MISS, HIT | 1000 | 2026-10-16T12:28:52+00:00 | True | stripped |
| 2 | sweep #2 | 2 | MISS, HIT | 1000 | 2026-10-16T12:28:52+00:00 | True |  |
| 2 | item #1 | 0 | MISS, MISS | 1000 | 2026-10-16T12:28:52+00:00 | True | kept |
| 2 | item #2 | 1 | MISS, HIT | 1000 | 2026-10-16T12:28:52+00:00 | True |  |
| 150 | plain | 29936 | MISS, HIT | 1000 | 2026-09-18T19:54:22+00:00 | | |
| 150 | sweep #1 | 29937 | MISS, HIT | 1000 | 2026-09-18T19:54:22+00:00 | True | stripped |
| 150 | sweep #2 | 29938 | MISS, HIT | 1000 | 2026-09-18T19:54:22+00:00 | True |  |
| 150 | item #1 | 0 | MISS, MISS | 1000 | 2026-09-19T04:55:17+00:00 | False | kept |
| 150 | item #2 | 1 | MISS, HIT | 1000 | 2026-09-19T04:55:17+00:00 | False |  |
| 300 | plain | 2843 | MISS, HIT | 1000 | 2026-08-28T14:38:40+00:00 | | |
| 300 | sweep #1 | 2844 | MISS, HIT | 1000 | 2026-08-28T14:38:40+00:00 | True | stripped |
| 300 | sweep #2 | 2845 | MISS, HIT | 1000 | 2026-08-28T14:38:40+00:00 | True |  |
| 300 | item #1 | 0 | MISS, MISS | 1000 | 2026-08-28T15:19:11+00:00 | False | kept |
| 300 | item #2 | 1 | MISS, HIT | 1000 | 2026-08-28T15:19:11+00:00 | False |  |

Verdicts: {"sweep": ["stripped", "stripped", "stripped"], "item": ["kept", "kept", "kept"]}
