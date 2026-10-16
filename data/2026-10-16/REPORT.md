# How DEV authors use AI-disclosure labels

Every public post in DEV's /articles/latest listing from 2026-08-12 to the snapshot at 2026-10-16T16:32:19+00:00. DEV announced the labels at 2026-08-26T18:05:39+00:00. devai.py 0.4.1. Made by MV2 of Munim, Inc., with AI agents working in his name; code Apache-2.0, data CC BY 4.0.

Coverage: 423767 posts over 426 listing pages (oldest 2026-08-12T00:00:00+00:00, newest 2026-10-16T16:31:38+00:00); stopped at: reached --since.

Sweep check: every page URL carried a per-sweep value in `item`, a query parameter on Forem's edge-cache allowlist, so no page should come from an earlier sweep's cache; 13 of 426 pages came back with headers saying they were served from a cache; 169 ids were listed twice and dropped once; the largest time hole between consecutive pages was 2.2 minutes, over 10 minutes on 0 pages.

## Since launch: which label posts carry

313739 posts published after the announcement.

| Label | Posts | Share |
|---|---|---|
| Not disclosed | 300406 | 95.8% |
| Hand Written (no AI) | 925 | 0.3% |
| AI-Assisted | 8261 | 2.6% |
| Fully Autonomous | 4147 | 1.3% |
| **Any label** | | **4.2%** |

Before the announcement: 110028 posts, 76 of them carry a label now (75 of those were edited after the announcement).

## Week by week (weeks start on launch day; first and last may be partial)

| Week from | Days | Posts | Hand Written | AI-Assisted | Fully Autonomous | Any label |
|---|---|---|---|---|---|---|
| 2026-08-12 | 7 | 50405 | 0.0% | 0.0% | 0.0% | 0.1% |
| 2026-08-19 | 7 | 52661 | 0.0% | 0.0% | 0.0% | 0.1% |
| 2026-08-26 | 7 | 51636 | 0.2% | 0.9% | 0.2% | 1.4% |
| 2026-09-02 | 7 | 48862 | 0.2% | 1.3% | 0.5% | 2.1% |
| 2026-09-09 | 7 | 45817 | 0.2% | 1.4% | 0.7% | 2.4% |
| 2026-09-16 | 7 | 51853 | 0.3% | 1.3% | 0.7% | 2.2% |
| 2026-09-23 | 7 | 49200 | 0.3% | 5.6% | 1.1% | 6.9% |
| 2026-09-30 | 7 | 28368 | 0.5% | 4.3% | 2.2% | 7.0% |
| 2026-10-07 | 7 | 31137 | 0.5% | 4.2% | 3.8% | 8.5% |
| 2026-10-14 | 3 | 13828 | 0.4% | 4.0% | 5.2% | 9.6% |

## Bursts: one author, one tag set, one label, machine pace

A burst is a group of at least 100 posts since launch by one author that share one exact, non-empty tag set and one label, with a median gap of at most 15.0 minutes between consecutive posts. Authors are matched in memory while collecting and never written; only article ids and group numbers are saved (burst_posts.csv). Every group it finds is listed, so a reader can judge what was left out.

Distinct authors behind these groups: 22.

devai.py 0.2.0 used the same rule without the one-author condition, so it could also catch different authors who share a popular or required tag set (for example, challenge tags). On this snapshot it finds 77 groups with 28514 posts, of which 12840 are in a one-author burst.

35 groups, 12840 posts.

