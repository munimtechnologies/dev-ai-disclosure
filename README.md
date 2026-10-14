# How DEV authors use AI-disclosure labels

On 26 August 2026 DEV ([dev.to](https://dev.to)) added three labels an author can put on a post: **Hand Written (no AI)**, **AI-Assisted** and **Fully Autonomous** ([announcement](https://dev.to/devteam/introducing-ai-disclosure-on-dev-tools-for-nuance-clarity-and-better-feeds-34mk)). Posts with no label show as *Not disclosed*. DEV's public API returns the label with every post, so the whole platform can be counted rather than sampled.

This repo counts it: every public post in DEV's `/articles/latest` listing from 12 August 2026 (two weeks before the labels) to the day of the snapshot. As of 14 October 2026 that is roughly 6,000 posts a day. We found no published count of how DEV's labels are used (searches on 2026-10-14). DEV's announcement gives no usage numbers.

Made by MV2 of Munim, Inc., with AI agents working in his name. Code Apache-2.0, data CC BY 4.0.

## Status

**Method published, results pending.** This commit holds only the method. It goes out before the first full collection has run, so the questions below were set before any results were seen. The results (`data/`) and a write-up will follow in a later commit.

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
- Standard library only (Python 3.10+).

## Limits

- A label is what the author chose, not a measurement of how a post was written. *Not disclosed* does not mean no AI.
- The API shows each post's label as it is now. A label added later looks the same as one set when the post was published.
- Labels go together with other differences (topic, language, posting habits, spam), so any gap in reactions is a correlation, not an effect of the label.
- Posts deleted or unpublished before the snapshot are missing.

Related: [devchallenge-study](https://github.com/munimtechnologies/devchallenge-study), which compares DEV challenge winners with the other entries in the same challenge.
