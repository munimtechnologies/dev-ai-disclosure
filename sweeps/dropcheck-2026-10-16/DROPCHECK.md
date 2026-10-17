# Did DEV's post volume fall because of the late-September anti-spam changes?

dropcheck.py 0.1.0, sweep started 2026-10-16T23:16:38+00:00. Predictions and thresholds were committed before this sweep ran (PREREG.md). Made by MV2 of Munim, Inc., with AI agents working in his name; code Apache-2.0, data CC BY 4.0.

Sweep: 313206 posts since 2026-08-27 over 316 pages; stopped at: reached since; 9 pages had cache headers; 36 ids listed twice; largest time hole between pages 2.0 min.

Coverage gate (per-day posts within 1% of the 2026-10-16 snapshot on every day 2026-08-27..2026-10-14): PASS; 49 days, largest difference -0.04% on 2026-10-09.

## Verdict: MIXED

- P1 (the fall is in posts with no reactions or comments): holds. Zero-engagement ratio minus engaged ratio: test -0.74 (needed <= -0.15), placebo 0.00 (needed within +/-0.15).
- P2 (heavy authors fall, occasional authors do not): fails. Heavy retention test 0.18 vs placebo 0.68 (needed at least 0.2 lower); occasional test 0.41 vs placebo 0.54 (needed no more than 0.1 lower).

## Windows

| Window | Dates | Days | Posts | Posts/day | With a reaction or comment /day | With neither /day | Authors |
|---|---|---|---|---|---|---|---|
| A | 2026-08-27..2026-09-11 | 16 | 114005 | 7,125 | 750 | 6,375 | 20314 |
| B | 2026-09-12..2026-09-27 | 16 | 110482 | 6,905 | 725 | 6,180 | 20106 |
| C | 2026-09-30..2026-10-14 | 15 | 64369 | 4,291 | 931 | 3,361 | 23450 |

## A -> B (placebo)

Engaged posts/day ratio 0.97; zero-engagement posts/day ratio 0.97. Authors are classed by their posts in A: heavy >= 16, regular 4-15, occasional 1-3.

| Class (by posts in A) | Authors | Posts/day in A | Their posts/day in B | Retention | Authors with no post in B | Their posts/day in A |
|---|---|---|---|---|---|---|
| heavy | 1067 | 3,952 | 2,706 | 0.68 | 176 | 1,025 |
| regular | 3879 | 1,840 | 1,399 | 0.76 | 961 | 398 |
| occasional | 15368 | 1,333 | 724 | 0.54 | 11073 | 882 |
| no post in A | 12002 | 0 | 2,076 | | | |
| **all** | | **7,125** | **6,905** | | | |

## B -> C (test)

Engaged posts/day ratio 1.28; zero-engagement posts/day ratio 0.54. Authors are classed by their posts in B: heavy >= 16, regular 4-15, occasional 1-3.

| Class (by posts in B) | Authors | Posts/day in B | Their posts/day in C | Retention | Authors with no post in C | Their posts/day in B |
|---|---|---|---|---|---|---|
| heavy | 1043 | 3,716 | 680 | 0.18 | 585 | 2,188 |
| regular | 4095 | 1,885 | 786 | 0.42 | 1796 | 802 |
| occasional | 14968 | 1,304 | 538 | 0.41 | 11029 | 897 |
| no post in B | 16754 | 0 | 2,288 | | | |
| **all** | | **6,905** | **4,291** | | | |

## Tags with at least 320 posts in B, largest fall in posts/day from B to C

| Tag | A /day | B /day | C /day | C/B |
|---|---|---|---|---|
| (no tags) | 2,273 | 2,191 | 836 | 0.38 |
| in | 153 | 245 | 8 | 0.03 |
| for | 165 | 238 | 2 | 0.01 |
| sale | 123 | 182 | 2 | 0.01 |
| productivity | 447 | 485 | 343 | 0.71 |
| seo | 105 | 214 | 73 | 0.34 |
| training | 44 | 147 | 8 | 0.06 |
| ai | 1,317 | 1,267 | 1,142 | 0.90 |
| massage | 0 | 124 | 0 | 0.00 |
| brussels | 0 | 119 | 0 | 0.00 |
| guide | 26 | 117 | 5 | 0.04 |
| flats | 71 | 111 | 1 | 0.01 |
| technology | 93 | 126 | 23 | 0.18 |
| programming | 356 | 381 | 290 | 0.76 |
| flat | 57 | 81 | 0 | 0.00 |
| automation | 206 | 204 | 134 | 0.66 |
| gaming | 63 | 67 | 7 | 0.11 |
| webdev | 558 | 629 | 572 | 0.91 |
| rent | 39 | 56 | 0 | 0.00 |
| android | 69 | 81 | 34 | 0.42 |
| devops | 204 | 245 | 198 | 0.81 |
| property | 30 | 44 | 0 | 0.01 |
| business | 84 | 73 | 31 | 0.43 |
| tutorial | 299 | 255 | 217 | 0.85 |
| dns | 2 | 41 | 6 | 0.16 |

## Limits

- This tests whether the fall looks like what the anti-spam changes would do; it cannot see which accounts DEV marked, and other changes in the same days could act the same way.
- Reactions and comments are counted at the sweep; window C posts are younger, which lowers C's engaged count and works against P1.
- Posts deleted or unpublished before the sweep are missing from every window.
- Classes come from one window's post count, so heavy authors fall back somewhat in any later window; the placebo transition measures that baseline.
