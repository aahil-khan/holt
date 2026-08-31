# Trajectory — NixOS/nixpkgs

**Verdict:** `viable`  
**Rule that decided it:** 15 first-time merges by 15 distinct people, out of 100 attempts by 72; median first response 0.8h

Replayed from committed fixtures and recorded model output. No model ran.

## 1. Evidence retrieved (tool call)

`provider.fetch("NixOS/nixpkgs")` → **449 records**, every one asserted to be dated at or before the cutoff 2026-06-01.

## 2. Signals computed — arithmetic, no model

```
{
 "total_threads": 200,
 "outsider_threads": 100,
 "outsider_merged": 15,
 "outsider_ignored": 63,
 "median_first_response_hours": 0.8,
 "bot_share": 0.085,
 "distinct_outsider_authors": 72,
 "distinct_merged_authors": 15,
 "reviewed_share": 0.56,
 "merge_rate": 0.15,
 "merged_files_median": 1.0,
 "merged_dirs_median": 1.0,
 "merged_with_files": 50
}
```

## 3. Stage A — what kind of repository is this?

*Model:* `gpt-5-mini-2025-08-07` · *3530 in / 573 out tokens · $0.0020*

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
Repository: NixOS/nixpkgs

Metadata (evidence id: repo:NixOS/nixpkgs:meta)
  description: 'Nix Packages collection & NixOS'
  primary language: 'Nix'
  homepage: ''
  archived: False  fork: False  mirror: False

README (evidence id: repo:NixOS/nixpkgs:readme)
<p align="center">
  <a href="https://nixos.org">
    <picture>
      <source media="(prefers-color-scheme: light)" srcset="https://brand.nixos.org/logos/nixos-logo-default-gradient-black-regular-horizontal-minimal.svg">
      <source media="(prefers-color-scheme: dark)" srcset="https://brand.nixos.org/logos/nixos-logo-default-gradient-white-regular-horizontal-minimal.svg">
      <img src="https://brand.nixos.org/logos/nixos-logo-default-gradient-black-regular-horizontal-minimal.svg" width="500px" alt="NixOS logo">
    </picture>
  </a>
</p>

<p align="center">
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/github/contributors-anon/NixOS/nixpkgs" alt="Contributors badge" /></a>
  <a href="https://opencollective.com/nixos"><img src="https://opencollective.com/nixos/tiers/supporter/badge.svg?label=supporters&color=brightgreen" alt="Open Collective supporters" /></a>
</p>

