# dev-ai-disclosure

How DEV authors use the AI-disclosure labels: every public dev.to post counted, not sampled.
Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0, data CC BY 4.0.

Write-up (snapshot 2026-10-14): https://dev.to/munimv2/devs-ai-disclosure-labels-after-seven-weeks-1-post-in-25-and-a-quarter-of-ai-assisted-was-one-burst-25fk

## Background

On 2026-08-26 DEV introduced three labels an author can pick per post: **Hand Written (no AI)**,
**AI-Assisted** and **Fully Autonomous**. A post with no label shows as **Not disclosed**. DEV's public
API returns the label with every article (`ai_disclosure_level`), so the whole platform can be counted.
`devai.py collect` pages through `/api/articles/latest` back to 2026-08-12; `devai.py analyse` writes
the tables below. No username or author id is ever written to disk.

## Results (snapshot 2026-10-16, devai 0.4.1)

423,767 posts over 426 listing pages; 313,739 published after the announcement. Every page URL was new
to DEV's edge cache (see below). Full tables: `data/2026-10-16/REPORT.md`.

1. **About 1 post in 24 carries a label.** Since launch: AI-Assisted 2.6%, Fully Autonomous 1.3%,
   Hand Written 0.3%, any label 4.2% (13,333 posts). Of 110,028 posts from before the announcement, 76
   carry a label now; 75 of those were edited after it.
2. **Nearly a quarter of AI-Assisted was one burst.** 1,912 AI-Assisted posts by one author, all tagged
   `massage training brussels`, posted a median 2.3 minutes apart from Sep 24 to Oct 4: 23.1% of all
   AI-Assisted posts. It is the only labelled group among the 35 machine-paced bursts the rule finds
   (12,840 posts, 22 authors); the other 34 carry no label. Without all 35, the labelled share is 3.8%.
3. **The rise started on 30 September and is still going.** Weekly labelled share (weeks start on launch
   day): 1.4%, 2.1%, 2.4%, 2.2%, then 6.9% in the Sep 23 week (3.3% without bursts), 7.0%, 8.5%, and 9.6%
   for Oct 14-16. Not only the share rose: labelled posts per week went from 1,156 (Sep 16-22) to 2,637
   (Oct 7-13).
4. **Fully Autonomous now outnumbers AI-Assisted.** Its weekly share went 0.2%, 0.5%, 0.7%, 0.7%, 1.1%,
   2.2%, 3.8%, 5.2% (Oct 14-16), against 4.0% for AI-Assisted that week. Fully Autonomous posts per week:
   350 (Sep 16-22), 1,187 (Oct 7-13). On every day from Oct 12 to Oct 16 more posts were labelled Fully
   Autonomous than AI-Assisted (Oct 14: 290 against 204). The rise is not one account: the share of each
   week's active authors who used the label went from 0.9% (launch week) to 3.5% (Oct 7 week), and no
   machine-paced burst carries it.
5. **DEV's daily post count fell by about 40% at the end of September.** Weekday posts were about
   7,000-8,000 a day through Sep 28 and 3,300-4,900 a day from Sep 30 on (weekly 45,800-52,700 before,
   28,368 and 31,137 after). Both cache-free sweeps show the same step, so it is not a counting artefact.
   The cause is not known here; DEV's own announcements from those weeks do not mention one (by title).
   Part of the rise in label shares is this smaller denominator.
6. **Challenge entries label much more often.** Hacktoberfest entries (`hf26challenge`): 17.9% labelled;
   all `devchallenge` posts: 19.0%.
7. **Labelled posts get more reactions, which proves little.** Ranked within their own publishing day,
   Hand Written posts sit at the 0.66 percentile, AI-Assisted at 0.58 and Fully Autonomous at 0.52 (0.50
   is typical). These are correlations: topic, language and author habits differ too.
8. **Labelling is concentrated.** 98 authors wrote half of all Fully Autonomous posts; 169 wrote half
   of AI-Assisted. 5,162 of 51,961 authors who posted since launch used a label at least once.

**Against the 2026-10-14 snapshot** (v1, the numbers in the write-up): any label 4.1% then, 4.2% now; the
burst was 24.2% of AI-Assisted then, 23.1% now; `hf26challenge` 18.0% then, 17.9% now. The write-up's
headline ("1 post in 25", "a quarter of AI-Assisted was one burst") still describes its own snapshot;
the shares have moved by the new posts since, not by a correction.

