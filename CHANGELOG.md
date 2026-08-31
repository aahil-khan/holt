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

---

## Iteration 10 — an evidence-matched ablation (2026-08-30)

**Tried.** A single prompt given *everything Holt sees* — the same arithmetic
signals, the same twelve-thread digest Stage C reads, the same three-valued
verdict — to isolate what the orchestration is worth once evidence access is
held constant.

**A naming correction, made before reporting the numbers.** This is an
**ablation, not a baseline**. The brief defines a baseline as a reasonable basic
way to handle the task *before* using the solution; a person assessing a
repository does not have a temporal-holdout GraphQL crawler that reconstructs
pre-cutoff pull request threads. That evidence layer *is* Holt. Feeding its
output to a prompt measures the pipeline's orchestration, not a competitor. The
baseline remains README-and-metadata.

**Evidence.** Mean over three runs, 22 graded repositories:

| Configuration | MCC | Sensitivity | Specificity | Verdicts stable across runs |
|---|---|---|---|---|
| baseline (README only) | 0.21 ±0.13 | 0.67 | 0.54 | 18/22 |
| ablation: same evidence, one prompt | **0.53 ±0.05** | 0.93 | 0.54 | 20/22 |
| Holt (full pipeline) | 0.49 ±0.00 | 0.93 | 0.50 | **22/22** |

**Where the improvement comes from, which is what an ablation is for:**

| Change | MCC |
|---|---|
| README-only → the same evidence Holt reads | **0.21 → 0.53** |
| single prompt → staged pipeline | 0.53 → 0.49 |

Reading contribution history instead of a landing page is worth **+0.32 MCC**.
The orchestration on top of it buys **no measurable accuracy**.

**Is the 0.53 against 0.49 real? No.** McNemar p = 1.00 in all three runs. The
two configurations disagree on exactly two repositories out of 22 and each gets
one right: the ablation correctly rejects `NousResearch/hermes-agent`, Holt
correctly rejects `runelite/plugin-hub`. Reporting the ablation as beating Holt
would be the same overclaim, in the other direction, that we corrected in
iteration 8.

**What orchestration does buy, measurably:** 22/22 run-to-run verdict stability
against 20/22 and 18/22. A deterministic verdict function cannot disagree with
itself. That is reproducibility rather than accuracy, and it is a narrower claim
than the one this project started with.

**Decision.** Both results published. The baseline comparison is
README-only 0.21 → Holt 0.49; the ablation explains where that gain came from.
The uncomfortable half — that the staged pipeline adds no accuracy over one
well-prompted call with identical evidence — stays in the README rather than
being reframed away.

**What it points at.** Specificity is 0.50–0.54 across *every* method including
the constant answers. We reject non-viable repositories at close to chance, and
rejection is the thing this project exists to do. That is the next entry.

---

## Iteration 11 — shipping a validated rule, and measuring whether our citations hold up (2026-08-30)

**Shipped: the rubber-stamp rejection rule.** Validated out-of-sample on pool 2
before shipping — specificity 0.58 → 0.83, all three pre-registered predictions
holding. Rejects when `reviewed_share < 0.20` *and* `merge_rate > 0.60`:
contributions land easily and nobody looks at them. Both halves are required,
and the test suite pins the case that killed the previous attempt — `nixpkgs`
merges without visible review but is *hard* to land in, so it is not a rubber
stamp.

**The contributor's time budget is now a parameter, not an assumption.** Every
time-shaped threshold scales from `--days` (default 7). A maintainer whose median
reply is five days is fine with three months and useless with three days, and
that is the same repository with a different answer.

This is also the clearest thing the orchestration buys that a single prompt
cannot: **re-running with a different budget costs zero model calls**, because
the findings are already computed and only `verdict.py` re-runs. A prompt has to
pay for the whole assessment again.

**New evaluation dimension: evidence integrity.** Accuracy is not the only thing
a report can be wrong about. A claim can cite a pull request that does not exist,
or quote words never said in it. Neither appears in a confusion matrix.

| Method | Citations resolving | Quotes | Faithful to source |
|---|---|---|---|
| Holt | **696/696 (100%)** | 528 | 420/528 (80%) |
| evidence-matched prompt | 638/638 (100%) | **0** | not measurable |

**Two predictions of ours failed here, and both are informative.**

We expected the matched prompt to fabricate citations. It does not — 100% of its
638 references resolve, because it copies ids it was shown. The real difference
is not honesty, it is **auditability**: it emits no quotes at all, so there is
nothing to check. Holt makes claims that can be falsified; the prompt makes
claims that cannot.