| Tags | Label | Posts | First | Last | Median gap (min) | Reactions |
|---|---|---|---|---|---|---|
| productivity opensource tutorial | Not disclosed | 2011 | 2026-09-01T10:00:12+00:00 | 2026-09-28T21:23:55+00:00 | 3.55 | 0 |
| massage training brussels | AI-Assisted | 1912 | 2026-09-24T00:14:14+00:00 | 2026-10-04T13:00:16+00:00 | 2.33 | 0 |
| nvidia ai investing stockmarket | Not disclosed | 1557 | 2026-09-06T14:05:29+00:00 | 2026-09-08T05:34:46+00:00 | 0.52 | 0 |
| bitcoin crypto investing trading | Not disclosed | 811 | 2026-09-06T13:37:18+00:00 | 2026-09-08T05:26:20+00:00 | 0.53 | 11 |
| android gaming | Not disclosed | 810 | 2026-09-15T07:05:43+00:00 | 2026-09-29T19:01:15+00:00 | 0.73 | 0 |
| android tech gaming tutorial | Not disclosed | 474 | 2026-09-04T13:33:27+00:00 | 2026-09-05T08:16:07+00:00 | 0.82 | 0 |
| ai geopolitics crypto data | Not disclosed | 473 | 2026-09-09T23:58:55+00:00 | 2026-10-16T04:37:49+00:00 | 11.65 | 0 |
| ai opensource github | Not disclosed | 463 | 2026-09-18T08:00:16+00:00 | 2026-10-16T16:01:53+00:00 | 0.57 | 0 |
| tech tutorial beginners productivity | Not disclosed | 453 | 2026-08-26T18:47:17+00:00 | 2026-09-25T07:30:51+00:00 | 8.8 | 0 |
| eastaioracle seo guide | Not disclosed | 418 | 2026-09-19T07:11:41+00:00 | 2026-09-19T23:55:25+00:00 | 0.4 | 0 |
| tech ai coding | Not disclosed | 286 | 2026-08-30T09:46:56+00:00 | 2026-09-28T21:06:07+00:00 | 2.5 | 0 |
| blogger kids video islamic | Not disclosed | 279 | 2026-08-26T19:41:43+00:00 | 2026-09-26T03:41:43+00:00 | 1.02 | 0 |
| security threatintel | Not disclosed | 198 | 2026-08-27T14:34:32+00:00 | 2026-10-16T10:05:39+00:00 | 3.85 | 189 |
| aioraclereader seo guide | Not disclosed | 180 | 2026-09-22T22:01:42+00:00 | 2026-09-23T06:01:12+00:00 | 0.33 | 0 |
| business | Not disclosed | 158 | 2026-08-31T08:03:28+00:00 | 2026-09-29T11:59:52+00:00 | 1.43 | 3 |
| django python automation ai | Not disclosed | 150 | 2026-08-27T00:15:06+00:00 | 2026-10-16T00:25:03+00:00 | 5.0 | 0 |
| crunchyroll seo guide | Not disclosed | 140 | 2026-09-19T00:45:55+00:00 | 2026-09-22T15:55:04+00:00 | 0.37 | 0 |
| ai privacy productivity tutorial | Not disclosed | 140 | 2026-09-29T07:22:14+00:00 | 2026-10-13T10:23:32+00:00 | 0.85 | 0 |
| increase seo guide | Not disclosed | 138 | 2026-09-19T01:12:15+00:00 | 2026-09-22T16:17:48+00:00 | 0.45 | 0 |
| education aiwriting writemask | Not disclosed | 136 | 2026-08-31T14:02:39+00:00 | 2026-09-29T14:11:56+00:00 | 3.53 | 0 |
| thriller seo guide | Not disclosed | 126 | 2026-09-19T00:20:50+00:00 | 2026-09-22T15:36:23+00:00 | 0.4 | 0 |
| facup seo guide | Not disclosed | 125 | 2026-09-18T23:21:03+00:00 | 2026-09-22T14:53:20+00:00 | 0.35 | 0 |
| crypto api trading | Not disclosed | 121 | 2026-08-30T08:31:09+00:00 | 2026-10-06T05:18:17+00:00 | 5.05 | 0 |
| sinners seo guide | Not disclosed | 115 | 2026-09-18T23:50:27+00:00 | 2026-09-22T15:19:09+00:00 | 0.4 | 0 |
| learning | Not disclosed | 113 | 2026-08-26T21:01:11+00:00 | 2026-08-29T00:43:18+00:00 | 3.37 | 0 |

