# dev-ai-disclosure

How DEV authors use the AI-disclosure labels: every public dev.to post counted, not sampled.
Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0, data CC BY 4.0.

Write-up: https://dev.to/munimv2/devs-ai-disclosure-labels-after-seven-weeks-1-post-in-25-and-a-quarter-of-ai-assisted-was-one-burst-25fk

## Background

On 2026-08-26 DEV introduced three labels an author can pick per post: **Hand Written (no AI)**,
**AI-Assisted** and **Fully Autonomous**. A post with no label shows as **Not disclosed**. DEV's public
API returns the label with every article (`ai_disclosure_level`), so the whole platform can be counted.
`devai.py collect` pages through `/api/articles/latest` back to 2026-08-12; `devai.py analyse` writes
the tables below. No username or author id is ever written to disk.

## Results (snapshot 2026-10-14, v0.1.0)

414,144 posts; 304,071 published after the announcement. Full tables: `data/REPORT.md`.

1. **About 1 post in 25 carries a label.** Since launch: AI-Assisted 2.6%, Fully Autonomous 1.2%,
   Hand Written 0.3%, any label 4.1%. Of 110,073 posts from before the announcement, 76 carry a label
   now; 75 of those were edited after it.
2. **A quarter of AI-Assisted was one burst.** 1,912 AI-Assisted posts tagged `massage training brussels`
   were posted minutes apart over ten days; they are 24.2% of all AI-Assisted posts and most of the
   late-September spike. Without them the labelled share is 3.5%.
3. **The real rise started on 30 September.** Weekly labelled share: 1.4% (launch week), about 2.2%
   through mid-September, then 7.0% (Sep 30 week), 8.5% (Oct 7 week) and 10.4% on Oct 14 (one day).
   Part of the rise is a smaller denominator: weekly posts fell from about 50,000 to about 30,000.
4. **Challenge entries label much more often.** Hacktoberfest entries (`hf26challenge`): 18.0% labelled;
   all `devchallenge` posts: 19.3%.
5. **Labelled posts get more reactions, which proves little.** Ranked within their own publishing day,
   Hand Written posts sit at the 0.66 percentile and AI-Assisted at 0.58; Fully Autonomous at 0.52 is
   near typical. These are correlations: topic, language and author habits differ too.
6. **Labelling is concentrated.** 109 authors wrote half of all Fully Autonomous posts; 165 wrote half
   of AI-Assisted.

## Later sweeps lost posts: DEV serves listing pages from an edge cache (found 2026-10-16)

Repeating the sweep gave fewer posts each time over the same window:

| Sweep | Snapshot (UTC) | Posts | Pages | Posts written per page |
|---|---|---|---|---|
| v1 (devai 0.1.0) | 2026-10-14 19:01 | 414,144 | 417 | 993 |
| v3 (devai 0.2.0) | 2026-10-15 18:31 | 348,461 | 422 | 826 |
| v5 (devai 0.3.0) | 2026-10-16 12:44 | 295,145 | 425 | 694 |

The posts were not deleted: a post present in v3 and absent from v5 is still served by
`/api/articles/<id>`. The collect logs explain it. The "oldest post on page N" was **identical across
sweeps hours or days apart** (page 275 in all four sweeps over 42 hours; page 150 in two sweeps 23.5
hours apart), which offset pagination over a listing that grows by about 5,000 posts a day cannot
produce unless pages are served from a cache. A sweep that mixes cached and fresh pages gets pages
that overlap (duplicate ids, dropped) and pages with holes between them (posts never seen). The first
sweep at `per_page=1000` (v1) had every page fresh and is the only coherent snapshot; its numbers are
the ones published. The v3 and v5 per-day counts are kept under `sweeps/` as evidence only, not as
platform counts.

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
  cache until it expires or until an article on it is saved.
