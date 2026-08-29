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

---

## Iteration 4 — attacking our own metric (2026-08-30)

**Tried.** Before shipping, score the trivial strategies against our own ground
truth: answer "viable" to everything, and answer "not viable" to everything.

**Why.** The plan said to attack our own metric before a judge does. Perfect
agreement is a smell; so is a metric nobody has tried to break.

**Evidence.** It broke immediately.

| Method | MCC | Balanced acc. | F1 |
|---|---|---|---|
| always "viable" | 0.00 | 0.50 | **0.78** |
| always "not viable" | 0.00 | 0.50 | 0.00 |
| baseline solution | 0.33 | 0.67 | 0.74 |
| **Holt** | **0.49** | **0.71** | 0.84 |

**A constant answer scores F1 0.78 and beats our own baseline solution.** The
graded pool is 14 positive against 8 negative, so F1 rewards a method for
recommending everything. Precision@10 is nearly as bad: the constants score 0.60
against 0.70 for every real method.

An ablation says the same thing from the other side:

| Configuration | F1 |
|---|---|
| full Holt | 0.84 |
| without Stage A's repository-kind rules | 0.82 |
| without the arithmetic signal thresholds | 0.79 |
| neither — everything viable | 0.78 |

On F1 the entire pipeline is worth 0.06 over answering yes to everything.

**Decision.** Matthews correlation becomes the primary metric, with balanced
accuracy alongside it. Both are 0.00 and 0.50 respectively for any constant
strategy, so neither can be gamed by a method that has no opinion. Under MCC the
same system, on the same data, scores 0.49 against the baseline's 0.33 — the
pipeline is worth 0.49 over a constant rather than 0.06.

The constant strategies stay in the results table permanently, scored as methods.
A reader should be able to see the floor rather than take our word for where it
is.

**What this cost us.** F1 0.84 against 0.74 was the headline for a day. It was
not wrong, it was uninformative, and we would not have noticed by staring at it.
The only reason we caught it is that scoring a constant answer takes four lines
and we wrote them before shipping rather than after being asked.

**Related finding, published rather than buried.** Holt's specificity is 0.50
against the baseline's 0.62: it over-recommends. Its whole advantage is
sensitivity, 0.93 against 0.71, plus the extreme cases where it rejects four of
five traps and the baseline none. That is a narrower claim than "better at
judging repositories" and it is the one the evidence supports.

---

## Iteration 5 — a pre-registered experiment that failed (2026-08-30)

**Tried.** Make Stage C load-bearing. Its sentiment signals had already been
measured and found inverted, but one structural feature did separate the
classes: **review ratio**, the share of merges that received substantive review
rather than being waved through — 0.68 for genuine opportunities against 0.50 for
the rest.

**Why the experiment was pre-registered.** The feature was chosen *after* seeing
it separate on the scored pool. Fitting a threshold there as well would have made
any reported gain a measurement of our own hindsight. So the rule, the threshold,
the direction it could act in, and three numeric predictions were written to
[`eval/PREREGISTRATION.md`](eval/PREREGISTRATION.md) and committed before a line
of it was implemented. Threshold 0.5, the natural midpoint, not a searched value.
The rule could only ever *withhold* a recommendation, never create one.

**Evidence.**

| | MCC | Balanced acc. | F1 | Sensitivity | Specificity |
|---|---|---|---|---|---|
| without the rule | **0.49** | 0.71 | 0.84 | 0.93 | 0.50 |
| with the rule | 0.19 | 0.60 | 0.64 | 0.57 | 0.62 |

Specificity improved exactly as predicted. It was bought at roughly five good
recommendations per bad one avoided: of six changed verdicts, **five were genuine
opportunities withheld** — including `NixOS/nixpkgs`.

| Prediction, recorded in advance | Outcome | |
|---|---|---|
| Specificity rises above 0.50 | 0.62 | held |
| Sensitivity falls | 0.93 → 0.57 | held |
| MCC moves by less than ±0.15 | −0.30 | **failed** |

**Decision: removed.** `verdict.py` is byte-identical to before the experiment.
The pre-registration file stays, with the result appended — a pre-registration
quietly deleted when it fails is worse than none.

**What it taught us, which is the point.** Absence of in-thread review is not
absence of engagement. `nixpkgs` merges a great deal of outsider work with no
visible review comment because the review happened in the issue, on a mailing
list, or between people who already trust each other. **The pull request thread
records the merge, not the conversation that produced it.**

