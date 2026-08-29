# Trajectory — SecureBananaLabs/bug-bounty

**Verdict:** `not_viable`  
**Rule that decided it:** 200/200 outsider attempts drew no response and none merged

Replayed from committed fixtures and recorded model output. No model ran.

## 1. Evidence retrieved (tool call)

`provider.fetch("SecureBananaLabs/bug-bounty")` → **262 records**, every one asserted to be dated at or before the cutoff 2026-06-01.

## 2. Signals computed — arithmetic, no model

```
{
 "total_threads": 200,
 "outsider_threads": 200,
 "outsider_merged": 0,
 "outsider_ignored": 200,
 "median_first_response_hours": null,
 "bot_share": 0.0,
 "distinct_outsider_authors": 38
}
```

## 3. Stage A — what kind of repository is this?

*Model:* `gpt-5-mini-2025-08-07` · *1308 in / 462 out tokens · $0.0013*

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
Repository: SecureBananaLabs/bug-bounty

Metadata (evidence id: repo:SecureBananaLabs/bug-bounty:meta)
  description: None
  primary language: 'JavaScript'
  homepage: None
  archived: False  fork: False  mirror: False

README (evidence id: repo:SecureBananaLabs/bug-bounty:readme)
# Project
<img width="663" height="183" alt="Image" src="https://github.com/user-attachments/assets/1a920eb5-e581-44ce-bcef-2ebf0566777f" />

# FreelanceFlow Monorepo

FreelanceFlow is a full-stack freelance marketplace monorepo built with a modern TypeScript-first architecture.

## Workspace Structure

- `apps/web` — Next.js 14 App Router frontend
- `apps/api` — Express.js backend with layered REST API
- `packages/db` — Prisma schema and database package
- `packages/ui` — Shared UI components

## Frontend

The web app includes pages for:

- Landing
- Job listings and job detail
- Post a job
- Freelancer profiles and freelancer search
- Client and freelancer dashboards
- Messaging
- Notifications
- Settings
- Billing
- Admin panel

## Backend

The API includes:

- Auth routes (register, login, OAuth callback, JWT refresh)
- CRUD routes for users, jobs, and proposals
- Payments routes (Stripe-focused service placeholder)
- Reviews, messaging, notifications
- File uploads and search
- Admin routes

Backend architecture follows:

- Middleware layer (auth, rate limiting, error handling)
- Controller layer
- Service layer
- Route layer
- Validation schemas (Zod)
- Utility helpers

## Getting Started

```
```
</details>

**What it answered:**

```json
{
 "repo_kind": "real_software",
 "confidence": "high",
 "rationale": "The README describes a full-stack monorepo with runnable apps (Next.js frontend, Express backend), packages (Prisma schema, shared UI), run scripts, and database schema \u2014 all indicating this is an actual software project rather than a registry or docs-only repo. The contributing file references code merges and bounty payments tied to merged PRs, further implying real code changes are the meaningful merges. (See README for app/package layout and run commands; CONTRIBUTING for PR/merge behavior.)",
 "evidence_ids": [
  "repo:SecureBananaLabs/bug-bounty:readme",
  "repo:SecureBananaLabs/bug-bounty:contributing",
  "repo:SecureBananaLabs/bug-bounty:meta"
 ],
 "governance_flags": [
  "none"
 ]
}
```

## 4. Stage B — is there a real route in?

*Model:* `gpt-5-mini-2025-08-07` · *1107 in / 479 out tokens · $0.0012*

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
Repository: SecureBananaLabs/bug-bounty

CONTRIBUTING (evidence id: repo:SecureBananaLabs/bug-bounty:contributing)
<img width="1859" height="935" alt="logo" src="https://github.com/user-attachments/assets/31e54d5c-d336-4294-8f73-9782465dbbda" />

<img width="952" height="328" alt="Image" src="https://github.com/user-attachments/assets/2da5d257-dd5b-4bef-831e-e39b44ce4b94" />

# Contributing Guidelines

Thank you for contributing to this bug bounty repository.

## Eligibility for Bounty Payment

- Bounty is paid **only** when your code is merged into the `main` branch.
- Opening a pull request or receiving review feedback does **not** guarantee payment.
- Closed, rejected, or stale pull requests are not eligible for payout.

## Pull Request Scope Rules

- Each pull request must address **exactly one** GitHub issue.
- Do **not** combine fixes for multiple issues in a single PR.
- PRs that touch more than one issue will be closed without review.

## How to Contribute

1. Pick an open GitHub issue.
2. Comment on the issue if you are working on it.
3. Create a branch for that issue.
4. Implement and test only the changes needed for that single issue.
5. Open a pull request that references the issue (for example: `Closes #123`).

## Pull Request Requirements