## Repeat sweeps lost posts: DEV serves listing pages from an edge cache

### What happened

Repeating the sweep with plain page URLs gave fewer posts each time over the same window:

| Sweep | Snapshot (UTC) | Page URLs | Posts | Pages |
|---|---|---|---|---|
| v1 (devai 0.1.0) | 2026-10-14 19:01 | plain, first sweep at `per_page=1000` | 414,144 | 417 |
| v3 (devai 0.2.0) | 2026-10-15 18:31 | plain | 348,461 | 422 |
| v5 (devai 0.3.0) | 2026-10-16 12:44 | plain | 295,145 | 425 |
| v7 (devai 0.4.1) | 2026-10-16 16:32 | per-sweep token in `item` | 423,767 | 426 |

The posts were not deleted: a post present in v3 and absent from v5 is still served by
`/api/articles/<id>`. **v1 and v7 agree:** on every full day from Aug 12 to Oct 13, their per-day post
counts differ by at most 17 posts (0.43%, Oct 10), and before Oct 5 v7 is never higher than v1, as
deletions between the two snapshots would make it. v3 and v5 lost up to three quarters of some days
(v5: 1,225 posts on Sep 27 against 4,920 in v7). So v1, the first sweep at that page size, was coherent,
and its published numbers stand. A day-by-day table of all four sweeps is computed by `compare.py`
(results to follow in `sweeps/compare-2026-10-16/`).

### Live measurements (2026-10-16)

`probe.py`, plain URLs, 15:44 UTC (`sweeps/probe-2026-10-16/`). Shallow pages were fresh, deep pages old:

| Page | 1-3 | 40-42 | 80-81 | 82 | 121 | 122 | 201 | 301 | 401 |
|---|---|---|---|---|---|---|---|---|---|
| `Age` (s) | 0 | 0 | 0 | 10,498 | 27,185 | 10,409 | 75,102 | 159,216 | 158,509 |

Every page with `Age` > 0 came back `X-Cache: MISS, HIT`. Neighbouring pages of different ages overlapped
or fell out of time order: pages 121 and 122 shared 653 ids, and pages 201-202, 301-302 and 401-402 were
out of time order. 159,216 s is 44 hours, longer than the 24-hour default in Forem's code, so dev.to runs
a longer edge lifetime or serves pages past it. A page fetched twice 4.8 minutes apart came back with the
same 1,000 ids, `Age` 0 then 289.

`bustcheck.py`, 16:31 UTC (`sweeps/bustcheck-2026-10-16/`): on pages 2, 150 and 300, a fresh
`&sweep=<value>` came back with the same `Age` and ids as the plain URL (stripped before the cache
lookup), while a fresh `&item=<value>` came back `Age: 0`, `MISS, MISS`, and on pages 150 and 300 with a
newer set of posts than the cached plain page; the same `item` URL again was a hit. Verdict on all
three pages: `sweep` stripped, `item` kept.

The v7 sweep check: 13 of 426 pages came back with `Age` > 0 or a hit although their URLs were new to the
cache (their headers were not kept, so why is not known); 169 ids were listed twice and dropped once,
about the number of posts published during the 43-minute sweep, which push items one offset down; the
largest time hole between consecutive pages was 2.2 minutes, and no hole was over 10 minutes.

### What Forem's source says (forem/forem, main, read 2026-10-16)

- `app/controllers/api/v1/articles_controller.rb`: `before_action :set_cache_control_headers, only:
  %i[index show show_by_slug]`. The `/api/articles/latest` listing is served by `index`.
- `app/controllers/concerns/caching_headers.rb`: `set_cache_control_headers` sets `Surrogate-Control:
  max-age` from `EDGE_CACHE_DURATION_IN_HOURS`, default 24 hours, with `stale-if-error` 26,400 s. The
  edge cache is Fastly.
- `app/controllers/concerns/api/articles_controller.rb`: `index` tags the response with the surrogate
  keys of the articles table and of each listed article.