That is the same lesson as the inverted-sentiment finding, reached independently:
*what a thread displays is a poor proxy for what a project does.* Registries look
welcoming because they are easy; mature projects look unreviewed because their
review is elsewhere. Two experiments, two directions, one conclusion — and it is
why Stage C informs the report a human reads while the verdict rests on
repository kind and arithmetic.

---

## Iteration 6 — a positive control (2026-08-30)

**Tried.** Three repositories nobody would argue about —
`home-assistant/core`, `rust-lang/rust`, `astral-sh/uv` — assessed as a declared,
hand-picked control outside the scored pool.

**Why.** Every result so far measures the ability to *reject*: registries, traps,
contribution-dead repositories. A detector that answered "not viable" to
everything would ace all of it. Nothing in the evaluation distinguished a working
detector from a broken pessimistic one.

**Verified before use, not assumed.** Each was labelled by the same L1 pipeline
used on the pool, from post-cutoff evidence:

| Repo | Qualifying merges | Distinct contributors |
|---|---|---|
| `home-assistant/core` | 152 | 62 |
| `rust-lang/rust` | 66 | 44 |
| `astral-sh/uv` | 35 | 13 |

**Evidence.**

| | Recovered |
|---|---|
| **Holt** | **3 / 3** |
| baseline solution | 1 / 3 |

The baseline returns *insufficient evidence* for `home-assistant/core` and
`astral-sh/uv`. Both are among the most contributor-friendly projects in open
source; neither README says so. That is the same failure the project is built
around, seen from the positive side: the landing page does not carry the
information, and only the contribution history does.

**Decision.** Kept, reported as a declared diagnostic and never mixed into the
scored pool. Hand-picked cases belong in a table labelled hand-picked.

---

## Iteration 7 — variance across three runs (2026-08-30)

**Tried.** Three complete, independent live runs of every method over the pool,
recorded into separate trajectory sets. $1.08 total.

**Why.** Every number until now came from one run. The plan said report variance
rather than one lucky number, and it was first in the cut order only because we
expected to be short of time. We were not.

**Evidence.** Mean ± half-range over three runs:

| Method | MCC | Balanced acc. | F1 | Sensitivity | Specificity |
|---|---|---|---|---|---|
| always "viable" | 0.00 ±0.00 | 0.50 | 0.78 | 1.00 | 0.00 |
| name-only probe | 0.16 ±0.07 | 0.58 | 0.52 | 0.40 | 0.75 |
| baseline solution | 0.28 ±0.07 | 0.64 | 0.68 | 0.62 | 0.67 |
| **Holt** | **0.46 ±0.05** | **0.70 ±0.02** | 0.83 ±0.02 | 0.90 ±0.04 | 0.50 ±0.00 |

Per-run MCC — baseline `0.19, 0.31, 0.33`; Holt `0.49, 0.49, 0.39`.

**Holt's worst run beats the baseline's best run.** 0.39 against 0.33, no
overlap. That is a claim a single run could not have supported, and the earlier
single-run figure of 0.49 turns out to have been Holt's *good* day.

**The second result is about the architecture.** Verdict stability across the
three runs:

| Method | Repositories identical in all three runs |
|---|---|
| baseline solution | 13 / 22 |
| **Holt** | **21 / 22** |

The baseline puts the entire decision inside one model call, so it wobbles on
nine of twenty-two repositories between runs. Holt puts the decision in
`verdict.py`, which is a plain function; model variance can only enter through
the stage classifications, and those are mostly stable. The determinism argument
was made on principle in the first commit of this project. This is the
measurement of it.

**Decision.** Kept. All headline figures are now reported as mean ± half-range,
and the single-run numbers in earlier entries are left as they were written.

---

## Iteration 8 — an adversarial review, and what it broke (2026-08-30)

**Tried.** A reviewer given the rubric and told to attack the submission
aggressively, with read-only access and instructions to verify every number
itself rather than trust the docs.

**Why.** Everything measured so far had been measured by the people who built
it. "Attack our own metric before a judge does" only works if someone actually
attacks it.

**What it found, verified independently before acting on any of it:**

**The uncertainty was reported on the wrong axis.** The README said Holt's worst
run beat the baseline's best and that the intervals did not overlap. Those
intervals measure how much the model wobbles between runs. They say nothing
about whether 22 repositories support the difference. Measured over
*repositories* — 20,000 bootstrap resamples plus exact McNemar:

| Run | McNemar p | Bootstrap MCC difference | P(difference ≤ 0) |
|---|---|---|---|
| 1 | 0.39 | +0.30 [−0.37, +0.93] | 0.18 |
| 2 | 0.55 | +0.18 [−0.41, +0.76] | 0.27 |
| 3 | 1.00 | +0.05 [−0.62, +0.71] | 0.44 |

