# Pre-registration 2 — rubber-stamp rejection

Written **2026-08-30, before pool 2 labels have been computed and before the
rule has been run against anything except the development pool.**

## The problem this addresses

Specificity is 0.50–0.54 for **every** method measured, including the constant
answers. Holt exists to reject repositories that look thriving and are not, and
it currently does so at close to chance. Sensitivity is 0.90+; saying yes is
easy. The thesis is unproven until rejection works.

## The principle

A repository where contributions land easily *and* nobody looks at them is
running a rubber stamp, not a review. Both halves are needed: landing easily
alone describes a welcoming project, and going unreviewed alone describes a
project whose review happens elsewhere (the lesson of pre-registration 1 —
`nixpkgs` merges without visible review because the conversation happened in the
issue). It is the **conjunction** that describes a pipeline where an outsider's
work is waved through without anyone engaging.

## The rule

Computed mechanically from pre-cutoff evidence, over *all* merged threads — not
from model judgement, and not from the 12-thread sample that pre-registration 1
used and which is the most likely reason that attempt failed:

    reviewed_share = merged threads with any non-bot reply from someone other
                     than the author / all merged threads
    merge_rate     = first-time merges / first-time attempts

> If the verdict would otherwise be VIABLE, and `reviewed_share < 0.20`, and
> `merge_rate > 0.60`, return NOT_VIABLE instead.

Thresholds are round and interpretable — "fewer than one in five merges drew any
human response" and "more than three in five attempts land". **They were chosen
after inspecting a grid on pool 1**, which is development data. That is fitting,
it is disclosed, and it is why pool 2 exists.

The rule may only ever *withhold or reject*; it cannot create a VIABLE verdict.

## Predictions, recorded before pool 2 labels exist

Measured on **pool 2**, which is hash-committed (`a7cd0a663121cb1c`), disjoint
from pool 1, and whose labels have not been computed at the time of writing:

1. Specificity on pool 2 rises above 0.60 (from the 0.50 baseline on pool 1).
2. Sensitivity on pool 2 falls by no more than 0.15.
3. MCC on pool 2 improves by at least +0.05.

## How this will be reported

**Pool 2 is the result.** Pool 1's improvement (0.49 → 0.61) is a development
figure produced by a threshold search on the same data and will be labelled as
such wherever it appears. If the rule fails on pool 2, it is removed and the
failure is a changelog entry, exactly as pre-registration 1 was.

## Why this differs from pre-registration 1, which failed

That rule used Stage C's *model-judged* outcomes over a 12-thread sample.
This one is mechanical and covers every merged thread. If it works where the
other did not, the difference is measurement, not concept — and that is itself
worth reporting.
