# Holt — where we are and how we got here

Written 2026-08-30; last revised midday 2026-08-31, after the discovery,
progression and model-choice features shipped and the frozen benchmark landed.
60+ commits, 128 tests, ~$14.60 spent in total.

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

### Stage five — the product grows outward (2026-08-31)

Three commands shipped in one night, each shaped by an earlier kill rather than
repeating it.

**`holt discover` — find repositories, from a stated profile.** The inferred
profile was cut in iteration 15/16 (the median contributor has 1 merged PR and 5
files; 98% of cross-repo overlap was generic-path collisions), so the profile is
*asked*: `holt profile` stores four answers — languages, topics, contribution
type, days — each of which demonstrably changes the output; experience level is
deliberately not asked because nothing could map it to a threshold. The flow:
GitHub repository search sources candidates (disclosed, unclaimed), a screening
pass runs every arithmetic rule at **zero model cost** — possible because
`verdict.py` needs exactly one model-derived input, `repo_kind` — and only the
survivors are re-crawled at full depth and analysed (~$0.02 each). We claim the
filter (the p = 0.048 trap rejection and the out-of-sample rubber-stamp rule),
never the sourcing or the ordering; rows come out in screening order.

**Live is the primary mode.** `holt discover --live` searches today's GitHub;
`--record <name>` writes the whole session down; bare `holt discover` replays
the committed demo with no token and no key. The recorded demo is a real live
run from this morning: 25 python+cli candidates, 9 rejected across all four
buckets at $0.00, five survivors analysed for $0.08 — and `tqdm/tqdm` survived
shallow screening then flipped to insufficient at full depth (median first
reply 1,128 h), the screen-versus-full noise disclosure demonstrating itself.

**`holt next <repo> --as <login>` — the simple rule that won, shipped.** The
weighted progression scorer was cut for losing to `path_overlap` (hit@10 0.234
vs 0.211); the winning rule now ships, semantically identical to what the
harness measured. The renderer prints the measurement — including the 95%
interval [−0.003, +0.132] that spans zero — with every ranking, and each row
says which path tokens overlapped or that none did. No model call in the path.

**The narration no longer speaks evaluation jargon.** The prompt header
"Measured before the cutoff:" leaked "before the cutoff" into user-facing
prose; it now reads "Measured in the sampled window:" and the system prompt
forbids the word "cutoff". That edit invalidated all trajectories by design
(replay keys cover prompt text; exactly one test failed, with a replay miss),
and the fifth full re-record is running via the new one-command
`scripts/rerecord_trajectories.py`, which also covers the discover demo's
survivors.

**The frozen benchmark ran the same day**, batched deliberately after the
wording fixes so it measures the prompts that ship: three tagged runs per pool,
both pools, $3.50, every run replay-verified from the committed recordings.
Section 3 below holds the results.

---

## 3. Where the numbers stand — frozen 2026-08-31, on the shipped prompts

Three live runs per pool, every one replay-verified from the committed
recordings. Total benchmark spend $3.50.

### The headline: reading history beats reading a landing page

| MCC, mean over 3 runs | Pool 1 (n=22) | Pool 2, out-of-sample (n=33) |
|---|---|---|
| name-only probe | +0.16 | +0.10 |
| baseline — README and metadata | +0.09 ±0.09 | +0.21 ±0.02 |
| same-evidence ablation | — | +0.32 ±0.07 |
| **Holt** | **+0.61 ±0.00** | **+0.63 ±0.00** |

**Holt's verdicts were identical on all 55 repositories across all three runs**
(the baseline changed its mind on 16). Specificity — the number that had been
stuck at coin-flip — is **0.75 in sample and 0.83 out of sample**, the
rubber-stamp rule's pre-registered prediction now frozen into the committed
benchmark, at the predicted cost of a few points of sensitivity (0.86/0.81).

### The result that moved, and the honest account of it

