# Trajectory — NixOS/nixpkgs

**Verdict:** `viable`  
**Rule that decided it:** 15 outsider merges from 72 people, median first response 0.8h

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
 "distinct_outsider_authors": 72
}
```

## 3. Stage A — what kind of repository is this?

*Model:* `gpt-5-mini-2025-08-07` · *3530 in / 1013 out tokens · $0.0029*

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
 "rationale": "The repository is the Nix Packages collection and implements NixOS (meta and README) and contains Nix expressions, NixOS modules, build scripts and patches. Merged PRs modify package expressions, NixOS modules, build hooks and patches (not just catalogue entries), which indicates changes to code that builds and runs software rather than only registry/list updates. Examples: PRs touching NixOS modules and Python package expressions (pr:NixOS/nixpkgs#526362), multiple package.nix files (pr:NixOS/nixpkgs#526372, pr:NixOS/nixpkgs#526321), patches and build outputs for fwupd (pr:NixOS/nixpkgs#526390), and package build logic for Home Assistant components (pr:NixOS/nixpkgs#526539). The repository description also states it implements a Linux distribution and a collection of software packages (repo:NixOS/nixpkgs:meta, repo:NixOS/nixpkgs:readme), and the CONTRIBUTING file documents contributing code under the project license (repo:NixOS/nixpkgs:contributing).",
 "evidence_ids": [
  "repo:NixOS/nixpkgs:meta",
  "repo:NixOS/nixpkgs:readme",
  "repo:NixOS/nixpkgs:contributing",
  "pr:NixOS/nixpkgs#526362",
  "pr:NixOS/nixpkgs#526390",
  "pr:NixOS/nixpkgs#526372",
  "pr:NixOS/nixpkgs#526321",
  "pr:NixOS/nixpkgs#526539"
 ],
 "governance_flags": [
  "none"
 ]
}
```

## 4. Stage B — is there a real route in?

*Model:* `gpt-5-mini-2025-08-07` · *2868 in / 674 out tokens · $0.0021*

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
 "rationale": "The repository includes concrete, followable onboarding documentation. CONTRIBUTING gives step\u2011by\u2011step instructions for setting up a local fork/branch, making and committing changes, pushing and creating a pull request, following commit/PR templates, and responding to CI and reviews (including mention of ofborg) \u2014 i.e. a clear documented process for proposing work (repo:NixOS/nixpkgs:contributing). The README links to manuals (Nixpkgs/Nix/NixOS manuals), lists community contact points (Discourse, Matrix, wiki) and CI/Hydra build pages so newcomers know where to get help and see build status (repo:NixOS/nixpkgs:readme). The CONTRIBUTING file does note it assumes basic Git/GitHub knowledge and points to resources to learn those, but does not require insider access.",
 "evidence_ids": [
  "repo:NixOS/nixpkgs:contributing",
  "repo:NixOS/nixpkgs:readme"
 ]
}
```

## 5. Stage C — what happened to people who tried?

*Model:* `gpt-5-mini-2025-08-07` · *4900 in / 4975 out tokens · $0.0112*

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
   "outcome": "changes_requested",
   "signal": "neutral",
   "quote": "[AUTHOR]"
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526361:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "You need to add the `lualine` dependency like this"
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526489:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "those look mostly okay"
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526457:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "The removal of the file should only be done on non `darwin` platforms."
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
   "quote": "Upstream changes ... look okay."
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526428:opened",
   "outcome": "changes_requested",
   "signal": "welcoming",
   "quote": "Sure, I use it. Happy to take care of maintenance."
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526410:opened",
   "outcome": "merged_without_engagement",
   "signal": "neutral",
   "quote": "1 package built: adguardian"
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526325:opened",
   "outcome": "merged_without_engagement",
   "signal": "neutral",
   "quote": "@NixOS/nixpkgs-merge-bot merge"
  },
  {
   "pr_id": "pr:NixOS/nixpkgs#526451:opened",
   "outcome": "merged_without_engagement",
   "signal": "neutral",
   "quote": "Looking at the code I found `USE_LTE_RATES` which seams to be the correct variable name"
  },
  {
```

## 6. Stage D — verification (tool calls, no model)