**At 22 repositories the aggregate difference is not statistically
distinguishable.** The README now says so, and `eval/stats.py` prints it. What
the sample does carry is trap rejection (4/5 against 0/5, Fisher exact p =
0.048) and the positive control (3/3 against 1/3), both stable across all runs.

**The arithmetic gate never binds.** Setting `MIN_MERGES` and
`MIN_DISTINCT_AUTHORS` to zero leaves all 22 verdicts and the confusion matrix
identical. One of the four design choices the README calls load-bearing does
nothing on this pool.

**A user-visible claim was false.** `verdict.py` printed "15 outsider merges from
72 people" for nixpkgs; `distinct_outsider_authors` counts everyone who
*attempted*, not everyone who *landed*. The correct figure is 15 merges by 15
people out of 100 attempts by 72. Fixed, with a test, and a separate
`distinct_merged_authors` signal added.

**The reproduction guide had drifted.** It promised `42 passed` (actual 47) and
called F1 the primary metric, contradicting the README. Both are the first things
a reproducibility grader checks. Expected outputs are now pasted from actual runs,
and `eval/aggregate.py` gives the headline means a documented reproduction path —
previously the most prominent figures were the least checkable ones.

**Decision.** All of the above corrected. The reviewer's score was 68 against our
own estimate of 88; the gap was mostly these four items plus label sensitivity,
which is the next entry.

**Not everything it reported was right.** It flagged a stale "single run" line in
the README that had already been removed. Findings were verified before being
acted on, which is the same rule this project applies to its own claims.

---

## Iteration 9 — publishing what the result depends on (2026-08-30)

**Tried.** Measure how much the headline depends on choices we made ourselves,
and publish both answers whether or not they flatter the project.

**Ground-truth sensitivity.** L1 keeps an outsider merge only if the diff is
*substantive* and a human *reviewed* it. Both filters are ours. Mean MCC over
three runs:

| Ground truth | Positives | Holt | Baseline |
|---|---|---|---|
| L1 as shipped | 14/22 | **+0.46** | +0.28 |
| drop `reviewed` | 16/22 | **+0.61** | +0.16 |
| **drop `substantive`** | 16/22 | +0.13 | **+0.43** |
| drop both (≈ L0) | 18/22 | +0.28 | +0.33 |

**Remove the diff-shape filter and the baseline wins outright.** Holt's advantage
exists only against a ground truth that counts what a merged contribution
changed.

That definition is defensible and it is the project's opening claim rather than
one introduced later: appending a line to a JSON manifest is not a software
contribution. But the dependency is one filter deep, and Stage A's prompt asks
the model to judge a repository by what its merged diffs touch — the same
concept the filter encodes mechanically. Label and agent operationalise one
construct two ways, one by rule and one by judgement. `signals.py` claims the
agent shares no diff-shape rules with the label; that is true of the code and
looser than it sounds about the concept. Now stated in the README.

**Pipeline ablation, in MCC rather than the F1 this project calls degenerate:**

| Configuration | MCC |
|---|---|
| full pipeline | +0.46 |
| Stage A repository-kind rules disabled | +0.42 |
| arithmetic thresholds set to zero | +0.46 |
| both disabled | +0.42 |

Three model stages and a verification pass are worth **+0.04 MCC** over a rule
that says "insufficient evidence if nobody tried, otherwise viable". What they
buy that this table cannot show is the trap rejection, 4 of 5 against 0 of 5,
which is the only comparison here that reaches significance.

**Two components measured and found inert on this pool, now disclosed:**

- **Stage D dropped 0 of 1,402 findings** across three runs and 22 repositories.
  That is the correct outcome of citations that resolve, not evidence the
  mechanism works — the mechanism is covered by `tests/test_verify.py`, not by
  the pool. It also only checks that an id *exists*, never that the evidence
  supports the claim. The README described it as load-bearing; it now says this.
- **Stage B (`onboarding`) reaches the report and not the verdict**, like Stage C,
  and was mentioned in no user-facing document. Now it is.

**Also corrected:** the holdout is structural for timestamps and procedural for
payloads. Repository metadata is timestamped at repository *creation*, so its
payload carries `pushed_at`, `is_archived` and `stargazer_count` as of fetch. No
pool repository is archived so nothing leaked, but "a subclass cannot return
evidence from the wrong side" was a wider claim than the code makes good.

**Decision.** All published in the README under "What this result depends on".
None of it improves the score. A reader finding these unaided would discount
everything else; a reader finding them declared has one fewer reason to.
