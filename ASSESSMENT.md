# Holt — where we are and how we got here

Written 2026-08-30, revised through Path Finder. 31 commits, 53 tests, ~$5.10 spent.

This is the orientation document. Read it if you have lost the thread.

---

## 1. What Holt is, in one paragraph

A developer with a week to spare wants to contribute to open source. Every signal
GitHub shows them — stars, activity, open issues, `good first issue` labels —
measures whether a project is *alive*, not whether it accepts work from
strangers. A domain registry with 40,000 merged pull requests looks identical to
a welcoming software project on all of them. Holt reads the contribution history
instead and produces a written assessment where every claim carries a link to the
pull request it came from.

---

## 2. How we got here

### Stage one — building something to measure against (blocks 1–3)

You cannot claim your system is better without a truth to be better at. So the
first two thirds of the work was not the agent at all:

- **An evidence layer** where every fact passes through one interface that
  asserts a **temporal cutoff, T = 2026-06-01**. The agent only ever sees
  evidence from before it; the answer key is computed only from after it.
- **A repository sample drawn from history.** GitHub search returns *today's*
  stars no matter what date you ask for, so any pool drawn from it silently
  excludes repositories that died. We sampled instead from GH Archive event logs
  from the days before T — repositories as they looked at the cutoff. **Three of
  the first thirty had been deleted by the time we crawled them.** A search-based
  sample would never have shown us those.
- **Two answer keys, deliberately.** L0 counts any merged outsider pull request.
  L1 adds bot exclusion, a diff-shape filter, and a human-review requirement.

**The first real finding:** under L0, `runelite/plugin-hub` ranks **first in the
pool** — every merged contribution there is a one-line plugin manifest — and
`NixOS/nixpkgs` ranks 17th. Under L1, plugin-hub drops to **last of 22**. That
gap is the whole thesis, and it is a measured number rather than an argument.

### Stage two — the agent (blocks 4–5)

Five stages. Two of them run **no model at all**: arithmetic signals, and
verification. The verdict itself is a **plain function** — `verdict.py` — so a
judge rerunning Holt gets our numbers rather than a resample of them.

### Stage three — measuring it, and being wrong repeatedly

This is where most of the value came from, and almost all of it was uncomfortable:

| What we tried | What happened |
|---|---|
| Predicted `is-a-dev/register` would top the naive metric | **Wrong.** It ranked 15th. But three *other* registries took the top five, which was a stronger finding. |
| Shipped F1 as the primary metric | **Broken.** Answering "viable" to everything scores F1 0.78 — above our own baseline. Switched to MCC, which is 0.00 for any constant answer. |
| Tried to make the thread-reading stage drive the verdict | **Failed twice.** Sentiment signals came out *inverted* (registries read as welcoming because they are easy). A pre-registered review-ratio rule cost five genuine opportunities to catch one bad one. Both removed, both documented. |
| Claimed "the intervals do not overlap" | **Overclaim.** Those measured model noise, not sampling error. Measured properly, the difference was not statistically distinguishable at n=22. |
| Hired an adversarial reviewer | Found four real errors, all since corrected. Scored us 68 where we had scored ourselves 88. |

### Stage four — where we are as of this morning

Two things changed the picture.

**A second pool.** 45 more repositories, new seed, drawn from the same frame with
pool 1 excluded, **hash-committed before anything ran against it**. 33 gradable.
This is genuine out-of-sample replication rather than a bigger single sample.

**A rejection rule that works.** Specificity had been stuck at 0.50 across every
method — we were rejecting non-viable repositories at chance, which is the one
thing Holt exists to do. Exploring pool 1 surfaced a rule: *contributions land
easily and nobody reviews them*. It was pre-registered with three numeric
predictions before pool 2 labels existed, then tested once.

---

## 3. Where the numbers stand

### The headline: reading history beats reading a landing page

| | Pool 1 (n=22) | Pool 2, out-of-sample (n=33) |
|---|---|---|
| baseline — README and metadata | +0.21 | **+0.04** |
| Holt | +0.49 | +0.42 |
| gap | +0.28 | **+0.38** |

Holt replicates. The baseline **collapses to near-chance** on pool 2, because
pool 2 skews toward quieter repositories where a README tells you nothing. The
advantage widens out of sample.

### The rejection rule, tested once on data it was never fitted to

| Pool 2 | MCC | Sensitivity | Specificity |
|---|---|---|---|
| Holt as shipped | +0.42 | 0.83 | 0.58 |
| **with the rule** | **+0.59** | 0.78 | **0.83** |

All three pre-registered predictions held. **Specificity 0.58 → 0.83.** The
coin-flip problem is solved, on a pool drawn and labelled after the rule was
written down.

### The result that goes against us

Given **identical evidence**, a single prompt matches the staged pipeline
exactly: on pool 2 both score MCC 0.42, sensitivity 0.83, specificity 0.58. The
evidence layer is worth +0.38. The orchestration on top of it is worth, in
accuracy, nothing.

