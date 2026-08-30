# Pre-registration 3 — personalised contribution discovery

Written **2026-08-30, before any implementation exists**. Nothing in this file was
edited after a number was seen. The two earlier pre-registrations
(`PREREGISTRATION.md`, a rule that failed; `PREREGISTRATION-2.md`, one that
worked) follow the same discipline.

---

## The question

Not *"which issues in this repository are approachable?"* — that is what
`good first issue` already answers, and our own evaluation
(`PATHFINDER-DESIGN.md`) shows we do not beat it.

Instead: **given what this person has already merged here, which open issues are
a sensible next step for them?**

The problem is one contributors actually hit. Completing a beginner issue is the
easy part. The progression from there into larger work is unmarked: nothing tells
you *you touched this, so you now understand that, so these are the next things
you could take*. No label encodes it, because it is not a property of the issue —
it is a property of the pair.

**Why the prototype failed, stated before building its replacement.** `find_paths`
never sees the contributor. It emits one ranking for everybody, so it is
structurally answering the label's question, and tying the label is the expected
outcome of that. It is kept as the contributor-blind ablation below.

---

## A confound found before building, which would have faked a win

Of the 655 issues open at T that a pre-existing contributor later closed with a
merged pull request, **299 — 46% — were issues that same person had opened
themselves.**

Predicting that someone will fix the bug they filed is not a recommendation. The
intent is already legible in pre-cutoff evidence, so any ranker that noticed
"this person wrote this issue" would score a large, meaningless win. Had this
gone unchecked it would have been the `good first issue` mistake a second time:
a comparator-shaped artefact mistaken for a result.

**The primary analysis excludes self-opened issues from both the label and the
candidate set.** The full set is reported as a secondary line, labelled.

---

## Evaluation unit

One **(repository, contributor)** pair. The contributor merged at least one pull
request in that repository before T.

| | |
|---|---|
| Pairs with ≥1 pre-T merge | 1,022 |
| **Scorable** (≥1 realised next issue, self-opened excluded) | **126** |
| Realised resolutions in the primary set | 356 |
| Repositories represented | 29 |
| Largest single repository's share | 20/126 (16%) |
| Median candidate issues per pair | 182 |
| Median pre-T merged PRs per contributor | 2 |
| Median pre-T distinct files touched | 7 |

Pairs with **no** realised next issue are excluded, declared here and not after:
precision is identically zero there for every method including the comparators,
so they add nothing but a constant. The 126/1,022 rate is itself reported.

---

## Temporal split

Unchanged: **T = 2026-06-01**, enforced by assertion in `EvidenceProvider`.

The ranker sees only pre-T evidence — the contributor's merged pull requests,
their file lists, the review threads on them, and the issues open at T. The label
uses only post-T evidence. No new crawl is required; both windows are already
captured and committed.

Known leak, already measured: **2.6%** of issue bodies were edited after T
(95/3,613).

---

## Ground truth

An issue is a **realised next contribution** for contributor *c* if:

1. it was open at T,
2. it was **not opened by *c***,
3. it was later closed by a merged pull request **authored by *c***.

Mechanical, binary, computed from `closing_prs`. **Resemblance is not used.**
A similarity threshold chosen after seeing results is the same post-hoc move
pre-registration exists to prevent; "did this person actually resolve this exact
issue" needs no threshold.

---

## Metrics

Base rates, arithmetic from the candidate sets, computed before any method exists:

| | random |
|---|---|
| precision@3 | 0.024 |
| hit@3 | 0.066 |
| **hit@10** | **0.175** |

**Primary: hit@10** — the fraction of contributors for whom at least one of the
top ten was an issue they actually resolved. Chosen for the reason stated here
and not afterwards: at a mean base rate of 2.4%, precision@3 puts almost every
pair at 0.000 for every arm, and a metric that is constant across arms cannot
separate them. Ten of ~182 is a shortlist a person would actually read.

**Secondary: precision@3**, reported always, whichever way it falls.

Paired over the 126 pairs: bootstrap 95% CI on the difference, plus an exact
two-sided sign test over non-ties. Reported for every arm, not only the flattering
ones.

---

## Arms

| | What it is |
|---|---|
| `random` | The base rate. 0.175 at hit@10 by construction. |
| `recency` | Newest open issue first. |
| **`path_overlap`** | **The bar.** Issues naming a file or directory the contributor has already touched, first; recency within each group. |
| `blind` | The existing contributor-blind `find_paths`, unchanged. Isolates the entire claim: **does knowing who is asking help at all?** |
| `holt_arith` | Declared-weight scoring over the features below. **No model call.** |
| `holt_full` | Same features, plus one LLM-derived competence term. |

