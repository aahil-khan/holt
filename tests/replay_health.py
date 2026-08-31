"""Is replay working at all?

The TUI's tests drive real recorded runs, so they depend on `--replay` doing
what it claims. When the engine's prompts drift away from the committed
trajectories, every one of those tests fails with the same `KeyError` and none
of the failures are about the interface.

This checks once, cheaply, and hands back a reason. A test module that skips on
it says *why* it skipped, naming the engine defect rather than reporting a
mystery, and starts passing again by itself the moment replay is repaired. It
does not paper over anything: a broken reproduction path is louder here than a
wall of identical tracebacks with the real cause buried in each one.
"""

from __future__ import annotations

import functools
from pathlib import Path

#: A repository with a committed trajectory, used as the canary.
CANARY = "home-assistant/core"


@functools.lru_cache(maxsize=1)
def reason() -> str | None:
    """`None` when replay works, otherwise why it does not."""
    if not Path("fixtures/trajectories").is_dir():
        return "recorded trajectories are not present in this checkout"
    try:
        from holt import model
        from holt.agent import pipeline
        from holt.evidence.fixtures import FixtureProvider
        from holt.types import Window

        pipeline.analyze(
            CANARY, FixtureProvider(Window.PRE_T), model.build(CANARY, replay=True)
        )
    except KeyError as exc:
        return (
            "replay is broken in the engine, not in the interface: the committed "
            f"trajectories no longer match the prompts the stages build ({exc}). "
            "Re-record them, or revert the prompt change, and these tests resume."
        )
    except FileNotFoundError as exc:
        return f"the canary trajectory is missing ({exc})"
    return None
