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
the software project, and that is exactly the population this tool exists for.
On the trap repositories — 100+ inbound attempts, zero qualifying
contributions — Holt rejects **4 of 5 in every run we have ever recorded**; the
baseline has scored anywhere from 0 to 3 of 5 depending on the day it was asked.

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

| What you did | MCC (pool 1) | MCC (pool 2, out of sample) |
|---|---|---|
| Asked a model that already knows the repo, name only | 0.16 | 0.10 |
| **Pasted the README and the numbers into one prompt** | **0.09** | **0.21** |
| Ran Holt | **0.61** | **0.63** |

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

- **Provable claims.** Every statement carries an evidence id that resolves to a
  real thread, and every quotation is words that thread actually said — 9 claims
  across the committed runs quoted something it did not, and were dropped rather
  than softened (`eval/evidence_integrity.py`). A chat answer cannot be checked
  without redoing the work.
- **A bounded, honest horizon.** Every fact passes a cutoff assertion, so the
  answer cannot come from what the model remembers. We also bound what memory
  alone buys: **MCC 0.16**.
- **The same answer twice.** On the frozen runs Holt returned identical
  verdicts on **55 of 55** repositories across three runs per pool. The
  one-prompt baseline changed its answer on 16 of them.
- **It says no.** A written, versioned rejection rule rather than an agreeable
  paragraph — and it is the one change that measurably improved accuracy
  (specificity 0.58 → 0.83, out of sample).

**What Holt is not is a better analyst.** We have measured four separate times
that the model layer adds nothing over arithmetic, and we publish each one below.
The value is in assembly, provability, determinism and refusal.

---

## Result

Measured over two pools drawn and hash-committed **before any method ran**,
against ground truth computed only from evidence *after* a temporal holdout
neither method could see. Three independent live runs per pool, frozen
2026-08-31 on the shipped prompts and rules; every number below reproduces
from the committed recordings with no key and no spend.

**Pool 1** (30 repositories, 22 gradable):

| Method | MCC | Balanced acc. | F1 | Sensitivity | Specificity |
|---|---|---|---|---|---|
| always answer "viable" | 0.00 ±0.00 | 0.50 | **0.78** | 1.00 | 0.00 |
| name-only probe (memorisation control) | 0.16 ±0.03 | 0.58 | 0.52 | 0.40 | 0.75 |
| baseline solution (one prompt over README + metadata) | 0.09 ±0.09 | 0.55 | 0.63 | 0.60 | 0.50 ±0.12 |
| **Holt** | **0.61 ±0.00** | **0.80 ±0.00** | 0.86 ±0.00 | 0.86 ±0.00 | 0.75 ±0.00 |

**Pool 2** (45 repositories, 33 gradable — drawn, labelled and held out *after*
every rule was written; genuine out-of-sample replication):

| Method | MCC | Balanced acc. | F1 | Sensitivity | Specificity |
|---|---|---|---|---|---|
| name-only probe | 0.10 ±0.02 | 0.55 | 0.47 | 0.35 | 0.75 |
| baseline solution | 0.21 ±0.02 | 0.61 | 0.60 | 0.49 | 0.72 ±0.04 |
| evidence-matched ablation (same evidence, one prompt) | 0.32 ±0.07 | 0.65 | 0.78 | 0.83 | 0.47 ±0.04 |
| **Holt** | **0.63 ±0.00** | **0.82 ±0.00** | 0.85 ±0.00 | 0.81 ±0.00 | **0.83 ±0.00** |

Mean and half-range over the three runs. **Holt's half-range is ±0.00 because
its verdicts were identical on all 55 repositories in all three runs** — the
verdict is a plain function over verified evidence, so re-running it moves
nothing. The baseline changed its answer on 16 of 55.

**Those intervals measure the wrong thing, and we are saying so.** ±0.00 is how
much the model wobbles between runs; it is not how much a 22-repository sample
can tell you. Measured over repositories instead — bootstrap resampling, 20,000
draws, pool 1 — the Holt−baseline difference is **+0.42 to +0.59 with
`P(difference ≤ 0)` = 0.04–0.08, and a 95% interval that still touches zero**.
Exact McNemar gives p = 0.15–0.23. At this sample size the aggregate gap is
large but not formally distinguishable, and we print that rather than round it
up. Run `PYTHONPATH=. uv run python eval/stats.py` to see it.

- **Trap rejection — including the part that got worse for us.** Repositories
  with 100+ inbound outsider attempts and zero qualifying contributions: Holt
  rejects **4 of 5 in every run** (it has never caught `hermes-agent`). When
  this was first measured, the baseline rejected 0 of 5 (Fisher exact
  p = 0.048); on the frozen re-runs the baseline rejected **2–3 of 5**, so that
  significance claim did not survive re-measurement and we are retiring it
  rather than citing the old number. What remains is the stable version: Holt
  4/5 every time, a baseline that wanders between 0 and 3 depending on the day.
- **Positive control.** Three verified-genuine repositories outside the pool:
  Holt recovers 3 of 3, the baseline 1 of 3.

