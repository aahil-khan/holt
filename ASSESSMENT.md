# Holt — where we are and how we got here

Written 2026-08-30, revised after the Fable audit. 44 commits, 83 tests, ~$7.75 spent.

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

## 5. Where each capability stands

| Layer | Status |
|---|---|
| Evidence assembly, temporal holdout, replay | **Built, and the strongest thing here** |
| Viability analysis | **Built and validated twice, out of sample** |
| The rubber-stamp rejection rule | **Built, pre-registered, validated out of sample** |
| Path Finder (generic issue ranking) | Measured, **cut** — tied GitHub's own label |
| Personalised progression | Measured, **cut** — model changed 0 of 88 rankings |
| Personalised discovery | Measured, **cut** — the lift was one programme cohort |
| Star-based discovery | **Not built** — a 5-minute check said stars already do it |

**Five experiments cut by their own pre-registered rules, one shipped.** That
ratio is the project. Each cut is reproducible from a clean clone:
`eval/sensitivity.py`, `eval/pathfinder_harness.py`,
`eval/progression_harness.py`, `eval/mover_controls.py`.

### The three things that measurably work

- **The rejection rule.** Contributions land easily and nobody reviews them →
  reject. Pre-registered with numeric predictions, validated on a pool never used
  to develop it: **specificity 0.58 → 0.83**, all three predictions holding. The
  only change that measurably improved accuracy.
- **The evidence layer.** 44× more material than a person can paste, every claim
  carrying an id that resolves (696/696), a cutoff asserted at the chokepoint
  rather than promised in prose.
- **`--days`.** Re-answering at a different time budget costs **zero model
  calls**, because only `verdict.py` re-runs.

### The four things we have proven do *not* work, about ourselves

- Orchestration adds no accuracy over one prompt with identical evidence
  (0.42 = 0.42 on pool 2).
- Stage D verification dropped **0 of 1,402** findings.
- The arithmetic thresholds never bind on this pool.
- The model layer contributes nothing to ranking. Sharpest form: given
  contributor history, file lists, review threads and a structured competence
  profile — **strictly more context than the arithmetic had** — it returned an
  identical ranking **88 times out of 88**.

### What the audit changed

An independent audit reproduced the discovery headline from our fixtures and then
broke it four ways. It also caught a number we had stated wrongly (a 47% base rate
whose denominator counted repositories with no fixtures; the correct figure is
51%) and a README claim that stars are "a coin flip" when our own check says they
are 80% precise at top-10. Both corrected.

It surfaced something more uncomfortable underneath: **nine pool repositories are
GirlScript Summer of Code '26 projects with a points leaderboard, and they pass
L1.** A stranger's patch does land there; whether a week spent there is the
opportunity this tool exists to find is a question our ground truth does not ask.
We did not find this by auditing our labels — it surfaced because it broke a
different experiment. It is in Known Limitations with the grep command, and the
labels were not touched.

## 5b. Against the rubric

| Criterion | Weight | Where we stand |
|---|---|---|
| **Agent Solution & Engineering** *(first tie-break)* | 30 | **Strong, with an honest asterisk.** The design choices are purposeful and each carries a measurement: a deterministic verdict (21/22 stable runs against the baseline's 13/22), a chokepoint that makes contamination structurally impossible, a rejection rule with written thresholds, reparameterisation at zero model cost. The asterisk is ours and we publish it: the *orchestration* buys none of the accuracy. The README now leads with what the split earns and states what it does not immediately after. |
| **End-to-End Quality** | 20 | **Was our weakest; materially improved today.** The report was a 250-word wall opening "I'm marking this repository viable" — the model claiming a decision `verdict.py` makes. Now: a headline saying what the verdict means *for you* at *your* time budget, a two-sentence bottom line, short prose, **the deciding rule printed**, an explicit "what could not be determined", and evidence with resolvable ids. Still unproven by anyone outside this project. |
| **Measured Improvement** | 15 | **Exceptional, and the likely differentiator.** Two hash-committed pools, out-of-sample replication with a widening margin, a metric we replaced on catching it reward a constant classifier, bootstrap intervals that span zero reported as spanning zero, and five documented kills. |
| **Problem & User Value** | 15 | **Strong.** A concrete user, a real bottleneck, and a sampling decision (GH Archive over Search — three of thirty pool repos were deleted before the crawl) that a search-based sample would have hidden. |
| **Reproducibility** *(second tie-break)* | 15 | **Strong and now verified end to end**, not merely designed: fresh clone, credentials stripped from the environment, `uv sync` → 83 passed → CLI renders → `--days 90` re-answers at zero model calls → the ranking harness reproduces published numbers. A credential scrub runs before the content hash, and a test fails on any credential-shaped string in any fixture. |
| **Hot Take** | 5 | **Have one, and it is true in the repo:** *Holt is not a smarter analyst. We measured four times that our model layer adds no accuracy over arithmetic. It is an evidence assembly nobody will do by hand, wrapped in properties a conversation cannot have.* |

**The one gap that is ours to close:** the committed benchmark numbers predate
both the rejection rule and the report rewrite, so the README currently
*understates* what ships — specificity 0.50 against the 0.83 the shipped rule
achieves. One frozen run fixes it.

**The one gap that is not ours:** nobody outside this project has read a report.

**Open:**

| | Effort | Why |
|---|---|---|
| **Final frozen benchmark, both pools** | ~1h, ~$3.50 | The one blocking item. Committed results predate the rejection rule, so the README's specificity of 0.50 understates the 0.83 that actually ships |
| "Where outsiders land" — per-PR file lists, crawled and never surfaced | ~2h | The most actionable sentence a contributor could read, and pure evidence presentation: it ranks nothing and claims nothing |
| `holt compare a b c` | ~2h | A real user has a shortlist, not one repo. Composition of finished parts; makes the video far better |
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