- Clearly describe the problem and your fix.
- Include test coverage or evidence of validation when applicable.
- Keep changes focused and minimal to the linked issue.
- Be responsive to maintainer feedback and requested updat
```
</details>

**What it answered:**

```json
{
 "onboarding": "substantive",
 "rationale": "The repository provides concrete onboarding steps and a clear contributor workflow. The README includes setup and run commands (npm install; npm run dev -w apps/web and apps/api) and notes where configuration (.env, Prisma schema) lives. The CONTRIBUTING file gives a specific, actionable process for proposing and doing work: pick an open issue, comment you\u2019re working on it, create a branch, implement and test changes for that single issue, and open a PR that references the issue; it also spells out PR requirements, review/merge rules, and bounty eligibility tied to merging to main. These items together constitute a real route for an outsider to start contributing and seek payment (evidence: repo:SecureBananaLabs/bug-bounty:readme, repo:SecureBananaLabs/bug-bounty:contributing).",
 "evidence_ids": [
  "repo:SecureBananaLabs/bug-bounty:readme",
  "repo:SecureBananaLabs/bug-bounty:contributing"
 ]
}
```

## 5. Stage C — what happened to people who tried?

*Model:* `gpt-5-mini-2025-08-07` · *2315 in / 3093 out tokens · $0.0068*

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
Repository: SecureBananaLabs/bug-bounty

Pull request threads:

--- evidence id: pr:SecureBananaLabs/bug-bounty#3185:opened  (open)
    opened by s0584273828-ctrl; 45 files, +896/-88
    files: ['apps/api/src/app.js', 'apps/api/src/config/env.js', 'apps/api/src/controllers/authController.js', 'apps/api/src/controllers/jobController.js']
    [AUTHOR] Update: I added scope for my issue #3186 (POST /api/payments auth + notification server-owned id/read) in this same PR after additional hardening. Both commits are now in securebanana-route-hardening-3184 (hash 5b6d9a1) and linked issue #3186 above.
    [AUTHOR] Update: I added additional #743-scoped hardening in commit 5730931 (auth required for review/proposal/message/upload POSTs) and extended securityHardening.test.js to cover all protected post endpoints. Existing /issues #3184,#3186 scope remains in the same PR.
    [AUTHOR] Update: Added 5 additional hardening fixes in commit e5a2d19 (registration role hardening + admin metrics role guard + upload file-size bound + related regression coverage). Files: apps/api/src/validators/auth.js, apps/api/src/services/authService.js, apps/api/src/middleware/requireRole.js, apps/api/src/routes/adminRoutes.js, apps/api/src/routes/uploadRoutes.js, apps/api/src/tests/securityHardening.test.js Validation: node --test apps/api/src/tests/securityHardening.test.js This keeps the PR aligned with #743 and the forked branch is updated.
    [AUTHOR] Follow-up commit 822be63 added 5 more hardening p
```
</details>

**What it answered:**

```json
{
 "threads": [
  {
   "pr_id": "pr:SecureBananaLabs/bug-bounty#3185:opened",
   "outcome": "ignored",
   "signal": "discouraging",
   "quote": "Update: I added scope for my issue #3186 (POST /api/payments auth + notification server-owned id/read) in this same PR after additional hardening."
  },
  {
   "pr_id": "pr:SecureBananaLabs/bug-bounty#3062:opened",
   "outcome": "ignored",
   "signal": "discouraging",
   "quote": "Quick follow-up from my side: this PR is ready for review and I can apply any requested adjustments immediately."
  },
  {
   "pr_id": "pr:SecureBananaLabs/bug-bounty#3063:opened",
   "outcome": "ignored",
   "signal": "discouraging",
   "quote": "This PR is ready for review and I can patch any requested changes fast. Happy to adapt to maintainer feedback."
  },
  {
   "pr_id": "pr:SecureBananaLabs/bug-bounty#3128:opened",
   "outcome": "ignored",
   "signal": "discouraging",
   "quote": "/claim #30"
  },
  {
   "pr_id": "pr:SecureBananaLabs/bug-bounty#3050:opened",
   "outcome": "ignored",
   "signal": "discouraging",
   "quote": "Patch is intentionally small and scoped to validation + tests only."
  },
  {
   "pr_id": "pr:SecureBananaLabs/bug-bounty#3227:opened",
   "outcome": "ignored",
   "signal": "discouraging",
   "quote": "Added a demo GIF to the PR body to satisfy the parent bounty's video/demo requirement:"
  },
  {
   "pr_id": "pr:SecureBananaLabs/bug-bounty#2969:opened",
   "outcome": "ignored",
   "signal": "discouraging",
   "quote": "Bounty eligibility note: I created issue #2975 under the parent bounty #743 as my own issue for this work. This PR addresses #2975"
  },
  {
   "pr_id": "pr:SecureBananaLabs/bug-bounty#3053:opened",
   "outcome": "ignored",
   "signal": "discouraging",
   "quote": "Reviewer-ready summary... Scope is narrow 
```

## 6. Stage D — verification (tool calls, no model)