- `app/services/edge_cache/bust_article.rb`: saving an article purges that article's own key and a
  list of site paths (`/latest`, tag pages, some `/api/articles?tag=...&top=...` URLs). Nothing purges
  `/api/articles/latest` pages when a new article is published, so an old listing page can stay in the
  cache until it expires or until an article on it is saved. (Shallow pages, whose posts are new and
  often edited, were fresh in every probe; that this is why is a guess, not measured.)
- `config/fastly/snippets/safe_params_list.vcl`: before the cache lookup, every query parameter that is
  not on an allowlist is removed from the URL (`querystring.regfilter_except`), except on a few paths and
  on `/api` requests that send an `api-key` header. `page`, `per_page` and `item` are on the allowlist;
  an arbitrary name such as `sweep` is not.
- The API documentation for `/api/articles/latest` calls it "Ideal for building RSS feeds, chronological
  timelines, or 'latest posts' widgets" and does not mention edge caching.

### The fix, and a correction

devai 0.4.0 added a per-sweep token as `&sweep=...`. Because of the allowlist, that parameter is removed
before the cache lookup, so **0.4.0's token could not work** (confirmed live above). **devai 0.4.1** puts
the token in `item`, which is on the allowlist and which neither the API controllers nor
`ArticleApiIndexService` read, so each sweep's URLs are new to the cache while the endpoint returns the
same listing. A cache-busted sweep sends every page to DEV's servers, so the collector keeps to one request
a second (about 430 requests per sweep) and should be run rarely.

If you page through a Forem listing by offset and need a consistent snapshot, check `Age` / `X-Cache`
on every page, de-duplicate by id, measure the time gap between the oldest post on one page and the newest
on the next, and do not assume consecutive pages were built at the same moment.

## Data

- `data/2026-10-16/` (devai 0.4.1, the current snapshot): `REPORT.md` (every table), `summary.json`
  (every table as JSON), `daily.csv` (posts per day by label, with burst posts), `tags.csv` (label shares
  per tag with 100+ posts), `bursts.csv` (every burst group: tag set, label, size, span, median gap),
  `burst_posts.csv` (article id and group number only), `authors.json` (author counts only), `meta.json`
  (sweep settings and the coverage check).
- `data/` top level: the 2026-10-14 snapshot (v1) behind the write-up.
- Per-post rows: the write-up promised one row per post. That file (`posts.csv.gz`, about 420,000 rows)
  failed to upload twice and is not in this repository. Until it is, open an issue here and it will be
  shared; a split into small weekly CSV files is planned. Its columns: `article_id, published_at, date,
  level, language, reading_time, reactions, comments, n_tags, tags, has_cover, is_org, crossposted,
  edited_after_launch` (no username or author id).
- `sweeps/`: collect logs of every sweep, the v3/v5 `daily.csv` and `meta.json` as evidence for the
  cached-listing finding, and the 2026-10-16 probe and bustcheck outputs (headers, ids and counts only;
  no username or title).

## Code

```
python bustcheck.py --out-dir out                                # ~1 min: which parameters reach the cache key
python devai.py collect --since 2026-08-12 --out-dir out        # ~45 min at one request a second
python devai.py analyse --posts out/posts.csv --meta out/meta.json --authors out/authors.json \
    --burst-posts out/burst_posts.csv --out-dir out
python -m unittest -v                                            # offline tests, no network
```

Standard library only; no API key. Versions: 0.1.0 counts; 0.2.0 bursts by tag set (could merge
different authors sharing challenge tags, so never used for published numbers); 0.3.0 bursts must
come from one author; 0.4.0 sweep coverage check (its `sweep` token is stripped by the cache, see
above); 0.4.1 token in the allowlisted `item` parameter, header samples.

## Limits

- A label is the author's choice, not a measurement of how a post was written. Not disclosed does not
  mean no AI.
- The API gives the label as it is now; later edits look like labels set at publishing time.
- Reaction differences are correlations, not effects of the label.
- The burst rule catches only one author's exact repeats of one tag set at machine pace.
- Deleted or unpublished posts are missing; a sweep whose pages come from a cache misses more (above).
- The cache measurements are of dev.to on 2026-10-16; another Forem site, or dev.to later, may differ.

Related: [devchallenge-study](https://github.com/munimtechnologies/devchallenge-study), what DEV
challenge winners have in common.
