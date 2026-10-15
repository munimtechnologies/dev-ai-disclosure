# How DEV authors use AI-disclosure labels

On 26 August 2026 DEV ([dev.to](https://dev.to)) added three labels an author can put on a post: **Hand Written (no AI)**, **AI-Assisted** and **Fully Autonomous** ([announcement](https://dev.to/devteam/introducing-ai-disclosure-on-dev-tools-for-nuance-clarity-and-better-feeds-34mk)). Posts with no label show as *Not disclosed*. DEV's public API returns the label with every post, so the whole platform can be counted rather than sampled.

This repo counts it: every public post in DEV's `/articles/latest` listing from 12 August 2026 (two weeks before the labels) to the day of the snapshot. We found no published count of how DEV's labels are used (searches on 2026-10-14), and DEV's announcement gives no usage numbers.

Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0, data CC BY 4.0.

## Results (snapshot 2026-10-14 19:01 UTC, v0.1.0)

Full tables: [`data/REPORT.md`](data/REPORT.md). Machine-readable: [`data/summary.json`](data/summary.json), [`data/daily.csv`](data/daily.csv), [`data/tags.csv`](data/tags.csv), [`data/authors.json`](data/authors.json) (counts only). The one-row-per-post file (`posts.csv.gz`, article ids, no usernames) did not upload with this snapshot; it will be added with the v0.2 snapshot.

414,144 posts were read; 304,071 of them were published after the labels launched (26 Aug 18:05 UTC).

1. **About 1 post in 25 carries a label.** Hand Written 881 (0.3%), AI-Assisted 7,886 (2.6%), Fully Autonomous 3,647 (1.2%), no label 291,657 (95.9%). Of the 110,073 posts from before the launch, 76 carry a label now, 75 of them edited after the launch.
2. **A quarter of all "AI-Assisted" labels came from one burst.** 1,912 AI-Assisted posts share the exact tag set `massage training brussels`: 664 on 24 Sep, 1,245 more by 27 Sep 05:46 UTC, and 3 on 4 Oct, often a few minutes apart. That is 24.2% of every AI-Assisted post since launch. All 1,912 are in English and none has a single reaction or comment. They make the week of 23 Sep look like a jump in AI-Assisted posts (5.6%) that did not happen: without them that week is 1.8% AI-Assisted and 3.2% labelled. Without the burst, since launch: AI-Assisted 2.0%, any label 3.5% (10,502 of 302,159).
3. **The real rise starts on 30 Sep.** Labelled share by week, burst removed: 1.4%, 2.1%, 2.4%, 2.2%, 3.2%, then 7.0% (week of 30 Sep), 8.5% (7 Oct) and 10.4% on the one day of 14 Oct in the snapshot. Labelled posts per week went from about 1,160 (week of 16 Sep) to 2,630 (week of 7 Oct), and Fully Autonomous from about 350 to 1,180. In the same weeks the total number of listed posts fell from about 50,000 a week to about 30,000, so part of the rise in *share* is a smaller denominator. We do not know why the total fell; posts deleted before the snapshot are missing from every week.
4. **Challenge entries label far more often.** Hacktoberfest challenge entries (`hf26challenge`, 3,766 posts) are 18.0% labelled (AI-Assisted 14.0%, Fully Autonomous 3.2%, Hand Written 0.8%); all `devchallenge` posts 19.3%.
5. **Labelled posts get more reactions than unlabelled posts from the same day** (posts at least 7 days old; 0.50 = typical for the day): Hand Written 0.66, AI-Assisted 0.58, Fully Autonomous 0.52, no label 0.50. This is a correlation, not an effect of the label: labelled posts also have cover images and tags far more often, and the AI-Assisted figure includes the 1,912 burst posts with no reactions.
6. **Concentration.** 4,937 of 50,138 authors used a label at least once. 109 authors wrote half of all Fully Autonomous posts and 165 half of all AI-Assisted posts, against 1,422 for unlabelled posts. 1,636 authors have both labelled and unlabelled posts.

## Next: v0.2 (queued)

`devai.py` 0.2.0 (in this repo since 2026-10-15) flags every machine-paced burst by a fixed rule (at least 100 posts since launch with one exact non-empty tag set and one label, median gap between consecutive posts at most 15 minutes), lists every group it finds, and recomputes the headline, weekly and reaction tables without them. It also counts, per week, the share of active *authors* who used each label, so one prolific account cannot move the trend. The rule was set after this snapshot showed the burst above; it is published here before the next snapshot runs.

## Questions, fixed before the first run

1. What share of new posts carries each label, and how did that change week by week after launch?
2. Did posts published *before* the labels get them later? That only happens if authors edit old posts.
3. Do labelled posts get more or fewer reactions and comments than unlabelled posts published on the same day? Each post is ranked against that day's other posts, and only posts at least 7 days old count.
4. How do labelled posts differ in reading time, language, cover images, organisation accounts and cross-posting?
5. How concentrated is each label? For example, how many authors account for half of all Fully Autonomous posts?
6. Which tags have the most and the fewest labelled posts? How do Hacktoberfest challenge entries (`hf26challenge`) compare?

## How it works

```
python -m unittest -v                     # offline tests, no network
python devai.py collect --since 2026-08-12 --out-dir out
python devai.py analyse --posts out/posts.csv --meta out/meta.json --authors out/authors.json --out-dir out
```

- `collect` pages through `https://dev.to/api/articles/latest` (1,000 posts per page, about 1 s apart, with a User-Agent naming MV2 of Munim, Inc.). For each post it writes the article id, publish time, label, language, reading time, reactions, comments, tags, and cover/organisation/cross-post flags. Usernames and author ids are **never written**. Author ids are held in memory only, to count distinct authors per label (`authors.json` has counts only).
- `analyse` writes `daily.csv`, `tags.csv`, `summary.json` and `REPORT.md`.
- Standard library only (Python 3.10+). The v0.1.0 snapshot took 418 requests and 43.5 minutes.

## Limits

- A label is what the author chose, not a measurement of how a post was written. *Not disclosed* does not mean no AI.
- The API shows each post's label as it is now. A label added later looks the same as one set when the post was published.
- Labels go together with other differences (topic, language, posting habits, spam), so any gap in reactions is a correlation, not an effect of the label.
- Posts deleted or unpublished before the snapshot are missing.
- The burst in finding 2 was found by reading the tag table and checked row by row in `posts.csv`; v0.2 will apply a fixed rule to every tag set.

Related: [devchallenge-study](https://github.com/munimtechnologies/devchallenge-study), which compares DEV challenge winners with the other entries in the same challenge.