What orchestration buys instead: run-to-run stability (32/33 against the
baseline's 17/33), citations that resolve, and a verdict a model cannot override.
That is reproducibility, not accuracy, and we say so.

---

## 4. What is decided

- The pool is closed. Neither pool has been edited after seeing results.
- Two experiments failed, were removed, and stayed in the changelog.
- Every uncomfortable number is published: the constant-classifier floor, the
  label sensitivity, the ablation showing orchestration adds no accuracy.
- Stage B and Stage C reach the report but not the verdict, and that is disclosed
  rather than quietly true.

## 5. What has happened since, and what is open

**Shipped since this document was first written:**

- **The rubber-stamp rejection rule.** Rejects when contributions land easily and
  nobody reviews them. Validated out-of-sample on pool 2 *before* shipping —
  specificity 0.58 → 0.83, all three pre-registered predictions holding. This is
  the first thing that makes the pipeline itself, rather than the evidence layer,
  earn its place.
- **`--days`.** The contributor's time budget is a parameter, not a hardcoded
  week. Re-running with a different budget costs **zero model calls**, because
  only `verdict.py` re-runs. That is the cleanest thing the orchestration buys
  that a single prompt cannot, and unlike the accuracy claim it is not in dispute.
- **Evidence integrity as an evaluation dimension.** Holt's citations resolve
  696/696. Two of our predictions failed here: the matched prompt does *not*
  fabricate (638/638 resolve), and our own quote fidelity is 80% rather than
  near-perfect. The real difference is that the prompt emits no quotes at all, so
  its claims cannot be checked while Holt's can. The metric also found a defect in
  our own prompt on its first run — 80 of 108 unfaithful quotes were Holt's own
  scaffolding being quoted back as evidence.

**Path Finder: built, measured, decision open.** It is the one thing in the
project whose fate is not settled, so it gets the full record here.

*What it does.* Given a repository already judged viable, rank the issues open at
the cutoff by how likely an outsider is to land a merged pull request resolving
one. Ground truth was designed before implementation
([`eval/PATHFINDER-DESIGN.md`](eval/PATHFINDER-DESIGN.md)): an issue is a
*realised entry point* if it was later closed by a merged pull request from
someone who had not already landed work in that repository.

*What it scores.* Combined over both pools, 25 scorable repositories, precision@3:

| Method | precision@3 |
|---|---|
| random (base rate) | 0.151 |
| recency | 0.160 |
| `good first issue` label | **0.187** |
| Holt | **0.173** |

Paired per repository, Holt − label is **−0.013, 95% CI [−0.133, +0.120]**, 3
wins / 6 losses / 16 ties, sign test **p = 0.51**. The honest reading is not that
Holt is worse — it is that after ranking 3,613 issues we **cannot distinguish our
ranking from a label GitHub applies for free**. Total cost to find out: $0.14.

*The case for cutting.* Cut condition 2 of the design document, written before a
line of the feature existed, reads: *"the `good first issue` comparator matches
Holt's precision — the feature then has no argument for existing."* That is met
verbatim. The premise of the feature was that existing signals do not tell an
outsider where to start; if the free label ranks as well as we do, the premise is
false. And because the measurement lives in our own repository, shipping the
ranking anyway is the single move most likely to make the rest of the honesty
look like theatre.

*The case against cutting.* The per-repository pattern is not flat. Holt scores
1.00 where the label scores 0.00 on `JhaSourav07/commitpulse`, 0.67 against 0.00
on `NixOS/nixpkgs`, 0.33 against 0.00 on `PostHog/posthog` — and loses on smaller
repositories where a maintainer curates the label by hand. There may be a real
effect where the label is useless at scale and Holt is not. **This is post-hoc
slicing on n = 25 with 16 ties, and it is exactly the move pre-registration
exists to prevent.** It is recorded as a hypothesis, not a finding.

*The three live options.*

| | What ships | Cost |
|---|---|---|
| **1. Ship the ranking, drop the claim** | Entry points appear in the assessment, and the tool's own output states "this ranking is not measurably better than GitHub's `good first issue` label — 0.173 vs 0.187 over 25 repositories" | ~20 min |
| **2. Cut** | Nothing user-facing; `find_paths` stays in the tree marked as withdrawn, harness stays runnable | done already |
| **3. Pre-register the subgroup** | Declare "Holt beats the label on repositories with more than N open issues" *before* scoring, then test it | ~40 min, likely underpowered |

**Current state of the tree: option 2 is what is committed** — `find_paths` is
annotated as cut and is not called by `pipeline.analyze`. Nothing is deleted, so
options 1 and 3 remain about twenty minutes of work away. **The decision is
yours and is not made.**

*One side finding worth keeping regardless:* the post-cutoff issue-body edit rate
is 86/2,678 on pool 2 (3.2%) against 9/935 on pool 1 (1.0%), 95/3,613 combined
(2.6%). Pool 1 alone understated the leak threefold — a small argument for two
pools that has nothing to do with Path Finder.

**Open:**

| | Effort | Why |
|---|---|---|
| Final frozen benchmark, both pools | ~1h, ~$3.50 | Committed results still predate the rejection rule |
| Doc pass | ~1h | README describes the pre-rule, pre-Path-Finder world |
| **Video** | yours | Required deliverable |
| **Human-time number** | yours, ~30m | The brief asks for it; only you can produce it |

## 6. The honest summary

The thing we set out to prove — that an agent reading pull request threads beats
naive metrics — is **proven twice**, out of sample, with a widening margin.

The thing we assumed — that the staged pipeline is what delivers that — is
**false**, and we measured it ourselves rather than waiting to be caught. The
evidence layer does the work.

The rejection rule is the first evidence that orchestration can add something
accuracy-wise, and it arrived through the same discipline that killed the two
experiments before it: write the rule down, predict the outcome, run it once.
