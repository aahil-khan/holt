# Trajectory — is-a-dev/register

**Verdict:** `not_viable`  
**Rule that decided it:** repo_kind=registry: merged work here is not a software contribution

Replayed from committed fixtures and recorded model output. No model ran.

## 1. Evidence retrieved (tool call)

`provider.fetch("is-a-dev/register")` → **771 records**, every one asserted to be dated at or before the cutoff 2026-06-01.

## 2. Signals computed — arithmetic, no model

```
{
 "total_threads": 200,
 "outsider_threads": 191,
 "outsider_merged": 35,
 "outsider_ignored": 122,
 "median_first_response_hours": 12.3,
 "bot_share": 0.0,
 "distinct_outsider_authors": 145
}
```

## 3. Stage A — what kind of repository is this?

*Model:* `gpt-5-mini-2025-08-07` · *1934 in / 572 out tokens · $0.0016*

<details><summary>Instructions given to the model</summary>

```
You identify what kind of GitHub repository you are looking at.

The distinction that matters is what a merged pull request *is* here:

  real_software    changes to code that runs: features, fixes, refactors
  registry         entries in a catalogue -- package manifests, domain records,
                   plugin listings, adapter stubs. Merges are easy and frequent
                   and change no software.
  awesome_list     a curated list of links
  portfolio        someone's personal work, coursework, or a collection of demos
  course_material  exercises or teaching material
  docs             a documentation site
  mirror           a read-only copy of a project developed elsewhere
  unclear          the evidence does not settle it

Registries are the common trap: they look extremely healthy on every activity
metric precisely because contributing to them is trivial. Judge by what the
merged diffs touch, not by how many there are.

Cite evidence ids for what you claim. Only cite ids you were given. If the
evidence does not settle the question, answer unclear rather than guessing.
```
</details>

<details><summary>Evidence it was shown (first 1500 chars)</summary>

```
Repository: is-a-dev/register

Metadata (evidence id: repo:is-a-dev/register:meta)
  description: "Grab your own sweet-looking '.is-a.dev' subdomain."
  primary language: 'JavaScript'
  homepage: 'https://is-a.dev'
  archived: False  fork: False  mirror: False

README (evidence id: repo:is-a-dev/register:readme)
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

Not all announcem
```
</details>

**What it answered:**

```json
{
 "repo_kind": "registry",
 "confidence": "high",
 "rationale": "The repository is a catalogue of domain entries rather than an application: the README describes a user workflow to fork the repo and open a PR to register a .is-a.dev subdomain and states merged PRs publish DNS records. Recent merged PRs only add or modify JSON files under the domains/ directory (manifest-like entries), not code that implements runtime behavior. This matches the pattern of a registry where merges add entries to a catalogue.",
 "evidence_ids": [
  "repo:is-a-dev/register:meta",
  "repo:is-a-dev/register:readme",
  "repo:is-a-dev/register:contributing",
  "pr:is-a-dev/register#39601",
  "pr:is-a-dev/register#39604",
  "pr:is-a-dev/register#39666",
  "pr:is-a-dev/register#39735"
 ],
 "governance_flags": [
  "none"
 ]
}
```

## 4. Stage B — is there a real route in?

*Model:* `gpt-5-mini-2025-08-07` · *1150 in / 483 out tokens · $0.0013*

<details><summary>Instructions given to the model</summary>

```
You judge whether a repository offers an outsider a real
route in, using its own onboarding material.

What counts as a real route: a documented setup that someone could follow, a
described process for proposing work, named places where help is wanted, some
indication of who to ask. What does not: a CONTRIBUTING file that only restates
a code of conduct, a README that is purely marketing, or instructions that
assume commit access.

Answer from the material given. If there is no onboarding material at all, say
so rather than inferring from the project's fame. Cite only evidence ids you
were given.
```
</details>

<details><summary>Evidence it was shown (first 1500 chars)</summary>

