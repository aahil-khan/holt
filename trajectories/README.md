# Agent trajectories

Each file walks one complete run from the instructions the agent was given to the verdict it produced, in the order it happened: the evidence it retrieved, what each stage was asked and answered, which findings verification removed, and how the rules turned what survived into a verdict.

All of it replays from committed fixtures and recorded model output, so nothing here needs a key.

| Trajectory | Verdict | Why it is worth reading |
|---|---|---|
| [`is-a-dev/register`](is-a-dev__register.md) | `not_viable` | A registry with hundreds of merged outsider pull requests. The baseline solution calls it viable. |
| [`NixOS/nixpkgs`](NixOS__nixpkgs.md) | `viable` | A genuine opportunity that the naive label ranked 17th of 22. |
| [`SecureBananaLabs/bug-bounty`](SecureBananaLabs__bug-bounty.md) | `not_viable` | A thousand inbound attempts, nothing merged. |

Raw records for every repository, one JSON object per model call with the full request, response and token usage, are in [`../fixtures/trajectories/`](../fixtures/trajectories/).

Regenerate with `PYTHONPATH=. uv run python scripts/render_trajectories.py`.
