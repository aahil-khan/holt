# Improvement Changelog

Holt decides whether a GitHub repository is a genuine opportunity for an
*external* contributor, and writes an evidence-backed assessment saying why.
This is how it got from a one-line merge rate to the shipped system.

**One evaluation, held constant from the baseline to the final result.** Two
hash-committed pools of repositories — 22 in sample, 33 out of sample — under a
temporal holdout at **T = 2026-06-01**: the agent sees only records timestamped
at or before T, and the labels are computed only from records after it. The
primary metric is **Matthews correlation** on a three-valued verdict, chosen in
iteration 4 for the reason recorded there. Every number below replays from
committed recordings with no API key and no spend.

Entries were written the day each experiment ran. This is the abridged record;
the unabridged log, with the full evidence tables and the engineering work that
moved no benchmark number, is
[`docs/CHANGELOG-FULL.md`](docs/CHANGELOG-FULL.md) and
[`docs/INTERFACE-LOG.md`](docs/INTERFACE-LOG.md). Entry numbers are the
originals, so the two files line up.

---

## The story in one table

| Stage | What we tried and why | Evidence | Decision / learning |
|---|---|---|---|
| **Baseline** (08-29) | One prompt over the README and repository metadata — how a developer screens a repository today | MCC **+0.09** in sample, **+0.21** out of sample | Kept as the comparator behind every number below |
| **Ground truth** (08-29) | Label by outsider merge rate; then require the merge to touch source and to have been reviewed by a human | The naive rate puts three registries in its top five and `NixOS/nixpkgs` 17th of 22 | L1 becomes the label. The two filters catch different repositories — either alone leaves half the problem standing |
| **The pipeline** (08-29) | Stage the work, call a model only where interpretation is needed; signals and verification call none | 4/4 correct on a development set disjoint from the pool, **$0.012** per repository | Kept, small model at every stage |
| **Attack our own metric** (08-30) | Score constant answers against our own ground truth before a judge does | Answering "viable" to everything scores **F1 0.78** and beats our own baseline | Primary metric changed to **MCC**, which is 0.00 for any constant. The constants stay in the results table permanently |
| **Thread sentiment → verdict** (08-30) | Pre-registered: let the review ratio decide, since it separates the classes | Specificity rose exactly as predicted; MCC **0.49 → 0.19**, and five of six changed verdicts were genuine opportunities withheld | **Removed.** A pull request thread records the merge, not the conversation that produced it |
| **The rubber-stamp rule** (08-30) | Reject where contributions land easily and nobody reviews them — validated out of sample *before* shipping | Specificity **0.58 → 0.83**, all three pre-registered predictions holding | **Shipped.** The single largest accuracy gain in the project |
| **Same-evidence ablation** (08-30) | Give one prompt everything Holt sees, to separate the evidence layer from the orchestration | README-only **+0.21** → same evidence **+0.53** | Both published. Reading contribution history rather than a landing page is most of the gain |
| **Path Finder** (08-30) | Rank a repository's open issues by how likely an outsider is to land a fix | precision@3 **0.173** against GitHub's own `good first issue` label at 0.187, over 3,613 issues | **Cut** on a condition written before the feature existed. Ships behind a flag that prints its own losing number |
| **Personalised discovery** (08-30) | Profile a contributor from their merged work, rank what they should do next | The model call moved **0 of 88** rankings — 0 wins, 0 losses, 88 ties | **Cut.** Second independent measurement that the model layer does not move a ranking |
| **Discovery from movement** (08-30) | Recommend repositories from where contributors actually went: 89% landed somewhere viable against a 51% base rate | **66 of the 74** transitions sat inside one summer-of-code cohort; a free co-occurrence heuristic answers the harder question better | **Cut before implementation.** Ninety minutes, no model calls |
| **What shipped instead** (08-31) | `discover`, `next`, `compare`, and where outsider work actually lands in the tree — the parts of cut experiments that beat their comparators | Screening rejects candidates at **$0.00** and zero model calls; every ranking prints the measurement behind it | Shipped |
| **Frozen benchmark** (08-31) | Three live runs per pool on the shipped prompts and rules, recorded so a judge reproduces every number with no key | Holt **+0.61 / +0.63** against the baseline's +0.09 / +0.21; specificity 0.75 / 0.83; **55 of 55** verdicts identical across runs against the baseline's 39 | The headline verdict result. $3.50 |
| **Score the report** (08-31) | Count *checkable* statements per report — the axis no confusion matrix can see | **11.8** per report against the same-evidence ablation's 3.4, on identical evidence, 100% resolving | Kept. Two axes, two different winners, both published |
| **Final** (08-31) | Ship the ablation as a mode: `--no-model`, the verdict from the rules alone, no key and no spend | **+0.60** in sample, **+0.55** out of sample, against the full pipeline's +0.61 / +0.63 | Ships, printing both numbers in its own output |

**Baseline → final, same repositories, same task, same holdout:**

| | Pool 1 (in sample, n=22) | Pool 2 (out of sample, n=33) |
|---|---|---|
| baseline solution | +0.09 ±0.09 | +0.21 ±0.02 |
| **Holt** | **+0.61 ±0.00** | **+0.63 ±0.00** |
| verdict stability across three runs | 22/22 against 17/22 | 33/33 against 22/33 |