```
Repository: is-a-dev/register

CONTRIBUTING (evidence id: repo:is-a-dev/register:contributing)
# Contributing

## Pull requests
- If the PR template is updated, any pre-existing PRs must follow the updated template, in order to be merged.
- We reserve the right to deny any pull request for any reason.

## Issues
- **Report an abusive domain** - Create a new issue with the label `report-abuse`.
- **Report a problem with your domain** - Create a new issue with the label `support`.
- **Suggestions** - Create a new issue with the label `suggestion`.
- **For any questions** - Create a new issue with the label `question`.
- **Report any other issues related to this repository** - Create a new issue with any label that fits.


README (evidence id: repo:is-a-dev/register:readme)
<!-- <p align="center">
   <img alt="is-a.dev Banner" src="https://raw.githubusercontent.com/is-a-dev/register/main/media/banner.png">
</p> -->

<p align="center">
   <img height="350" alt="is-a.dev Banner" src="https://raw.githubusercontent.com/is-a-dev/register/main/media/banner.png">
</p>

<p align="center">
   <img alt="Domains" src="https://img.shields.io/github/directory-file-count/is-a-dev/register/domains?color=5c46eb&label=domains&style=for-the-badge">
   <img alt="Open Pull Requests" src="https://img.shields.io/github/issues-raw/is-a-dev/register?color=5c46eb&label=issues&style=for-the-badge">
   <img alt="Open Issues" src="https://img.shields.io/github/issues-pr-raw/is-a-dev/register?color=5c46eb&l
```
</details>

**What it answered:**

```json
{
 "onboarding": "substantive",
 "rationale": "The repository provides a clear, documented route for outsiders to contribute and get a subdomain: the README contains step-by-step directions to fork the repo, follow the project documentation (docs.is-a.dev), and open a pull request which will be reviewed (including instructions to respond to requested changes and that DNS is published after merge). It also points people to the project Discord for announcements/support. The CONTRIBUTING file documents how to file issues (labels to use for abuse/support/suggestion/question) and some PR expectations. These items together give an outsider a concrete, followable onboarding path.",
 "evidence_ids": [
  "repo:is-a-dev/register:readme",
  "repo:is-a-dev/register:contributing"
 ]
}
```

## 5. Stage C — what happened to people who tried?

*Model:* `gpt-5-mini-2025-08-07` · *2718 in / 3397 out tokens · $0.0075*

<details><summary>Instructions given to the model</summary>

```
You read pull request threads and judge what each one reveals
about an outsider's chances of landing meaningful work in this repository.

This is not sentiment. A polite refusal and an impatient acceptance point in
opposite directions from how they sound. Judge the path the contributor was left
on, not the tone of the words.

Two cases that are easy to get backwards:

  "Thanks for taking the time. We're moving this into the new architecture, so
   closing." -- warm words, but the contributor is told this class of work is not
  wanted. That is discouraging.

  "This isn't right yet. Change X and Y and I'll merge it." -- a rejection at
  this moment, and strong evidence of a working contribution process. That is
  welcoming.

Outcomes:
Cite the exact evidence id shown for each thread, in full, including the
":opened" suffix. Do not abbreviate it to a number.

  merged_after_review        merged, with substantive human feedback on the way
  merged_without_engagement  merged, nobody said anything of substance
  changes_requested          not merged yet, but a maintainer gave a route in
  closed_with_guidance       closed, and the contributor was told where to go instead
  closed_dismissive          closed with no route forward
  ignored                    nobody replied at all

Signal is what the thread tells a prospective contributor: welcoming, neutral,
or discouraging. Quote the words you judged from, verbatim and short. Cite only
pull request ids you were given.
```
</details>

<details><summary>Evidence it was shown (first 1500 chars)</summary>