We also expected Holt's fidelity to be near-perfect. It is 80%, and Stage D
guarantees nothing here — it checks that an id *exists*, never that the evidence
*says* what the claim says. That gap is ours and it is now measured.

**The metric immediately found a defect in our own prompt.** Of 108 unfaithful
quotes, **80 were our own scaffolding**: `_render_thread` printed
"(no replies from anyone)" for a silent thread, which reads like thread content,
and the model quoted it back as evidence. Excluding that artefact, fidelity is
**94%**. The scaffold is now `NO_REPLIES`, unquotable by construction, and Stage C
is explicitly told to return an empty quote rather than describe silence.

**Not yet re-measured.** The prompt change invalidates recorded trajectories by
design, and the corrected figure will come from the final frozen run rather than
being estimated here.

---

## Iteration 12 — Path Finder, first result: it ties the label it was meant to beat (2026-08-30)

**Tried.** Extend Holt from a verdict to an action: given a repository judged
viable, rank the issues open at the cutoff by how likely an outsider is to land a
merged pull request resolving them.

**Ground truth was designed before any implementation**
([`eval/PATHFINDER-DESIGN.md`](eval/PATHFINDER-DESIGN.md)). An issue is a
*realised entry point* if it was later closed by a merged pull request from
someone who had not already landed work there — mechanical, and reusing L1's
outsider definition so there is one definition rather than two.

**Feasibility was counted, not assumed.** 1,184 candidate issues across 14 viable
pool-1 repositories, 114 realised, a **9.6% base rate**.

**Result on pool 1 — precision@3, per repository, averaged:**

| Method | precision@3 |
|---|---|
| recency (newest first) | 0.042 |
| random (the base rate) | 0.119 |
| **`good first issue` label** | **0.125** |
| **Holt** | **0.125** |

**This meets cut condition 2, written before the feature existed:** *"the
`good first issue` comparator matches Holt's precision — the feature then has no
argument for existing."* It ties GitHub's own label and barely beats chance.

Underneath the tie, Holt wins decisively on `NixOS/nixpkgs` (0.67 against the
label's 0.00) and loses on `career-pilot` and `space-station-14` (0.00 against
0.33). Six of eight scorable repositories score zero for every method. **n = 8 is
too thin to separate anything**, which is the per-repository variance the design
document flagged as the main risk, arriving exactly as predicted.

**Pre-committed before seeing pool 2:** the combined result across both pools is
the answer. Pool 2's issues are being crawled and will roughly double the scorable
set. If Path Finder ties or loses on the combined set it is cut, and this entry
stands as the record. Choosing whichever pool flatters the feature is the failure
mode this commitment exists to prevent.

**A measurement bug caught before it shipped as a finding.** The first version
reported that **100% of issue bodies were edited after the cutoff** — an alarming
leak. It was false: `updatedAt` bumps on any comment or label change, so it
measured "had activity" rather than "was edited". Corrected to `lastEditedAt`,
the real figure is **9 of 935, 1.0%**. Had it shipped, it would have been a
self-inflicted wound: a leak loudly disclosed that did not exist.

**Also declared before scoring:** repositories with zero realised entry points are
excluded from the mean, because precision@k is identically zero there for every
method including the comparators. On pool 1 that is 6 of 14 — which is itself a
fact worth reporting about how rare these opportunities are.

---

## Iteration 13 — Path Finder is cut, on the number we said would cut it (2026-08-30)

**Pool 2 arrived, and the combined result is worse for us than pool 1 was.**

Pool 1 alone had Holt tying `good first issue` at 0.125. On pool 2 it *loses* to
both comparators. Combined across 25 scorable repositories, the pre-committed
answer:

| Method | precision@3 |
|---|---|
| random (base rate) | 0.151 |
| recency | 0.160 |
| **`good first issue` label** | **0.187** |
| **Holt** | **0.173** |

Paired over repositories, Holt − `good first issue` is **−0.013, 95% CI
[−0.133, +0.120]**; 3 wins, 6 losses, 16 ties, sign test **p = 0.51**. So Holt is
not reliably *worse* than the label either — the honest statement is that after
ranking 3,613 issues we **cannot distinguish our ranking from a label GitHub
already puts on the issue for free**.

