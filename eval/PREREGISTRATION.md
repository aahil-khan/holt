# Pre-registration — review ratio as a Stage C input

Written **2026-08-30, before implementing or running anything**, because the
feature was selected after observing that it separates the classes on the scored
pool. Fitting a threshold on that same pool as well would make any reported
improvement a measurement of our own hindsight.

## The principle, stated without reference to the data

A repository where merged contributions typically receive substantive review is
one where a newcomer's work will be *engaged with* rather than waved through or
ignored. Review is the mechanism by which an outsider's first contribution
becomes a second one. A repository that merges without reviewing is either
trivially easy to contribute to — a registry — or is not really reading what
arrives.

## The rule

    review_ratio = merged_after_review / (merged_after_review + merged_without_engagement)

computed over the pull request threads Stage C read, before the cutoff.

**Threshold: 0.5.** Chosen as the natural midpoint — a simple majority of merges
being reviewed — not by searching for the value that scores best.

**Where it acts:** Holt's weakness is specificity (0.50 against the baseline's
0.62); it over-recommends. So the rule may only ever *withhold* a recommendation,
never create one:

> If the verdict would otherwise be VIABLE, and review_ratio < 0.5, and the
> repository has enough threads to measure it (at least 4 merges), return
> INSUFFICIENT_EVIDENCE instead.

It cannot turn NOT_VIABLE into VIABLE, and it cannot turn INSUFFICIENT_EVIDENCE
into VIABLE.

## Predictions, recorded before running

1. Specificity rises above 0.50.
2. Sensitivity falls; some genuine opportunities become insufficient_evidence.
3. MCC moves by less than ±0.15 either way.

## How this will be reported

The result is reported **whatever it is**, including if it makes Holt worse, and
this file stays in the repository either way. One run, no threshold search. If
the rule fails, it is removed and the failure becomes a changelog entry.

## Known limitation of this design

There is no truly held-out set. The development set is four repositories,
disjoint from the pool but too small to validate a threshold on. The honest
statement is: the *feature* was chosen after seeing pool data, the *threshold*
was not fitted, and the rule was constrained in advance to a direction that can
only cost us sensitivity.

---

# Result — recorded 2026-08-30, one run, no threshold search

**The rule failed and was removed.**

| | MCC | Balanced acc. | F1 | Sensitivity | Specificity |
|---|---|---|---|---|---|
| without the rule | **0.49** | 0.71 | 0.84 | 0.93 | 0.50 |
| with the rule | 0.19 | 0.60 | 0.64 | 0.57 | 0.62 |

Six verdicts changed. **Five of the six were genuine opportunities** that the
rule withheld — `DefiLlama/dimension-adapters`, `NixOS/nixpkgs`,
`Pasta-Devs/Marinara-Engine`, `anurag3407/career-pilot`,
`vellum-ai/vellum-assistant`. It caught one repository correctly
(`PerryTS/perry`) and cost five to do it.

## Predictions against outcomes

| Prediction | Outcome | |
|---|---|---|
| 1. Specificity rises above 0.50 | 0.62 | held |
| 2. Sensitivity falls | 0.93 → 0.57 | held |
| 3. MCC moves by less than ±0.15 | −0.30 | **failed** |

Two of three held. The one that failed is the one that mattered: the trade was
far worse than predicted, and specificity was bought at roughly five good
recommendations per bad one avoided.

## Why it failed

Absence of in-thread review is not absence of engagement. `NixOS/nixpkgs` merges
a great deal of outsider work without a visible review comment, because the
review happened in the issue, on the mailing list, or between people who already
trust each other. The pull request thread records the *merge*, not the
conversation that produced it.

This is the same lesson as the earlier sentiment finding, arriving from a
different direction: **what a pull request thread displays is a poor proxy for
what a project does.** Registries look welcoming because they are easy; mature
projects look unreviewed because their review is elsewhere.

## What was kept

Nothing was kept from this rule. `verdict.py` is unchanged from before the
experiment. This file stays in the repository because a pre-registration that is
quietly deleted when it fails is worse than none.