- **The "orchestration adds no accuracy" finding is superseded.** When measured
  (pre-rule), the same-evidence single prompt tied the pipeline 0.42 = 0.42. On
  the frozen runs the pipeline leads it 0.63 to 0.32 — and the difference is
  the deterministic verdict layer, not smarter model stages: the fresh ablation
  shows the model stages and kind rules worth **+0.01 MCC** over arithmetic.
  A prompt can be handed identical evidence; it cannot be handed a rule it is
  unable to override.
- **The trap-rejection significance claim is retired.** Holt rejects 4/5 traps
  in every recorded run, but the baseline — 0/5 when the p = 0.048 was computed
  — scored 2–3/5 on the frozen re-runs. The stable claim is Holt's 4/5 every
  time against a baseline that wanders; the significance did not survive
  re-measurement and we say so instead of citing the old number.
- **The label-sensitivity vulnerability shrank.** Dropping the `substantive`
  filter used to flip the advantage to the baseline; on the frozen runs Holt
  leads under every ground-truth variant (worst case +0.39 vs +0.28).
- Repository-level stats (pool 1): bootstrap MCC difference +0.42 to +0.59,
  P(difference ≤ 0) = 0.04–0.08, CIs still touching zero; McNemar p = 0.15–0.23.
  Large but not formally distinguishable at n=22, and printed as such.

---

## 4. What is decided

- The pool is closed. Neither pool has been edited after seeing results.
- Two experiments failed, were removed, and stayed in the changelog.
- Every uncomfortable number is published: the constant-classifier floor, the
  label sensitivity, the ablation showing where the accuracy does and does not
  live, and a significance claim retired when it failed to re-measure.
- Stage B and Stage C reach the report but not the verdict, and that is disclosed
  rather than quietly true.

## 5. Where each capability stands

| Layer | Status |
|---|---|
| Evidence assembly, temporal holdout, replay | **Built, and the strongest thing here** |
| "Where outsider work landed" (per-PR file lists) | **Built** — claims nothing, so nothing can beat it |
| `holt compare` over a shortlist | **Built** — sorts nothing, for the same reason |
| Viability analysis | **Built and validated twice, out of sample** |
| The rubber-stamp rejection rule | **Built, pre-registered, validated out of sample** |
| `holt discover` from a stated profile | **Built** — live GitHub search sourcing (disclosed, unclaimed), screening at zero model cost, recorded demo replays with no credentials |
| `holt next` (path_overlap progression) | **Built** — the measured winner among five methods, its interval printed with every ranking |
| Path Finder (generic issue ranking) | Measured, **cut** — tied GitHub's own label |
| Personalised progression (weighted scorer) | Measured, **cut** — model changed 0 of 88 rankings; the simple rule that beat it is what `holt next` ships |
| *Inferred*-profile discovery | Measured, **cut** — the lift was one programme cohort; the *stated*-profile `holt discover` is its replacement |
| Star-based discovery | **Not built** — a 5-minute check said stars already do it |

**Six experiments cut by their own pre-registered rules, one rule shipped.**
That ratio is the project. Each cut is reproducible from a clean clone:
`eval/sensitivity.py`, `eval/pathfinder_harness.py`,
`eval/progression_harness.py`, `eval/mover_controls.py`. Two of the cuts later
produced shipped features by subtraction — `holt next` is the cheap rule the
weighted scorer lost to, and `holt discover` is the stated-profile replacement
for the inferred profile — which is the difference between abandoning a
capability and abandoning a claim.

### The three things that measurably work

- **The rejection rule.** Contributions land easily and nobody reviews them →
  reject. Pre-registered with numeric predictions, validated on a pool never used
  to develop it: **specificity 0.58 → 0.83**, all three predictions holding. The
  only change that measurably improved accuracy.