```
Repository: is-a-dev/register

Pull request threads:

--- evidence id: pr:is-a-dev/register#39741:opened  (closed unmerged)
    opened by toanduneee; 1 files, +9/-0
    files: ['domains/toandunee.json']
    [AUTHOR] <img width="1763" height="1402" alt="image" src="https://github.com/user-attachments/assets/830ed39a-9f4b-4f7b-862a-748677b2f178" />
    [FufuUwU] Ai Ahh site
    [AUTHOR] Actually, this is a website I created using AI. I created it with the purpose of providing multiple-choice test preparation materials for myself and my friends.You can try it with username: `a` and password: `aaaaaa`. I've just created one quiz and one test. Thank you very much.
    [furina-x-lumine] Many dead giveaways it's an AI slopsite. Think the funniest giveaway is via Dev Tools, the meta tag sets the language to english, when it's in vietnamese, hence browsers set to english cannot translate them natively...
    [AUTHOR] Thanks for pointing that out! I'm still learning and I appreciate the feedback. I've just updated the lang attribute to vi in the meta tags and redeployed. To be honest, I am quite new to web development, so I didn't pay close attention to every detail and couldn't catch all the subtle issues generated by AI. While I did use AI to assist with some parts of the development, the project is a genuine, serious effort to create a practical tool for my studies. If you still feel that this site doesn't meet the criteria for a subdomain, please feel free to close this pull reques
```
</details>

**What it answered:**

```json
{
 "threads": [
  {
   "pr_id": "pr:is-a-dev/register#39741:opened",
   "outcome": "closed_dismissive",
   "signal": "discouraging",
   "quote": "That... wasn't meant to be feedback, was meant to be glazing your stupidity."
  },
  {
   "pr_id": "pr:is-a-dev/register#39749:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "On hold since you are removing a NS record domain, wait for the user's reply."
  },
  {
   "pr_id": "pr:is-a-dev/register#39588:opened",
   "outcome": "merged_after_review",
   "signal": "welcoming",
   "quote": "provide proper preview link or screenshot"
  },
  {
   "pr_id": "pr:is-a-dev/register#39612:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "fill in checklist in pr description and provide site preview screenshot/url"
  },
  {
   "pr_id": "pr:is-a-dev/register#39684:opened",
   "outcome": "closed_with_guidance",
   "signal": "discouraging",
   "quote": "sites must be software development related"
  },
  {
   "pr_id": "pr:is-a-dev/register#39610:opened",
   "outcome": "merged_after_review",
   "signal": "welcoming",
   "quote": "you need to verify your domain on vercel - get the TXT record to verify your main domain on vercel dashboard (TXT under `@` domain, not `www`)"
  },
  {
   "pr_id": "pr:is-a-dev/register#39700:opened",
   "outcome": "closed_dismissive",
   "signal": "discouraging",
   "quote": "what you want to do actually? do you want to show your github profile or have site and showing that using CNAME????"
  },
  {
   "pr_id": "pr:is-a-dev/register#39694:opened",
   "outcome": "closed_with_guidance",
   "signal": "welcoming",
   "quote": "do not forget to add txt verification record. read https://docs.is-a.dev/guides/vercel/"
  },
  {
   "pr_id": "pr:is-a-dev/register#
```

## 6. Stage D — verification (tool calls, no model)

Every evidence id cited by every finding was looked up against the provider: **33 lookups, 33 resolved, 0 did not.**

Verification works at two levels. An id that does not resolve is stripped from the finding that cited it. A finding left with *no* resolving id at all is dropped entirely — not softened, not hedged, removed.

Findings before verification: **15**  
Findings after verification: **15**  
Findings dropped outright: **0**  
Individual citations stripped: **0**

No finding lost every one of its citations on this run, so none was dropped outright.


## 7. Verdict — a plain function, no model

`verdict.py` turned the surviving findings and the signals into a verdict.
The model was not consulted and could not have overridden it.

```
repo_kind=registry: merged work here is not a software contribution
=> not_viable
```

## 8. Stage E — narration

The verdict above was passed to Stage E as an input it cannot change.

---

# is-a-dev/register

> Replaying recorded model output. No model was called for this run.

**Verdict:** not_viable
**Method:** holt (A classify, B opportunity, C outcomes, D verify, deterministic verdict, E narrate)

