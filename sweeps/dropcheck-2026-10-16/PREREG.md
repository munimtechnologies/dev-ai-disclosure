# Pre-registration: did DEV's post volume fall because of Forem's late-September anti-spam changes?

Written and committed on 2026-10-16, before the sweep that tests it ran. Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0 (`dropcheck.py`, `test_dropcheck.py`), text CC BY 4.0.

## What we saw

The cache-fresh snapshot of 2026-10-16 (`data/2026-10-16/daily.csv`, devai.py 0.4.1) shows DEV's public listing with 6,600-9,200 posts on most weekdays through 2026-09-28, then 6,136 on 09-29 and 3,300-4,900 a day from 09-30 on, roughly 40% fewer. A second cache-fresh sweep (2026-10-14) agrees on every day within 0.43%, so this is not a collection artefact. DEV's own posts from its team say nothing about it.

## A candidate cause, from Forem's public repository

In the same days Forem (the software behind DEV) merged three changes to its automatic spam handling:

- [#23883](https://github.com/forem/forem/pull/23883), merged 2026-09-28: authors with fewer than 4 badges and repeated spam flags from the automatic checker get the `spam` role, which "blocks posting and hides the author's article pages". The PR estimates it "would have marked 693 accounts over the last 2 days" on DEV.
- [#23904](https://github.com/forem/forem/pull/23904), merged 2026-09-29: only when the flagged posts are at least 75% of the author's posts in the past month; it mentions "~1,650 accounts marked so far" on DEV.
- [#23925](https://github.com/forem/forem/pull/23925), merged 2026-10-02: any automatic flag counts, and a third copy of one title from one author within 24 hours is labelled clear spam.

Issue [#23931](https://github.com/forem/forem/issues/23931) reports that a spam-marked author's posts stay `published` in the public API. That would explain why the days before the change still show the old volume.

This is a hypothesis. We have not established it: merge dates are not deploy dates, and other changes could act the same way.

## Test

`dropcheck.py` makes one sweep of `/api/articles/latest` (per-sweep token in the allowlisted `item` parameter, as devai.py 0.4.1) back to 2026-08-27. It keeps each post's author id in memory only, together with its day, whether it has at least one reaction or comment at the sweep, and its tags. Only aggregate counts are written.

Windows (UTC dates, inclusive):

| Window | Dates | Days |
|---|---|---|
| A | 2026-08-27 .. 2026-09-11 | 16 |
| B | 2026-09-12 .. 2026-09-27 | 16 |
| C | 2026-09-30 .. 2026-10-14 | 15 |

2026-09-28 and 09-29 (the change days) are left out. Posts from 10-15 on are too young for reactions. **A -> B is the placebo** (no known change). **B -> C is the test.** Rates are per day.

Authors are classed by their post count in the earlier window of each transition: heavy >= 16 (one a day or more), regular 4-15, occasional 1-3. Retention of a class = that class's posts per day in the later window / its posts per day in the earlier window. Heavy authors regress toward the mean in any later window, so the placebo transition measures that baseline.

### Predictions (if the anti-spam changes caused the fall)

- **P1, engagement.** Let gap = (posts/day with no reaction and no comment, later / earlier) - (posts/day with at least one, later / earlier). P1 holds if gap <= -0.15 for B -> C and |gap| < 0.15 for A -> B. C posts are younger and so have had less time to collect reactions, which works against P1.
- **P2, who stopped.** P2 holds if heavy-author retention B -> C is at least 0.20 below heavy-author retention A -> B, and occasional-author retention B -> C is no more than 0.10 below occasional-author retention A -> B.

**Verdict:** SUPPORTED if both hold, NOT SUPPORTED if neither holds, MIXED otherwise. An incomplete sweep (one that does not reach 2026-08-27) is no test.

**Coverage gate:** the sweep's posts per day must be within 1% of `data/2026-10-16/daily.csv` on every day from 2026-08-27 to 2026-10-14. If it fails, the result is reported but called unconfirmed. A failure concentrated before 09-28 would itself be news: it would mean old posts are being removed.

**Also reported, with no prediction:** posts per day from authors new to the later window, authors who stopped posting entirely, and the 25 tags (>= 320 posts in B) whose posts per day fell most from B to C.

Whatever the verdict, it will be published here (`sweeps/dropcheck-2026-10-16/`), including a negative one. The thresholds above will not be changed after the data is seen. Any further analysis will be labelled exploratory.
