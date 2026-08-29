# Holt

**Is this repository worth an outside contributor's week?**

Holt reads a GitHub repository the way a careful developer would after an
afternoon in its pull request threads, and produces an evidence-backed written
assessment. Every claim it makes carries an evidence id that resolves to a real
pull request, review or comment.

Named after Captain Holt: procedure, and refusing to state anything the evidence
does not support.

---

## Who this is for, and what it costs them today

A developer who wants to contribute to open source and has a week to spend.
Usually early in their career, for whom a wasted week is expensive.

Every signal GitHub surfaces measures **project health**, not **outsider
experience**, and those are different things. A domain registry with 40,000
merged pull requests, a curated links list, a read-only corporate mirror and a
genuinely welcoming software project are indistinguishable on stars, recency,
contributor count and open issues.

The only way to tell them apart today is to read twenty pull request threads per
repository, at roughly fifteen minutes each. Nobody does that, so people pick by
stars — and the data says that is a coin flip.

Two closed pull requests are the same integer in every GitHub statistic:

> "Thanks for this! Merged in #4821 — could you also look at the sibling case?"

> "We're rewriting this module internally, closing."

One says a newcomer can land work here. The other says don't bother.

---

## Result

Measured over a pool of 30 repositories drawn and hash-committed **before any
method ran**, against ground truth computed only from evidence *after* a
temporal cutoff neither method could see. 22 are gradable.

| Method | MCC | Balanced acc. | F1 | Sensitivity | Specificity |
|---|---|---|---|---|---|
| always answer "viable" | 0.00 ±0.00 | 0.50 | **0.78** | 1.00 | 0.00 |
| name-only probe (memorisation control) | 0.16 ±0.07 | 0.58 | 0.52 | 0.40 | 0.75 |
| baseline solution (one prompt over README + metadata) | 0.28 ±0.07 | 0.64 | 0.68 | 0.62 | 0.67 |
| **Holt** | **0.46 ±0.05** | **0.70 ±0.02** | 0.83 ±0.02 | 0.90 ±0.04 | 0.50 ±0.00 |

Mean and half-range over **three independent live runs**.

**That interval measures the wrong thing, and we are saying so.** ±0.05 is how
much the language model wobbles between runs. It is not how much a
22-repository sample can tell you. Measured over repositories instead —
bootstrap resampling, 20,000 draws — the difference between Holt and the
baseline is **+0.05 to +0.30 depending on the run, with a 95% interval that
spans zero in all three** (`P(difference ≤ 0)` = 0.18, 0.27, 0.44). Exact
McNemar on per-repository correctness gives p = 0.39, 0.55, 1.00.

**At this sample size the aggregate difference is not statistically
distinguishable.** Run `PYTHONPATH=. uv run python eval/stats.py` to see it.

Two results the sample *can* carry, both robust across all three runs:

- **Trap rejection.** Repositories with 100+ inbound outsider attempts and zero
  qualifying contributions: Holt rejects 4 of 5, the baseline 0 of 5 (Fisher
  exact p = 0.048).
- **Positive control.** Three verified-genuine repositories outside the pool:
  Holt recovers 3 of 3, the baseline 1 of 3.

**The constant answers are in that table on purpose.** F1 was this project's
original primary metric, and on a pool that is 64% positive it is degenerate:
answering "viable" to everything scores **F1 0.78**, beating our own baseline
solution. We found that by attacking our own metric before shipping it, and the
row stays in so a reader can see the floor rather than take our word for it.

Matthews correlation is the honest headline, because it is **0.00 for any
constant strategy**. Holt reaches 0.49 against the baseline's 0.33 — a 48%
relative improvement no trivial answer can fake.

**Where the advantage is, and where it is not.** Averaged over three runs Holt
recovers 12.7 of 14 genuine opportunities against the baseline's 8.7
(sensitivity 0.90 vs 0.62). Its **specificity is worse** — 0.50 against 0.67 —
so it over-recommends on ordinary repositories. A user following Holt tries more
repositories than they need to; what they do not do is spend a week on a
registry.

**Positive control.** A detector that answers "not viable" to everything would
reject every trap in the table above and look excellent doing it. So three
repositories nobody would dispute — `home-assistant/core` (152 qualifying
contributions from 62 people after the cutoff), `rust-lang/rust` (66 from 44) and
`astral-sh/uv` (35 from 13) — are assessed as a declared, hand-picked control,
separate from the scored pool.

| | Recovered |
|---|---|
| **Holt** | **3 / 3** |
| baseline solution | 1 / 3 |

