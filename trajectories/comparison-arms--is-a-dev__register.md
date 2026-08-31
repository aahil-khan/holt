# Trajectory — the comparison arms on is-a-dev/register

Three methods are scored against Holt in the headline table, and each is one model call. This is all three on the repository where they part company with Holt: a domain registry where an outsider's merged pull request is one line of their own name in a data file.

| Arm | What it is shown | Verdict here |
|---|---|---|
| `name_only` (memorisation probe) | the repository name, nothing else | `insufficient_evidence` |
| `baseline` (the baseline solution) | README + repository metadata | `viable` |
| `baseline_matched` (evidence-matched ablation) | the same signals and threads Holt reads, in one prompt | `not_viable` |
| **Holt** | the full pipeline | **`not_viable`** |

Holt's rule: repo_kind=registry: merged work here is not a software contribution

The full Holt walkthrough for this repository is [`is-a-dev__register.md`](is-a-dev__register.md).

Replayed from committed recordings. No model ran.

---

## 1. `name_only` — what a chat model recalls from the name

*Model:* `gpt-5-mini-2025-08-07` · *94 in / 214 out tokens · $0.0005*

<details><summary>Instructions given to the model</summary>

```
You are told only a repository's name. Say whether an outside developer could realistically land a meaningful contribution there.

You have no evidence beyond the name. Answer from what you already know.
```
</details>

<details><summary>Evidence it was shown (first 400 chars)</summary>

```
Repository: is-a-dev/register
```
</details>

**What it answered:**

```json
{
 "verdict": "insufficient_evidence"
}
```

## 2. `baseline` — one prompt over README and metadata

*Model:* `gpt-5-mini-2025-08-07` · *1019 in / 733 out tokens · $0.0017*

<details><summary>Instructions given to the model</summary>

```
You assess whether a GitHub repository is a worthwhile place for an outside developer -- someone with no prior connection to the project -- to spend a week contributing.

Answer with one of three verdicts:
  viable                 an outsider could realistically land a meaningful change
  not_viable             an outsider could not, or the work would not be software
  insufficient_evidence  the material does not support a call either way

Prefer insufficient_evidence to a confident guess.
```
</details>

<details><summary>Evidence it was shown (first 1500 chars)</summary>

```
Repository: is-a-dev/register

Metadata:
  description: "Grab your own sweet-looking '.is-a.dev' subdomain."
  primary_language: 'JavaScript'
  stargazer_count: 11107
  pushed_at: '2026-08-29T15:55:43Z'
  is_archived: False
  is_fork: False
  is_mirror: False
  homepage_url: 'https://is-a.dev'

README:
<!-- <p align="center">
   <img alt="is-a.dev Banner" src="https://raw.githubusercontent.com/is-a-dev/register/main/media/banner.png">
</p> -->

<p align="center">
   <img height="350" alt="is-a.dev Banner" src="https://raw.githubusercontent.com/is-a-dev/register/main/media/banner.png">
</p>

<p align="center">
   <img alt="Domains" src="https://img.shields.io/github/directory-file-count/is-a-dev/register/domains?color=5c46eb&label=domains&style=for-the-badge">
   <img alt="Open Pull Requests" src="https://img.shields.io/github/issues-raw/is-a-dev/register?color=5c46eb&label=issues&style=for-the-badge">
   <img alt="Open Issues" src="https://img.shields.io/github/issues-pr-raw/is-a-dev/register?color=5c46eb&label=pull%20requests&style=for-the-badge">
   <br>
</p>

<h1 align="center">is-a.dev</h1>

<p align="center"><strong>is-a.dev</strong> is a service that allows developers to get a sweet-looking <code>.is-a.dev</code> subdomain for their personal websites.</p>

---

## Announcements
Please join our [Discord server](https://discord.gg/is-a-dev-830872854677422150) for announcements, service updates, and downtime notifications regarding the service.

Not all announcements are p
```
</details>

**What it answered:**

```json
{
 "verdict": "viable",
 "summary": "The project explicitly invites outside contributions (fork \u2192 PR to add a subdomain), has clear docs/Discord for support, is active and well-maintained, and the changes an outsider would make (adding a domain file or doc fixes) are small and reviewable \u2014 so a newcomer could realistically land a meaningful change within a week.",
 "reasons": [
  "README provides an explicit, step-by-step contribution flow (fork, follow docs, open PR) aimed at outsiders registering a subdomain.",
  "The repository is active (recent push), not archived, and has a large community (11k stars) \u2014 indicators of responsive maintainers and ongoing review.",
  "The typical contribution (adding a domain entry or small docs change) is low-risk and small in scope, so it\u2019s feasible to complete and get merged quickly.",
  "There is a public Discord and documentation linked for support if the PR needs changes, lowering the barrier for a newcomer to iterate on requested reviews.",
  "Possible blockers: maintainers explicitly warn about spam/AI-generated PRs and will close or reject non-compliant submissions, so contributors must follow the docs and respond to review requests.",
  "Uncertainty: the codebase (JS) and automation details aren\u2019t shown in the README excerpt \u2014 more complex code changes might require more ramp-up, but simple domain/docs contributions are clearly supported."
 ]
}
```

**The report it produced:**

---

# is-a-dev/register

> Replaying recorded model output. No model was called for this run.

**Worth your time** — for a contributor with 7 days.

## What the evidence shows

The project explicitly invites outside contributions (fork → PR to add a subdomain), has clear docs/Discord for support, is active and well-maintained, and the changes an outsider would make (adding a domain file or doc fixes) are small and reviewable — so a newcomer could realistically land a meaningful change within a week.

## Evidence