Every evidence id cited by every finding was looked up against the provider: **34 lookups, 34 resolved, 0 did not.**

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
15 outsider merges from 72 people, median first response 0.8h
=> viable
```

## 8. Stage E — narration

The verdict above was passed to Stage E as an input it cannot change.

---

# NixOS/nixpkgs

> Replaying recorded model output. No model was called for this run.

**Verdict:** viable
**Method:** holt (A classify, B opportunity, C outcomes, D verify, deterministic verdict, E narrate)

I read through a sample of 200 threads (100 from outside contributors) and the repository looks viable for outsiders. It’s a real software project (Nixpkgs/NixOS) with merges that change build logic, modules and patches, not just catalog edits, and the CONTRIBUTING/README point to concrete onboarding steps and community contact points. Response times are fast (median first response 0.8h) and maintainers give specific, actionable feedback (examples include "You need to add the `lualine` dependency like this" and other change requests that are phrased helpfully), and there are both human-reviewed merges and automated merges after successful local checks (quotes such as "Approved automatically following the successful run of `nixpkgs-review`." appear in the sample). From 100 outsider threads, 15 were merged and 63 were ignored; there are 72 distinct outside authors, and bot activity is relatively low (~8.5%). Those numbers are the main tradeoff: onboarding and reviewer behavior are clearly welcoming and effective, but a substantial fraction of outsider PRs in this sample were not acted on — I could not determine from the thread text whether that was due to low quality, duplicates, timing, or maintainers’ capacity. Overall the verdict “viable” rests on the combination of substantive onboarding, quick human responses, concrete reviewer guidance, and real merges (including code that builds/runs), tempered by the nontrivial ignored rate which is the main limit to a stronger signal.

## Evidence
- repo_kind = real_software (The repository is the Nix Packages collection and implements NixOS (meta and README) and contains Nix expressions, NixOS modules, build scripts and patches. Merged PRs modify package expressions, NixOS modules, build hooks and patches (not just catalogue entries), which indicates changes to code that builds and runs software rather than only registry/list updates. Exampl — `repo:NixOS/nixpkgs:meta`
- onboarding = substantive (The repository includes concrete, followable onboarding documentation. CONTRIBUTING gives step‑by‑step instructions for setting up a local fork/branch, making and committing changes, pushing and creating a pull request, following commit/PR templates, and responding to CI and reviews (including mention of ofborg) — i.e. a clear documented process for proposing work (repo:N — `repo:NixOS/nixpkgs:contributing`
- outsider_posture = welcoming (Most threads show active reviewer engagement: maintainers or reviewers give concrete guidance or approve changes, several PRs were merged (some after human review, some via automated approvals), and contributors are offered maintainer roles. That pattern indicates a generally welcoming path for contributors: specific, actionable feedback is provided and merges happen  — `pr:NixOS/nixpkgs#526518:opened`
- neutral: changes_requested — “[AUTHOR]” — `pr:NixOS/nixpkgs#526518:opened`
- welcoming: changes_requested — “You need to add the `lualine` dependency like this” — `pr:NixOS/nixpkgs#526361:opened`
- welcoming: changes_requested — “those look mostly okay” — `pr:NixOS/nixpkgs#526489:opened`
- welcoming: changes_requested — “The removal of the file should only be done on non `darwin` platforms.” — `pr:NixOS/nixpkgs#526457:opened`
- neutral: merged_without_engagement — “Approved automatically following the successful run of `nixpkgs-review`.” — `pr:NixOS/nixpkgs#526430:opened`
- welcoming: merged_after_review — “Upstream changes ... look okay.” — `pr:NixOS/nixpkgs#526475:opened`
- welcoming: changes_requested — “Sure, I use it. Happy to take care of maintenance.” — `pr:NixOS/nixpkgs#526428:opened`
- neutral: merged_without_engagement — “1 package built: adguardian” — `pr:NixOS/nixpkgs#526410:opened`
- neutral: merged_without_engagement — “@NixOS/nixpkgs-merge-bot merge” — `pr:NixOS/nixpkgs#526325:opened`
- neutral: merged_without_engagement — “Looking at the code I found `USE_LTE_RATES` which seams to be the correct variable name” — `pr:NixOS/nixpkgs#526451:opened`
- neutral: merged_without_engagement — “Merge: `b631779f8349ee53a611aec126abcff175f52bb2`” — `pr:NixOS/nixpkgs#526499:opened`
- neutral: merged_without_engagement — “Approved automatically following the successful run of `nixpkgs-review`.” — `pr:NixOS/nixpkgs#526419:opened`

