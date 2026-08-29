# Holt — honest assessment

Revised 2026-08-30, after the metric reframe, the variance runs, the
pre-registered Stage C experiment, and the positive control.
Deadline 2026-08-31 23:30.

---

## 1. What exists

17 commits, 46 tests, ~3,000 lines. Reproduces from a clean clone with no
credentials, verified by actually doing it. Total spend across the entire
project: **$1.48**.

| Deliverable | State |
|---|---|
| Code + Improvement Changelog | done — 7 iterations, including 2 experiments that failed and were removed |
| Reproduction guide | done — every command run with all keys unset before being written down |
| Agent trajectories | done — 3 rendered walkthroughs + 29 raw records |
| Video ≤5 min | **not started** (yours) |

---

## 2. The numbers

Mean ± half-range over **three independent live runs**, 22 gradable repositories
from a pool of 30 hash-committed before any method ran, against ground truth
computed only from post-cutoff evidence.

| Method | MCC | Balanced acc. | Sensitivity | Specificity |
|---|---|---|---|---|
| always "viable" | 0.00 ±0.00 | 0.50 | 1.00 | 0.00 |
| name-only probe | 0.16 ±0.07 | 0.58 | 0.40 | 0.75 |
| baseline solution | 0.28 ±0.07 | 0.64 | 0.62 | 0.67 |
| **Holt** | **0.46 ±0.05** | **0.70 ±0.02** | 0.90 ±0.04 | 0.50 ±0.00 |

**Holt's worst run (0.39) beats the baseline's best (0.33).** No overlap.

Three supporting results:

- **Trap rejection.** Repositories with 100+ inbound attempts and zero
  qualifying contributions: Holt rejects 4 of 5, baseline 0 of 5.
- **Positive control.** Three verified-genuine repositories outside the pool:
  Holt recovers 3 of 3, baseline 1 of 3.
- **Stability.** Across three runs, Holt returns identical verdicts on 21 of 22
  repositories; the baseline on 13 of 22.

---

## 3. Rubric estimate

My own scoring, stated so it can be argued with. Previous estimate in brackets.

| Criterion | Points | Estimate | Reasoning |
|---|---:|---:|---|
| Agent Solution & Engineering | 30 | ~26 (was 22) | Determinism is now measured, not asserted: 21/22 vs 13/22 stability. Stage C's exclusion is justified by a pre-registered experiment rather than left unexplained. |
| End-to-End Quality | 20 | ~16 | Reports read like a person wrote them. No video yet. |
| Problem & User Value | 15 | ~13 | Clear user, real bottleneck, measured. Not a novel problem. |
| Measured Improvement | 15 | ~14 (was 10) | Non-overlapping intervals over three runs, floor published, positive control, two failed experiments recorded. |
| Reproducibility | 15 | ~14 | Clean-clone verified, zero-credential, pinned dated model ids. |
| Hot Take / Insights | 5 | ~5 (was 4) | Two independent measurements converging on one non-obvious conclusion. |
| | **100** | **~88** (was ~79) | |

---

## 4. Remaining weaknesses, honestly

### 4.1 Holt over-recommends

**Specificity 0.50 against the baseline's 0.67.** Of 22 repositories it calls 17
viable and is wrong on 4. Its entire advantage is sensitivity (0.90 vs 0.62) plus
the extreme cases. A user following Holt tries more repositories than they need
to; they just do not waste a week on a registry.

This was attacked directly and the attack failed — the pre-registered review
ratio rule improved specificity to 0.62 and cost five genuine opportunities to do
it. It is a real limitation with a documented failed remedy, which is a better
position than an undocumented one, but it is still a limitation.

### 4.2 The flagship stage does not drive the verdict

Holt's pitch is that it reads pull request threads, and `verdict.py` does not
consult what Stage C concluded. This is now defensible rather than accidental:
**two independent measurements** say thread signals do not predict viability —
sentiment came out inverted (registries read as welcoming *because they are
easy*), and review ratio failed a pre-registered test.

A judge may still count it against the pitch. The honest framing, which the
README uses, is that Stage C informs the report a human reads and does not decide
anything — and that we measured that rather than assumed it.

### 4.3 Small sample, and one model

22 of 30 graded: 3 repositories deleted before the run, 5 with no post-cutoff
attempts. Both disclosed, neither fixable. Every claim rests on 22 cases.

Everything also rides on one small model (`gpt-5-mini-2025-08-07`). Per-stage
model choice was measured, but only against itself — we never tested whether a
stronger model changes the conclusions.

### 4.4 Not done

- **Video** — required deliverable, yours.
- **Human time per task** — the brief's own metric table asks for it. Holt takes
  69 seconds per repository. The manual figure can only come from you timing
  yourself reading twenty threads.

---

## 5. What I would spend remaining time on

47 hours to deadline; roughly 1–2 hours of work left on my side.

| Priority | Item | Effort | Why |
|---|---|---|---|
| 1 | Video | yours | Required. Without it the submission is incomplete. |
| 2 | Human-time measurement | ~30m, yours | The brief asks for it and it is the most legible number in the submission. |
| 3 | Anything else | — | Optional. The submission is complete without it. |

**My recommendation is to stop building.** Everything the rubric asks for exists
and is measured. Two failed experiments are documented. The floor is published.
Further changes risk breaking a working, reproducible submission for marginal
gain — and every change now invalidates recorded trajectories and needs a re-run.

If you want one more thing, the highest-value candidate is testing whether a
stronger model on Stage A changes the conclusions (§4.3), because it is the one
claim that rests on a single untested assumption. It costs about $2 and an hour,
and it could go either way — which is the point.
