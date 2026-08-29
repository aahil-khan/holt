# Holt — where we stand, and where we could go

Written 2026-08-30. Deadline 2026-08-31 23:30.

---

## 1. What exists

12 commits, 46 tests, ~3,000 lines. Reproduces from a clean clone with no
credentials, verified by actually doing it.

| Deliverable | State |
|---|---|
| Code + Improvement Changelog | done — 319-line changelog, entry per experiment including removed ones |
| Reproduction guide | done — every command run with all keys unset before being written down |
| Agent trajectories | done — 3 rendered walkthroughs + 29 raw JSONL records |
| Video ≤5 min | **not started** (yours) |

The pipeline: evidence chokepoint enforcing a temporal holdout → arithmetic
signals → three model stages → verification that drops unsupported claims →
a deterministic verdict function → narration that cannot change the verdict.

---

## 2. What the numbers actually say

Ground truth is L1: at least two distinct people landing a qualifying
contribution *after* a cutoff neither method could see. 22 of 30 pool
repositories are gradable (3 deleted, 5 had no post-cutoff attempts).

| Method | F1 | Balanced acc. | **MCC** | Sensitivity | Specificity |
|---|---|---|---|---|---|
| always answer "viable" | 0.78 | 0.50 | **0.00** | 1.00 | 0.00 |
| name-only probe | 0.48 | 0.55 | 0.11 | 0.36 | 0.75 |
| baseline solution | 0.74 | 0.67 | 0.33 | 0.71 | 0.62 |
| **Holt** | 0.84 | **0.71** | **0.49** | 0.93 | 0.50 |

**The most important line in this document:** a constant classifier that answers
"viable" to everything scores **F1 0.78** — beating our baseline solution's 0.74.
F1 is degenerate on a pool that is 64% positive. Anyone from an evaluation lab
will notice this in under a minute, and if we ship F1 as the headline they will
notice it before we do.

MCC is the honest metric here: it is 0.00 for any constant classifier. **Holt 0.49
against the baseline's 0.33** is a genuine 48% relative improvement that no
trivial strategy can fake.

**Ablation — what is actually doing the work:**

| Configuration | F1 |
|---|---|
| full Holt | 0.84 |
| without Stage A's repository-kind rules | 0.82 |
| without the arithmetic signal thresholds | 0.79 |
| neither (everything viable) | 0.78 |

On F1 the whole pipeline buys 0.06 over answering yes to everything. On MCC it
buys 0.49 over 0.00. Same system, same data — the metric was the problem, and
we have to say so ourselves.

---

## 3. Honest rubric estimate

My own scoring, stated so it can be argued with.

| Criterion | Points | Estimate | Why not full marks |
|---|---:|---:|---|
| Agent Solution & Engineering | 30 | ~22 | Stage C is decorative — see §4 |
| End-to-End Quality | 20 | ~16 | Reports read well; no video yet |
| Problem & User Value | 15 | ~13 | Clear user, real bottleneck, measured |
| Measured Improvement | 15 | ~10 | Single run, no variance; margins thin |
| Reproducibility | 15 | ~14 | Clean-clone verified, zero-credential |
| Hot Take / Insights | 5 | ~4 | Genuine, unglamorous, measured |
| | **100** | **~79** | |

---

## 4. The three real weaknesses

### 4.1 The flagship stage does not affect the answer

Holt's pitch is that it *reads pull request threads*. Stage C does read them, and
its output appears in every report. But `verdict.py` never consults it — because
when measured, its signals were **inverted**: repositories that are not genuine
opportunities showed a *higher* share of threads offering a real route in (0.75
against 0.54), since registries read as welcoming precisely by being easy.

Excluding it was the right call on the evidence. But it leaves the most expensive
stage, and the one the story leans on hardest, decorative. A judge who reads
`verdict.py` will see three model stages feeding a function that reads one of
them. That is the single largest gap between what the project claims and what it
demonstrably does.

There is one thread-derived feature that *does* separate the classes:
**review ratio** — the share of merges that received substantive review rather
than sailing through (0.68 for genuine opportunities against 0.50 for the rest).
Structural rather than sentimental. It is the obvious candidate for making Stage
C load-bearing, and it is untested.

### 4.2 Holt over-recommends

Specificity 0.50 against the baseline's 0.62. It calls 17 of 22 viable and is
wrong on 4. Its advantage is entirely in *finding* opportunities (sensitivity
0.93 vs 0.71), not in rejecting bad ones — except on the extreme cases, where it
rejects 4 of 5 traps and the baseline rejects none.

### 4.3 Single run, and a quarter of the pool ungraded

Every number is one run; the plan itself said report variance rather than one
lucky number. 22 of 30 graded: 3 repositories were deleted, 5 had no post-cutoff
attempts. Both are honestly disclosed, neither is fixable, but together they mean
the sample supporting every claim is small.

---

## 5. Where this could go, ranked by payoff per hour

| # | Move | Effort | Payoff |
|---|---|---|---|
| 1 | **Reframe the metric, and publish the trivial baselines** | 2h | High — turns the biggest vulnerability into an honesty credential |
| 2 | **Variance across three runs** | 40m | High — closes a stated expectation for ~$1 |
| 3 | **Make Stage C load-bearing via review ratio** | 3h | High but uncertain — could lift specificity and close §4.1 |
| 4 | **Positive control** | 1h | Medium — guards against a detector that rejects everything |
| 5 | **Human-time measurement** | yours | Medium — the brief asks for it and only you can produce it |
| 6 | **Video** | yours | Required |

### On #1, which I would do first regardless

Replace F1 with MCC as the headline, and publish the constant-classifier row in
the README. "Our original primary metric was degenerate; here is the trivial
strategy that beats our own baseline on it; here is the metric that cannot be
gamed and the result under it" is a stronger position than any number we could
report, in front of judges whose profession is measurement validity.

### On #3, the one with real upside

If review ratio makes Stage C load-bearing, three things improve at once: the
flagship stage stops being decorative, specificity likely rises, and the
changelog gains its best arc — *tried sentiment, it inverted, refined to a
structural signal, it worked*. If it does not help, that is also publishable and
costs one entry.

**Risk to manage:** the feature is measured on the same 22 repositories we score
on. Fitting it there and then reporting the improvement would be tuning on the
test set. It has to be justified on the dev set or on a stated principle, and the
fitting has to be disclosed either way.

---

## 6. What I need from you

1. **Which of #1–#4 to run**, and in what order. My recommendation: 1, 2, 3, 4.
2. **The human-time number** — time yourself reading twenty pull request threads
   on one pool repository. Holt takes 69 seconds. That comparison is the most
   legible thing in the submission and only you can produce it.
3. **Whether to spend anything further.** Total spend so far is $0.35. Variance
   runs cost about $1. Nothing else needs money.