- `config/fastly/snippets/safe_params_list.vcl`: before the cache lookup, every query parameter that is
  not on an allowlist is removed from the URL (`querystring.regfilter_except`). `page` and `per_page`
  are on it; an arbitrary name such as `sweep` is not.
- The API documentation for `/api/articles/latest` calls it "Ideal for building RSS feeds, chronological
  timelines, or 'latest posts' widgets" and does not mention edge caching.

Open question: page 300's oldest post was identical in v1, v3 and v4 (about 37 hours), longer than the
24-hour default, so either DEV runs a longer edge TTL or pages are served past it. `bustcheck.py` and
`probe.py` record the `Age` headers that answer this.

### The fix, and a correction

devai 0.4.0 (written 2026-10-16) added a per-sweep token as `&sweep=...`. Because of the allowlist
above, that parameter is removed before the cache lookup, so **0.4.0's token could not work**.
**devai 0.4.1** puts the token in `item`, a parameter that is on the allowlist and that neither the
API controllers nor `ArticleApiIndexService` read, so each sweep's URLs are new to the cache while the
endpoint returns the same listing. Every sweep still counts pages whose headers report a cache hit,
ids listed twice, and time holes between consecutive pages (`meta.json` `coverage`, the "Sweep check"
line in `REPORT.md`), and keeps the cache headers of every hundredth page. A fresh 0.4.1 sweep,
preceded by `bustcheck.py`, is queued; its results will be added here, and until then no new platform
counts are claimed.

`bustcheck.py` fetches a few listing pages plain, with `&sweep=<new value>` twice and with
`&item=<new value>` twice, and reports for each parameter whether it reaches the cache key (first
request a miss, identical second request a hit) or is stripped. `probe.py` checks the mechanism from
the other side: items per 1,000-slot page with cache headers, overlap and time order between adjacent
pages, random unlisted ids fetched one by one, and one page fetched twice minutes apart.

If you page through a Forem listing by offset and need a consistent snapshot, check `Age` / `X-Cache`
on every page, de-duplicate by id, and do not assume consecutive pages were built at the same moment.

## Data (`data/`, snapshot 2026-10-14)

- `REPORT.md`: every table. `summary.json`: every table as JSON.
- `daily.csv`: posts per day by label. `tags.csv`: label shares per tag (tags with 100+ posts).
- `authors.json`: author concentration counts only.
- `posts.csv.gz` (when present; it is uploaded on its own): one row per post (414,144): `article_id,
  published_at, date, level, language, reading_time, reactions, comments, n_tags, tags, has_cover,
  is_org, crossposted, edited_after_launch`. No username or author id.
- `sweeps/`: collect logs of the four sweeps and the v3/v5 `daily.csv` and `meta.json`, as evidence
  for the cached-listing finding.

## Code

```
python bustcheck.py --out-dir out                                # ~1 min: which parameters reach the cache key
python devai.py collect --since 2026-08-12 --out-dir out        # ~30-45 min at one request a second
python devai.py analyse --posts out/posts.csv --meta out/meta.json --authors out/authors.json \
    --burst-posts out/burst_posts.csv --out-dir out
python -m unittest -v                                            # offline tests, no network
```

Standard library only; no API key. Versions: 0.1.0 counts; 0.2.0 bursts by tag set (could merge
different authors sharing challenge tags, so never used for published numbers); 0.3.0 bursts must
come from one author; 0.4.0 sweep coverage check (its `sweep` token is stripped by the cache, see
above); 0.4.1 token in the allowlisted `item` parameter, header samples.

## Limits

- A label is the author's choice, not a measurement of how a post was written.
- The API gives the label as it is now; later edits look like labels set at publishing time.
- Reaction differences are correlations, not effects of the label.
- Deleted or unpublished posts are missing; a sweep whose pages came from a cache misses more (above).

Related: [devchallenge-study](https://github.com/munimtechnologies/devchallenge-study), what DEV
challenge winners have in common.