**Cut condition 2, written before a line of it existed, is met:** *"the
`good first issue` comparator matches Holt's precision — the feature then has no
argument for existing."* `find_paths` is therefore withdrawn from the shipped
pipeline pending a final ship/cut call; nothing is deleted and the evaluation
stays runnable, because the negative result is worth more than a quietly deleted
branch. The open question is whether to ship the ranking with the losing
measurement printed in the tool's own output, which keeps the capability without
making the claim. That decision is recorded in `ASSESSMENT.md` and is not yet
made.

**What it cost to find out: $0.14 and about four hours.** What it bought is the
knowledge that our headline claim is about *repository-level* viability, and that
we have no evidence for issue-level guidance. Shipping it would have added a
confident-sounding ranking that a judge could have falsified in ten minutes with
a label filter.

**The leak measurement is also worse on pool 2** — 86 of 2,678 issue bodies
edited after the cutoff (3.2%) against pool 1's 1.0%, 95 of 3,613 (2.6%)
combined. It does not change the decision, but it is the number, and pool 1 alone
would have understated it by three-fold.

**What went right in this experiment even though the feature failed:** ground
truth was designed and the cut conditions written before implementation; the
combined-pool rule was fixed before pool 2 was scored; and the pool-1 result was
published as a tie rather than as the win the nixpkgs row (0.67 against 0.00)
would have supported on its own. Every one of those was a chance to fool
ourselves that we declined in advance rather than resisted in the moment.

---

## Iteration 14 — the coverage query, and shipping a feature that lost (2026-08-30)

**A five-minute query decided Path Finder, and it was a property of the inputs
rather than a slice on outcomes.** Before cutting on the tie or keeping on
sentiment, we asked one thing: *how many of the 25 scorable repositories have any
beginner-labelled issue at all?*

```
13/25  have none at all
17/25  have fewer than 3 — the label cannot fill a top-3 there
497/3,613 candidate issues carry a beginner label (13.8%)
```

**On 17 of 17 label-absent repositories, `good_first` scored identically to
recency, to the decimal.** With nothing labelled, the comparator reorders nothing
— it *is* recency wearing the label's name. So "we tied the `good first issue`
label" was, on two thirds of the pool, "we tied recency". That is a flaw in how we
reported our own comparator, and it was ours to find.

**Path Finder ships, and ships losing.** Every rendered ranking now carries this,
emitted by the renderer rather than by any caller, so no code path can print a
ranking without it:

> **This ranking is not measurably better than picking at random.** precision@3
> was 0.173 for this ranking, 0.187 for GitHub's `good first issue` label and
> 0.151 for a random pick — differences well inside noise. It is printed anyway
> because 13 of those 25 repositories had no beginner-labelled issue at all.

A test asserts both that the disclaimer accompanies any ranking and that its
printed numbers track the recorded measurement, so the two cannot drift.

**One function now serves both the CLI and the harness**, and the candidate set is
defined once in `holt.issues`, owned by neither the agent nor the label modules.
If the ranked set and the scored set could drift, every precision number would be
meaningless. Replay proves the refactor is prompt-identical: both pools reproduce
their previous scores exactly, to three decimals.

**The isolation test we said existed did not exist.** `CLAUDE.md` and three module
docstrings claimed a test enforced that `eval/labels/` cannot import
`src/holt/agent/`. Nothing did. A documented-and-unenforced guarantee is worse
than an undocumented one, because a reader trusts it. It is now checked
structurally with `ast`, so even an unexecuted import fails.

**The fresh-clone check found somebody else's credentials, not ours.** Sweeping a
clean clone for key material turned up **13 credential-shaped strings across 7
fixtures**, including two full-length GitHub personal access tokens pasted into
public issue bodies. One appeared twice in the same issue — once normally, once
**reversed**, to defeat scanners.

Ours were clean; these were third parties'. Crawling public issues that contain
leaked keys is unavoidable, but redistributing them inside a submitted artifact is
a choice, and we declined it. Scrubbing now runs on the way to disk and *before*
the content hash, so the committed hash describes the committed bytes. Two tiers:
recognised formats everywhere, plus long opaque runs inside a record that already
tripped tier one — which is what catches the reversed copy. Records keep their
evidence id, so every citation still resolves, and carry a `redacted` flag.

All 59 verdict trajectories and all 25 ranking trajectories still replay with zero
stale keys: **none of the removed strings had reached a prompt.** A test now walks
every committed fixture and fails on any credential-shaped string — the check that
would have caught this before the first capture was committed.