I agree with the not_viable verdict because this repository is a registry/catalogue, not a software project: the README documents a fork-and-PR workflow to register .is-a.dev subdomains and merged PRs only add/modify manifest-like JSON entries under domains/ which publish DNS records. In short, merged work is adding domain records (catalog entries), not producing code or runtime behavior, so merged contributions are not software contributions. Measured activity before the cutoff: 200 total threads, 191 outsider threads, 35 outsider-merged, 122 outsider-ignored, median first response 12.3 hours, bot share 0.0, 145 distinct outsider authors. Onboarding is substantive and clear — README, CONTRIBUTING, docs.is-a.dev and a Discord link give outsiders a concrete path to contribute — which explains the high outsider participation. Maintainer posture is mixed: there are many concrete, actionable reviews and successful merges (for example reviewers asking for previews or verification steps), but there are also closed or dismissive threads and some terse or discouraging replies (one quote: "That... wasn't meant to be feedback, was meant to be glazing your stupidity."). That mixed tone is worth noting for community health, but it doesn’t change the core reason for the verdict: this repo’s merged changes are registry entries rather than software contributions. Where evidence is thin: I could not fully characterize long‑term consistency of maintainer behavior beyond the sampled PRs, but the classification as a registry is well supported by the README and the nature of merged files.

## Evidence
- repo_kind = registry (The repository is a catalogue of domain entries rather than an application: the README describes a user workflow to fork the repo and open a PR to register a .is-a.dev subdomain and states merged PRs publish DNS records. Recent merged PRs only add or modify JSON files under the domains/ directory (manifest-like entries), not code that implements runtime behavior. This matches — `repo:is-a-dev/register:meta`
- onboarding = substantive (The repository provides a clear, documented route for outsiders to contribute and get a subdomain: the README contains step-by-step directions to fork the repo, follow the project documentation (docs.is-a.dev), and open a pull request which will be reviewed (including instructions to respond to requested changes and that DNS is published after merge). It also points peopl — `repo:is-a-dev/register:readme`
- outsider_posture = mixed (Maintainers frequently give concrete, actionable feedback (requesting previews, verification TXT records, checklist completion) and merge after fixes, which is welcoming to contributors who follow directions (see pr:is-a-dev/register#39588:opened, pr:is-a-dev/register#39601:opened, pr:is-a-dev/register#39610:opened). However, some PRs are closed with little constructive f — `pr:is-a-dev/register#39741:opened`
- discouraging: closed_dismissive — “That... wasn't meant to be feedback, was meant to be glazing your stupidity.” — `pr:is-a-dev/register#39741:opened`
- welcoming: changes_requested — “On hold since you are removing a NS record domain, wait for the user's reply.” — `pr:is-a-dev/register#39749:opened`
- welcoming: merged_after_review — “provide proper preview link or screenshot” — `pr:is-a-dev/register#39588:opened`
- welcoming: changes_requested — “fill in checklist in pr description and provide site preview screenshot/url” — `pr:is-a-dev/register#39612:opened`
- discouraging: closed_with_guidance — “sites must be software development related” — `pr:is-a-dev/register#39684:opened`
- welcoming: merged_after_review — “you need to verify your domain on vercel - get the TXT record to verify your main domain on vercel dashboard (TXT under `@` domain, not `www`)” — `pr:is-a-dev/register#39610:opened`
- discouraging: closed_dismissive — “what you want to do actually? do you want to show your github profile or have site and showing that using CNAME????” — `pr:is-a-dev/register#39700:opened`
- welcoming: closed_with_guidance — “do not forget to add txt verification record. read https://docs.is-a.dev/guides/vercel/” — `pr:is-a-dev/register#39694:opened`
- welcoming: closed_with_guidance — “You can't register a domain with NS records.” — `pr:is-a-dev/register#39655:opened`
- welcoming: merged_after_review — “why did you remove pr template? add it back and fill in checklist” — `pr:is-a-dev/register#39601:opened`
- welcoming: changes_requested — “incomplete pr checklist.” — `pr:is-a-dev/register#39695:opened`
- neutral: merged_without_engagement — “[dragsbruh]” — `pr:is-a-dev/register#39677:opened`