---

## Baseline — the label to measure against, and the solution to beat (2026-08-29)

The task has two halves, so it needs two baselines.

**The label.** Of the pull requests outsiders opened after the cutoff, what
fraction merged? No filter on what the diff touches, no bot exclusion, no
requirement that a human reviewed anything — the metric a reasonable engineer
writes first, run over the hash-committed pool.

**Evidence.** It fails in a systematic direction. Its top five contains three
registries — `runelite/plugin-hub` (#1), `DefiLlama/dimension-adapters` (#3),
`Homebrew/homebrew-cask` (#5) — where every merged contribution is a manifest
entry or an adapter stub. The two most plausibly genuine opportunities in the
pool sit below them: `space-wizards/space-station-14` at #12 and `NixOS/nixpkgs`
at #17. A developer following this metric tries three registries before reaching
nixpkgs. Two repositories score 0.00 across 500 attempts — maximum inbound
activity, nothing merged.

**The solution baseline.** A single prompt over the README and repository
metadata: what a developer actually does today when deciding whether to spend a
week somewhere. It is the comparator for every number in this file.

**Decision.** Both kept. The label needs a filter that separates a merge which
touched real source from a merge that appended a line to a data file — that is
the discriminator the top of the table is missing.

---

## Iteration 1 — L1, the qualifying label (2026-08-29)

**Tried.** Keep an outsider merge only if the author is not a bot, the diff is
not docs-only or data-file-only or a one-line change to a single file, and a
human other than the author reviewed or commented. Built as a five-stage funnel
counted per repository, so each filter's effect is inspectable rather than
folded into one number.

**Evidence — the two filters do different work.** Over 22 repositories, 7,059
human attempts fall to 2,302 merged, 1,211 substantive, 619 reviewed. They do
not catch the same repositories:

| Removed by diff shape | Removed by review | Repo |
|---|---|---|
| 392 | 0 | `runelite/plugin-hub` |
| 367 | 0 | `is-a-dev/register` |
| 16 | 277 | `Pasta-Devs/Marinara-Engine` |
| 25 | 114 | `anurag3407/career-pilot` |

Diff shape catches registries — manifest entries that merge cleanly and change
no software. Review catches auto-merge farms — real-looking diffs no human ever
engaged with. **Either filter alone leaves half the problem standing.** The
prior going in was that review would dominate; it does not.

Under L1, `plugin-hub` goes from rank 1 to 22, `is-a-dev/register` from 15 to
20, and `NixOS/nixpkgs` rises from 17 to 12.

**Decision.** Kept, both filters. L1 is the label the agent is scored against,
hash-committed before any method was run against it.

**Recorded because it happened in this order:** the first diff-shape rule read
"exactly one changed data file", and `is-a-dev/register` *rose* to 9 under it —
a domain registration there touches two files. Counting files was the wrong
test; what matters is whether any changed file is source. Widened to "every
changed file is a data file", and the rule was changed after seeing its output.

---

## Iteration 2 — the staged pipeline, and where a model earns its call (2026-08-29)

**Tried.** A → B → C → D → verdict → E, with the model used only where
interpretation is needed. Signals (counts, latencies, first-contribution rates)
and Stage D verification run no model at all. Model choice was made per stage and
empirically, starting everything on the small model and promoting only on
evidence.

**Why.** Two questions need judgement arithmetic cannot reach: what kind of
repository this is, and what a pull request thread reveals about an outsider's
odds. The rest is counting, lookup, or prose.

**Evidence — a pilot on four repositories deliberately outside the scored
pool**, so inspecting behaviour during development cannot tune the agent against
graded cases:

| Repo | Verdict | Rule that fired | Findings kept |
|---|---|---|---|
| `pallets/flask` | viable | 7 outsider merges from 111 people, median response 0.4 h | 15/15 |
| `microsoft/winget-pkgs` | not_viable | `repo_kind=registry` | 16/16 |
| `sindresorhus/awesome` | not_viable | `repo_kind=awesome_list` | 14/15 |
| `tensorflow/tensorflow` | insufficient_evidence | 4/4 ignored is too thin to call hostile | 8/8 |

All four correct, at **$0.0484 for four full pipeline runs** — about $0.012 a
repository. The small model is sufficient at every stage including thread
interpretation: on `winget-pkgs` it wrote, unprompted, that "most interaction is
automated (wingetbot/validation logs). Maintainers rarely provide substantive
human feedback" — the exact distinction the stage exists to make.

**A guard the pilot bought.** `tensorflow/tensorflow` is 97% bot traffic, leaving
four outsider threads, all ignored — and the hostility rule fired on four data
points. It now requires at least eight attempts before calling a repository
hostile, and returns insufficient evidence below that. Caught on the development
set, which is what a development set is for.

**Decision.** Kept.

---

## Iterations 3–4 — the first evaluation, and attacking our own metric (2026-08-29/30)

**Tried.** Score four methods over the committed pool against L1: popularity
(stars), the baseline solution, Holt, and a name-only memorisation probe. Then,
before shipping, score the trivial strategies — answer "viable" to everything,
answer "not viable" to everything.

**Evidence. The metric broke immediately.**

| Method | MCC | Balanced acc. | F1 |
|---|---|---|---|
| always "viable" | 0.00 | 0.50 | **0.78** |
| always "not viable" | 0.00 | 0.50 | 0.00 |
| baseline solution | 0.33 | 0.67 | 0.74 |
| **Holt** | **0.49** | **0.71** | 0.84 |

**A constant answer scores F1 0.78 and beats our own baseline solution.** The
graded pool is 14 positive against 8 negative, so F1 rewards a method for
recommending everything, and precision@10 is nearly as bad — the constants score
0.60 against 0.70 for every real method.

**Decision.** Matthews correlation becomes the primary metric, with balanced
accuracy alongside it. Both are 0.00 and 0.50 for any constant strategy, so
neither can be gamed by a method with no opinion. Under MCC the same system on
the same data is worth **0.49 over a constant** rather than F1's 0.06. The
constant strategies stay in the results table permanently — a reader should be
able to see the floor rather than take our word for where it is.

**A component measured and left out.** Stage C's sentiment signals were computed
and never read by `verdict.py`, which looked like a wiring bug worth fixing.
Measuring first showed it was not: threads in *non*-opportunities read as more
welcoming (0.75 against 0.54) and more likely to offer a route in.
`runelite/plugin-hub` scores 1.00 on "offers a real route in"; `NixOS/nixpkgs`
scores 0.50. Registries read as maximally welcoming *because they are easy*.
Wiring it into the verdict would have made Holt worse. Left out of the decision,
and left computed, because it is the most useful thing in the report for a human
reader.

---

## Iteration 5 — a pre-registered experiment that failed (2026-08-30)

**Tried.** Make Stage C load-bearing after all. Its sentiment signals were
inverted, but one structural feature did separate the classes: **review ratio**,
the share of merges that received substantive review — 0.68 for genuine
opportunities against 0.50 for the rest.

**Why it was pre-registered.** The feature was chosen *after* seeing it separate
on the scored pool. Fitting a threshold there as well would have made any
reported gain a measurement of our own hindsight. So the rule, the threshold, the
direction it could act in and three numeric predictions were written to
[`eval/PREREGISTRATION.md`](eval/PREREGISTRATION.md) and committed before a line
of it was implemented. Threshold 0.5, the natural midpoint, not a searched value.
The rule could only ever *withhold* a recommendation, never create one.

**Evidence.**

| | MCC | Sensitivity | Specificity |
|---|---|---|---|
| without the rule | **0.49** | 0.93 | 0.50 |
| with the rule | 0.19 | 0.57 | 0.62 |

| Prediction, recorded in advance | Outcome | |
|---|---|---|
| Specificity rises above 0.50 | 0.62 | held |
| Sensitivity falls | 0.93 → 0.57 | held |
| MCC moves by less than ±0.15 | −0.30 | **failed** |

Specificity improved exactly as predicted, and it was bought at roughly five good
recommendations per bad one avoided: of six changed verdicts, five were genuine
opportunities withheld — including `NixOS/nixpkgs`.

**Decision: removed.** `verdict.py` is byte-identical to before the experiment.
The pre-registration file stays with the result appended; a pre-registration
quietly deleted when it fails is worse than none.

**What it taught us, which is the point.** Absence of in-thread review is not
absence of engagement. `nixpkgs` merges a great deal of outsider work with no
visible review comment because the review happened in the issue, on a mailing
list, or between people who already trust each other. **A pull request thread
records the merge, not the conversation that produced it.** That is the same
lesson as the inverted-sentiment finding, reached independently: what a thread
*displays* is a poor proxy for what a project *does*. It is why Stage C informs
the report a human reads while the verdict rests on repository kind and
arithmetic.

---

## Iterations 6–8 — a positive control, variance, and a red-team pass (2026-08-30)

**A positive control, because every result so far measured the ability to
reject.** A detector answering "not viable" to everything would have aced the
evaluation to this point. Three repositories nobody would argue about —
`home-assistant/core`, `rust-lang/rust`, `astral-sh/uv` — labelled by the same L1
pipeline and assessed as a declared, hand-picked control outside the scored pool.
**Holt recovers 3/3; the baseline 1/3**, returning *insufficient evidence* for
two of the most contributor-friendly projects in open source, because neither
README says so. That is the failure this project is built around, seen from the
positive side.

**Variance, because every number until now came from one run.** Three complete
independent runs of every method, $1.08. Holt's worst run beat the baseline's
best with no overlap — a claim a single run could not have supported. The
architectural result was the sharper one: the baseline puts the whole decision
inside one model call and wobbles on nine of twenty-two repositories between
runs, where Holt puts it in `verdict.py`, a plain function that cannot disagree
with itself. All headline figures became mean ± half-range from here on.

**A red-team pass, because everything so far had been measured by the people who
built it.** A reviewer with the rubric, read-only access, and instructions to
verify every number rather than trust the docs. Its durable finding was about
which axis the uncertainty was reported on: run-to-run intervals say how much the
model wobbles, not whether 22 repositories support a difference. Measured over
*repositories* — 20,000 bootstrap resamples plus exact McNemar — the aggregate
difference at this pool size is not statistically separable. The README says so
and `eval/stats.py` prints it.

**Decision.** All kept. The uncertainty statement is now the one the sample can
carry, and hand-picked cases live in a table labelled hand-picked.

---

## Iteration 10 — the same-evidence ablation (2026-08-30)

**Tried.** A single prompt given *everything Holt sees* — the same arithmetic
signals, the same twelve-thread digest Stage C reads, the same three-valued
verdict — to isolate what the orchestration is worth once evidence access is held
constant.

**A naming correction made before reporting the numbers.** This is an
**ablation, not a baseline**. The brief defines a baseline as a reasonable basic
way to handle the task *before* using the solution, and a person assessing a
repository does not have a temporal-holdout GraphQL crawler that reconstructs
pre-cutoff pull request threads. That evidence layer *is* Holt. The baseline
remains README-and-metadata.

**Evidence — where the improvement comes from, which is what an ablation is
for:**

| Change | MCC |
|---|---|
| README-only → the same evidence Holt reads | **0.21 → 0.53** |
| single prompt → staged pipeline | 0.53 → 0.49 |

Reading contribution history instead of a landing page is worth **+0.32 MCC**. On
this pool, at this point in the project, the orchestration on top of it bought no
measurable accuracy — and what it did buy showed up in a different column: 22/22
run-to-run verdict stability against the ablation's 20/22 and the baseline's
18/22.

**Decision.** Both results published, including the uncomfortable half. It is
also the entry that pointed at the next one: specificity sat at 0.50–0.54 across
*every* method including the constants, and rejection is the thing this project
exists to do.

---

## Iteration 11 — the rubber-stamp rule, validated out of sample (2026-08-30)

**Shipped.** Reject when `reviewed_share < 0.20` **and** `merge_rate > 0.60`:
contributions land easily and nobody looks at them. Both halves are required.
Validated on the second pool before shipping — **specificity 0.58 → 0.83**, all
three pre-registered predictions holding — and the test suite pins the case that
killed the previous attempt: `nixpkgs` merges without visible review but is
*hard* to land in, so it is not a rubber stamp.

This is the largest accuracy gain in the project, and it is a written rule the
model cannot override.

**Also shipped: the contributor's time budget as a parameter, not an
assumption.** Every time-shaped threshold scales from `--days` (default 7). A
maintainer whose median reply is five days is fine with three months and useless
with three days — the same repository, a different answer. It is also the
clearest thing the orchestration buys that a single prompt cannot: **re-running
at a different budget costs zero model calls**, because the findings are already
computed and only `verdict.py` re-runs. A prompt has to pay for the whole
assessment again.

**A new evaluation dimension: evidence integrity.** Accuracy is not the only
thing a report can be wrong about — a claim can cite a pull request that does not
exist, or quote words never said in it, and neither appears in a confusion
matrix. Measuring it produced two results we had predicted wrong. The
evidence-matched prompt does *not* fabricate citations: 100% of its 638
references resolve, because it copies ids it was shown. The real difference is
**auditability** — it emits no quotes at all, so there is nothing to check. Holt
makes claims that can be falsified; the prompt makes claims that cannot. And our
own quote fidelity was 80%, not the near-perfect we had assumed, because Stage D
checked that an id *exists* and never that the evidence said what the claim said.
That gap is measured here and closed in iterations 23–26.

---

## Iterations 12–14 — Path Finder: cut on its own pre-registered condition (2026-08-30)

**Tried.** Extend Holt from a verdict to an action: given a repository judged
viable, rank the issues open at the cutoff by how likely an outsider is to land a
merged pull request resolving them.

**Ground truth was designed before any implementation**
([`eval/PATHFINDER-DESIGN.md`](eval/PATHFINDER-DESIGN.md)), reusing L1's outsider
definition so there is one definition rather than two, with four cut conditions
written down. Feasibility was counted, not assumed: 1,184 candidate issues, 114
realised, a 9.6% base rate.

**Evidence, combined across both pools, 25 scorable repositories, 3,613 issues
ranked** — the combined-pool rule was fixed before the second pool was scored,
precisely so we could not choose whichever pool flattered the feature:

| Method | precision@3 |
|---|---|
| random (base rate) | 0.151 |
| recency | 0.160 |
| **`good first issue` label** | **0.187** |
| **Holt** | **0.173** |

Paired over repositories, Holt − `good first issue` is −0.013, 95% CI [−0.133,
+0.120], sign test p = 0.51. After ranking 3,613 issues we cannot distinguish our
ranking from a label GitHub already puts on the issue for free.

**Decision: cut condition 2 met, and honoured.** `find_paths` came out of the
shipped pipeline. **Cost to find out: $0.14 and about four hours** — against a
confident-sounding ranking a judge could have falsified in ten minutes with a
label filter.

**Then a five-minute query changed what shipped.** Before cutting, we asked one
thing about the *inputs* rather than the outcomes: how many of those 25
repositories have any beginner-labelled issue at all? **13 have none; 17 have
fewer than three**, so the label cannot fill a top-3 there. On all 17 of those,
`good first issue` scored identically to recency, to the decimal — it *is*
recency wearing the label's name. So Path Finder ships after all, behind a flag,
and every rendered ranking carries this, emitted by the renderer so that no code
path can print a ranking without it:

> **This ranking is not measurably better than picking at random.** precision@3
> was 0.173 for this ranking, 0.187 for GitHub's `good first issue` label and
> 0.151 for a random pick — differences well inside noise. It is printed anyway
> because 13 of those 25 repositories had no beginner-labelled issue at all.

A test asserts both that the disclaimer accompanies any ranking and that its
printed numbers track the recorded measurement, so the two cannot drift.

---

## Iterations 15–16 — two discovery features, both cut by a cheap comparator (2026-08-30)

**Tried, first: personalised progression.** Not "find an approachable issue" —
the prototype tied GitHub's label at that because it never saw who was asking.
Instead: *given what this person has already merged here, which open issues are a
sensible next step?* A question no label answers, because it is a property of the
pair rather than of the issue. Pre-registered in full before a line of code
(`eval/PREREGISTRATION-3.md`): six arms, eight feature weights, numeric
predictions, decision rule, four binding cut conditions.

**A confound found before building, which would have faked a large win.** Of the
655 issues an existing contributor later closed with a merged pull request, **299
— 46% — were issues that same person had opened.** Predicting that somebody fixes
the bug they filed is not a recommendation; the intent is already legible in
pre-cutoff evidence. Excluded from both the label and the candidate set.

**Evidence.** Out of sample the weighted scorer reached hit@10 0.205 against the
`path_overlap` heuristic's 0.193 — inside noise, 3W/2L/83T, p = 1.000 — and
combined over both pools it *lost*: 0.211 against 0.234. But the finding is the
other row:

> `holt_full_repaired` − `holt_repaired` = **+0.000. 0 wins, 0 losses, 88 ties.**
> The model call — one competence profile per contributor, built from their
> merged pull requests and the review feedback on them — moved not one ranking
> position for any of the 88 contributors.

The model had **strictly more context** than the arithmetic — history, files,
review threads, a structured profile — and returned an identical ranking 88 times
out of 88.

**Tried, second: which repositories should you even consider?** The evidence
looked strong: of 74 contributor→new-repository transitions in the pool, **66
landed in an L1-viable repository — 89%** against a 51% base rate.

**It survives none of four controls**, all reproducible with
`eval/mover_controls.py`, which re-derives the headline first, because a
refutation that cannot reproduce what it refutes is not one:

- **It is one programme, not a preference.** 66 of the 74 transitions have both
  endpoints inside a single nine-repository cluster, and that cluster is a
  summer-of-code cohort with a points leaderboard. Programme membership causes
  both the move and the merge. Nothing was chosen.
- **Outside the cluster the signal inverts.** Eight transitions remain and two
  land viable — one of which is GitHub's deleted-account placeholder, which is
  not a person, and the other a maintainer moving inside his own ecosystem. The
  independent evidence is one transition.
- **The base rate was the wrong null.** A mover can only appear where an
  outsider's pull request merges, and viability is *defined* by outsider merges.
  Weighting by where merges actually happen, 69% of post-cutoff merge slots sit
  in viable repositories, not 51%.
- **The cheap comparator wins outright.** Leave-one-out cohort co-occurrence —
  *"where else did people from your repository go"* — predicts the exact
  destination top-1 22% of the time and top-3 45%. A viability filter only
  narrows 69 repositories to 35. The free heuristic answers a strictly harder
  question, and answers it well.

**Decision: both cut.** The second cost ninety minutes and no model calls,
because the comparator ran before a line of the feature existed. **Five
experiments have now been cut by their own pre-registered rules, and one
shipped.** That ratio is the project.

---

## Iterations 17–19 — what survived the kills, shipped (2026-08-30/31)

Each of these is the part of a cut experiment that beat its comparator, or a
capability that makes no claim a comparator could beat.

**Where outsider work actually landed.** Every pull request Holt reads carries
its file list; it was used to decide whether a diff was substantive, then
discarded. Now it is counted, over outsider threads only:

```
pkgs/by-name      13 merged of 62 attempted (21%)
pkgs/top-level     3 merged of 11 attempted (27%)
never landed:  maintainers/maintainer-list.nix (11), pkgs/applications (6),
               pkgs/build-support (6), doc/release-notes (2)
```

That is the sentence a newcomer most needs about a 200,000-file tree and cannot
get anywhere — GitHub does not show it and `CONTRIBUTING` does not say it. Pure
arithmetic, no model call. An attempt counts once per pull request rather than
per file; outsider status is decided per thread in time order, so one prolific
newcomer's fortieth merge cannot make a repository look open; and a directory is
named as "never landed" only when at least two people tried.

**`holt compare a b c`.** A shortlist is the real situation. It sorts nothing —
rows come out in the order asked for, because sorting is a claim — and the `why`
column is the rule that fired, so the comparison is on the deterministic part
rather than on prose.

**`holt discover`.** Iterations 15–16 cut *inferred* profiles on the data: the
median contributor in our pool has one merged pull request and five touched
files, and 98% of cross-repository area overlap was generic-path collisions
(`src`, `docs`, `tests`). Inferring "you work on Python developer tooling" from
one pull request would be invention, so `holt profile` asks instead — four
questions, stored locally — and every question maps to something that changes the
output or is not asked. Experience level is deliberately absent: nothing
downstream could map it to a threshold, so asking it would be decoration.

**The structural fact that makes screening free:** `verdict.py` needs exactly one
model-derived input, `repo_kind`. Every other rule — rubber-stamp, hostile,
slow-response, the outsider-merge floor — is arithmetic over crawled signals. So
discovery sources candidates from GitHub search, screens them at one page of
threads with **zero model calls**, and spends model money only on the survivors,
re-crawled at full depth. In the recorded demo session, screening rejected 9 of
25 candidates at **$0.00**, and five survivors were analysed at full depth for
$0.079 total.

**`holt next <repo> --as <login>`.** Iteration 15 cut the weighted scorer for
failing to beat `path_overlap` — *open issues naming a file or directory you have
already worked on here* — and the winning rule was discarded along with the
loser. It ships now, semantically identical to the one the harness measured, with
the claim stated exactly: best of five methods tried, hit@10 **0.234** against
0.211, 0.188 and chance at 0.172; +0.06 over chance on an interval that spans
zero. The renderer emits that measurement with every ranking, so no code path can
print the order without the number that says how well it works. No model call
anywhere in the path.

---

## Iteration 21 — the model becomes a choice, the benchmark stays pinned (2026-08-31)

`holt models` lets a user swap the model behind every stage: other OpenAI models,
Claude via the Anthropic SDK, and any OpenAI-compatible endpoint. Per-stage
overrides ride on the `STAGE_MODELS` seam that already existed; `model.py`
remains the only file that touches an LLM, and the `complete()` contract holds
across providers.

**The design decision that matters: the library never reads the user's model
configuration on its own.** Every committed trajectory, every benchmark number
and every replay was produced under pinned dated model ids, and an eval script
silently inheriting somebody's local Ollama config would be exactly the
reproducibility failure this project is built to prevent. Only the CLI opts in. A
test proves the library resolves the pinned defaults even when a config file
exists on disk, and another that replay keys are byte-stable under them. Costs
for unpriced models are recorded as $0 and labelled "unknown" rather than
invented.

---

## Iteration 22 — the frozen benchmark (2026-08-31)

**Tried.** Three live runs per pool, both pools, on the shipped prompts and rules
— run *after* the narration and wording changes, precisely so it measures what
ships. $3.50. Every run's recordings are committed and replay-verified: a judge
reproduces every number below with no key and no spend
(`eval/harness.py --replay --run-tag run1` … `p2r3`).

| MCC, mean ± half-range | Pool 1 (n=22) | Pool 2, out of sample (n=33) |
|---|---|---|
| name-only probe | +0.16 ±0.03 | +0.10 ±0.02 |
| baseline | +0.09 ±0.09 | +0.21 ±0.02 |
| same-evidence ablation | +0.60 ±0.11 | +0.32 ±0.07 |
| **Holt** | **+0.61 ±0.00** | **+0.63 ±0.00** |

- **Specificity 0.75 in sample, 0.83 out of sample** — the rubber-stamp rule's
  pre-registered number, frozen into the committed benchmark, against the 0.50
  coin flip every method showed before it.
- **Verdicts identical on all 55 repositories, all three runs, both pools.** The
  baseline changed its answer on 16 of 55. Determinism was a design claim in the
  first commit of this project; it is now a measured 55/55.
- **The ablation stops tying out of sample.** The same evidence in one prompt
  holds up in sample (+0.60) and falls to +0.32 on the pool it was never tuned
  on, against the pipeline's +0.63. The written rule layer is what generalises.
- **The result does not depend on our own label definition.** L1's two filters
  are ours, so both were dropped in turn and everything re-scored: Holt leads
  under every ground-truth variant, worst case +0.39 against +0.28.
- Repository-level uncertainty stays reported as the sample can carry it:
  bootstrap difference +0.42 to +0.59, P(difference ≤ 0) = 0.04–0.08.

**One claim did not survive re-measurement, and is retired everywhere.** Holt
rejects 4 of 5 traps — high-volume repositories that merge nothing qualifying —
in every run ever recorded. The earlier significance test paired that against a
baseline that rejected 0 of 5; the frozen baseline rejects 2–3, which is model
drift between recording sessions and exactly the hazard a frozen replay exists to
surface. The stable statement, and the one now used everywhere: **Holt rejects 4
of 5 every time; the baseline wanders between 0 and 3 depending on the day.**

---

## Iterations 23–26 — hardening the report against the model behind it (2026-08-31)

Running the pipeline under a deliberately weak local model (a 3B `llama3.2`)
produced three reports that were wrong in three different ways — a software
project classified `registry`, `pytorch/pytorch` described as "a mirror of the
official PyTorch repository", and a report reaching the reader with **zero**
surviving evidence claims. Each failure was worth a guard.

**The deterministic half held in all three**, which is the design working:
`psf/requests` still came out `viable` on 13 merges by 13 people at a 4.9 h
median first reply, with no model able to move it. Stage D behaved as specified,
dropping every unresolvable citation rather than softening it.

**The report now names the model that wrote it.** `Assessment` carries the model
ids that actually answered, recorded at the one seam every call passes through,
and the footer prints them. On a replay these are the ids from the recording, not
whatever the reader has configured today.

**A quotation that is not in the record it cites is now dropped**, using the
*same* matcher `eval/evidence_integrity.py` measures with, imported rather than
reimplemented, so the metric and the guarantee cannot drift apart. Over all 69
committed recordings, 994 claims, **9 removed** — including one quotation that
resolves, reads perfectly, and belongs to a different pull request. Raw model
fidelity is 514/523 (98%); the report's fidelity is 100% by construction, and the
number worth reading is the 9 the reader never sees.

**A report that lost every claim now says so.** When findings existed and none
survived, the page opens with it rather than presenting an empty evidence list,
which a reader would otherwise read as *there was little to say* — the opposite
of what happened. The deterministic half is explicitly not disowned along with
the prose.

**And the one field that could decide alone can now be contradicted.**
`repo_kind` is the only model-derived input that returns `not_viable` before any
arithmetic runs, and Stage D cannot check it — a classification is not a
quotation, so a model that answers `mirror` while citing a real README produces a
claim that verifies perfectly and is false. The evidence now contests the
*consequence*: a catalogue entry lands in one directory; a mirror does not merge
outsiders' pull requests. Where the evidence disagrees the field is **dropped** —
no verdict asserted in its place, the arithmetic decides, and the disagreement is
printed where a reader can argue with it. That is `CLAUDE.md`'s standing rule for
contradictory sources, finally applied to the field that was exempt from it.
Pre-registered ([`eval/PREREGISTRATION-4.md`](eval/PREREGISTRATION-4.md)); one of
four predictions failed, on a criterion that misfired on a correctly-classified
registry, and the pre-registered consequence was that the criterion does not
ship. It did not.

**Nothing measured moved.** The guards are verdict-neutral by construction — a
test asserts `verdict.classify` reads only `repo_kind` and `is_archived` from
findings — and the frozen benchmark replays unchanged: pool 1 **0.61**, pool 2
**0.63**.

---

## Iteration 27 — scoring the report, not just the verdict (2026-08-31)

**Tried.** Add a third measure to evidence integrity: **yield**, the number of
*checkable* statements a report makes per repository — where checkable means the
cited id resolves and, if words are attributed to somebody, they said them.

**Why.** Every headline number in this project is MCC on a three-valued verdict,
and `verdict.py` decides that with arithmetic. An assessor reading only the
verdict metrics concludes the model layer is decorative. That conclusion follows
from what was measured, not from what the thing does: the deliverable is an
*evidence-backed written assessment*, and no arithmetic has ever produced one.
The verdict axis was the only axis being scored.

**Evidence** (`eval/evidence_integrity.py`, replay, $0), over both pools and all
six frozen runs:

| | reports | resolve | faithful | checkable/report |
|---|---|---|---|---|
| **holt** | 55 | 100% | 99% | **11.8** |
| same-evidence ablation | 55 | 100% | no quotes | 3.4 |

**The correction the count forced, which a rate would have hidden.** The ablation
is *not* careless about the ids it uses — every reference it makes resolves,
100%. Its failure is not making one: **273 of its 832 statements, 33%, cite
nothing a reader could open.** A resolution rate cannot show that, because a
method that cites once and correctly scores 100% on it. Yield is a count, so
writing nothing scores zero.

**What this does and does not claim.** It does not rehabilitate the verdict
ablation: the rule layer still supplies the accuracy lead in sample, and every
sentence saying so stands. What is now measured is that the verdict was never the
whole deliverable — on the report itself the ordering is reversed, and the rule
layer scores **zero**, because arithmetic does not cite. Two axes, two different
winners, both published.

**Decision.** Kept. This is the measurement that should have existed before the
ablation result was published rather than after: the finding was reported
honestly on the only axis that had a metric, and the missing axis was the one the
model owns.

---

## Iteration 28 — the ablation ships as a mode (2026-08-31)

**Tried.** `holt analyze <repo> --no-model`: the verdict from the rules alone. No
API key, no spend, no model call anywhere. Stages A, B, C and E do not run;
`verdict.py` decides on the same `Signals` from the same evidence.

**Why.** A finding that large about your own architecture should change the
architecture rather than only the write-up. If the written rules are what decide,
the verdict must be obtainable without a model — and the failure mode where the
key is missing or the provider is down becomes a documented mode instead of a
crash.

**`is_archived` never needed a model.** Stage A was asking a model to read a
boolean the provider already had. In this mode it is taken from the record and
cited to it — the clearest single illustration of why the stages measured small
in sample: part of what they were doing was not model work.

**Evidence — and it corrects the claim we were about to ship.** The first draft
of the mode's own text generalised the in-sample ablation. Measured against the
same ground truth on both pools:

| | Pool 1 (n=22) | Pool 2, out of sample (n=33) |
|---|---|---|
| Holt, full pipeline | **+0.61** | **+0.63** |
| `--no-model` | +0.60 | +0.55 |
| gap | −0.01 | **−0.08** |

**In sample the model stages are worth one point of MCC; out of sample they are
worth eight.** Specificity 0.63 against 0.75 in sample, 0.75 against 0.83 out of
sample. Both numbers are printed in the mode's own "what could not be determined"
section, so no reader gets the friendlier one alone.

**What the mode loses, which is the larger part.** Zero citable statements
against the full pipeline's 11.8 per report. No thread quotes, no `repo_kind`, no
prose. The report says so in those words rather than presenting a thin page as a
complete one.

**Decision.** Ships. **Cost: $0.** No model was called, which is the point.

---

## Iteration 29 — the guide for someone who just wants to use it (2026-08-31)

`REPRODUCTION.md` had become the only entry point, and it is written for a
judge: a clean machine, a test count, six replay tags, a pool draw, a labels
re-run. Nothing on that page answers *"I have a week, is this repository worth
it?"* — the question the product exists for. The user we wrote the README's
"who this is for" section about had no page to land on.

`USAGE.md` is that page. Install, ask about one repository, read the three
headlines and what each section is for, `--days` for the budget you actually
have, `compare` for a shortlist, `discover` when you have none, `next` after
you have landed something, and the free `--no-model --live` path for a reader
with a GitHub token and no model key. It states the one number a user will act
on — balanced accuracy 0.80 in sample, 0.82 out of sample, so roughly a fifth
of calls are wrong — because a filter that hides its error rate is worse than
no filter.

The failure recorded in iteration 24 is exactly the one this page invites: a
documented command nobody runs. So `tests/test_docs_claims.py` now parses
`USAGE.md` alongside the reproduction guide and runs every keyless command
either one prints, and recomputes the balanced accuracy figures from the frozen
runs. The paid and interactive commands (`--live`, `tui`) are skipped by name.

**No benchmark number moved.** This is a documentation split, recorded here
because "the intended user has no page to start from" was a real defect and the
log is meant to include the ones that were not measurable.

Separately, the self-assessment moved out of the repository altogether. It was
a working document about our own gaps — including that a PAT and an API key had
appeared in working sessions — and it does not belong in a public clone. Its
name is in `.gitignore` now, so it cannot come back by accident.

---

## The main failure mode

**A sentence is not an assertion, and unverified sentences are where this system
degrades — in the model's prose first, and in our own documentation second.**

Everything Holt guards, it guards mechanically. Evidence passes one provider that
asserts the temporal holdout on every record. Stage D drops a finding whose
citation does not resolve, and since iteration 24 one whose quotation is not in
the thread it cites. Replay refuses to serve a recording whose prompt has
changed. Every one of those guards is covered by a test, and each of them held
through the weak-model runs that broke everything around them.

What none of them guarded was prose. A model's narration can quote a statistic
nothing backs — and the same shape one level up, a number written into a README
on the day it was measured stays there after the thing it measured is re-run, and
no test fails. That is how this repository came to state its own verdict
stability three different ways at once, in three files, while all three
underlying measurements were correct. The measurements were never the problem.
The sentences about them rotted, silently, because nothing was watching whether a
published claim was still true.

**What we changed because of it.** The guards now cover the claims.
`tests/test_docs_claims.py` recomputes the verdict-stability counts and every
headline MCC from the committed results and fails if `README.md` or
`ASSESSMENT.md` disagrees; it parses `REPRODUCTION.md` for the commands it tells
a judge to run and runs each one, including under a model chosen with
`holt models`; and it checks the promised test count against what the suite
actually collects. That is 21 tests whose only job is to make a stale sentence a
build failure — and writing them turned up two documented commands that no longer
did what they said, which is exactly the class of defect that fails for nobody
except the person reading the docs for the first time.

---

## Hot take

**Holt is not a smarter analyst, and we measured that four separate times.**

The staged pipeline was the part we assumed was doing the work. It is not. One
prompt handed the same evidence matches it in sample. Ablating the model stages
costs +0.01 MCC in sample. A contributor-profile model call moved 0 of 88
rankings. What actually separates Holt from a chat window is duller than
intelligence and much harder to fake:

- **An evidence assembly nobody will do by hand** — a median of 642 records and
  253,000 characters per repository, 44× what a person can paste into a prompt.
  Worth **+0.32 MCC** on its own, the largest single source of the gain over the
  baseline.
- **Claims that can be falsified.** Every statement carries an id that resolves
  to a real thread: **11.8** checkable statements per report against 3.4 for the
  same evidence in one prompt.
- **A verdict that is a plain function**, so it returned the identical answer on
  **55 of 55** repositories across three runs while the one-prompt baseline moved
  on 16.
- **The ability to say no, in a written rule the model cannot override** —
  specificity **0.58 → 0.83** out of sample, the single change that most improved
  accuracy.

And the model layer is not decorative — it is doing a different job from the one
we were scoring. It is worth +0.01 MCC in sample and **+0.08 out of sample**, and
it writes every checkable sentence in the report, where the rule layer scores
zero. We only learned that by building a metric for the axis we had not been
measuring.

**What we would build differently next time:** put the decision in code and the
model in front of the evidence, not the other way round — then score the thing
you actually ship, not just the part that fits in a confusion matrix. An agent's
guarantees are worth exactly as much as the tests on the claims you make about
them, and prose is where reliability goes to die.