**Fresh clone, no credentials, verified end to end:** `uv sync`, **71 passed**,
`holt analyze --replay` renders, `--days 90` re-answers with zero model calls, and
`eval/pathfinder_harness.py --replay` reproduces the published ranking numbers.

**The README's engineering section was resequenced, same facts.** It now leads
with what the orchestration *buys* — the pre-registered rejection rule that took
out-of-sample specificity from 0.58 to 0.83, and the day budget that re-answers
the question at zero model calls — and states what it does not buy immediately
after. Previously a reader met "orchestration adds no accuracy" before meeting
either. The ablation reads better as the evidence that makes the first claim
credible than as a retraction of it.

---

## Iteration 15 — personalised contribution discovery: cut, and the model changed nothing (2026-08-30)

**Tried.** Not "find an approachable issue" — the prototype tied GitHub's label at
that, because it never saw who was asking. Instead: *given what this person has
already merged here, which open issues are a sensible next step?* A question no
label answers, because it is a property of the pair rather than of the issue.

**Pre-registered first** (`eval/PREREGISTRATION-3.md`), before a line of code:
unit, exclusions, metrics, six arms, eight feature weights, numeric predictions,
decision rule and four binding cut conditions.

**A confound found before building, which would have faked a large win.** Of the
655 issues open at the cutoff that an existing contributor later closed with a
merged pull request, **299 — 46% — were issues that same person had opened.**
Predicting that somebody fixes the bug they filed is not a recommendation; the
intent is already legible in pre-cutoff evidence. Self-opened issues are excluded
from both the label and the candidate set, leaving **128 scorable
(repository, contributor) pairs and 357 realised next contributions**.

**The comparator check we failed last time, run first this time.** `path_overlap`
— "issues naming a file or directory they have already touched" — genuinely
partitions the candidates on **77%** of pairs, unlike `good first issue` which was
recency under another name on two thirds of the pool. So the registered bar was
beating a real heuristic, not beating random.

**Result, out of sample on pool 2** (88 pairs, never used to diagnose or repair):

| Arm | hit@10 |
|---|---|
| recency | 0.136 |
| random | 0.150 |
| `blind` (the contributor-blind prototype) | 0.159 |
| **`path_overlap` — the bar** | **0.193** |
| `holt_full_repaired` | 0.205 |

