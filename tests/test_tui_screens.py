"""The screens, driven headlessly.

Skipped entirely when Textual is absent, which is the point of it being an
optional extra: a checkout that ran a plain `uv sync` runs the rest of the suite
and reports these as skipped rather than failing. Confirm with `pytest -rs`.

The async bodies are driven with `asyncio.run` rather than `pytest-asyncio`, so
these tests add no dependency of their own — not even a development one. Motion
is switched off for the same reason: an assertion should not race a fade.

What is asserted is what the interface is *for* — that you can get from an empty
screen to an answer, that a recent answer is reused rather than re-bought, that
the drop is visible, and that a stored result never passes as a fresh one. Pixel
arrangement is not asserted; it would break on every layout change and tell
nobody anything.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

pytest.importorskip("textual", reason="the TUI is an optional extra")

os.environ.setdefault("HOLT_TUI_NO_ANIMATION", "1")

from tests.replay_health import reason as _replay_reason

pytestmark = pytest.mark.skipif(
    _replay_reason() is not None, reason=_replay_reason() or ""
)

DROPS = "Sistema-de-certificacion-academica/Sistema-de-certificacion-academica"
CLEAN = "home-assistant/core"


def screen_text(app) -> str:
    return "\n".join(
        "".join(segment.text for segment in strip)
        for strip in app.screen._compositor.render_strips()
    )


def stored(root: Path, repo: str, mode: str = "replay", age: float = 0.0):
    """Put one assessment in a private store, without running anything."""
    from tests.test_tui_store import entry

    from holt.tui import store

    keep = store.Store(root=root)
    keep.save(entry(repo=repo, mode=mode, age=age))
    return keep


def drive(
    body,
    store_root: Path,
    size=(100, 44),
    repo: str | None = None,
    stay_on_live: bool = False,
):
    """Open the app on a private store, then hand the pilot to `body`.

    `stay_on_live` holds the run screen open instead of letting it hand off to
    the report. Tests that assert on what the run *showed* need the screen that
    showed it; in normal use nobody wants to sit on a finished run.
    """
    from holt.tui import store
    from holt.tui.app import HoltApp
    from holt.tui.screens import live as live_screen
    from holt.tui.session import RunOptions

    options = RunOptions(repo=repo, replay=True) if repo else None
    original = live_screen.HANDOFF_SECONDS
    if stay_on_live:
        live_screen.HANDOFF_SECONDS = 3600

    async def main():
        app = HoltApp(options, assessments=store.Store(root=store_root))
        async with app.run_test(size=size) as pilot:
            await pilot.pause(0.2)
            await body(app, pilot)

    try:
        asyncio.run(main())
    finally:
        live_screen.HANDOFF_SECONDS = original


async def settle(app, pilot, limit: int = 300):
    for _ in range(limit):
        await pilot.pause(0.05)
        if app.session is not None and app.session.finished:
            break
    await pilot.pause(0.3)
    assert app.session is not None, "no run was started"


async def type_repo(pilot, repo: str) -> None:
    keys = {"/": "slash", "-": "minus", ".": "full_stop", "_": "underscore"}
    for char in repo:
        await pilot.press(keys.get(char, char))


# ─── home ───────────────────────────────────────────────────────────────────


def test_home_opens_on_an_empty_state_that_says_what_to_do(tmp_path):
    async def body(app, pilot):
        text = screen_text(app)
        assert "Assess a repository" in text
        assert "Nothing assessed yet" in text
        # The suggestion has a committed recording, so following it costs
        # nothing. An empty state must not send someone down a paid path.
        assert "astral-sh/uv" in text

    drive(body, tmp_path)


def test_typing_filters_what_you_already_have(tmp_path):
    stored(tmp_path, "astral-sh/uv")
    stored(tmp_path, "home-assistant/core")

    async def body(app, pilot):
        assert "astral-sh/uv" in screen_text(app)
        assert "home-assistant/core" in screen_text(app)

        await type_repo(pilot, "astral")
        await pilot.pause(0.4)
        text = screen_text(app)
        assert "astral-sh/uv" in text
        assert "home-assistant/core" not in text

    drive(body, tmp_path)


def test_a_repository_that_is_not_one_is_refused_before_the_network(tmp_path):
    async def body(app, pilot):
        app.screen.mode = "replay"
        await type_repo(pilot, "notarepo")
        await pilot.press("enter")
        await pilot.pause(0.3)
        assert "is not an owner/name" in screen_text(app)
        assert app.session is None, "nothing should have been started"

    drive(body, tmp_path)


def test_replay_without_a_recording_says_so_instead_of_failing(tmp_path):
    async def body(app, pilot):
        app.screen.mode = "replay"
        await type_repo(pilot, "nobody/nothing")
        await pilot.press("enter")
        await pilot.pause(0.3)
        assert "No recording" in screen_text(app)
        assert app.session is None

    drive(body, tmp_path)


def test_a_recent_assessment_is_reused_rather_than_re_bought(tmp_path):
    """The cache exists so asking twice costs once. It must also say so."""
    stored(tmp_path, CLEAN, age=120)

    async def body(app, pilot):
        app.screen.mode = "replay"
        await type_repo(pilot, CLEAN)
        await pilot.press("enter")
        await pilot.pause(0.5)

        assert app.screen.__class__.__name__ == "AssessmentScreen"
        assert app.session.restored_from is not None
        assert app.session._thread is None, "a cache hit must not start a run"

        text = screen_text(app)
        assert "min ago" in text
        assert "ctrl+r" in text

    drive(body, tmp_path)


def test_a_stale_assessment_is_not_reused(tmp_path):
    from holt.tui import store

    stored(tmp_path, CLEAN, age=store.DEFAULT_MAX_AGE_SECONDS + 60)

    async def body(app, pilot):
        app.screen.mode = "replay"
        await type_repo(pilot, CLEAN)
        await pilot.press("enter")
        await settle(app, pilot)
        assert app.session.restored_from is None

    drive(body, tmp_path)


def test_finishing_a_run_stores_it_and_home_lists_it(tmp_path):
    async def body(app, pilot):
        await settle(app, pilot)
        assert app.session.error is None, app.session.error
        await pilot.pause(0.9)
        assert app.screen.__class__.__name__ == "AssessmentScreen"

        await pilot.press("escape")
        await pilot.pause(0.6)
        assert app.screen.__class__.__name__ == "HomeScreen"
        text = screen_text(app)
        assert CLEAN in text
        assert "just now" in text
        assert "Worth your time" in text

    drive(body, tmp_path, repo=CLEAN)


# ─── the run ────────────────────────────────────────────────────────────────


def test_the_live_view_shows_the_drop_and_names_the_claim(tmp_path):
    async def body(app, pilot):
        await settle(app, pilot)
        assert app.session.error is None, app.session.error
        text = screen_text(app)
        assert "15 findings → 14 kept, 1 dropped" in text
        assert "onboarding" in text
        assert "Dropped, not softened" in text

    drive(body, tmp_path, repo=DROPS, stay_on_live=True)


def test_a_replay_never_shows_a_dollar_figure(tmp_path):
    """Nothing was bought, so nothing is priced.

    `ReplayModel` reports the token counts the original run recorded. Rendering
    their cost would tell a reader they had just spent money on a run that made
    no calls.
    """

    async def body(app, pilot):
        await settle(app, pilot)
        assert "$" not in screen_text(app)
        assert app.session.cost_usd == 0.0
        await pilot.pause(0.9)
        assert "$" not in screen_text(app)

    drive(body, tmp_path, repo=DROPS)


def test_a_failing_run_reports_it_and_stops_every_spinner(tmp_path):
    """A stage left turning after a failure reads as still working."""
    from holt.tui.widgets.stages import StageRow

    async def body(app, pilot):
        await settle(app, pilot)
        assert app.session.error is not None
        text = screen_text(app)
        assert "No recording" in text
        assert not [
            row for row in app.screen.query(StageRow) if row._state == "running"
        ]

    drive(body, tmp_path, repo="nobody/nothing", stay_on_live=True)


# ─── the report ─────────────────────────────────────────────────────────────


def test_the_report_leads_with_the_answer_and_keeps_its_limits(tmp_path):
    async def body(app, pilot):
        await settle(app, pilot)
        assert app.session.error is None, app.session.error
        await pilot.pause(0.9)
        text = screen_text(app)

        assert "Worth your time" in text
        assert "for a contributor with 7 days" in text
        assert "WHAT THE EVIDENCE SHOWS" in text
        assert "WHAT DECIDED IT" in text
        # A section in the body, in the engine's own order — not a footnote.
        assert "WHAT COULD NOT BE DETERMINED" in text

    drive(body, tmp_path, repo=CLEAN, size=(100, 90))


def test_a_stored_assessment_says_the_record_is_not_loaded(tmp_path):
    """Three states, three sentences.

    "does not resolve" is a statement about the evidence. A reopened assessment
    has no provider, so the honest thing is that nothing was looked up.
    """
    stored(tmp_path, CLEAN, age=60)

    async def body(app, pilot):
        app.screen.mode = "replay"
        await type_repo(pilot, CLEAN)
        await pilot.press("enter")
        await pilot.pause(0.5)
        app.inspect("repo:x:meta")
        await pilot.pause(0.4)
        text = screen_text(app)
        assert "not loaded" in text
        assert "does not resolve" not in text

    drive(body, tmp_path)


def test_an_unknown_event_renders_instead_of_raising(tmp_path):
    """A stage that learns a new event must not break a screen that predates it."""

    class Invented:
        __slots__ = ("stage",)

        def __init__(self):
            self.stage = "something_new"

    async def body(app, pilot):
        await pilot.pause(0.3)
        app.screen._handle(Invented())
        await pilot.pause(0.3)
        assert "Invented" in screen_text(app)

    drive(body, tmp_path, repo=CLEAN, stay_on_live=True)