**The constant answers are in that table on purpose.** F1 was this project's
original primary metric, and on a pool that is 64% positive it is degenerate:
answering "viable" to everything scores **F1 0.78**, beating our own baseline
solution. We found that by attacking our own metric before shipping it, and the
row stays in so a reader can see the floor rather than take our word for it.

Matthews correlation is the honest headline, because it is **0.00 for any
constant strategy**. Holt reaches 0.61 against the baseline's 0.09 in sample
and **0.63 against 0.21 out of sample** — and the out-of-sample gap is the
wider one, because pool 2 skews toward quieter repositories where a README
tells you nothing.

**Where the advantage is now.** Earlier versions of this table showed Holt
over-recommending: specificity 0.50, a coin flip on ordinary repositories. The
pre-registered rubber-stamp rule — *contributions land easily and nobody
reviews them* — was written against pool 1, predicted numerically, then tested
once on pool 2: specificity moved to **0.75 in sample and 0.83 out of sample**
at a cost of a few points of sensitivity (0.86/0.81 against 0.90 before),
exactly the trade the pre-registration predicted. The ablation row shows what
it is worth: given the identical evidence in one prompt, specificity is 0.47.
The rule is the difference between flagging a registry and recommending it.

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
no model. Across three runs Holt returns identical verdicts on **22 of 22**
repositories; the baseline, which puts the whole decision inside one model call,
on **17 of 22**.

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

## What the report tells you that GitHub does not

**Where outsider work actually landed.** Every pull request Holt reads carries its
file list. That list decided whether a diff counted as substantive and was then
thrown away; now it is counted. For `NixOS/nixpkgs`:

> - **`pkgs/by-name`** — 13 merged of 62 attempted (21%)
> - **`pkgs/top-level`** — 3 merged of 11 attempted (27%)
>
> Outsiders attempted these and none were merged: `maintainers/maintainer-list.nix`
> (11), `pkgs/applications` (6), `pkgs/build-support` (6), `doc/release-notes` (2).

In a tree of that size, that is where a stranger's week has a chance and where it
does not. GitHub does not show it, `CONTRIBUTING` does not say it, and no amount
of star-counting implies it. **It ranks nothing and predicts nothing** — after five
capabilities cut for losing to a cheap comparator, a section that makes no claim
is a deliberate choice. An attempt counts once per pull request rather than once
per file; only outsiders count, decided per thread in time order; and a directory
is named as "never landed" only when at least two people tried.

**A shortlist, not one repository.** Nobody is deciding about a single project.

```
$ holt compare runelite/plugin-hub NixOS/nixpkgs is-a-dev/register stablyai/orca --replay

| repository          | verdict    | outsiders in | first reply | why
| runelite/plugin-hub | not_viable | 70/101       | 4.2h        | repo_kind=registry: merged work here is…
| NixOS/nixpkgs       | viable     | 15/100       | 0.8h        | 15 first-time merges by 15 distinct people…
| is-a-dev/register   | not_viable | 35/191       | 12.3h       | repo_kind=registry: merged work here is…
| stablyai/orca       | viable     | 4/7          | 0.3h        | 4 first-time merges by 4 distinct people…
```

The `why` column is **the rule that fired**, not a summary of the prose, so the
comparison is on the deterministic part. Rows come out in the order you asked for;
it sorts nothing, because sorting is a claim.

`runelite/plugin-hub` is the row that makes the case: 70 of 101 outsiders merged,
replies in 4.2 hours — the best-looking project on the list — and it is rejected,
with the reason in the same row.

**If you have no shortlist yet,** `holt discover` builds one from a stated
profile — languages, topics, what you want to contribute, how many days you
actually have. Ask once with `holt profile`, or pass flags. Candidates come from
GitHub repository search; Holt claims the *screening*, not the sourcing or the
ordering, and the screening is free: `verdict.py` needs exactly one
model-derived input, so every rejection rule runs as arithmetic at $0.00.

```
$ holt discover        # replays the recorded demo session; no token, no key

Screened 25 candidates … Rejected 9:
- 3 nobody outside has landed work in
- 2 outsider attempts went unanswered
- 2 work merged without review (the rubber-stamp rule)
- 2 replies too slow for a 7-day budget

| repository    | verdict               | outsiders in | first reply |
| tqdm/tqdm     | insufficient_evidence | 26/179       | 1128.2h     |
| fastapi/typer | viable                | 7/48         | 14.9h       |
| beetbox/beets | viable                | 33/87        | 9.1h        |
|   ↳ tests: outsider work has merged in `test` (26 merged)
```

Screening reads only the newest page of threads, so its numbers are noisier than
the benchmark's — the recorded session shows the disclosure earning its keep:
`tqdm/tqdm` survived shallow screening and flipped to insufficient at full
depth, where the median first reply turned out to be 1,128 hours. Model spend
for the whole session: $0.08, all of it on the five survivors.

