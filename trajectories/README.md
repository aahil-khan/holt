# Agent trajectories

Each file walks one run from the instructions the agent was given to the result
it produced, in the order it happened: the evidence it retrieved, what each
stage was asked and answered, which findings verification removed, and how the
rules turned what survived into a verdict.

All of it replays from committed fixtures and recorded model output, so nothing
here needs a key.

## The full pipeline, end to end

| Trajectory | Verdict | Why it is worth reading |
|---|---|---|
| [`is-a-dev/register`](is-a-dev__register.md) | `not_viable` | A registry with hundreds of merged outsider pull requests. The baseline solution calls it viable. |
| [`NixOS/nixpkgs`](NixOS__nixpkgs.md) | `viable` | A genuine opportunity that the naive label ranked 17th of 22. |
| [`SecureBananaLabs/bug-bounty`](SecureBananaLabs__bug-bounty.md) | `not_viable` | A thousand inbound attempts, nothing merged. |

Each covers Stages A, B and C (one model call each), Stage D verification (tool
calls, no model), the verdict function, and Stage E narration.

## The other prompted agents

| Trajectory | What it is |
|---|---|
| [comparison arms on `is-a-dev/register`](comparison-arms--is-a-dev__register.md) | all three scored comparison arms — `name_only`, `baseline`, `baseline_matched` — on the case where they disagree with Holt |
| [Path Finder on `NixOS/nixpkgs`](pathfinder--NixOS__nixpkgs.md) | ranking a repository's open issues by how likely an outsider is to land a fix; ships behind a flag that prints its own losing number |
| [contributor profile, `home-assistant/core`](profile--home-assistant__core__epenet.md) | turning one contributor's merged work into a competence profile for `holt next` |

Together with the pipeline files above, that is one reading copy per prompted
agent in the project. The one exception is `describe()`
(`src/holt/agent/progression.py`), which has no recorded calls because the model
call it wraps moved 0 of 88 rankings when measured and was cut — `holt next`
runs no model at all.

## The raw record

[`../fixtures/trajectories/`](../fixtures/trajectories/) holds every model call
made anywhere in the project, one JSON object per call with the full system
prompt, prompt, response and token usage. The benchmark directories carry all
seven scored labels for all 22 pool-1 repositories —

```
baseline 22   baseline_matched 22   name_only 22
classify 22   opportunity 22        outcomes 22   narrate 22
```

— with `pathfinder/` (57 calls), `progression/` (88), `discover/`, `control/`
and `dev/` alongside them.

## Retries, and where a human decides

**No retry appears in these trajectories because the design has nowhere to put
one.** Output shape is enforced at the API with a strict JSON schema, so a
malformed answer is impossible rather than retried; the only retries in the
system are transport-level (`max_retries = 4` on the client in
`src/holt/model.py`, for network and 5xx failures) and they never produce a
second answer to the same question. A stage that returns a finding whose
evidence does not resolve is not re-prompted either — Stage D drops the finding.
Verification subtracts; it never asks again.

**There is no human approval step mid-run because there is no consequential
action to approve.** Holt never writes to GitHub, opens a pull request or
contacts a maintainer; it reads public data. The human decisions are the ones
before and after: what to ask (`holt profile`, `--days`), whether to spend
anything at all (`--replay` and `--no-model` against `--live`), a cap on how
many full analyses a discovery session may run (`--survivors`), and reading the
evidence section before committing a week. In the terminal interface, the two
questions that destroy work — stopping a live run, quitting with runs in flight
— are confirmed before they happen.

Regenerate everything here with
`PYTHONPATH=. uv run python scripts/render_trajectories.py`.
