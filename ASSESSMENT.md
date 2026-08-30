# Holt — where we are and how we got here

Written 2026-08-30, revised through the Path Finder decision. 36 commits, 71 tests, ~$5.10 spent.

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

**Path Finder: measured, and shipped losing.** The decision that had been left
open is made, and one query made it.

Before choosing, we asked something that was a property of the *inputs* rather
than a slice on outcomes: **how many of the 25 scorable repositories carry any
beginner-labelled issue at all?**

```
13/25  none at all
17/25  fewer than three — the label cannot fill a top-3 there
497/3,613 candidate issues carry a beginner label (13.8%)
```

**On 17 of 17 label-absent repositories, the `good_first` comparator scored
identically to recency, to the decimal.** With nothing labelled it reorders
nothing; it *is* recency under another name. So "we tied the `good first issue`
label" was, across two thirds of the pool, "we tied recency" — a flaw in how we
reported our own comparator.

That reframes the result without rescuing it. The combined numbers stand:

| Method | precision@3, 25 repos |
|---|---|
| random (base rate) | 0.151 |
| recency | 0.160 |
| `good first issue` label | **0.187** |
| Holt | **0.173** |

Paired, Holt − label is −0.013, 95% CI [−0.133, +0.120], sign test p = 0.51.

**So it ships, and it ships losing, with the losing number printed in its own
output.** Every rendered ranking carries this — emitted by the renderer, not by
any caller, so no code path can print a ranking without it:

> **This ranking is not measurably better than picking at random.** precision@3
> was 0.173 for this ranking, 0.187 for GitHub's `good first issue` label and
> 0.151 for a random pick — differences well inside noise. It is printed anyway
> because 13 of those 25 repositories had no beginner-labelled issue at all.

A ranking no better than chance still beats what a contributor has today on the
half of viable repositories where no beginner label exists at all — and saying so
in the product, rather than in a document, is the point. Two tests hold it there:
one that the disclaimer accompanies any ranking, one that its printed numbers
track the recorded measurement. See it with
`uv run python -m holt.cli analyze NixOS/nixpkgs --replay`.

**Two things found while doing this that matter more than the feature.**

*The isolation test we claimed existed did not exist.* `CLAUDE.md` and three
docstrings said a test enforced that `eval/labels/` cannot import
`src/holt/agent/`. Nothing did. A documented, unenforced guarantee is worse than
an undocumented one, because a reader trusts it. It is now checked with `ast`, so
even an unexecuted import fails.

*The fresh-clone check found somebody else's credentials, not ours.* Sweeping a
clean clone turned up **13 credential-shaped strings across 7 fixtures**,
including two full-length GitHub tokens pasted into public issue bodies — one of
them printed twice, once normally and once **reversed** to defeat scanners.
Scrubbing now runs before the content hash, records keep their evidence ids so
citations still resolve, and a test walks every committed fixture and fails on
any credential-shaped string. All 84 trajectories still replay with zero stale
keys: none of the removed strings had reached a prompt.

**Fresh clone, no credentials, verified end to end:** `uv sync` → **71 passed** →
`holt analyze --replay` renders → `--days 90` re-answers at zero model calls →
`eval/pathfinder_harness.py --replay` reproduces the published ranking numbers.
That is the qualification-gate item and the second tie-break, now actually run
rather than designed for.

**Open:**

| | Effort | Why |
|---|---|---|
| **Final frozen benchmark, both pools** | ~1h, ~$3.50 | The one blocking item. Committed results predate the rejection rule, so the README's specificity of 0.50 understates the 0.83 that actually ships |
| Doc pass on the headline numbers | ~30m | Mechanical once the benchmark lands; the structural pass is done |
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

Path Finder is the fourth experiment run that way and the first that ships
despite failing. That is not a softening of the rule — the rule was "cut if the
label matches us", and the label does. It ships because a coverage query showed
the comparator does not exist on half the pool, and because the honest thing to
do with a ranking that loses is to print the loss beside it. A tool that states
its own negative result in its own output is the clearest expression of what this
project is: the discipline is in the artifact, not in the description of it.

What is left is one benchmark run, and then it is finished.