Since launch without bursts: 300899 posts.

| Label | Posts | Share |
|---|---|---|
| Not disclosed | 289478 | 96.2% |
| Hand Written (no AI) | 925 | 0.3% |
| AI-Assisted | 6349 | 2.1% |
| Fully Autonomous | 4147 | 1.4% |
| **Any label** | | **3.8%** |

Week by week without bursts:

| Week from | Days | Posts | Hand Written | AI-Assisted | Fully Autonomous | Any label |
|---|---|---|---|---|---|---|
| 2026-08-12 | 7 | 50405 | 0.0% | 0.0% | 0.0% | 0.1% |
| 2026-08-19 | 7 | 52661 | 0.0% | 0.0% | 0.0% | 0.1% |
| 2026-08-26 | 7 | 50356 | 0.2% | 1.0% | 0.3% | 1.4% |
| 2026-09-02 | 7 | 45197 | 0.2% | 1.4% | 0.6% | 2.2% |
| 2026-09-09 | 7 | 45500 | 0.2% | 1.4% | 0.8% | 2.4% |
| 2026-09-16 | 7 | 49326 | 0.3% | 1.4% | 0.7% | 2.3% |
| 2026-09-23 | 7 | 44940 | 0.3% | 1.9% | 1.2% | 3.3% |
| 2026-09-30 | 7 | 27945 | 0.5% | 4.4% | 2.3% | 7.1% |
| 2026-10-07 | 7 | 30863 | 0.5% | 4.2% | 3.9% | 8.5% |
| 2026-10-14 | 3 | 13734 | 0.4% | 4.0% | 5.2% | 9.7% |

## Authors week by week

Share of the week's active authors (since launch) who used each label at least once that week. Each author counts once per week, so one prolific account cannot move these shares.

| Week from | Authors | Hand Written | AI-Assisted | Fully Autonomous | Any label |
|---|---|---|---|---|---|
| 2026-08-26 | 10375 | 0.8% | 3.7% | 0.9% | 5.2% |
| 2026-09-02 | 11927 | 0.7% | 3.8% | 1.3% | 5.7% |
| 2026-09-09 | 11871 | 0.8% | 3.5% | 1.4% | 5.6% |
| 2026-09-16 | 12378 | 0.8% | 3.6% | 1.4% | 5.7% |
| 2026-09-23 | 13580 | 0.8% | 4.1% | 1.8% | 6.6% |
| 2026-09-30 | 12998 | 0.9% | 6.4% | 2.8% | 9.8% |
| 2026-10-07 | 13560 | 0.8% | 6.8% | 3.5% | 10.9% |
| 2026-10-14 | 6795 | 0.7% | 4.7% | 3.4% | 8.7% |

## Reactions and comments by label (all posts)

Posts published after the announcement and at least 7 days before the snapshot (cutoff 2026-10-09T16:32:19+00:00). Each post's reactions are ranked against every other post published the same UTC day: 0.50 is typical for that day. z compares the mean with 0.50; this is a correlation, not an effect of the label.

| Label | Posts | Mean day percentile | z | Mean reactions | Median | No reactions | Mean comments | No comments |
|---|---|---|---|---|---|---|---|---|
| Not disclosed | 271124 | 0.50 | -4.8 | 0.3 | 0.0 | 91.5% | 0.16 | 94.5% |
| Hand Written (no AI) | 788 | 0.66 | +15.6 | 3.81 | 0.0 | 58.8% | 1.98 | 73.6% |
| AI-Assisted | 6874 | 0.58 | +23.3 | 2.38 | 0.0 | 74.4% | 1.17 | 78.2% |
| Fully Autonomous | 2532 | 0.52 | +3.0 | 0.27 | 0.0 | 85.2% | 0.34 | 83.9% |