**Cut condition 2 met:** +0.011 against a +0.05 bar, 3W/2L/**83T**, p = 1.000.

**Cut condition 3 met, and it is the finding.**
`holt_full_repaired` − `holt_repaired` = **+0.000. 0 wins, 0 losses, 88 ties.**
The model call — one competence profile per contributor, built from their merged
pull requests and the review feedback on them — **moved not one ranking position
for any of the 88 contributors.**

**Combined over both pools it is worse**: `holt_repaired` 0.211 against
`path_overlap` 0.234, and the scorer *exactly as registered* scores 0.164 —
**below random's 0.172**. Pool 2 alone flattered it. The combined number is
reported because reporting the friendlier pool is the failure mode
pre-registration exists to stop.

**Why the registered scorer lost to random, diagnosed from the inputs.** Three of
its eight features fired on 66–90% of all candidates with lift at or below 1.11 —
`scope_step`, `actionable`, `discussion`. **They are constants, not features**,
and together they contributed 2.0 points of near-uniform score that outweighed
`dir_hit` entirely and rivalled `file_hit`. Amendment 1 declared a repair rule
stated as a property of a feature's own distribution — *fires on >50% of
candidates and lift < 1.15* — fitted on pool 1 alone, changing no weight. It
lifted the arm from 0.164 to 0.205 out of sample and still did not clear the bar.

**A reproducibility bug the replay layer caught.** `histories()` iterated a Python
`set` of pull-request numbers, and string hashing is randomised per process, so
the same contributor produced a **different prompt on every run** — every recorded
trajectory an unreplayable miss. Now sorted, and verified identical across three
`PYTHONHASHSEED` values. Nobody re-running our work would have reproduced the
ranking, and only the replay discipline exposed it.

**What survives.** Not a feature. The second independent measurement that Holt's
model layer does not improve accuracy — and a much sharper one than the first.
The orchestration ablation could be waved away as the verdict task being too easy
for the extra machinery. This one cannot: the model had **strictly more context**
than the arithmetic — history, files, review threads, a structured profile — and
returned an identical ranking 88 times out of 88.

**Cost: $0.49 and about four hours.** `holt next` does not ship. Everything stays
runnable, including the arm that lost to random.

---

## Iteration 16 — the fifth kill: personalised discovery was one summer-of-code cohort (2026-08-30)

**Tried.** Move one step earlier than "analyse this repo": *given who you are,
which repositories should you even consider?* The argument was composition rather
than competition — stars say **alive**, language says **my world**, and neither
says **will they take a patch from a stranger**, which is the one thing this
project has evidence it can measure.

**The evidence for it looked strong.** Of 74 (contributor → new repository)
transitions in the pool, **66 landed in an L1-viable repository — 89%** against a
51% base rate. On that number the feature was worth about three hours.

**It survives none of four controls.** Reproduce all of them with
`PYTHONPATH=. uv run python eval/mover_controls.py`, which re-derives the headline
first, because a refutation that cannot reproduce what it refutes is not one.

**(a) It is one programme, not a preference.** **66 of the 74 transitions have
both endpoints inside a single nine-repository cluster**, and that cluster is
GirlScript Summer of Code '26 — projects with a points leaderboard.
`grep -oic gssoc fixtures/post_t/leonagoel__hybrid-recommender.json` returns
**1,605**; commitpulse returns 867. Contributors move between these repositories
because they are enrolled in the same programme. Programme membership causes both
the move and the merge. Nothing was chosen.

**(b) Outside the cluster the signal inverts.** Eight transitions remain and only
two land viable. One of those two is `(ghost)` — GitHub's deleted-account
placeholder, which aliases every deleted contributor into a single login, so it is
not a person. Another is `frenck`, a home-assistant maintainer moving inside his
own ecosystem: an insider, not a stranger. **The independent evidence is one
transition.**

**(c) The base rate was the wrong null.** A mover can only appear where an
outsider's pull request merges — and L1-viability is *defined* by outsider merges.
Weighting by where merges actually happen, **11,578 of 16,892 post-cutoff merge
slots sit in viable repositories: 69%, not 51%.** The lift collapses from +38
points to +21, and control (a) accounts for the remainder.

**(d) The cheap comparator wins outright.** Leave-one-out cohort co-occurrence —
*"where else did people from your repository go"* — predicts the **exact
destination** top-1 22% and top-3 45% of the time. A viability filter only narrows
69 repositories to 35. The free heuristic answers a strictly harder question,
*which one*, and answers it well.

**Cost of this kill: about ninety minutes and no model calls.** The comparator-first
discipline that saved us on `good first issue` and path-overlap saved us again,
and this time before a line of the feature existed.

**A finding underneath the kill, which now sits in Known Limitations.** Those nine
GSSoC repositories **pass L1**. Leaderboard-driven pull requests are substantive
by our diff-shape filter and mentors comment on them, so they label as viable.
"A stranger's patch lands here" is true of them. Whether a week spent there is the
opportunity this tool exists to find is a question our ground truth does not ask.
We did not discover it by inspecting our labels — we discovered it because it
broke a different experiment. **The labels are hash-committed and were not touched
after the fact**, and a judge can grep for it in our own fixtures, so it is stated
in the README rather than left to be found.

**Also corrected here:** the README claimed picking by stars "is a coin flip".
Our own check says otherwise — the ten most-starred repositories in this pool are
**80% viable against 51%**. Stars are a decent liveness signal and we now say so.
What they cannot do is separate a registry, a mirror or a links list from a
software project, which is where the only significant result in this project lives
(4 of 5 traps rejected, baseline 0 of 5, exact p = 0.048).

**Five experiments have now been cut by their own pre-registered rules, and one
shipped.** That ratio is the project.

---

## Iteration 17 — two capabilities that claim nothing, and a regression they exposed (2026-08-30)

After five features cut for losing to a cheap comparator, both additions here were
chosen for making **no claim that a comparator could beat**.

**Where outsider work landed.** Every pull request Holt reads carries its file
list. It decided whether a diff was substantive and was then discarded. Now it is
counted, over outsider threads only:

```
pkgs/by-name      13 merged of 62 attempted (21%)
pkgs/top-level     3 merged of 11 attempted (27%)
never landed:  maintainers/maintainer-list.nix (11), pkgs/applications (6),
               pkgs/build-support (6), doc/release-notes (2)
```

That is the sentence a newcomer most needs about a 200,000-file tree and cannot
get anywhere: GitHub does not show it, `CONTRIBUTING` does not say it. **Pure
arithmetic, no model call, no trajectory invalidated.**

Care taken where it would otherwise mislead: an attempt counts once per pull
request, not once per file; outsider status is decided per thread in time order,
so one prolific newcomer's fortieth merge cannot make a repository look open; a
directory is named as "never landed" only when at least two people tried; and the
text says plainly that this describes the sample rather than stating a rule.

**Two segments group a source tree and destroy a registry.** On
`runelite/plugin-hub`, where every plugin owns a directory, the first version
emitted ninety rows of one merge each — rows that read as insight and carried
none. Above a ratio of areas to pull requests the split falls back to one segment,
collapsing it to the single true row: **70 merged of 99 attempted, all in
`plugins`**. The caption states which grouping was used.

**`holt compare a b c`.** A shortlist is the real situation. It sorts nothing —
rows come out in the order asked for — because sorting is a claim. The `why`
column is the **rule that fired**, so the comparison is on the deterministic part
rather than on prose.

**A regression that only this feature could have caught.** Adding the
contributor's day budget to the narration prompt in iteration 16 made that prompt
**vary with `--days`**, so `--days 3 --replay` became a replay *miss*. That
silently falsified the claim that re-answering the question at a different time
budget costs zero model calls — one of the few things orchestration buys that a
single prompt cannot. Nothing failed loudly; the claim was simply no longer true.
`compare --days 3` exercised the path and exposed it.

The budget never needed to reach the model: the renderer prints it and
`verdict.py` already reflects it, both without a model call. Removed, and a test
now asserts `contributor_days` appears in neither `narrate` nor its system prompt.

**The uncomfortable part:** this regression was introduced *by the change that
fixed our weakest graded area*, and it was live for about eight hours. It would
have survived into the submission had a second feature not happened to touch it.
Every recorded trajectory was re-recorded a third time as a result.

## Iteration 18 — `holt discover`: the user states a profile, screening is free (2026-08-31)

Discovery returns, shaped by two earlier kills instead of repeating them.

**The input is a stated profile, not an inferred one.** Iteration 15/16 tried to
infer a profile from the person's GitHub history and was cut on data: the median
contributor in our pool has **1 merged pull request and 5 touched files**, and
98% of cross-repository area overlap was generic-path collisions (`src`, `docs`,
`tests`). Inferring "you work on Python developer tooling" from one pull request
would be invention, so `holt profile` asks — once, four questions, stored in
`~/.config/holt/profile.toml`. The earlier objection that *"a form cannot be
evaluated"* was a benchmark argument wrongly applied to a product decision: the
benchmark decides what we may claim, not what we may build.

**Every question maps to something that changes the output, or it is not asked.**
Languages and topics become search qualifiers — sourcing only, no claim. Days
feeds `verdict.py`, where the slow-response threshold is `days × 24`.
Contribution type is matched against the directories where outsider work
actually merged (the landing analysis). Experience level is deliberately absent:
nothing downstream could map it to a threshold, so asking it would be decoration.

**The structural fact that makes screening free:** `verdict.py` needs exactly
one model-derived input, `repo_kind`. Every other rule — rubber-stamp, hostile,
slow-response, the outsider-merge floor — is arithmetic over crawled signals.
So `holt discover` sources candidates from GitHub repository search, screens
them at one page of pull-request threads with **zero model calls**, and spends
model money only on the survivors, re-crawled at full depth. A prior live probe
measured screening at ~6 s per repository, $0.00 — and it rejected correctly
(`tqdm/tqdm`: median first reply 837 h against a 7-day budget).

**Claim discipline.** We claim the filter — that is the 4/5-vs-0/5 trap
rejection, exact p = 0.048, and the out-of-sample rubber-stamp rule. We do not
claim the sourcing (candidates come from GitHub search, and the output prints
the query) or the ordering (rows come out in screening order; nothing is
ranked). The output states that screening numbers are noisier than full-depth
ones, and which depth produced each.

**Evidence so far.** Fourteen new tests: every rejection bucket is walked from
synthetic threads (rubber-stamp, hostile, slow-against-budget, too-thin,
archived), the same repository flips from rejected to survivor when the budget
moves from 7 to 90 days, screening's signature admits no model client, and a
recorded session replays end-to-end from fixtures with no credentials. 108
passing overall.

**The recorded demo session** (`fixtures/discover/demo`, replayed by
`holt discover` with no flags, no token, no key): 25 candidates from
`language:python topic:cli pushed:>2026-07-02 archived:false fork:false
stars:>=10`. Screening rejected 9 — 3 with no outsider landings, 2 hostile
(`Textualize/textual`, `sherlock-project/sherlock` on their newest page), 2
rubber-stamp, 2 too slow for 7 days — at $0.00. Five survivors analysed at full
depth for $0.079 total: typer, click, beets and pipx viable; **tqdm/tqdm
survived shallow screening and flipped to insufficient at full depth** (median
first reply 1128 h against a 168 h budget), which is the screen-versus-full
noise the output discloses doing exactly what the disclosure says.
`yt-dlp/yt-dlp`'s full-depth crawl died on a GitHub server error and is listed
as unanalysed rather than silently dropped. The contribution-type note fired on
every analysed row: the user asked for `tests`, and each row shows where
outsider test work actually merged (beets: 26 merged in `test`).

## Iteration 19 — `holt next`: the simple rule that won, shipped as measured (2026-08-31)

Iteration 15 cut the weighted progression scorer for failing to beat
`path_overlap` — *open issues naming a file or directory you have already
worked on here* — and the winning rule was mistakenly discarded along with the
loser. It ships now, as `holt next <repo> --as <login>`.

**The rule is byte-identical in semantics to the one the harness measured**
(`eval/progression_harness.py`): recency order, issues whose path-ish tokens
match the contributor's touched files or directories first. Shipping a
"cleaned-up" variant under the measured numbers would be an unpinned claim, so
`overlap_tokens` reproduces the harness predicate and a test walks the same
file/dir/suffix cases.

**The claim, exactly:** best of five methods tried — hit@10 0.234 against
0.211 (weighted scorer), 0.188 (recency), 0.172 (chance); +0.06 over chance,
95% interval [−0.003, +0.132], an interval that spans zero. The renderer emits
that measurement with every ranking — the same pattern Path Finder uses — so no
code path can print the order without the number that says how well it works.
Each row states *why* it is where it is: the tokens that overlapped, or "no
overlap with your history; ranked by recency only".

**No model call anywhere in the path.** History comes from the pull-request
threads already crawled, candidates from the issue fixtures already captured;
`--live` works the same way. A contributor with no merged work here is refused
with a pointer to `holt analyze` — ranking for a stranger is the contributor-
blind Path Finder, which loses to GitHub's own label and stays behind its flag.

## Iteration 22 — the frozen benchmark: what it gave, and what it took away (2026-08-31)

Three live runs per pool, both pools, on the shipped prompts and rules — run
after the narration and wording fixes precisely so it measures what ships.
$3.50. Every run's recordings are committed and replay-verified: a judge
reproduces every number below with no key and no spend
(`eval/harness.py --replay --run-tag run1` … `p2r3`).

**What it gave.**

| MCC, mean ± half-range | Pool 1 (n=22) | Pool 2, out-of-sample (n=33) |
|---|---|---|
| name-only probe | +0.16 ±0.03 | +0.10 ±0.02 |
| baseline | +0.09 ±0.09 | +0.21 ±0.02 |
| same-evidence ablation | — | +0.32 ±0.07 |
| **Holt** | **+0.61 ±0.00** | **+0.63 ±0.00** |

- **Specificity 0.75 in sample, 0.83 out of sample** — the rubber-stamp rule's
  pre-registered number, now frozen into the committed benchmark, against the
  0.50 coin flip the previous committed runs showed.
- **Verdicts identical on all 55 repositories, all three runs, both pools.**
  The baseline changed its answer on 16 of 55. Determinism was a design claim;
  it is now a measured 55/55.
- **The ablation stopped tying.** Same evidence in one prompt: 0.32 ±0.07
  against the pipeline's 0.63 ±0.00 — and the fresh verdict-layer ablation
  shows the model stages + kind rules worth **+0.01 MCC** over arithmetic, so
  the entire lead is the deterministic rule layer. The honest sentence
  changed from "orchestration adds no accuracy" to "the model stages add
  none; the written rules add all of it."
- **The label-sensitivity vulnerability shrank.** Dropping `substantive` used
  to hand the baseline the lead (+0.13 vs +0.43); on the frozen runs Holt
  leads under every ground-truth variant (worst case +0.39 vs +0.28).
- Repository-level stats improved but stay honest: bootstrap difference +0.42
  to +0.59, P(difference ≤ 0) = 0.04–0.08, intervals still touching zero.

**What it took away.** The trap-rejection significance claim — 4/5 against
0/5, Fisher exact p = 0.048, previously "the only comparison that reaches
significance" — **did not survive re-measurement**. Holt still rejects 4 of 5
traps in every run ever recorded (it has never caught `hermes-agent`), but the
frozen baseline rejected 2–3 of 5 where the recorded one rejected 0. That is
model drift between recording sessions, the exact hazard the frozen-replay
design exists to surface. The claim is retired everywhere it appeared —
README, assessment, `stats.py`'s own footer, the discover docstring — and
replaced with the version that is stable: Holt 4/5 every time, a baseline that
wanders 0–3 depending on the day.

Also fixed while freezing: bare `eval/harness.py --replay` (no run tag) now
exits with a pointer to the tagged runs instead of dividing by zero, and
`REPRODUCTION.md`'s expected outputs are the frozen tables.

## Iteration 21 — the model becomes a choice, and the benchmark stays pinned (2026-08-31)

`holt models` lets a user swap the model behind every stage: other OpenAI
models, Claude via the Anthropic SDK, and any OpenAI-compatible endpoint —
Ollama and Gemini ship as presets, `openai-compatible` covers vLLM and the
rest. Per-stage overrides (`--stage narrate=claude-opus-5`) ride on the same
`STAGE_MODELS` seam that already existed; `model.py` remains the only file
that touches an LLM, and the `complete()` contract — a dict matching the
stage's declared JSON schema — holds across providers (Anthropic via
structured outputs; a safety refusal raises loudly instead of recording an
empty finding).

**The design decision that matters: the library never reads the user's model
configuration on its own.** Every committed trajectory, every benchmark
number and every replay was produced under the pinned dated ids, and an eval
script silently inheriting somebody's Ollama config would be exactly the
reproducibility failure this project is built to prevent. Only the CLI opts
in (`enable_user_models_config()`, one deliberate call a front end can also
make). A test proves the library resolves the pinned defaults even when a
config file exists on disk, and another that replay keys are byte-stable
under the defaults. When the configuration diverges, `holt models` says in
its own output that committed recordings will fail loudly under it rather
than serve another model's answers — the same principle as labelling
replayed output.

Costs for unpriced models are recorded as $0 and labelled "unknown" rather
than invented. Eleven new tests; no recorded artifact invalidated, because
no prompt changed.

## Iteration 20 — the reader is not running an experiment (2026-08-31)

The narration prompt fed the model a section headed `Measured before the
cutoff:`, so reports told users things happened "before the cutoff" — internal
evaluation jargon leaking into prose meant for someone deciding where to spend
a week. A live user has no cutoff; they have a window of history that was read.

Changed to `Measured in the sampled window:`, and NARRATE_SYSTEM now forbids
the word "cutoff" outright, offering "in the period read" / "in this sample"
instead. The date bound itself already reaches the reader through the
renderer's `*Evidence up to …*` line, which is computed, not narrated.

A prompt edit invalidates every recorded trajectory by design — the replay key
covers the prompt text — and the failure was exactly one test, the discover
demo replay, failing with a replay miss rather than serving stale prose. Fifth
full re-record, this time via `scripts/rerecord_trajectories.py` (pools plus
the demo session's survivors in one command). Batched deliberately with the
frozen benchmark that follows, so the benchmark measures the prompts that
ship.

**The word also lived in two deterministic rule traces** — "no outsider
attempts before the cutoff" and "only N outsider merges before the cutoff",
printed verbatim under *What decided it* (a TUI screenshot surfaced the first
one). Reworded to "in the period read". Because the traces enter the narration
prompt, that staled the recordings of exactly the repositories where those
rules fire — 7 of 69 — and healing them cost **$0.019** instead of another
$1.05 re-record, via a new patch mode (`PatchModel`; `--patch` on the
re-record script and the benchmark harness): replay every call whose prompt
is unchanged, re-record only what the change touched, never overwrite a
recorded run's results file.

**And the cutoff leaked into behaviour, not just prose.** The TUI (built on a
separate branch, against the promised `Assessment` contract) constructed
`LiveGitHubProvider(Window.PRE_T)` bare — and the library default for a *live*
provider was the benchmark's T. Result, observed in the wild: a live run with a
paid token reported `inni918/warashi` — created 2026-06-17, 105 stars, real
pull requests — as having no history at all, because its crawl asked GitHub for
`created:<2026-06-01`. The CLI had already fixed this for itself (`as_of_from`,
yesterday); the trap remained for every other caller. The default is now
**live means now**: both live providers default their cutoff to the current
moment, the one caller that genuinely wants T (the benchmark fixture capture)
passes it explicitly, and a test pins the default above T. An evaluation
device was reachable from the product path; it no longer is.