- **The evidence layer.** 44× more material than a person can paste, every claim
  carrying an id that resolves *and* a quotation the thread actually contains
  (985 claims over the committed runs; the 9 that quoted otherwise were
  dropped), a cutoff asserted at the chokepoint rather than promised in prose.
- **`--days`.** Re-answering at a different time budget costs **zero model
  calls**, because only `verdict.py` re-runs.

### The things we have proven do *not* work, about ourselves

- The model stages add almost no accuracy: on the frozen ablation they and the
  kind rules together are worth **+0.01 MCC** over arithmetic. (The earlier,
  stronger form — a same-evidence prompt *tying* the whole pipeline, 0.42 =
  0.42 — held before the deterministic rejection rule shipped; the pipeline now
  leads 0.63 to 0.32, and the lead is the rule, not the model.)
- Stage D verification dropped **0 of 1,402** findings.
- The arithmetic thresholds never bind on this pool.
- The model layer contributes nothing to ranking. Sharpest form: given
  contributor history, file lists, review threads and a structured competence
  profile — **strictly more context than the arithmetic had** — it returned an
  identical ranking **88 times out of 88**.
- The trap-rejection significance (4/5 vs 0/5, p = 0.048) **did not survive
  re-measurement**: the baseline scored 2–3/5 on the frozen runs. Holt's own
  4/5 held in every run ever recorded.

### The two additions, and why they are shaped this way

After five features cut for losing to a cheap comparator, both things built today
were chosen for **making no claim a comparator could beat**.

- **Where outsider work landed.** We crawl every pull request's file list, used it
  to decide whether a diff was substantive, and threw it away. Counted over
  outsider threads it says: 13 of nixpkgs' 15 outsider merges landed in
  `pkgs/by-name`, and outsiders attempted `maintainers`, `pkgs/applications`,
  `pkgs/build-support` and `doc/release-notes` without a single merge. In a
  200,000-file tree that is where a stranger's week has a chance. Pure arithmetic,
  no model call, no trajectory invalidated.
- **`holt compare`.** A shortlist is the real situation. It sorts nothing; the
  `why` column is the rule that fired, so the comparison rests on the
  deterministic part.

**A regression the second one exposed, which matters more than either.** Adding
the contributor's day budget to the narration prompt — part of the report rewrite
that fixed our weakest graded area — made that prompt **vary with `--days`**, so
`--days 3 --replay` became a replay miss. That silently falsified the claim that
re-answering at a different budget costs zero model calls. Nothing failed loudly.
It was live for about eight hours and would have shipped, had a second feature not
happened to touch the same path. The budget never needed to reach the model; a
test now asserts it cannot.

