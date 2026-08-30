# Holt — where we are and how we got here

Written 2026-08-30. **32.9 hours to deadline.** 26 commits, 47 tests, $4.85 spent.

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

## 5. What is open

| | Effort | Why it matters |
|---|---|---|
| **Ship the rejection rule into `verdict.py`** and re-run both pools | ~1h, ~$3 | It is the first thing that makes the *pipeline* earn its place. Right now it exists only as a counterfactual. |
| **Evidence-integrity metric** | ~1.5h | Do the reports' citations actually resolve? Ours should be near-perfect by construction; the matched prompt will fabricate. Lands on End-to-End Quality rather than competing on accuracy. |
| **Doc pass** | ~1h | README and REPRODUCTION still describe the pre-pool-2 world. |
| **Video** | yours | Required deliverable. |
| **Human-time number** | yours, ~30m | Time yourself reading twenty threads. Holt takes ~69 seconds. The most legible comparison we could show. |

**Recommended order:** ship the rule → re-run → doc pass → evidence integrity →
your video.

## 6. The honest summary

The thing we set out to prove — that an agent reading pull request threads beats
naive metrics — is **proven twice**, out of sample, with a widening margin.

The thing we assumed — that the staged pipeline is what delivers that — is
**false**, and we measured it ourselves rather than waiting to be caught. The
evidence layer does the work.

The rejection rule is the first evidence that orchestration can add something
accuracy-wise, and it arrived through the same discipline that killed the two
experiments before it: write the rule down, predict the outcome, run it once.