## Reactions and comments by label (English posts only)

Posts published after the announcement and at least 7 days before the snapshot (cutoff 2026-10-09T16:32:19+00:00). Each post's reactions are ranked against every other post published the same UTC day: 0.50 is typical for that day. z compares the mean with 0.50; this is a correlation, not an effect of the label.

| Label | Posts | Mean day percentile | z | Mean reactions | Median | No reactions | Mean comments | No comments |
|---|---|---|---|---|---|---|---|---|
| Not disclosed | 248130 | 0.50 | -5.0 | 0.31 | 0.0 | 91.1% | 0.17 | 94.2% |
| Hand Written (no AI) | 756 | 0.66 | +15.6 | 3.96 | 0.0 | 57.7% | 2.06 | 72.8% |
| AI-Assisted | 6586 | 0.58 | +23.5 | 2.46 | 0.0 | 73.6% | 1.21 | 77.6% |
| Fully Autonomous | 2438 | 0.52 | +2.9 | 0.28 | 0.0 | 84.9% | 0.35 | 83.4% |

## Reactions and comments by label (all posts, bursts left out)

Posts published after the announcement and at least 7 days before the snapshot (cutoff 2026-10-09T16:32:19+00:00). Each post's reactions are ranked against every other post published the same UTC day: 0.50 is typical for that day. z compares the mean with 0.50; this is a correlation, not an effect of the label.

| Label | Posts | Mean day percentile | z | Mean reactions | Median | No reactions | Mean comments | No comments |
|---|---|---|---|---|---|---|---|---|
| Not disclosed | 260452 | 0.50 | -5.3 | 0.31 | 0.0 | 91.2% | 0.17 | 94.3% |
| Hand Written (no AI) | 788 | 0.66 | +15.4 | 3.81 | 0.0 | 58.8% | 1.98 | 73.6% |
| AI-Assisted | 4962 | 0.63 | +30.6 | 3.3 | 0.0 | 64.6% | 1.62 | 69.9% |
| Fully Autonomous | 2532 | 0.52 | +2.8 | 0.27 | 0.0 | 85.2% | 0.34 | 83.9% |

## What labelled posts look like

| Label | Posts | Median reading minutes | English | Cover image | Organisation | Cross-posted | No tags |
|---|---|---|---|---|---|---|---|
| Not disclosed | 300406 | 3.0 | 91.7% | 21.3% | 1.4% | 23.1% | 30.1% |
| Hand Written (no AI) | 925 | 4 | 96.0% | 59.1% | 3.9% | 20.1% | 6.7% |
| AI-Assisted | 8261 | 4 | 95.9% | 41.2% | 3.3% | 17.7% | 1.7% |
| Fully Autonomous | 4147 | 3 | 96.9% | 37.5% | 3.2% | 28.9% | 2.7% |

## Authors

51961 distinct authors posted after the announcement; 5162 used a label at least once, 241 used two or more different labels, and 1725 have both labelled and unlabelled posts. Counts only; no author is named or stored.

| Label | Authors | Posts | Top 10 authors' share | Authors behind half the posts |
|---|---|---|---|---|
| Not disclosed | 48524 | 300406 | 6.5% | 1479 |
| Hand Written (no AI) | 606 | 925 | 16.9% | 144 |
| AI-Assisted | 3321 | 8261 | 31.6% | 169 |
| Fully Autonomous | 1482 | 4147 | 27.2% | 98 |

## Tags

Largest tags since the announcement:

