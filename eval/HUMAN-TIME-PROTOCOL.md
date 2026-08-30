# Human-time comparison — protocol, written before the timing

The brief asks how much time the agent saves. This is the protocol, fixed before
any stopwatch started, so the number cannot be shaped by the result.

Not a user study. One person, self-timed, **n = 3 repositories**, reported with
that limit stated. The point is an order of magnitude, not a p-value.

## Repositories

Drawn from the committed pool so the same evidence is available to both sides.
Fixed here before timing:

1. `runelite/plugin-hub` — a trap: high merge rate, almost no human review
2. `NixOS/nixpkgs` — genuinely viable, and very large
3. `stablyai/orca` — small, quiet, and ambiguous

One of each kind, chosen so a good result on the easy case cannot carry the mean.

## The task, identically defined for both sides

> Decide whether an outside contributor with one week should attempt this
> repository, and write two sentences citing specific pull requests.

**Done** means a verdict of viable / not viable / insufficient evidence, plus at
least two citations of specific pull requests supporting it. Not "a feeling".

## Rules for the human side

- github.com only. No Holt, no fixtures, no scripts, no LLM.
- The clock starts at the repository page and stops when the two sentences are
  written.
- Stop at **20 minutes** and record it as "not reached" rather than pushing on.
  A censored observation is a result; an unbounded one is not.
- Record what was actually looked at — pull requests opened, whether
  CONTRIBUTING was read, whether reply latency was checked at all.

## Holt's side

`time PYTHONPATH=. uv run python -m holt.cli analyze <repo>` on a **live** run,
so the comparison includes crawling. Recorded separately: the replay path, which
is what a reader reproducing the work pays.

Already measured, for reference:
- Replay, no model and no network: **median 12 ms per repository**, whole pool in
  **0.9 s**.
- Evidence assembled: median **642 records, 253,000 characters, 200 pull-request
  conversations** per repository.

## What will be reported

Per repository: human minutes (or "not reached at 20"), Holt seconds, and
**whether the two verdicts agree**. Speed is worthless if the fast answer is
wrong, so disagreements are reported individually rather than averaged away.

## Declared in advance

- n = 3 is an illustration, not evidence of a population effect, and will be
  labelled that way wherever it appears.
- The timer is the author of the tool, who knows what to look for and is
  therefore **faster than a real first-time user**. This biases *against* Holt,
  which is the safe direction.
- If the human beats Holt, or finds something Holt missed, that goes in the
  README exactly as written here.
