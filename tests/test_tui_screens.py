"""The screens, driven headlessly against a scripted run.

Skipped entirely when Textual is absent, which is the point of it being an
optional extra: a checkout that ran a plain `uv sync` runs the rest of the suite
and reports these as skipped rather than failing. Confirm with `pytest -rs`.

No engine. The events and the `Assessment` come from `tests/fake_run.py`, so a
prompt change in `holt.agent` cannot break a test about layout or wording. The
tests that genuinely exercise the engine live in `test_tui_observe.py` and are
gated on replay being healthy; the ones here are about the interface and run
regardless.

The async bodies are driven with `asyncio.run` rather than `pytest-asyncio`, so
these add no dependency of their own — not even a development one. Motion is
switched off for the same reason: an assertion should not race a fade.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

pytest.importorskip("textual", reason="the TUI is an optional extra")

os.environ.setdefault("HOLT_TUI_NO_ANIMATION", "1")

from tests import fake_run  # noqa: E402

CLEAN = fake_run.REPO


def screen_text(app) -> str:
    return "\n".join(
        "".join(segment.text for segment in strip)
        for strip in app.screen._compositor.render_strips()
    )


def drive(body, store_root: Path, size=(100, 44)):
    """Open the app on a private store, then hand the pilot to `body`."""
    from holt.tui import store
    from holt.tui.app import HoltApp

    async def main():
        app = HoltApp(None, assessments=store.Store(root=store_root))
        async with app.run_test(size=size) as pilot:
            await pilot.pause(0.2)
            await body(app, pilot)

    asyncio.run(main())


async def show_run(app, pilot, complete: bool = True, **script_kw):
    """Put a scripted run on screen and let the live view consume it.

    `complete=False` withholds the final `RunFinished`, which is how a test
    stays on the run screen: a finished run hands off to the report, and
    asserting on the screen you have just left proves nothing.
    """
    from holt.tui.screens.live import LiveScreen
    from holt.tui import events as _events

    script = fake_run.script(**script_kw)
    if not complete:
        script = [e for e in script if not isinstance(e, _events.RunFinished)]
    app.session = fake_run.session(queued=script)
    await app.push_screen(LiveScreen())
    await pilot.pause(0.3)
    return app.screen


async def show_report(app, pilot, **kw):
    from holt.tui.screens.assessment import AssessmentScreen

    app.session = fake_run.finished(**kw)
    await app.push_screen(AssessmentScreen())
    await pilot.pause(0.3)
    return app.screen


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

    drive(body, tmp_path)


def test_the_suggested_repository_really_is_free():
    """The empty state promises the suggestion costs nothing. It has to be true.

    It said `astral-sh/uv` for a while, which has no committed trajectory — so
    the one path offered to someone with nothing on screen was a paid one, or a
    dead end without a key.
    """
    from holt.tui.screens.home import SUGGESTION
    from holt.tui.session import has_recording

    assert has_recording(SUGGESTION), (
        f"{SUGGESTION} has no committed trajectory, so the empty state is "
        "offering a repository that cannot be replayed for free"
    )


def test_recent_rows_carry_the_verdict_the_age_and_the_mode(tmp_path):
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(fake_run.stored_entry(repo="astral-sh/uv", age=300))

    async def body(app, pilot):
        text = screen_text(app)
        assert "astral-sh/uv" in text
        assert "Worth your time" in text
        assert "5 min ago" in text
        assert "replay" in text

    drive(body, tmp_path)


def test_typing_filters_what_you_already_have(tmp_path):
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(fake_run.stored_entry(repo="astral-sh/uv"))
    keep.save(fake_run.stored_entry(repo="home-assistant/core"))

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
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(fake_run.stored_entry(repo=CLEAN, age=120))

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
    """Older than the window: the interface must not quietly serve it."""
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(
        fake_run.stored_entry(repo=CLEAN, age=store.DEFAULT_MAX_AGE_SECONDS + 60)
    )

    async def body(app, pilot):
        home = app.screen
        home.mode = "replay"
        assert home.app.store.fresh(CLEAN, "replay", 7) is None

    drive(body, tmp_path)


# ─── the run ────────────────────────────────────────────────────────────────


def test_the_live_view_shows_the_drop_and_names_the_claim(tmp_path):
    async def body(app, pilot):
        await show_run(app, pilot, drop=True)
        text = screen_text(app)
        assert "15 findings → 14 kept, 1 dropped" in text
        assert "onboarding" in text
        assert "Dropped, not softened" in text
        # Cited nothing at all is a different sentence from a broken id.
        assert "no evidence at all" in text

    drive(body, tmp_path)


def test_a_clean_run_shows_no_drop_and_no_red(tmp_path):
    async def body(app, pilot):
        await show_run(app, pilot, drop=False)
        text = screen_text(app)
        assert "15 findings → 15 kept, 0 dropped" in text
        assert "Dropped, not softened" not in text

    drive(body, tmp_path)


def test_a_failing_run_reports_it_and_stops_every_spinner(tmp_path):
    """A stage left turning after a failure reads as still working."""
    from holt.tui.widgets.stages import StageRow

    async def body(app, pilot):
        screen = await show_run(app, pilot, fail="outcomes")
        text = screen_text(app)
        assert "the network went away" in text
        assert "escape to go back" in text
        assert not [row for row in screen.query(StageRow) if row._state == "running"]

    drive(body, tmp_path)


def test_a_replay_never_shows_a_dollar_figure(tmp_path):
    """Nothing was bought, so nothing is priced.

    `ReplayModel` reports the token counts the original run recorded. Rendering
    their cost would tell a reader they had just spent money on a run that made
    no calls.
    """
    from holt.tui import events

    async def body(app, pilot):
        script = fake_run.script()
        script.insert(
            2, events.UsageUpdated(input_tokens=19139, output_tokens=9484, cost_usd=0.0238)
        )
        await show_run_with(app, pilot, script)
        assert "$" not in screen_text(app)
        assert app.session.cost_usd == 0.0

    drive(body, tmp_path)


async def show_run_with(app, pilot, script):
    from holt.tui.screens.live import LiveScreen

    app.session = fake_run.session(queued=script)
    await app.push_screen(LiveScreen())
    await pilot.pause(0.3)
    return app.screen


def test_an_unknown_event_renders_instead_of_raising(tmp_path):
    """A stage that learns a new event must not break a screen that predates it."""

    class Invented:
        __slots__ = ("stage",)

        def __init__(self):
            self.stage = "something_new"

    async def body(app, pilot):
        screen = await show_run(app, pilot, complete=False)
        screen._handle(Invented())
        await pilot.pause(0.3)
        assert "Invented" in screen_text(app)

    drive(body, tmp_path)


def test_a_stage_the_engine_grew_appears_rather_than_vanishing(tmp_path):
    """The interface reports the pipeline that ran, not the one it was written
    against."""
    from holt.tui import events

    async def body(app, pilot):
        screen = await show_run(app, pilot, complete=False)
        screen._handle(events.StageStarted(stage="triage", model="gpt-5-mini"))
        screen._handle(
            events.StageFinished(stage="triage", seconds=0.2, summary="9 triaged")
        )
        await pilot.pause(0.3)
        text = screen_text(app)
        assert "triage" in text
        assert "9 triaged" in text

    drive(body, tmp_path)


# ─── the report ─────────────────────────────────────────────────────────────


def test_the_report_leads_with_the_answer_and_keeps_its_limits(tmp_path):
    async def body(app, pilot):
        await show_report(app, pilot)
        text = screen_text(app)

        assert "Worth your time" in text
        assert "for a contributor with 7 days" in text
        assert "WHAT THE EVIDENCE SHOWS" in text
        assert "WHAT DECIDED IT" in text
        # A section in the body, in the engine's own order — not a footnote.
        assert "WHAT COULD NOT BE DETERMINED" in text

    drive(body, tmp_path, size=(100, 90))


def test_every_claim_on_the_report_carries_an_evidence_id(tmp_path):
    async def body(app, pilot):
        screen = await show_report(app, pilot)
        from holt.tui.widgets.claims import ClaimList

        claims = screen.query_one("#claims", ClaimList)
        assert claims.claims
        assert all(c.evidence_id for c in claims.claims)
        assert "claims, every one carrying an id that resolved" in screen_text(app)

    drive(body, tmp_path, size=(100, 90))


def test_a_verdict_this_build_has_never_seen_renders_neutrally(tmp_path):
    """`holt.report` owns the enum. The interface must not need editing when a
    fourth answer is added to it."""
    from holt.tui import theme

    assert theme.verdict_colour("a_verdict_added_later") == theme.VERDICT_FALLBACK

    async def body(app, pilot):
        from holt.tui.widgets.recent import headline

        assert headline("something_new") == "something new"

    drive(body, tmp_path)


def test_the_measured_result_is_shown_in_full_and_not_behind_a_key(tmp_path):
    """The ranking's own negative result is visible without pressing anything,
    and it carries every comparator, including the two that beat it."""

    async def body(app, pilot):
        await show_report(app, pilot, with_entry_points=True)
        text = screen_text(app)
        assert "WHERE TO START" in text
        assert "not measurably better than picking at random" in text
        for label in ("this ranking", "good first issue", "recency", "random"):
            assert label in text
        assert "0.173" in text and "0.187" in text
        assert "eval/pathfinder_harness.py --replay" in text

    drive(body, tmp_path, size=(100, 140))


def test_a_stored_assessment_says_the_record_is_not_loaded(tmp_path):
    """Three states, three sentences.

    "does not resolve" is a statement about the evidence. A reopened assessment
    has no provider, so the honest thing is that nothing was looked up.
    """
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(fake_run.stored_entry(repo=CLEAN, age=60))

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


def test_finishing_a_run_stores_it_and_home_lists_it(tmp_path):
    async def body(app, pilot):
        await show_run(app, pilot)
        await pilot.pause(0.9)
        assert app.screen.__class__.__name__ == "AssessmentScreen"

        await pilot.press("escape")
        await pilot.pause(0.6)
        assert app.screen.__class__.__name__ == "HomeScreen"
        text = screen_text(app)
        assert CLEAN in text
        assert "just now" in text
        assert "Worth your time" in text

    drive(body, tmp_path)


# ─── discover, profile, what next ────────────────────────────────────────────


def test_discover_lists_survivors_and_what_it_cut(tmp_path):
    """The rejected candidates are the interesting half. They stay on screen."""
    from holt.tui import discovery

    if not discovery.manifest_path_exists():
        pytest.skip("the recorded discovery session is not present")

    async def body(app, pilot):
        await pilot.press("ctrl+f")
        await pilot.pause(0.6)
        assert app.screen.__class__.__name__ == "DiscoverScreen"
        text = screen_text(app)
        assert "screened at no model cost" in text
        assert "worth a closer look" in text
        assert "cut" in text
        assert "survived screening" in text

    drive(body, tmp_path, size=(100, 60))


def test_discover_says_so_when_the_session_is_missing(tmp_path):
    from holt.tui.screens.discover import DiscoverScreen

    async def body(app, pilot):
        await app.push_screen(DiscoverScreen("no-such-session"))
        await pilot.pause(0.4)
        text = screen_text(app)
        assert "No recorded search" in text
        assert "--record" in text

    drive(body, tmp_path)


def test_profile_round_trips_through_the_same_file_the_cli_uses(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    async def body(app, pilot):
        await pilot.press("ctrl+o")
        await pilot.pause(0.4)
        assert app.screen.__class__.__name__ == "ProfileScreen"

        from textual.widgets import Input

        app.screen.query_one("#profile-languages", Input).value = "python, rust"
        app.screen.query_one("#profile-topics", Input).value = "cli"
        app.screen.query_one("#profile-days", Input).value = "3"
        app.screen.action_save()
        await pilot.pause(0.3)
        assert "Saved to" in screen_text(app)

        from holt import profile as profile_mod

        stored = profile_mod.load()
        assert stored.languages == ["python", "rust"]
        assert stored.topics == ["cli"]
        assert stored.days == 3

    drive(body, tmp_path)


def test_profile_refuses_a_day_budget_that_is_not_a_number(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    async def body(app, pilot):
        await pilot.press("ctrl+o")
        await pilot.pause(0.4)
        from textual.widgets import Input

        app.screen.query_one("#profile-days", Input).value = "soon"
        app.screen.action_save()
        await pilot.pause(0.3)
        assert "is not a number of days" in screen_text(app)

        from holt import profile as profile_mod

        assert profile_mod.load() is None, "nothing should have been written"

    drive(body, tmp_path)


def test_what_next_says_plainly_when_the_login_has_landed_nothing(tmp_path):
    """An empty list would read as a ranking that found nothing, rather than a
    question that cannot be asked yet."""
    from holt.tui.screens.next_steps import NextScreen

    async def body(app, pilot):
        app.session = fake_run.finished()
        await app.push_screen(NextScreen(CLEAN))
        await pilot.pause(0.3)
        await type_repo(pilot, "nobody-at-all")
        await pilot.press("enter")
        await pilot.pause(0.6)
        text = screen_text(app)
        assert "no merged pull request here" in text

    drive(body, tmp_path)


# ─── masthead ───────────────────────────────────────────────────────────────


def test_home_leads_with_the_masthead(tmp_path):
    """An empty screen that says nothing is what this replaces."""
    from holt.tui import mascot

    async def body(app, pilot):
        text = screen_text(app)
        assert mascot.TAGLINE in text
        assert mascot.still("idle") in text
        # And the facts that make the space worth taking.
        assert "read-only" in text
        assert "dropped, not softened" in text

    drive(body, tmp_path, size=(110, 44))


def test_the_cat_has_a_mood_for_every_state_the_engine_has():
    """The face reports state or it has no business being on screen."""
    from holt.report import VERDICT_HEADLINES
    from holt.tui import mascot

    for verdict in VERDICT_HEADLINES:
        mood = mascot.mood_for_verdict(verdict.value)
        assert mood in mascot.MOODS, f"no cat for {verdict.value}"
        assert mascot.frames(mood)

    # A verdict this build has never seen falls back rather than raising.
    assert mascot.mood_for_verdict("something_new") == "idle"
    assert mascot.frames("something_new") == mascot.IDLE


def test_every_mood_animates_and_fits_its_column():
    """Each cycle has to actually change, and none may overflow the slot the
    chrome gives it."""
    from rich.cells import cell_len

    from holt.tui import mascot

    for mood, cycle in mascot.MOODS.items():
        assert len(set(cycle)) > 1, f"{mood} never changes, so it is not animated"
        widest = max(cell_len(frame) for frame in cycle)
        assert widest <= 12, f"{mood} is {widest} cells wide, the column is 12"


def test_the_accent_changes_between_launches_but_never_means_anything():
    """The one arbitrary colour in the app. It must stay clear of the five that
    carry meaning, or a session's decoration would read as a verdict."""
    from holt.tui import mascot, theme

    meaning = {
        theme.VIABLE,
        theme.NOT_VIABLE,
        theme.INSUFFICIENT,
        theme.DROP,
        theme.CITE,
    }
    assert not (set(mascot.ACCENTS) & meaning)
    assert len(set(mascot.ACCENTS)) > 1


def test_a_pinned_accent_wins_so_screenshots_and_tests_are_stable(monkeypatch):
    from holt.tui import mascot

    monkeypatch.setenv("HOLT_TUI_ACCENT", "#123456")
    assert mascot.pick_accent() == "#123456"


def test_a_long_verdict_does_not_run_into_the_age(tmp_path):
    """`Not enough evidence to say` is 26 characters; the column was 22, so it
    rendered as "Not enough evidence to say8 hours ago"."""
    from holt.report import Verdict
    from holt.tui import store
    from holt.tui.widgets.recent import HEADLINE_WIDTH

    from holt.report import VERDICT_HEADLINES

    assert HEADLINE_WIDTH > max(len(h) for h in VERDICT_HEADLINES.values())

    keep = store.Store(root=tmp_path)
    entry = fake_run.stored_entry(repo="inni918/warashi", mode="live", age=28800)
    entry.assessment.verdict = Verdict.INSUFFICIENT_EVIDENCE
    keep.save(entry)

    async def body(app, pilot):
        text = screen_text(app)
        assert "Not enough evidence to say" in text
        assert "8 hours ago" in text
        assert "say8 hours" not in text

    drive(body, tmp_path, size=(110, 44))