[Nixpkgs](https://github.com/nixos/nixpkgs) is a collection of over 120,000 software packages that can be installed with the [Nix](https://nixos.org/nix/) package manager.
It also implements [NixOS](https://nixos.org/nixos/), a purely-functional Linux distribution.

# Manuals

* [NixOS Manual](https://nixos.org/nixos/manual) - how to install
```
</details>

**What it answered:**

```json
{
 "repo_kind": "real_software",
 "confidence": "high",
 "rationale": "The repository is the Nixpkgs collection which contains Nix expressions, package definitions, and NixOS modules (i.e. code that builds and configures software and an OS). The README and meta describe it as a collection of software packages and implementation of NixOS (repo:NixOS/nixpkgs:readme, repo:NixOS/nixpkgs:meta). The contributing guide describes how to make code changes and PRs are used to modify package expressions (repo:NixOS/nixpkgs:contributing). Files changed by recent merged PRs are Nix package files and NixOS modules (e.g. pr:NixOS/nixpkgs#526362, pr:NixOS/nixpkgs#526390, pr:NixOS/nixpkgs#526372, pr:NixOS/nixpkgs#526402), showing active changes to runnable build definitions rather than merely catalog entries.",
 "evidence_ids": [
  "repo:NixOS/nixpkgs:meta",
  "repo:NixOS/nixpkgs:readme",
  "repo:NixOS/nixpkgs:contributing",
  "pr:NixOS/nixpkgs#526362",
  "pr:NixOS/nixpkgs#526390",
  "pr:NixOS/nixpkgs#526372",
  "pr:NixOS/nixpkgs#526402"
 ],
 "governance_flags": [
  "none"
 ]
}
```

## 4. Stage B — is there a real route in?

*Model:* `gpt-5-mini-2025-08-07` · *2868 in / 600 out tokens · $0.0019*

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
Repository: NixOS/nixpkgs

CONTRIBUTING (evidence id: repo:NixOS/nixpkgs:contributing)
# Contributing to Nixpkgs

This document is for people wanting to contribute to Nixpkgs.
This involves changes that are proposed using [GitHub](https://github.com) [pull requests](https://docs.github.com/pull-requests) to the [Nixpkgs repository](https://github.com/nixos/nixpkgs).

A GitHub account is recommended, which you can sign up for [here](https://github.com/signup).
See [here](https://discourse.nixos.org/t/about-the-patches-category/477) for how to contribute without a GitHub account.

This document assumes that you already know how to use GitHub and Git.
If that's not the case, we recommend learning about it [here](https://docs.github.com/en/get-started/quickstart/hello-world).

## Overview
[overview]: #overview

This file contains general contributing information.
More specific information about individual parts of Nixpkgs can be found here:
- [`doc`](./doc/README.md): Sources and infrastructure for the [Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/)
- [`lib`](./lib/README.md): Sources and documentation of the [library functions](https://nixos.org/manual/nixpkgs/stable/#chap-functions)
- [`maintainers`](./maintainers/README.md): Nixpkgs maintainer and team listings, maintainer scripts
- [`nixos`](./nixos/README.md): Implementation of [NixOS](https://nixos.org/manual/nixos/stable/)
- [`pkgs`](./pkgs/README.md): Package and [builder](https://nixos.org/manual/nixpkgs/stabl
```
</details>

**What it answered:**

```json
{
 "onboarding": "substantive",
 "rationale": "The repository provides a concrete, followable onboarding path: the CONTRIBUTING file gives step-by-step instructions for setting up a local fork/clone, choosing a base branch, creating a topic branch (with example git commands), committing, pushing, creating a pull request, and responding to reviews and CI (ofborg) results. It also links to more specific documentation (doc/, lib/, maintainers/, nixos/, pkgs/) and references commit and code conventions (repo:NixOS/nixpkgs:contributing). The README lists community contact points (Discourse, Matrix, wiki) and links to the Nixpkgs manual and contributor resources for further help (repo:NixOS/nixpkgs:readme).",
 "evidence_ids": [
  "repo:NixOS/nixpkgs:contributing",
  "repo:NixOS/nixpkgs:readme"
 ]
}
```

## 5. Stage C — what happened to people who tried?

*Model:* `gpt-5-mini-2025-08-07` · *4949 in / 5999 out tokens · $0.0132*

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
or discouraging.

Quote the words you judged from, verbatim and short, copied exactly from the
thread. If a thread shows NO_REPLIES there is nothing to quote: return an empty
quote rather than describing the silence. Never quote the scaffolding around the
thread -- only what a person actually wrote. Cite only pull request ids you were
given.
```
</details>

<details><summary>Evidence it was shown (first 1500 chars)</summary>

```
Repository: NixOS/nixpkgs

Pull request threads:

--- evidence id: pr:NixOS/nixpkgs#526518:opened  (open)
    opened by qweered; 11 files, +8/-58
    files: ['pkgs/build-support/setup-hooks/install-fonts.sh', 'pkgs/by-name/at/atkinson-hyperlegible-mono/package.nix', 'pkgs/by-name/at/atkinson-hyperlegible-next/package.nix', 'pkgs/by-name/be/beon/package.nix']
    [Sigmanificient] 
    [Sigmanificient] 
    [pancaek] 
    [Sigmanificient] 
    [AUTHOR] 
    [Sigmanificient] 
--- evidence id: pr:NixOS/nixpkgs#526361:opened  (open)
    opened by nyxar77; 3 files, +23/-4
    files: ['pkgs/applications/editors/vim/plugins/generated.nix', 'pkgs/applications/editors/vim/plugins/overrides.nix', 'pkgs/applications/editors/vim/plugins/vim-plugin-names']
    [PerchunPak] ## `nixpkgs-review` result Generated using [`nixpkgs-review`](https://github.com/Mic92/nixpkgs-review). Command: `nixpkgs-review pr 526361 --package vimPlugins.harpoon-lualine` Commit: `a65217085b3871b0b387c3490298fa73a18fa3f5` --- ### `x86_64-linux` <details> <summary>:x: 1 package failed to build:</summary> <ul> <li>vimPlugins.harpoon-lualine</li> </ul> </details> --- ### `aarch64-linux` <details> <summary>:x: 1 package failed to build:</summary> <ul> <li>vimPlugins.harpoon-lualine</li> </ul> </details> --- ### `x86_64-darwin` <details> <summary>:x: 1 package failed to build:</summary> <ul> 
    [PerchunPak] You need to add the `lualine` dependency like this https://github.com/NixOS/nixpkgs/blob/183cfa71568e398c8b419f9
```
</details>

**What it answered:**

```json
{
 "threads": [
  {
   "pr_id": "pr:NixOS/nixpkgs#526518:opened",
   "outcome": "ignored",
   "signal": "discouraging",
   "quote": ""
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526361:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "You need to add the `lualine` dependency like this https://github.com/NixOS/nixpkgs/blob/183cfa71568e398c8b419f9a763442344b352eda/pkgs/applications/editors/vim/plugins/overrides.nix#L2416-L2418"
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526489:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "Unfortunately, https://github.com/Keruspe/GPaste/compare/v45.5...v45.6 has bunch more AI changes that will require greater scrutiny."
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526457:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "The hash also needs to be changed :) It should be fine just squashing both commits together into the single update commit."
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526430:opened",
   "outcome": "merged_without_engagement",
   "signal": "neutral",
   "quote": "Approved automatically following the successful run of `nixpkgs-review`."
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526475:opened",
   "outcome": "merged_after_review",
   "signal": "welcoming",
   "quote": "Upstream changes (https://gitlab.gnome.org/GNOME/gegl/-/compare/GEGL_0_4_68...GEGL_0_4_70) look okay."
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526428:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "@wahjava (or someone else), would you like to replace me as a maintainer? I am no longer using weechat."
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526410:opened",
   "outcome": "merged_without_engagement",
   "signal": "neutral",
   "quote": "## `nixpkgs-r
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
15 first-time merges by 15 distinct people, out of 100 attempts by 72; median first response 0.8h
=> viable
```

## 8. Stage E — narration

The verdict above was passed to Stage E as an input it cannot change.

---

# NixOS/nixpkgs

> Replaying recorded model output. No model was called for this run.

**Worth your time** — for a contributor with 7 days.

If you open a first-time PR, you can expect a very quick initial reply (median 0.8 hours) and there are concrete examples of first-time contributors getting merged; at the same time a large share of outsider PRs in the sample received no visible reply (63 of 100). You will find good onboarding docs and active reviewers, but some contributions are handled automatically or ignored, so results will vary.

## What the evidence shows

Most important: in the sampled window 15 of 100 outsider threads were merged and those 15 merges came from 15 distinct first-time authors (72 distinct outsider authors total); the median time to first response was 0.8 hours. This shows the project is responsive and that first-time contributions do get through review to merge in real cases.

The repo provides substantive onboarding (CONTRIBUTING, manual links, community channels) and reviewers give concrete, actionable feedback and maintainer handovers (examples include “You need to add the `lualine` dependency like this …” and longer review threads). At the same time 63 outsider threads had no visible replies, some merges happened via automation (“Approved automatically following the successful run of `nixpkgs-review`”), and bots account for ~8.5% of activity — so engagement quality is mixed.

## What decided it

- 15 first-time merges by 15 distinct people, out of 100 attempts by 72; median first response 0.8h

## What could not be determined

I could not determine whether the ignored PRs represent a persistent pattern of inattention or a temporary backlog in the sampled period.

## Where outsider work landed

Counted over the 100 pull requests opened here by people with no prior merge, of which 15 were merged. Paths are cut to their first two segments, so a short path may name a file rather than a directory.

- **`pkgs/by-name`** — 13 merged of 62 attempted (21%)
- **`pkgs/top-level`** — 3 merged of 11 attempted (27%)
- **`pkgs/os-specific`** — 1 merged of 2 attempted (50%)
- **`pkgs/servers`** — 1 merged of 2 attempted (50%)

Outsiders attempted these and none were merged: `maintainers/maintainer-list.nix` (11), `pkgs/applications` (6), `pkgs/build-support` (6), `doc/release-notes` (2). That is what this sample shows, not a rule — a directory can appear here because newcomers are turned away from it, or because only a couple of people ever tried.

## Evidence

- repo kind: real_software — The repository is the Nixpkgs collection which contains Nix expressions, package definitions, and NixOS modules (i.e. code that builds and configures software and an OS). The README and meta describe it as a collection of software packages… — `repo:NixOS/nixpkgs:meta`
- onboarding: substantive — The repository provides a concrete, followable onboarding path: the CONTRIBUTING file gives step-by-step instructions for setting up a local fork/clone, choosing a base branch, creating a topic branch (with example git commands)… — `repo:NixOS/nixpkgs:contributing`
- outsider posture: welcoming — Most threads received timely, constructive responses: reviewers gave concrete guidance, offered maintainer handovers, and several PRs were approved/merged. Only one shown thread had no visible replies. Overall contributors are likely to… — `pr:NixOS/nixpkgs#526518:opened`
- ignored, nothing said — `pr:NixOS/nixpkgs#526518:opened`
- changes requested — “You need to add the `lualine` dependency like this https://github.com/NixOS/nixpkgs/blob/183cfa71568e398c8b419f9a763442344b352eda/pkgs/applications/editors/vim/plugins/overrides.ni…” — `pr:NixOS/nixpkgs#526361:opened`
- changes requested — “Unfortunately, https://github.com/Keruspe/GPaste/compare/v45.5...v45.6 has bunch more AI changes that will require greater scrutiny.” — `pr:NixOS/nixpkgs#526489:opened`
- changes requested — “The hash also needs to be changed :) It should be fine just squashing both commits together into the single update commit.” — `pr:NixOS/nixpkgs#526457:opened`
- merged without engagement — “Approved automatically following the successful run of `nixpkgs-review`.” — `pr:NixOS/nixpkgs#526430:opened`
- merged after review — “Upstream changes (https://gitlab.gnome.org/GNOME/gegl/-/compare/GEGL_0_4_68...GEGL_0_4_70) look okay.” — `pr:NixOS/nixpkgs#526475:opened`
- changes requested — “@wahjava (or someone else), would you like to replace me as a maintainer? I am no longer using weechat.” — `pr:NixOS/nixpkgs#526428:opened`
- merged without engagement — “## `nixpkgs-review` result Generated using [`nixpkgs-review`].” — `pr:NixOS/nixpkgs#526410:opened`
- merged without engagement — “@NixOS/nixpkgs-merge-bot merge” — `pr:NixOS/nixpkgs#526325:opened`
- merged after review — “Looking at the build logs, I noticed `ENABLE_LTE_RATES` doesn't exit.” — `pr:NixOS/nixpkgs#526451:opened`
- merged without engagement — “## `nixpkgs-review` result Generated using [`nixpkgs-review-gha`]” — `pr:NixOS/nixpkgs#526499:opened`
- merged without engagement — “Approved automatically following the successful run of `nixpkgs-review`.” — `pr:NixOS/nixpkgs#526419:opened`

*holt (A classify, B opportunity, C outcomes, D verify, deterministic verdict, E narrate)*
*Model output from gpt-5-mini-2025-08-07.*