Every evidence id cited by every finding was looked up against the provider: **29 lookups, 29 resolved, 0 did not.**

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
200/200 outsider attempts drew no response and none merged
=> not_viable
```

## 8. Stage E — narration

The verdict above was passed to Stage E as an input it cannot change.

---

# SecureBananaLabs/bug-bounty

> Replaying recorded model output. No model was called for this run.

**Verdict:** not_viable
**Method:** holt (A classify, B opportunity, C outcomes, D verify, deterministic verdict, E narrate)

I read through the PR threads and the repository documentation and concluded the not_viable verdict rests on a simple, well-supported pattern: outsiders follow the project’s explicit onboarding and PR process (the README and CONTRIBUTING lay out runnable apps, how to set up, how to pick an issue and open a PR, and state that bounties/payments are tied to merged PRs), but maintainers do not engage with outsider contributions. Measured behavior before the cutoff: 200 outsider threads, 200 ignored, 0 merged, 38 distinct outside authors, median first-response time is absent, and no bot activity to explain triage. Many PRs are explicitly marked “ready for review” or otherwise request feedback (quotes above show that contributors offered quick follow-ups, small-scoped patches, willingness to adapt, and /claim or /attempt notes), yet the threads received no maintainer replies. A few PRs were closed but typically by the author pointing to duplicates or closing after discovering overlapping work, not by maintainers merging or providing review guidance. The combination of a real codebase with an actionable contributor workflow and repeatedly ignored outsider PRs is the basis for the finding that the repository is not viable for outsiders seeking bounties via merged PRs. I could not see any on-repo evidence of private/alternate maintainer communication or merges that happened off-thread after the cutoff, so that remains a possible but unverified caveat.

## Evidence
- repo_kind = real_software (The README describes a full-stack monorepo with runnable apps (Next.js frontend, Express backend), packages (Prisma schema, shared UI), run scripts, and database schema — all indicating this is an actual software project rather than a registry or docs-only repo. The contributing file references code merges and bounty payments tied to merged PRs, further implying real cod — `repo:SecureBananaLabs/bug-bounty:readme`
- onboarding = substantive (The repository provides concrete onboarding steps and a clear contributor workflow. The README includes setup and run commands (npm install; npm run dev -w apps/web and apps/api) and notes where configuration (.env, Prisma schema) lives. The CONTRIBUTING file gives a specific, actionable process for proposing and doing work: pick an open issue, comment you’re working on i — `repo:SecureBananaLabs/bug-bounty:readme`
- outsider_posture = absent (Most open PRs show contributor 'ready for review' notes or small-scoped patches but no maintainer replies in the threads provided. A couple of PRs were closed by authors pointing at existing work (duplicates), not by maintainers providing review guidance. Overall the repository appears to lack visible maintainer engagement on these contributions.) — `pr:SecureBananaLabs/bug-bounty#3185:opened`
- discouraging: ignored — “Update: I added scope for my issue #3186 (POST /api/payments auth + notification server-owned id/read) in this same PR after additional hardening.” — `pr:SecureBananaLabs/bug-bounty#3185:opened`
- discouraging: ignored — “Quick follow-up from my side: this PR is ready for review and I can apply any requested adjustments immediately.” — `pr:SecureBananaLabs/bug-bounty#3062:opened`
- discouraging: ignored — “This PR is ready for review and I can patch any requested changes fast. Happy to adapt to maintainer feedback.” — `pr:SecureBananaLabs/bug-bounty#3063:opened`
- discouraging: ignored — “/claim #30” — `pr:SecureBananaLabs/bug-bounty#3128:opened`
- discouraging: ignored — “Patch is intentionally small and scoped to validation + tests only.” — `pr:SecureBananaLabs/bug-bounty#3050:opened`
- discouraging: ignored — “Added a demo GIF to the PR body to satisfy the parent bounty's video/demo requirement:” — `pr:SecureBananaLabs/bug-bounty#3227:opened`
- discouraging: ignored — “Bounty eligibility note: I created issue #2975 under the parent bounty #743 as my own issue for this work. This PR addresses #2975” — `pr:SecureBananaLabs/bug-bounty#2969:opened`
- discouraging: ignored — “Reviewer-ready summary... Scope is narrow and aligns exactly with issue intent.” — `pr:SecureBananaLabs/bug-bounty#3053:opened`
- neutral: closed_with_guidance — “Closing this PR as there is already an existing PR (#2851) by the issue creator that addresses this.” — `pr:SecureBananaLabs/bug-bounty#2949:opened`
- neutral: closed_with_guidance — “Closing this myself after a broader overlap refresh found existing open issues/PRs for the same unsupported OAuth provider surface (...) This should not stay in” — `pr:SecureBananaLabs/bug-bounty#2979:opened`
- discouraging: ignored — “Reviewer-ready summary... Happy to patch quickly if you want any naming/style adjustments.” — `pr:SecureBananaLabs/bug-bounty#3048:opened`
- discouraging: ignored — “/attempt” — `pr:SecureBananaLabs/bug-bounty#3046:opened`