The lesson we are taking from it: **our safeguards catch contamination and
citation drift, but nothing was watching whether a published claim was still
true.** That is the gap, and it is worth stating rather than quietly patching.

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
| **Agent Solution & Engineering** *(first tie-break)* | 30 | **Strong, with an honest asterisk.** The design choices are purposeful and each carries a measurement: a deterministic verdict (22/22 stable runs against the baseline's 17/22), a chokepoint that makes contamination structurally impossible, a rejection rule with written thresholds, reparameterisation at zero model cost. The asterisk is ours and we publish it: the *orchestration* buys none of the accuracy. The README now leads with what the split earns and states what it does not immediately after. |
| **End-to-End Quality** | 20 | **Was our weakest; materially improved, twice.** The report was a 250-word wall opening "I'm marking this repository viable" — the model claiming a decision `verdict.py` makes. Now: a headline saying what the verdict means *for you* at *your* time budget, a two-sentence bottom line, short prose, **the deciding rule printed**, an explicit "what could not be determined", evidence with resolvable ids, and a section counting where outsider work actually landed. The journey is now covered end to end: `holt discover` finds the shortlist from a stated profile, `holt compare` puts it side by side, `holt analyze` reads one repository deeply, `holt next` ranks what to do after your first merge. The narration no longer says "cutoff" to a user. Still unproven by anyone outside this project. |
| **Measured Improvement** | 15 | **Exceptional, and the likely differentiator.** Two hash-committed pools, out-of-sample replication with a widening margin, a metric we replaced on catching it reward a constant classifier, bootstrap intervals that span zero reported as spanning zero, and five documented kills. |
| **Problem & User Value** | 15 | **Strong.** A concrete user, a real bottleneck, and a sampling decision (GH Archive over Search — three of thirty pool repos were deleted before the crawl) that a search-based sample would have hidden. |
| **Reproducibility** *(second tie-break)* | 15 | **Strong and now verified end to end**, not merely designed: fresh clone, credentials stripped from the environment, `uv sync` → 266 passed (339 with `--extra tui`) → CLI renders → `--days 90` re-answers at zero model calls → the ranking harness reproduces published numbers → `holt discover` replays a recorded live session with no token and no key. A credential scrub runs before the content hash, a test fails on any credential-shaped string in any fixture, and re-recording every trajectory after a prompt change is one committed command. **The gap this rating used to hide:** every guard pointed at the agent and none at the prose, so `holt analyze --baseline --replay` — a documented command and the required baseline arm — failed from a clean clone while the benchmark stayed green. `tests/test_docs_claims.py` now runs every command this guide prints and recomputes every number it states. |
| **Hot Take** | 5 | **Have one, and it is true in the repo:** *Holt is not a smarter analyst. We measured four times that our model layer adds no accuracy over arithmetic. It is an evidence assembly nobody will do by hand, wrapped in properties a conversation cannot have.* |

**The gap that was ours to close is closed:** the frozen benchmark ran on the
shipped prompts, both pools, three runs each, every run replay-verified; the
README's headline tables now carry the frozen numbers (0.61/0.75 in sample,
0.63/0.83 out of sample) instead of the stale understatement.

**The one gap that is not ours:** nobody outside this project has read a report.

**Open:**

| | Effort | Why |
|---|---|---|
| **Video** | yours | Required deliverable. `holt discover` → `compare` → `analyze` → `next` is the arc of one contributor's week |
| **Human-time number** | yours, ~30m | The brief asks for it; only you can produce it |
| Rotate both tokens | yours, after submission | The PAT and the OpenAI key appeared in working sessions |

## 6. The honest summary

The thing we set out to prove — that an agent reading pull request threads beats
naive metrics — is **proven twice**, out of sample, with a widening margin.

The thing we assumed — that the staged pipeline is what delivers that — is
**false**, and we measured it ourselves rather than waiting to be caught. The
evidence layer does the work.

The rejection rule is the proof that orchestration can add accuracy — just not
where we assumed. The frozen benchmark shows the pipeline beating a
same-evidence prompt by 0.3 MCC out of sample, and the entire lead is the
deterministic layer the rule lives in; the model stages contribute +0.01. It
arrived through the same discipline that killed the experiments before it:
write the rule down, predict the outcome, run it once. The same freeze also
took something away — the trap-rejection significance claim did not
re-measure, and it is retired in the same tables that celebrate the rule.

Path Finder is the fourth experiment run that way and the first that ships
despite failing. That is not a softening of the rule — the rule was "cut if the
label matches us", and the label does. It ships because a coverage query showed
the comparator does not exist on half the pool, and because the honest thing to
do with a ranking that loses is to print the loss beside it. A tool that states
its own negative result in its own output is the clearest expression of what this
project is: the discipline is in the artifact, not in the description of it.
`holt next` extends the same pattern: the ranking it prints carries its own
interval, and the interval spans zero.

The last day turned the measurement discipline back into product surface: the
kills of the profile-inference and progression experiments dictated the shape
of `holt discover` (ask, don't infer; claim the filter, not the order) and
`holt next` (ship the winning rule, print its numbers), and the frozen
benchmark closed the loop on the numbers. What is left is the video and the
human-time study — the two deliverables only the author can produce.
