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

---

## Iteration 3 — the evaluation, and two results that went against us (2026-08-29)

**Tried.** Score four methods over the committed pool against the L1 ground
truth: popularity (stars), the baseline solution, Holt, and a name-only
memorisation probe. Same repositories, same pre-cutoff evidence, same task.

**Evidence — aggregate, 17 graded repositories.**

| Method | P@10 | Precision | Recall | Recommended |
|---|---|---|---|---|
| baseline solution | 0.70 | **0.73** | 0.89 | 11 |
| **holt** | 0.70 | 0.67 | 0.89 | 12 |
| popularity | 0.60 | — | — | — |
| name-only probe | 0.50 | 0.67 | 0.44 | 6 |

**On the aggregate, Holt does not beat the baseline.** It ties on precision@10
and is slightly behind on precision. That is the headline number and it is
reported first.

**Where the difference actually is.** Restricting to the repositories this
project exists to catch — 100 or more inbound outsider attempts and zero
qualifying contributions after the cutoff:

| Holt | Baseline | Stars rank | Repo |
|---|---|---|---|
| not_viable ✓ | viable ✗ | 5 | `is-a-dev/register` |
| not_viable ✓ | viable ✗ | 12 | `SecureBananaLabs/bug-bounty` |
| not_viable ✓ | insufficient | 11 | `runelite/plugin-hub` |
| not_viable ✓ | insufficient | 17 | `google-test/signclav2-probe-repo` |
| viable ✗ | insufficient | 1 | `NousResearch/hermes-agent` |

**Holt 4/5, the baseline 0/5**, and the baseline actively recommends two of them.
The aggregate hides this because both methods handle the easy majority the same
way; all of the difference sits in the hard cases. That is the shape the
benchmark-validity literature predicts — discriminating signal concentrates in
the hard tail while the easy majority saturates — and it is why a single
aggregate number was the wrong instrument for this claim.

**Removed: Stage C's thread signals as an input to the verdict.** Stage C is the
most expensive stage and the one the project's pitch leans on hardest. It was
computed and never read by `verdict.py`, which looked like a wiring bug worth
fixing. Measuring first showed it was not:

| | Genuine opportunities | Not opportunities |
|---|---|---|
| share of threads offering a real route in | 0.54 | **0.75** |
| share of threads judged welcoming | 0.46 | **0.54** |

The signal is inverted. `runelite/plugin-hub` scores 1.00 on "offers a real route
in"; `NixOS/nixpkgs` scores 0.50. Registries read as maximally welcoming
*because they are easy* — thread pleasantness measures low friction, not
viability, and real projects generate more friction precisely by having
standards. Wiring this into the verdict would have made Holt worse. Left out,
and left computed: it is the most useful thing in the report for a human reader
even though it is not a valid input to the decision.

**Fixed: the harness collapsed three label buckets into two.** The first run
scored Holt at 0.40 precision@10, behind everything. Three of its seven false
positives were repositories with *zero* post-cutoff outsider attempts — the
insufficient-evidence bucket that the plan and the L1 entry both define, in
advance, as a third category rather than a failure. Scoring them as negatives
punishes a method for saying "viable" about a project whose viability was never
tested. Restoring the pre-registered definition moved Holt from 0.40 to 0.70.
Recorded because the correction was made after seeing a bad number, and that
ordering is exactly when a reader should be most suspicious.

**Known limitations.**
- 17 of 30 repositories graded: 3 were deleted between the cutoff and the run,
  5 had no post-cutoff attempts to grade, and 5 are unrun because an OpenAI
  spend limit stopped the sweep partway.
- The name-only probe reaches 0.50 precision@10 knowing nothing but repository
  names. Some of every method's performance is recognition rather than reading,
  and that figure is the honest measure of it.

---

## Final — the complete sweep (2026-08-29)

**What changed.** Iteration 3's table was computed over 17 repositories, because
an OpenAI spend limit stopped the sweep at 22 of 27. With the limit raised and
the run resumed, all 22 gradable repositories are scored. The earlier partial
was not wrong, it was underpowered, and it pointed the wrong way.

**Result over the full graded pool (22 repositories, 14 genuine opportunities):**

| Method | Precision | Recall | F1 | Opportunities found |
|---|---|---|---|---|
| baseline solution | 0.77 | 0.71 | 0.74 | 10 / 14 |
| **holt** | 0.76 | **0.93** | **0.84** | **13 / 14** |
| popularity (stars) | — | — | — | — |
| name-only probe | 0.71 | 0.36 | 0.48 | 5 / 14 |

**Precision is a tie; recall is not.** At the same precision Holt surfaces
thirteen of fourteen genuine opportunities where the baseline surfaces ten. The
four the baseline misses are `DefiLlama/dimension-adapters`, `stablyai/orca`,
`tscircuit/kicad-to-circuit-json` and `volcengine/OpenViking` — projects whose
README does not advertise how workable they are. Holt misses one,
`Homebrew/homebrew-cask`, which it calls a registry; casks are Ruby files, and
whether writing one is a software contribution is a genuine judgement call the
label and the agent answer differently.

**And it still rejects the traps.** Among repositories with at least a hundred
inbound outsider attempts and zero qualifying contributions, Holt rejects four of
five and the baseline none of five, while the baseline recommends
`is-a-dev/register` and `SecureBananaLabs/bug-bounty` outright.

**Primary metric changed, and why.** Precision@10 reads 0.70 for Holt, the
baseline *and* popularity. With 14 positives among 22 repositories, a random
top-ten scores about 0.64: the metric is saturated and cannot separate anything.
It was chosen when the pool was expected to be larger and more lopsided. F1 over
the graded pool is reported as primary instead, with precision@10 retained so the
saturation is visible rather than quietly dropped.

**The probe result is the one to keep in view.** Knowing nothing but repository
names, it reaches 0.71 precision — recognising famous projects gets you most of
the way to being right about which are worth contributing to. Its recall is 0.36,
so recognition alone finds barely a third of the opportunities. That gap is a
fair statement of how much of any method's score here is reading rather than
remembering.

**Known limitations.** 22 of 30 graded: 3 repositories were deleted between the
cutoff and the run, and 5 had no post-cutoff outsider attempts to grade against.
Single run; variance across repeated runs is not measured.