- README provides an explicit, step-by-step contribution flow (fork, follow docs, open PR) aimed at outsiders registering a subdomain.
- The repository is active (recent push), not archived, and has a large community (11k stars) — indicators of responsive maintainers and ongoing review.
- The typical contribution (adding a domain entry or small docs change) is low-risk and small in scope, so it’s feasible to complete and get merged quickly.
- There is a public Discord and documentation linked for support if the PR needs changes, lowering the barrier for a newcomer to iterate on requested reviews.
- Possible blockers: maintainers explicitly warn about spam/AI-generated PRs and will close or reject non-compliant submissions, so contributors must follow the docs and respond to review requests.
- Uncertainty: the codebase (JS) and automation details aren’t shown in the README excerpt — more complex code changes might require more ramp-up, but simple domain/docs contributions are clearly supported.

*baseline (single prompt over README and metadata)*
*Model output from gpt-5-mini-2025-08-07.*


---

Note what the rendering does *not* do: the baseline cites nothing, because it was shown nothing citable. Its reasons are impressions of a README, and the report says so rather than dressing them as evidence.

## 3. `baseline_matched` — the same evidence, one call

*Model:* `gpt-5-mini-2025-08-07` · *3475 in / 1509 out tokens · $0.0039*

<details><summary>Instructions given to the model</summary>

```
You assess whether a GitHub repository is a worthwhile place for an outside developer -- someone with no prior connection to the project -- to spend a week contributing.

You are given the repository's README, its metadata, arithmetic measured from its
pull request history before the cutoff, and a sample of its pull request threads.

Judge what a merged contribution here actually *is*. A repository where merged
work means appending an entry to a catalogue -- package manifests, domain
records, plugin listings -- is easy to contribute to and is not a place to spend
a week writing software.

Answer with one of three verdicts:
  viable                 an outsider could realistically land a meaningful change
  not_viable             an outsider could not, or the work would not be software
  insufficient_evidence  the material does not support a call either way

Prefer insufficient_evidence to a confident guess. Cite evidence ids you were
given for the reasons you list.
```
</details>

<details><summary>Evidence it was shown (first 1500 chars)</summary>

```
Repository: is-a-dev/register

Metadata:
  description: "Grab your own sweet-looking '.is-a.dev' subdomain."
  primary_language: 'JavaScript'
  stargazer_count: 11107
  pushed_at: '2026-08-29T15:55:43Z'
  is_archived: False
  is_fork: False
  is_mirror: False
  homepage_url: 'https://is-a.dev'

Measured from pull request history before the cutoff:
  total_threads: 200
  outsider_threads: 191
  outsider_merged: 35
  outsider_ignored: 122
  median_first_response_hours: 12.3
  bot_share: 0.0
  distinct_outsider_authors: 145
  distinct_merged_authors: 35
  reviewed_share: 1.0
  merge_rate: 0.18324607329842932

README:
<!-- <p align="center">
   <img alt="is-a.dev Banner" src="https://raw.githubusercontent.com/is-a-dev/register/main/media/banner.png">
</p> -->

<p align="center">
   <img height="350" alt="is-a.dev Banner" src="https://raw.githubusercontent.com/is-a-dev/register/main/media/banner.png">
</p>

<p align="center">
   <img alt="Domains" src="https://img.shields.io/github/directory-file-count/is-a-dev/register/domains?color=5c46eb&label=domains&style=for-the-badge">
   <img alt="Open Pull Requests" src="https://img.shields.io/github/issues-raw/is-a-dev/register?color=5c46eb&label=issues&style=for-the-badge">
   <img alt="Open Issues" src="https://img.shields.io/github/issues-pr-raw/is-a-dev/register?color=5c46eb&label=pull%20requests&style=for-the-badge">
   <br>
</p>

<h1 align="center">is-a.dev</h1>

<p align="center"><strong>is-a.dev</strong> is a service that allows
```
</details>

**What it answered:**

```json
{
 "verdict": "not_viable",
 "summary": "This repository is a public registry for claiming .is-a.dev subdomains. Merged outsider contributions are overwhelmingly single JSON domain entries and small verification files rather than substantive software changes, so it\u2019s not a place to spend a week writing code.",
 "reasons": [
  "The PR samples show contributors mainly adding domain JSON files under domains/ (e.g. files like 'domains/*.json' in PRs #39588 (merged), #39601 (merged), #39677 (merged), #39741 (closed), #39612 (open)).",
  "Merged examples are small data additions and verification files (e.g. #39588, #39601, #39677 are domain registration/verification merges), indicating accepted work is registry entries rather than feature work.",
  "Maintainers repeatedly request checklist items, screenshots, and verification steps (see reviewer comments in #39612, #39601, #39695), which shows the bar to merge is correctness of a data entry, not implementing or reviewing code.",
  "Pull requests are often closed for non\u2011qualifying content or wrong type of site (e.g. #39684 closed because 'sites must be software development related', #39741 closed for AI\u2011generated content), showing active curation of domain entries rather than collaborative software development.",
  "Project metrics show many outsider PRs but a low overall merge rate (35 merged out of ~191 outsider threads, merge_rate \u2248 0.18), and distinct_merged_authors are contributors who added domains \u2014 again consistent with a registry workflow rather than ongoing code contributions."
 ]
}
```

This arm exists to separate two claims that are easy to confuse: *reading pull request history beats reading a landing page*, and *a staged pipeline beats one call*. It gets the same signals and the same thread digest Holt reads. What differs is only the architecture — one model call decides, instead of typed findings passing through verification into a model-free verdict function.

Its verdict here: `not_viable`. Out of sample it scores MCC 0.32 against Holt's 0.63, and specificity 0.47 against 0.83 — most of the remaining gap is the rejection rule the model cannot override.

