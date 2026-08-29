# Improvement Changelog

Every meaningful experiment gets an entry: what was tried, why, the evidence, and
what was decided. Experiments that were removed are included — what they taught
us about the problem is part of the result.

---

## Baseline — L0, the naive outsider merge rate (2026-08-29)

**Tried.** The metric a reasonable engineer writes first: of the pull requests
outsiders opened after the cutoff, what fraction merged? No filter on what the
diff touches, no bot exclusion, no requirement a human reviewed anything.
Outsider status derived from pre-cutoff merges only. Run over the hash-committed
pool of 30 repositories (sha256 `f100b2209c…`, seed 20260601).

**Why.** The project's central claim is that naive activity metrics reward the
wrong thing. That claim is worth nothing unless the naive metric is built
faithfully and actually run.

**Evidence.** 22 repositories scored, 5 insufficient evidence, 3 unavailable.

| Rank | Rate | Merged / Tried | Repo |
|---|---|---|---|
| 1 | 0.84 | 392 / 464 | `runelite/plugin-hub` |
| 3 | 0.81 | 271 / 336 | `DefiLlama/dimension-adapters` |
| 5 | 0.70 | 26 / 37 | `Homebrew/homebrew-cask` |
| 8 | 0.57 | 8 / 14 | `opencollective/opencollective-frontend` |
| 12 | 0.47 | 144 / 308 | `space-wizards/space-station-14` |
| 15 | 0.36 | 179 / 500 | `is-a-dev/register` |
| 17 | 0.32 | 67 / 210 | `NixOS/nixpkgs` |

**The prediction failed.** We expected `is-a-dev/register` — a registry where
every merged pull request is a one-line domain entry — to rank at or near the
top. It ranked **15th of 22**. Its merge rate is 0.36 because it rejects a large
volume of malformed requests. Writing this up as a confirmed prediction would
have been exactly the unpinned claim this project exists to avoid.

