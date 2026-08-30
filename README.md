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
stars. **Stars are not useless** — on this pool the ten most-starred repositories
are 80% viable against a 51% base rate, and we say so because we measured it.
What stars cannot do is separate the registry, the mirror and the links list from
the software project, and that is exactly the population this tool exists for. It
is also the only comparison here that reaches significance: **4 of 5 traps
rejected against the baseline's 0 of 5**, exact p = 0.048.

Two closed pull requests are the same integer in every GitHub statistic:

> "Thanks for this! Merged in #4821 — could you also look at the sibling case?"

> "We're rewriting this module internally, closing."

One says a newcomer can land work here. The other says don't bother.

---

## "Why not just paste it into ChatGPT?"

The fair answer is that **we measured that, and it is a scored arm in the
evaluation.** `baseline` is one prompt over the README and the repository
metadata, which is what a person actually pastes. `probe` is the repository name
alone with no evidence at all, which is what asking a chat model from memory
gets you.

| What you did | MCC |
|---|---|
| Asked a model that already knows the repo, name only | 0.16 |
| **Pasted the README and the numbers into one prompt** | **0.28** |
| Ran Holt | **0.46** |

**The premise is where the work hides.** "The same GitHub information" is not
pasteable. Per repository, Holt assembles a median of **642 evidence records and
253,000 characters** across **200 pull-request conversations** — a **44×** ratio
against the ~11,900 characters of README, CONTRIBUTING and landing-page numbers a
person can realistically copy. Seeing it by hand means opening about **202
github.com pages**; across this evaluation, **11,636**. Reproduce with
`PYTHONPATH=. uv run python eval/evidence_volume.py`.

And the pasteable material is not a smaller sample of the same thing. It contains
**no review states, no reply latencies, and no record of what happened to anyone
who tried** — which is the entire question.

Four properties follow from being a pipeline rather than a conversation, none of
which a chat transcript has:

- **Provable claims.** Every statement carries an evidence id; 696/696 resolve to
  a real thread. A chat answer cannot be checked without redoing the work.
- **A bounded, honest horizon.** Every fact passes a cutoff assertion, so the
  answer cannot come from what the model remembers. We also bound what memory
  alone buys: **MCC 0.16**.
- **The same answer twice.** Holt returns identical verdicts on 21 of 22
  repositories across three runs. The one-prompt baseline manages 13 of 22.
- **It says no.** A written, versioned rejection rule rather than an agreeable
  paragraph — and it is the one change that measurably improved accuracy
  (specificity 0.58 → 0.83, out of sample).

**What Holt is not is a better analyst.** We have measured four separate times
that the model layer adds nothing over arithmetic, and we publish each one below.
The value is in assembly, provability, determinism and refusal.

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

## What the orchestration buys

Four things follow from splitting this into stages rather than asking one model
one question. Each is stated with the measurement that supports it, and the
section after this one states what the split does **not** buy.

**1. A rejection rule that no single prompt can hold.** Holt rejects a repository
when contributions land *easily* and nobody reviews them — high merge rate, almost
no human review. That is a project where a stranger's pull request is waved
through into something nobody maintains, and it looks identical to a healthy
project on every signal GitHub displays. The rule lives in `verdict.py` as two
constants, it was **pre-registered with numeric predictions before it was run**
(`eval/PREREGISTRATION-2.md`), and it was validated on the second pool, which had
never been used to develop it:

| | before the rule | after |
|---|---|---|
| Specificity, pool 2 (out of sample) | 0.58 | **0.83** |

All three pre-registered predictions held. Specificity is the thing Holt exists
to provide — saying *no* — and before this rule it was a coin flip.

**2. Re-answering the question costs nothing.** The contributor's time budget is a
parameter: `holt analyze <repo> --days 3` and `--days 90` are different questions
with different answers. Because every time-shaped threshold is derived inside
`verdict.py` and the model output is unchanged, **re-running with a different
budget makes zero model calls**. A single prompt has to be re-asked, re-billed,
and may return a different verdict for reasons unrelated to the change.

**3. The model never owns the decision — and this is the one that measurably pays.**
`src/holt/agent/verdict.py` is the only path from findings to a verdict and runs
no model. Across three runs Holt returns identical verdicts on **21 of 22**
repositories; the baseline, which puts the whole decision inside one model call,
on **13 of 22**.

**4. Arithmetic where arithmetic works.** Counting landings and measuring reply
latency are not model problems. *But the arithmetic thresholds never bind on this
pool*: setting `MIN_MERGES` and `MIN_DISTINCT_AUTHORS` to zero leaves all 22
verdicts and the confusion matrix unchanged. They are guardrails that this
sample never tested.

Two further properties, both structural rather than accuracy-improving:

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

## What the orchestration does not buy

Everything above is what the split earns. This is what it does not, and it is
published because a claim about the first is worth nothing without the second.

**The pipeline's measurable contribution to accuracy is small**, and an ablation
that removes the orchestration entirely — one prompt over the *same* signals and
the *same* evidence digest — reaches the same MCC as the full pipeline on pool 2
(0.42 = 0.42). The stages buy determinism, reparameterisation, auditable
citations and a rejection rule with a written threshold. They do not buy raw
accuracy on this evidence, and we are not going to claim they do.

**Ablating the pipeline, in MCC**, holding recorded model output fixed and
varying only `verdict.py`:

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

**And Path Finder, which we shipped losing.** Ranking issues by how likely an
outsider is to land a merged fix scores precision@3 of 0.173 against GitHub's
`good first issue` label at 0.187 over 25 repositories — indistinguishable, and
its own pre-registered cut condition. It ships because 13 of those 25
repositories carry no beginner-labelled issue at all, and because **the tool
prints that result in its own output next to the ranking**, not here. Run
`holt analyze NixOS/nixpkgs --replay` and read the "Where to start" section.

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

---

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

**L1 counts programme-cohort review as review.** Nine repositories in the pool
are GirlScript Summer of Code '26 projects with a points leaderboard — grep
`gssoc` in `fixtures/post_t/leonagoel__hybrid-recommender.json` and you will find
1,605 mentions. Leaderboard-driven pull requests are substantive by our diff-shape
filter and mentors do comment on them, so those repositories label as viable.
"A stranger's patch lands here" is *true* of them. Whether a week spent there is
the opportunity this tool is meant to find is a separate question our ground truth
does not ask, and we did not discover this until it broke a different experiment
(`eval/mover_controls.py`). The labels are hash-committed and were not touched
after the fact.

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