The baseline calls `home-assistant/core` and `astral-sh/uv` *insufficient
evidence*, because their READMEs do not advertise how contributable they are.
That is the failure this project is about, in the positive direction.

Full numbers, every iteration including the ones that were removed, and the
results that went against us: [CHANGELOG.md](CHANGELOG.md).
Exact commands: [REPRODUCTION.md](REPRODUCTION.md).
An honest self-assessment of what is weak: [ASSESSMENT.md](ASSESSMENT.md).

---

## How it works

```
pre-cutoff evidence ──┬─► signals          arithmetic, no model
                      ├─► A classify       what kind of repository is this?
                      ├─► B opportunity    is there a real route in?
                      ├─► C outcomes       what happened to people who tried?
                      │        │
                      │   typed findings, each carrying evidence ids
                      │        │
                      │   D verify         drop any finding whose evidence
                      │        │           does not resolve
                      └────────┴─► verdict.py   a plain function, no model
                                       │
                                  E narrate     prose around a verdict it
                                                cannot change
```

Four design choices, and what measurement says about each:

**The model never owns the decision — and this is the one that measurably pays.**
`src/holt/agent/verdict.py` is the only path from findings to a verdict and runs
no model. Across three runs Holt returns identical verdicts on **21 of 22**
repositories; the baseline, which puts the whole decision inside one model call,
on **13 of 22**.

**Arithmetic where arithmetic works.** Counting landings and measuring reply
latency are not model problems. *But the arithmetic thresholds never bind on this
pool*: setting `MIN_MERGES` and `MIN_DISTINCT_AUTHORS` to zero leaves all 22
verdicts and the confusion matrix unchanged. They are guardrails that this
sample never tested.

**Verification can only subtract — and on this pool it subtracts nothing.**
Stage D resolves every evidence id a finding cites and drops what does not
resolve. Across three runs and 22 repositories it examined **1,402 findings and
dropped 0**. That is the correct outcome of citations that resolve, not evidence
that the mechanism works; the mechanism is covered by tests
(`tests/test_verify.py`) rather than by the pool. It also checks only that an id
*exists*, not that the evidence supports the claim.

**The holdout is structural for timestamps, procedural for payloads.** Every fact
passes through one `EvidenceProvider` whose base class asserts the cutoff on
every record, and a subclass cannot return a record with a post-cutoff
*timestamp*. Repository metadata is timestamped at repository creation, so its
*payload* — `pushed_at`, `is_archived`, `stargazer_count` — is as of fetch. No
pool repository is archived, so nothing leaked here, but the guarantee is
narrower than "structural" suggests.

**Stage B (`onboarding`) reaches the report and not the verdict**, like Stage C.
Only Stage A's `repo_kind` and the arithmetic signals are consulted by
`verdict.py`.

## What this result depends on

Two sensitivities a reader would otherwise have to find themselves. Both are
reproducible with `PYTHONPATH=. uv run python eval/sensitivity.py`.

**The ground truth is our own definition, and the headline turns on one half of
it.** L1 keeps an outsider merge only if the diff is *substantive* and a human
*reviewed* it. Mean MCC over three runs under each variant:

| Ground truth | Positives | Holt | Baseline |
|---|---|---|---|
| L1 as shipped | 14/22 | **+0.46** | +0.28 |
| drop the `reviewed` filter | 16/22 | **+0.61** | +0.16 |
| **drop the `substantive` filter** | 16/22 | +0.13 | **+0.43** |
| drop both (≈ the naive L0) | 18/22 | +0.28 | +0.33 |

**Remove the diff-shape filter and the baseline wins.** Holt's advantage exists
only against a ground truth that counts *what a merged contribution changed*.

We think that is the right definition, and it is the first claim this README
makes rather than one introduced afterwards: a merged pull request that appends a
line to a JSON manifest is not a software contribution. A reader who rejects that
premise should reject the project, not just the number. But the dependency is
real, it is not hidden, and it is one filter deep.

The honest tension: Stage A's prompt tells the model to judge a repository by
what its merged diffs touch, which is the same concept the `substantive` filter
encodes mechanically. Label and agent operationalise one construct two ways —
one by rule, one by judgement. That is not code sharing, and the temporal split
is intact, but it is closer than "the agent shares no diff-shape rules" implies.

**The pipeline's measurable contribution is small.** In MCC, holding recorded
model output fixed and varying only `verdict.py`:

| Configuration | MCC |
|---|---|
| full pipeline | +0.46 |
| Stage A repository-kind rules disabled | +0.42 |
| arithmetic thresholds set to zero | +0.46 |
| both disabled | +0.42 |