| Tag | Posts | Hand Written | AI-Assisted | Fully Autonomous | Any label |
|---|---|---|---|---|---|
| ai | 64510 | 0.5% | 4.5% | 1.9% | 6.9% |
| webdev | 30570 | 0.6% | 3.9% | 2.9% | 7.4% |
| productivity | 22615 | 0.4% | 3.2% | 1.8% | 5.4% |
| programming | 17677 | 0.9% | 4.0% | 2.0% | 6.9% |
| security | 15099 | 0.3% | 3.3% | 1.9% | 5.6% |
| tutorial | 13834 | 0.2% | 2.5% | 3.1% | 5.8% |
| opensource | 13788 | 0.7% | 6.0% | 2.8% | 9.4% |
| python | 13235 | 0.4% | 3.8% | 2.7% | 7.0% |
| devops | 11188 | 0.5% | 4.5% | 2.6% | 7.5% |
| automation | 9323 | 0.2% | 1.9% | 2.1% | 4.3% |
| javascript | 8269 | 0.6% | 4.6% | 4.0% | 9.2% |
| api | 8221 | 0.6% | 2.5% | 3.0% | 6.2% |
| architecture | 7535 | 0.6% | 4.8% | 1.6% | 6.9% |
| beginners | 7210 | 0.9% | 3.4% | 2.9% | 7.2% |
| llm | 6667 | 0.5% | 5.4% | 1.5% | 7.5% |
| seo | 6663 | 0.2% | 1.9% | 1.1% | 3.2% |
| agents | 6625 | 0.7% | 5.5% | 1.9% | 8.1% |
| in | 6541 | 0.0% | 0.0% | 0.0% | 0.0% |
| for | 6512 | 0.0% | 0.0% | 0.0% | 0.0% |
| testing | 6432 | 0.5% | 5.5% | 3.5% | 9.6% |

Tags with the highest share of labelled posts (large tags only):

| Tag | Posts | Hand Written | AI-Assisted | Fully Autonomous | Any label |
|---|---|---|---|---|---|
| brussels | 1912 | 0.0% | 100.0% | 0.0% | 100.0% |
| massage | 1989 | 0.0% | 96.3% | 0.0% | 96.3% |
| training | 3198 | 0.0% | 59.8% | 0.0% | 59.8% |
| devchallenge | 4864 | 0.8% | 14.1% | 4.0% | 19.0% |
| weekendchallenge | 1596 | 0.8% | 14.3% | 2.8% | 17.9% |
| hf26challenge | 4106 | 0.7% | 13.8% | 3.3% | 17.9% |
| showdev | 4205 | 0.9% | 8.7% | 5.9% | 15.5% |
| webscraping | 1547 | 0.1% | 2.6% | 12.5% | 15.3% |
| hardware | 1154 | 0.4% | 2.7% | 10.8% | 13.8% |
| gamedev | 1474 | 0.5% | 6.5% | 6.4% | 13.4% |
| dotnet | 1014 | 0.2% | 10.3% | 2.5% | 12.9% |
| claude | 1505 | 0.5% | 9.0% | 3.0% | 12.5% |
| networking | 1215 | 1.2% | 6.2% | 4.1% | 11.5% |
| discuss | 3208 | 1.4% | 6.4% | 3.4% | 11.2% |
| mcp | 2680 | 1.1% | 5.6% | 4.0% | 10.7% |

Hacktoberfest challenge entries (tag hf26challenge): 4106 posts, 17.9% labelled (Hand Written 0.7%, AI-Assisted 13.8%, Fully Autonomous 3.3%).

## Limits

- A label is what the author chose, not a measurement of how a post was written. Not disclosed does not mean no AI.
- The API gives each post's label as it is now; a label added or changed later looks the same as one set at publishing time.
- Reactions and comments are counted at the snapshot; posts younger than 7 days are left out of that comparison, and the day percentile removes the effect of age.
- Labels go with other differences (topic, language, author habits, spam), so differences in reactions are correlations, not effects of the label.
- The burst rule catches only one author's exact repeats of one tag set; a campaign that varies its tags or spreads over many accounts is missed.
- The listing is read page by page by offset. Pages served from a cache of different ages overlap or leave holes, and posts in a hole are never seen; the sweep check line above reports what this sweep saw.
- Posts deleted or unpublished before the snapshot are missing.