**Once you have landed work somewhere,** `holt next <repo> --as <your-login>`
ranks the open issues by one deterministic rule: issues naming a file or
directory you have already touched come first, newest first, then the rest by
recency. No model call. The rule ships because it is the best of five methods we
measured — hit@10 0.234 against 0.211 for a weighted eight-feature scorer that
was cut for losing to it, 0.188 for recency, 0.172 for chance — and the output
prints that measurement, including the 95% interval [−0.003, +0.132] that spans
zero, with every ranking. Each row says which path tokens overlapped, or that
none did.

## What the orchestration does not buy

Everything above is what the split earns. This is what it does not, and it is
published because a claim about the first is worth nothing without the second.

**The model stages' measurable contribution to accuracy is tiny, and we can now
say precisely where the accuracy lives.** When this was first measured — before
the rejection rule shipped — one prompt over the *same* signals and the *same*
evidence digest matched the full pipeline exactly (0.42 = 0.42 on pool 2). On
the frozen runs the pipeline leads that same-evidence ablation by a wide margin
(0.63 against 0.32 ±0.07 out of sample), and the difference is **not the model
stages getting smarter — it is the deterministic verdict layer**, where the
pre-registered rubber-stamp rule now lives. A prompt can be handed the same
evidence; it cannot be handed a rule it is structurally unable to override, and
the ablation's specificity (0.47, against the pipeline's 0.83) is what that
costs it.

**Ablating the pipeline, in MCC**, holding the frozen model output fixed and
varying only `verdict.py`:

| Configuration | MCC |
|---|---|
| full pipeline | +0.61 |
| Stage A repository-kind rules disabled | +0.60 |
| arithmetic thresholds set to zero | +0.61 |
| both disabled | +0.60 |

The model stages and kind rules are now worth **+0.01 MCC** over the arithmetic
alone — even the registry catch has migrated into the rubber-stamp rule, which
rejects a registry for the same reason a model would: work waved through
unread. The stages still buy what a rule cannot: the evidence a claim cites,
the prose a person reads, and `repo_kind` for the reports where naming the
category matters.

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

**The ground truth is our own definition.** L1 keeps an outsider merge only if
the diff is *substantive* and a human *reviewed* it — both filters chosen by
us, so the honest question is what happens when either is dropped. On the
earlier recorded runs this was a real vulnerability: dropping `substantive`
flipped the advantage to the baseline. On the frozen runs it no longer does —
Holt leads under **every** variant, though the margin narrows to +0.11 at its
thinnest. Mean MCC over the three frozen runs:

| Ground truth | Positives | Holt | Baseline |
|---|---|---|---|
| L1 as shipped | 14/22 | **+0.61** | +0.09 |
| drop the `reviewed` filter | 16/22 | **+0.60** | +0.01 |
| drop the `substantive` filter | 16/22 | **+0.39** | +0.28 |
| drop both (≈ the naive L0) | 18/22 | **+0.38** | +0.22 |

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
- **No provider variance in the numbers.** Every benchmark figure was measured
  under one pinned, dated model per stage, and the eval path resolves those ids
  unconditionally — a test proves it ignores any user configuration on disk.
  The *product* does let you choose (`holt models`: other OpenAI models, Claude,
  Ollama, Gemini, any OpenAI-compatible endpoint), and its own output warns that
  committed recordings replay only under the defaults. The line we hold is that
  portability must never move variance into a number being reported.
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

---

## The main failure mode, and the hot take

**The failure mode: nothing was watching whether a published claim was still
true.** Every guard in this project points at the agent — the holdout is
asserted on every record, Stage D drops a citation that does not resolve, replay
refuses a recording whose prompt moved — and each is covered by a test. None of
them guarded the prose. So a number stayed on this page after the run behind it
was redone, and this repository stated its own verdict stability three different
ways at once. Worse, `holt analyze <repo> --baseline --replay` — documented, and
the competition's required baseline arm — failed from a clean clone on every
repository, because baseline calls were recorded only where the harness looks
and the benchmark therefore never noticed. The evaluation and the documented
product path had drifted apart, and only the evaluation was tested.
`tests/test_docs_claims.py` now recomputes the numbers on this page from the
committed results and runs every command the guide prints.

**The hot take: Holt is not a smarter analyst, and we measured that four separate
times.** One prompt handed the same evidence matches the model stages almost
exactly; ablating Stage A's kind rules costs +0.01 MCC. What separates this from
a chat window is duller than intelligence and harder to fake — an evidence
assembly nobody will do by hand (642 records and 253,000 characters per
repository, 44× what a person can paste), and then three properties a
conversation structurally cannot have: every claim carries an id that resolves,
the verdict is a plain function that returned the identical answer on 55 of 55
repositories while the baseline moved on 16, and it can say *no* in a rule the
model cannot override — the single change that most improved accuracy
(specificity 0.58 → 0.83 out of sample).

**What we would build differently:** put the decision in code and the model in
front of the evidence, not the other way round — then spend what that saves on
the boring half, because an agent's guarantees are worth exactly as much as the
tests on the claims you make about them.

The full story, iteration by iteration: [CHANGELOG.md](CHANGELOG.md).
