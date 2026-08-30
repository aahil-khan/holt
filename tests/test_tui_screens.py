"""The screens, driven headlessly.

Skipped entirely when Textual is absent, which is the point of it being an
optional extra: a checkout that ran a plain `uv sync` runs the rest of the suite
and reports these as skipped rather than failing. Confirm with `pytest -rs`.

The async bodies are driven with `asyncio.run` rather than `pytest-asyncio`, so
these tests add no dependency of their own — not even a development one.

What is asserted is what the interface is *for*: that the drop is visible, that
the tool's negative result about itself is on the page without pressing
anything, and that an evidence id opens the record behind it. Pixel arrangement
is not asserted; it would break on every layout change and tell nobody anything.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

pytest.importorskip("textual", reason="the TUI is an optional extra")

pytestmark = pytest.mark.skipif(
    not Path("fixtures/trajectories").is_dir(),
    reason="recorded trajectories are not present in this checkout",
)

DROPS = "Sistema-de-certificacion-academica/Sistema-de-certificacion-academica"
RANKS = "home-assistant/core"


def screen_text(app) -> str:
    """Everything currently painted, as plain text."""
    return "\n".join(
        "".join(segment.text for segment in strip)
        for strip in app.screen._compositor.render_strips()
    )


def drive(body, repo: str, size=(100, 44)):
    """Run the app to completion in replay, then hand the pilot to `body`."""
    from holt.tui.app import HoltApp
    from holt.tui.session import RunOptions

    async def main():
        app = HoltApp(RunOptions(repo=repo, replay=True))
        async with app.run_test(size=size) as pilot:
            for _ in range(200):
                await pilot.pause(0.05)
                if app.session.finished:
                    break
            await pilot.pause(0.3)
            assert app.session.error is None, app.session.error
            await body(app, pilot)

    asyncio.run(main())


def test_the_live_view_shows_the_drop_and_names_the_id():
    async def body(app, pilot):
        text = screen_text(app)
        # The stage row reports the arithmetic Stage D performed.
        assert "15 findings → 14 kept, 1 dropped" in text
        # The lookup that failed is named, and labelled as a lookup, because no
        # model made this decision — the provider was asked and had no record.
        assert "lookup" in text
        assert "no_contributing_file" in text
        # And the consequence is spelled out rather than implied.
        assert "onboarding" in text
        assert "Dropped, not softened" in text

    drive(body, DROPS)


def test_the_assessment_shows_the_verdict_and_the_claims():
    async def body(app, pilot):
        await pilot.press("a")
        await pilot.pause(0.3)
        text = screen_text(app)
        assert "not viable" in text  # spelled out, never `not_viable`
        assert "claims, every one carrying an id that resolved" in text
        # The claim Stage D removed does not appear in the report.
        assert "no_contributing_file" not in text

    drive(body, DROPS)


def test_enter_on_a_claim_opens_the_record_behind_it():
    async def body(app, pilot):
        await pilot.press("a")
        await pilot.pause(0.3)
        await pilot.press("enter")
        await pilot.pause(0.3)
        text = screen_text(app)
        assert "resolved" in text
        # The inspector shows the id in full, not the folded display form, so
        # anyone checking a claim sees exactly what Stage D resolved.
        assert DROPS in text
        assert "github ·" in text

    drive(body, DROPS)


def test_the_measured_result_is_shown_in_full_and_not_behind_a_key():
    """The ranking's own negative result is visible without pressing anything,
    and it carries every comparator, including the two that beat it."""

    async def body(app, pilot):
        await pilot.press("a")
        await pilot.pause(0.4)
        text = screen_text(app)
        assert "WHERE TO START" in text
        assert "not measurably better than picking at random" in text
        for label in ("this ranking", "good first issue", "recency", "random"):
            assert label in text
        assert "0.173" in text and "0.187" in text
        assert "eval/pathfinder_harness.py --replay" in text

    drive(body, RANKS, size=(100, 220))


def test_an_unknown_event_renders_instead_of_raising():
    """A stage that learns a new event must not break a screen that predates it."""

    class Invented:
        __slots__ = ("stage",)

        def __init__(self):
            self.stage = "something_new"

    async def body(app, pilot):
        app.screen._handle(Invented())
        await pilot.pause(0.2)
        assert "Invented" in screen_text(app)

    drive(body, DROPS)