**What actually happened is a stronger result.** L0's top five contains three
registries — `plugin-hub` (#1), `dimension-adapters` (#3), `homebrew-cask` (#5).
Every merged contribution to those is a manifest entry or an adapter stub. Below
them sit the two most plausibly genuine opportunities in the pool:
`space-station-14` at #12 and `NixOS/nixpkgs` at #17. A developer following L0
would try three registries before reaching nixpkgs.

So the failure mode is real and systematic — registries cluster at the top,
software projects sit mid-pack — but it is a *category* effect, not the single
repository we had named in advance. One cherry-picked example replaced by a
pattern across four independent repositories is better evidence, not worse.

**Also observed.** Two repositories score 0.00 across 500 attempts:
`SecureBananaLabs/bug-bounty` and `google-test/signclav2-probe-repo`. Maximum
inbound activity, nothing merged. `NousResearch/hermes-agent` sits at 0.02 over
445 attempts. These are the opposite failure — repositories whose GitHub surface
looks extremely busy and which accept essentially nothing.

**Decision.** Kept as the baseline label. L1 must separate merges that touch real
source from merges that append a line to a data file; that is the discriminator
the top of this table is missing.

**Known limitation, recorded now.** Three repositories hit the 500 pull request
page cap (`is-a-dev/register`, `SecureBananaLabs/bug-bounty`,
`google-test/signclav2-probe-repo`), so their figures are the most recent 500
attempts rather than a census. `is-a-dev/register` is one of them, which means
its true rank is measured on a sample. Raising the cap before L1 is on the list.

---

## Iteration 1 — L1, the qualifying label (2026-08-29)

**Tried.** Keep an outsider merge only if the author is not a bot, the diff is
not docs-only or data-file-only or a one-line change to a single file, and a
human other than the author reviewed or commented. Built as a five-stage funnel
counted per repository, so each filter's effect is inspectable instead of folded
into one number.

**Why.** L0 ranked three registries in its top five and put `NixOS/nixpkgs` at
17. The missing discriminator is what a merged contribution actually *was*.

**Evidence — the two filters do different work.** Aggregate over 22 scored
repositories:

| Stage | Remaining | Removed |
|---|---|---|
| human attempts | 7,059 | — |
| merged | 2,302 | −67% |
| substantive (diff shape) | 1,211 | −47% |
| reviewed (human engagement) | 619 | −49% |

They are not redundant, and they do not catch the same repositories:

| Removed by diff shape | Removed by review | Repo |
|---|---|---|
| 392 | 0 | `runelite/plugin-hub` |
| 367 | 0 | `is-a-dev/register` |
| 16 | 277 | `Pasta-Devs/Marinara-Engine` |
| 25 | 114 | `anurag3407/career-pilot` |

Diff shape catches registries — manifest entries that merge cleanly and change
no software. Review catches auto-merge farms — real-looking diffs that no human
ever engaged with. **Either filter alone leaves half the problem standing.** The
prior going in was that review would dominate; it does not.

**Rank movement, L0 to L1:**

| Repo | L0 | L1 | Merged → qualifying |
|---|---|---|---|
| `runelite/plugin-hub` | 1 | **22** | 392 → 0 |
| `is-a-dev/register` | 15 | **20** | 367 → 0 |
| `Homebrew/homebrew-cask` | 5 | 6 | 25 → 11 |
| `NixOS/nixpkgs` | 17 | **12** | 67 → 14 |
| `space-wizards/space-station-14` | 12 | 8 | 144 → 53 |

**Removed and replaced: the first diff-shape rule.** Written as "exactly one
changed data file", it let 99 of `is-a-dev/register`'s 368 merges through and the
repo *rose* to 9. Inspecting the survivors showed why: a domain registration
there touches two files, the entry and a provider verification record. Counting
files was the wrong test — what matters is whether any changed file is source.
Widened to "every changed file is a data file", is-a.dev goes to 0 qualifying
merges and 20th. Recorded because the rule was changed after seeing its output,
which is exactly the kind of move that has to be visible.

**Decision.** Kept, both filters. L1 is the label the agent is scored against.

**Known limitations.**
- `is-a-dev/register`, `SecureBananaLabs/bug-bounty` and
  `google-test/signclav2-probe-repo` sit at GitHub search's own 1000-result
  ceiling, so their figures remain a sample. Raising the cap from 500 to 1000
  fixed what was fixable; the rest is an API boundary, not a choice.
- `Homebrew/homebrew-cask` keeps 11 qualifying merges because casks are Ruby
  files and pass the source test. Whether writing a cask is a software
  contribution is a genuine judgement call, and the rule does not resolve it.
- The one-line-single-file rule cannot distinguish a manifest entry from a real
  one-line bugfix. It is measured separately for that reason.

---

## Iteration 2 — the agent pipeline, and per-stage model selection (2026-08-29)

**Tried.** A → B → C → D → verdict → E, with the model used only where
interpretation is needed. Signals (counts, latencies, first-contribution rates)
and Stage D verification run no model at all. Model choice was made **per stage
and empirically**, starting everything on the small model and promoting only on
evidence.

**Why.** Two stages need judgement arithmetic cannot reach: what kind of
repository this is, and what a pull request thread reveals about an outsider's
odds. The rest is counting, lookup, or prose.

**Evidence — pilot on a development set disjoint from the scored pool.**
`microsoft/winget-pkgs`, `sindresorhus/awesome`, `pallets/flask`,
`tensorflow/tensorflow`. Chosen for category spread; deliberately *not* pool
repositories, so inspecting behaviour during development cannot tune the agent
against scored cases.

| Repo | Verdict | Rule that fired | Findings kept |
|---|---|---|---|
| `pallets/flask` | viable | 7 outsider merges from 111 people, median response 0.4h | 15/15 |
| `microsoft/winget-pkgs` | not_viable | `repo_kind=registry` | 16/16 |
| `sindresorhus/awesome` | not_viable | `repo_kind=awesome_list` | 14/15 |
| `tensorflow/tensorflow` | insufficient_evidence | 4/4 ignored is too thin to call hostile | 8/8 |

All four correct. **`gpt-5-mini` is sufficient for every stage, including thread
interpretation.** On `winget-pkgs` it wrote, unprompted, that "most interaction
is automated (wingetbot/validation logs). Maintainers rarely provide substantive
human [feedback]" — the exact distinction the stage exists to make. The Anthropic
credit stays unspent; per-stage promotion is available if the full pool shows a
stage failing.

**Cost: $0.0484 for four full pipeline runs**, about $0.012 a repository.

**Two bugs the pilot caught, neither visible without running it:**

*Bot detection was too narrow.* GitHub only flags accounts that are real GitHub
Apps. `wingetbot` posts every validation log as an ordinary user, so automated
traffic was being counted as human engagement — turning an auto-merge pipeline
into a conversational project. Detection is now applied at read time, so
fixtures stay as captured.

*Stage C citations were structurally unresolvable.* Stage C reasons about whole
threads, but only thread *events* (`#12:opened`, `#12:merged`) exist as evidence
ids. Citing the bare key meant Stage D correctly deleted 13 of 16 findings on the
first run. Threads are now presented with a real id, and shortened citations are
repaired before resolution — repairing a format is not excusing a claim, and an
id that resolves to nothing is still dropped.

*A guard added, not a tune.* `tensorflow/tensorflow` is 97% bot traffic, leaving
four outsider threads, all ignored. The hostility rule fired on four data points.
It now requires at least eight attempts before calling a repository hostile, and
returns insufficient evidence below that. Caught on the development set, which is
what the development set is for.

**Decision.** Kept. Small model everywhere, pending the full pool run.