Three model stages and a verification pass are worth **+0.04 MCC** over a rule
that answers "insufficient evidence if nobody tried, otherwise viable". What they
*are* worth is the trap rejection — 4 of 5 against the baseline's 0 of 5 — which
is the one comparison in this project that reaches significance.

---

## Read-only---

## Read-only, and about time rather than people

Holt never writes to GitHub, opens pull requests, or contacts maintainers. It
reads public data only.

Its verdicts are about **fit for a contributor's time**, not maintainer quality.
A repository can be excellent and still be a poor place to spend your first week.
Every negative claim links to the evidence behind it, so a maintainer who
disagrees can point at the same thread and say why. There is no ranking of
projects by how welcoming their maintainers are, and none should be inferred.

---

## Evaluation design

**Temporal holdout at T = 2026-06-01.** The agent sees only evidence dated at or
before T. Labels are computed only from evidence after it. T sits just past the
models' training cutoff so that the label window falls outside training data;
moving T earlier would drag the label window *into* it, which is the leak that
actually matters.

**The pool is sampled from history, not from today.** GitHub search returns
today's stars and today's activity whatever date filter you apply, so a pool
drawn from it is pre-filtered for repositories that survived. Holt's pool is
sampled from GH Archive events over three contiguous days before T — repositories
as they appeared at the cutoff, with no knowledge of which lived. **Three of the
thirty were deleted before the run**; a search-based sample would have silently
excluded all three.

**Three things about the pool, stated rather than buried:**

- `is-a-dev/register` was **drawn, not placed**. The seed (`20260601`) is
  committed and the draw is verifiable by re-running `eval/sample_pool.py`.
- The busiest volume band drew **6 of 8 available** — a near-census, not a
  sample. "Stratified random" is accurate for three bands and approximately
  exhaustive for the fourth.
- The universe is **1,674 of 40,731** repositories, filtered to those with at
  least two distinct human pull request openers. A repository with one opener
  carries no outsider signal at all.

**The pool is hash-committed** (`eval/pool.json`, sha256 `f100b2209c…`) and was
never edited after results were seen.

**Labels are computed, never hand-judged**, and shipped in two versions. L0 is
the naive outsider merge rate. L1 adds bot exclusion, a diff-shape filter and a
human-review requirement. Both are run; the gap between them is in the changelog.

---

## Deliberate non-uses

A documented non-use is a judgement, not an omission.

- **No memory or vector store.** Each assessment is independent; there is nothing
  to carry between them that the evidence provider does not already hold.
- **No multi-provider abstraction.** One model is pinned per stage. Portability
  would move variance into the number being reported.
- **No personal fit or skill matching.** No ground truth exists for "will this
  developer enjoy this", so it cannot enter the holdout, so it cannot contribute
  to a measured claim.
- **Stage C's thread signals are computed but excluded from the verdict.**
  Measuring them showed they are inverted — see the changelog.

---

## Known limitations

- **22 of 30 repositories graded.** Three were deleted between the cutoff and
  the run; five had no post-cutoff outsider attempts to grade against.
- **Single run.** Variance across repeated runs is not measured.
- **The memorisation probe reaches 0.71 precision knowing only repository
  names.** Some of every method's score here is recognition rather than reading.
  Its recall is 0.36, which bounds how much.
- **Three repositories sit at GitHub search's 1000-result ceiling**, so their
  label figures are a sample rather than a census. An API boundary, not a choice.
- **Star counts are as-of-fetch, not as-of-cutoff.** GitHub exposes no historical
  count. Only the popularity diagnostic reads them.
- **Absence of merged outsider code is not proof of hostility**, and a good
  project can have a quiet quarter. The three-month label window makes this
  sharper than a longer one would.
- **`Homebrew/homebrew-cask` is a genuine disagreement**, not a bug: Holt calls
  it a registry, the label counts eleven qualifying merges. Casks are Ruby files.
  Neither side was tuned to agree with the other.

---

## Provenance

Everything in this repository was written during the competition, apart from the
problem statement in `docs/`. No credentials ship with it: the headline result
reproduces with no API key and no GitHub token.

The evaluation design responds to *The Benchmark Ceiling: Human Judgment,
Evaluation Scarcity, and the Political Economy of AI Capability Measurement*
([arXiv:2607.01254](https://arxiv.org/abs/2607.01254)), which argues that
discriminating signal concentrates in hard-tail items while fixed metrics
degrade under strategic optimisation. L0 is such a metric and L1 is the hard-tail
reconstruction; the aggregate scores tie while the hard cases separate cleanly,
which is the shape that argument predicts.