### The comparator coverage check we failed to run last time

`good first issue` looked like a comparator and was recency wearing its name on
two thirds of the pool. So, before adopting `path_overlap`:

| | |
|---|---|
| Pairs where it matches nothing (degenerates to recency) | 38/126 → 20% of the wider set |
| Pairs where it matches everything (also degenerates) | 3% |
| **Pairs where it genuinely partitions the candidates** | **77%** |
| Median share of candidates matched | 13% |

It is a real comparator with real signal, and a strong one: 68% of returning
contributors touched a directory they already knew. **Beating random is not the
claim. Beating this is.**

---

## The ranking signal is separate from the explanation

The score is a **transparent weighted sum, with weights fixed here and never
fitted to the outcome**:

| Feature | Weight |
|---|---|
| `file_hit` — issue names a file the contributor has edited | 3.0 |
| `profile_hit` — issue matches an LLM-derived competence area (`holt_full` only) | 2.5 |
| `dir_hit` — issue names a directory they have worked in | 2.0 |
| `thread_reviewer` — someone who reviewed their work is active on this issue | 1.5 |
| `lang_hit` — issue names a file of a type they have edited | 1.0 |
| `scope_step` — issue's size band is at or one above their median merged PR | 1.0 |
| `actionable` — issue names any concrete path | 0.5 |
| `discussion` — `min(comments, 5) / 5` | 0.5 |

Ties broken by recency. **The model cannot reorder anything.** In `holt_full` it
produces one structured competence profile per contributor from their merged pull
requests and the review feedback on them, which feeds exactly one term; a second
call writes the prose for the top *k* only. `--why` prints the feature vector, so
a reader can see what caused a rank rather than trusting a paragraph.

This makes `holt_full` vs `holt_arith` a clean test of the project's central
question — **does the model add anything over arithmetic?** — on a task where,
unlike the verdict, arithmetic is not obviously sufficient.

---

## Predictions, written before running

hit@10 on the 126 primary pairs:

| Arm | Predicted |
|---|---|
| `random` | 0.175 (arithmetic, fixed) |
| `recency` | 0.22 |
| `blind` | 0.25 |
| `path_overlap` | 0.32 |
| `holt_arith` | 0.38 |
| `holt_full` | 0.42 |

Also predicted: `holt_full` beats `blind` by more than it beats `path_overlap`
(personalisation matters more than model quality), and the advantage is larger on
the 50/126 pairs with ≥3 pre-T merged pull requests than on the thin-history rest.

---

## Decision rule

**`holt_full` must exceed `path_overlap` by ≥ 0.05 absolute on hit@10, with an
exact sign test p < 0.10 over non-tied pairs.** Anything less is a tie and is
reported as one.

## Cut conditions, binding

1. ~~`path_overlap` degenerates on most pairs~~ — **checked, passed: 77%.**
2. `holt_full` does not clear the bar above → **cut**, and the negative result is
   published in `CHANGELOG.md` exactly as Path Finder's was.
3. `holt_full` does not beat `holt_arith` → the model adds nothing; ship the
   arithmetic ranker alone and say so in the output.
4. Not finished with **8 hours to the deadline** → stop, publish this document and
   whatever ran. The frozen benchmark and the credential-clean reproduction path
   are done and must stay done.

---

## Threats, listed before they can be excuses

**Thin history is the real risk.** The median contributor has 2 merged pull
requests and 7 touched files. There may simply not be enough of a footprint to
personalise against. Declared in advance: results are reported split by history
depth (≥3 pre-T merges, 50 pairs, versus the rest), whichever way it falls.

**Repository concentration.** One repository holds 20 of 126 pairs. Per-pair
averaging, never pooled.

**Survivorship.** Contributors who left between T and the crawl cannot appear as
positives. This biases every arm equally, and is why arms are compared to each
other rather than to an absolute.

**Post-cutoff issue edits.** 2.6%, measured, unchanged by this experiment.

---

## Cost and blast radius

~250 model calls on the small model, **≈ $0.30**. No crawl. New files only:
a label module, a harness, a ranker. **Nothing in the verdict pipeline, no
recorded trajectory, no committed benchmark, and no part of the reproduction path
is touched.**
