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
    session = fake_run.session(repo=script_kw.get("repo", fake_run.REPO), queued=script)
    # Registered exactly as `HoltApp.start_run` registers a real one. The app,
    # not the screen, is what drains a run, so a session the app does not know
    # about would sit there with a full queue and an empty screen.
    app.session = session
    app.runs[session.options.repo] = session
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


# ─── models ─────────────────────────────────────────────────────────────────


def test_the_model_screen_lists_providers_with_their_key_status(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    async def body(app, pilot):
        await pilot.press("ctrl+l")
        await pilot.pause(0.5)
        assert app.screen.__class__.__name__ == "ModelsScreen"
        text = screen_text(app)
        for name in ("openai", "anthropic", "ollama", "gemini", "openai-compatible"):
            assert name in text
        # Whether a provider can be used at all, before you pick it.
        assert "ANTHROPIC_API_KEY is not set" in text
        assert "set a base url first" in text

    drive(body, tmp_path, size=(110, 40))


def test_choosing_a_model_warns_that_replay_will_fail(tmp_path, monkeypatch):
    """The reproducibility guarantee is never a surprise sprung later."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    from holt import model as model_module
    from holt.tui import models as models_layer

    async def body(app, pilot):
        await pilot.press("ctrl+l")
        await pilot.pause(0.5)
        screen = app.screen
        screen.chosen = next(p for p in screen.providers if p.name == "anthropic")
        screen._use("claude-opus-5")
        await pilot.pause(0.3)

        text = screen_text(app)
        assert "fails loudly" in text
        assert model_module.model_for("classify") == "claude-opus-5"

        screen.action_reset()
        await pilot.pause(0.3)
        assert "fails loudly" not in screen_text(app)
        assert model_module.model_for("classify") == model_module.SMALL

    drive(body, tmp_path, size=(110, 40))
    models_layer.reset()


def test_the_model_screen_never_reaches_the_network_in_tests(tmp_path, monkeypatch):
    """The guard is on for the whole session; this proves the screen honours it
    rather than calling the SDK directly."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    from holt.tui import models as models_layer

    assert not models_layer.network_allowed()

    async def body(app, pilot):
        await pilot.press("ctrl+l")
        await pilot.pause(0.4)
        screen = app.screen
        screen.chosen = next(p for p in screen.providers if p.name == "ollama")
        await screen._show_models(models_layer.list_models(screen.chosen))
        await pilot.pause(0.3)
        assert models_layer.NO_NETWORK_ENV in screen_text(app)

    drive(body, tmp_path, size=(110, 40))


# ─── driving it without a mouse ─────────────────────────────────────────────


def rail_colour(app, needle: str) -> str | None:
    """The colour of the selection rail on the row containing `needle`.

    Asserting on text cannot see a highlight, and the highlight is exactly the
    thing that was broken: every rule in the stylesheet named `--highlight`,
    Textual sets `-highlight`, so no list in the app showed a keyboard position
    and all of them had to be clicked. A test that reads only characters would
    have stayed green through all of it.
    """
    from holt.tui import theme

    for strip in app.screen._compositor.render_strips():
        text = "".join(segment.text for segment in strip)
        # Every matching row, not the first: the notice under the input names
        # the highlighted repository too, and it is above the list.
        if needle not in text:
            continue
        for segment in strip:
            colour = getattr(getattr(segment.style, "color", None), "triplet", None)
            if colour is not None and colour.hex.lower() == theme.CITE.lower():
                return theme.CITE
    return None


def test_the_recent_list_shows_where_the_keyboard_is(tmp_path):
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(fake_run.stored_entry(repo="astral-sh/uv", age=120))
    keep.save(fake_run.stored_entry(repo="home-assistant/core", age=180))

    async def body(app, pilot):
        listing = app.screen.query_one("#recent")
        assert listing.index == 0, "something must be selected to move from"

        # The newest is first, so it is the one carrying the rail.
        assert rail_colour(app, "astral-sh/uv") is not None
        assert rail_colour(app, "home-assistant/core") is None

        await pilot.press("down")
        await pilot.pause(0.3)
        assert rail_colour(app, "home-assistant/core") is not None
        assert rail_colour(app, "astral-sh/uv") is None

    drive(body, tmp_path)


def test_arrows_move_through_recent_without_taking_the_input(tmp_path):
    """The input holds focus the whole time, so typing never stops working."""
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(fake_run.stored_entry(repo="astral-sh/uv", age=120))
    keep.save(fake_run.stored_entry(repo="home-assistant/core", age=180))

    async def body(app, pilot):
        home = app.screen
        await pilot.press("down")
        await pilot.pause(0.3)
        assert app.focused.id == "repo-input"
        assert home.query_one("#recent").selected.repo == "home-assistant/core"
        # And it says what enter now means, because enter has changed meaning.
        assert "enter opens home-assistant/core" in screen_text(app)

        await pilot.press("up")
        await pilot.pause(0.3)
        assert home.query_one("#recent").selected.repo == "astral-sh/uv"

        # Typing puts you back in the box.
        await type_repo(pilot, "x")
        await pilot.pause(0.3)
        assert home._browsing is False

    drive(body, tmp_path)


def test_enter_opens_the_highlighted_one_and_nothing_is_run(tmp_path):
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(fake_run.stored_entry(repo="astral-sh/uv", age=120))
    keep.save(fake_run.stored_entry(repo="home-assistant/core", age=180))

    async def body(app, pilot):
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause(0.5)
        assert app.screen.__class__.__name__ == "AssessmentScreen"
        assert app.session.assessment.repo == "home-assistant/core"
        assert app.session._thread is None, "opening a stored answer must run nothing"

    drive(body, tmp_path)


def test_a_pasted_url_finds_the_repository_you_already_have(tmp_path):
    """It filtered to nothing and announced "nothing matches that" about a
    repository in the store, while enter on the same text opened it."""
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(fake_run.stored_entry(repo="astral-sh/uv", age=120))

    async def body(app, pilot):
        app.screen.query_one("#repo-input", __import__(
            "textual.widgets", fromlist=["Input"]
        ).Input).value = "https://github.com/astral-sh/uv"
        await pilot.pause(0.4)

        assert [e.repo for e in app.screen._entries] == ["astral-sh/uv"]
        text = screen_text(app)
        assert "Nothing assessed matches that" not in text
        # And it says so in words, not only as a row in a list.
        assert "Already assessed" in text

    drive(body, tmp_path)


def test_discover_starts_on_the_candidates_not_the_scroll_box(tmp_path):
    """Focus landed on the container, where ↑↓ scrolled past every candidate
    and enter did nothing at all."""

    async def body(app, pilot):
        await pilot.press("ctrl+f")
        await pilot.pause(0.5)
        if app.screen.error:
            pytest.skip("no recorded discover session in this checkout")
        assert app.focused.id == "candidates"
        assert app.screen.query_one("#candidates").index == 0

    drive(body, tmp_path, size=(110, 44))


def test_enter_on_a_claim_you_tabbed_to_opens_its_record(tmp_path):
    """`ListView` takes enter once it has focus, so the screen's own binding
    never fires — without a handler for the message it posts instead, the list
    is one you can move around in and never open."""

    async def body(app, pilot):
        await show_report(app, pilot)
        await pilot.press("tab")
        await pilot.press("down")
        await pilot.pause(0.2)
        assert app.focused.id == "claims"

        await pilot.press("enter")
        await pilot.pause(0.4)
        assert app.screen.__class__.__name__ == "InspectorScreen"

    drive(body, tmp_path)


# ─── taking the report with you ─────────────────────────────────────────────


def test_the_report_copies_as_the_markdown_the_engine_writes(tmp_path, monkeypatch):
    """Not a transcription of the screen — the artefact itself, ids and all."""
    from holt.tui import clipboard

    copied: list[str] = []
    # Patched, or a test run would overwrite the clipboard of whoever ran it.
    monkeypatch.setattr(clipboard, "native", lambda text: copied.append(text) or "xclip")

    async def body(app, pilot):
        await show_report(app, pilot)
        await pilot.press("c")
        await pilot.pause(0.3)

        assert copied == [app.session.assessment.render()]
        assert "# " in copied[0], "markdown, not the rendered screen"
        assert "Copied as markdown" in screen_text(app)

    drive(body, tmp_path)


def test_a_copy_that_cannot_be_confirmed_does_not_claim_it_was(tmp_path, monkeypatch):
    """OSC 52 is unacknowledged. Saying "copied" when nothing may have happened
    is the one thing this must not do."""
    from holt.tui import clipboard

    monkeypatch.setattr(clipboard, "native", lambda text: "")

    async def body(app, pilot):
        await show_report(app, pilot)
        await pilot.press("c")
        await pilot.pause(0.3)
        text = screen_text(app)
        assert "Asked your terminal" in text
        assert "Copied as markdown" not in text

    drive(body, tmp_path)


def test_the_clipboard_never_shells_out_to_a_tool_that_has_nothing_to_talk_to(
    monkeypatch,
):
    """`wl-copy` outside Wayland and `xclip` with no display both exist on a lot
    of machines and fail on all of them."""
    from holt.tui import clipboard

    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr(clipboard.shutil, "which", lambda name: f"/usr/bin/{name}")

    ran: list[tuple] = []
    monkeypatch.setattr(
        clipboard.subprocess, "run", lambda argv, **kw: ran.append(argv)
    )

    clipboard.native("anything")
    assert not any(argv[0] in ("wl-copy", "xclip", "xsel") for argv in ran)


# ─── the window a run actually read ─────────────────────────────────────────


def test_the_run_names_the_boundary_it_actually_read_to(tmp_path):
    """The evidence line reports the run's own cutoff, not the benchmark's T.

    This was wrong for as long as the date was a literal in the screen: a live
    run reads through today, and the line claimed a 2026-06-01 holdout anyway.
    """
    from datetime import UTC, datetime

    async def body(app, pilot):
        await show_run(app, pilot, complete=False, cutoff=datetime(2026, 8, 31, tzinfo=UTC))
        text = screen_text(app)
        assert "read through 2026-08-31" in text
        assert "2026-06-01" not in text
        assert "pre_t" not in text

    drive(body, tmp_path)


def test_a_replayed_run_still_says_it_is_reading_the_holdout(tmp_path):
    async def body(app, pilot):
        await show_run(app, pilot, complete=False)
        assert "holdout window, ≤ 2026-06-01" in screen_text(app)

    drive(body, tmp_path)


def test_the_evidence_line_says_nothing_it_cannot_back():
    """A provider that reports no cutoff gets no window claim at all."""
    from holt.tui import events
    from holt.tui.screens.live import evidence_line

    assert evidence_line(events.EvidenceLoaded(count=95, window="pre_t")) == (
        "95 evidence records"
    )


# ─── runs that outlive the screen watching them ─────────────────────────────


def attach(app, repo: str, script: list):
    """Register a scripted run the way `HoltApp.start_run` registers a real one."""
    session = fake_run.session(repo=repo, queued=script)
    app.session = session
    app.runs[repo] = session
    return session


async def watch(app, pilot):
    """Put the live screen up on whatever `app.session` currently is."""
    from holt.tui.screens.live import LiveScreen

    await app.push_screen(LiveScreen())
    await pilot.pause(0.2)


def unfinished(repo: str, **kw) -> list:
    from holt.tui import events as _events

    return [
        e
        for e in fake_run.script(repo=repo, **kw)
        if not isinstance(e, _events.RunFinished)
    ]


def test_a_run_that_finishes_while_nobody_watches_is_still_kept(tmp_path):
    """The reported bug, in one test.

    Start a run, go home before it lands, and the assessment it produces has to
    survive. Draining used to belong to the live screen, so popping that screen
    left the worker computing an answer that nothing would ever collect: the
    run looked stopped because its result was thrown away.
    """
    from holt.tui import events as _events

    async def body(app, pilot):
        session = attach(app, CLEAN, unfinished(CLEAN))
        await watch(app, pilot)

        app.go_home()
        await pilot.pause(0.2)
        assert app.screen.__class__.__name__ == "HomeScreen"
        assert not session.finished, "the run should still be in flight"

        # The run finishes with nobody on the live screen.
        session._queue.put(
            _events.RunFinished(assessment=fake_run.assessment(CLEAN), trace=None)
        )
        await pilot.pause(0.4)

        assert session.assessment is not None, "the result was never absorbed"
        assert [e.repo for e in app.store.all()] == [CLEAN]
        assert CLEAN not in app.runs, "a finished run stays registered as in flight"

    drive(body, tmp_path)


def test_two_repositories_can_be_assessed_at_once(tmp_path):
    from holt.tui import events as _events

    other = "pallets/flask"

    async def body(app, pilot):
        first = attach(app, CLEAN, unfinished(CLEAN))
        second = attach(app, other, unfinished(other))
        await pilot.pause(0.2)

        assert {s.options.repo for s in app.in_flight} == {CLEAN, other}

        for session, repo in ((first, CLEAN), (second, other)):
            session._queue.put(
                _events.RunFinished(assessment=fake_run.assessment(repo), trace=None)
            )
        await pilot.pause(0.4)

        assert {e.repo for e in app.store.all()} == {CLEAN, other}
        assert app.in_flight == []

    drive(body, tmp_path)


def test_rejoining_a_run_shows_what_happened_while_you_were_away(tmp_path):
    """The screen rebuilds from the log, so nothing that arrived is missed."""

    async def body(app, pilot):
        session = attach(app, CLEAN, unfinished(CLEAN))
        await pilot.pause(0.3)  # drains at home, with no live screen mounted
        assert len(session.log) > 5, "the app did not drain a run nobody was watching"

        app.watch_run(session)
        await pilot.pause(0.3)

        text = screen_text(app)
        assert "evidence records" in text
        assert "real_software" in text, "the stream did not replay from its start"

    drive(body, tmp_path)


def test_leaving_the_live_screen_does_not_stop_the_run(tmp_path):
    async def body(app, pilot):
        session = attach(app, CLEAN, unfinished(CLEAN))
        await watch(app, pilot)

        await pilot.press("escape")
        await pilot.pause(0.2)

        assert app.screen.__class__.__name__ == "HomeScreen"
        assert session in app.in_flight
        assert not session.cancelled

    drive(body, tmp_path)


def test_home_lists_a_run_in_flight_and_enter_rejoins_it(tmp_path):
    async def body(app, pilot):
        session = attach(app, CLEAN, unfinished(CLEAN))
        # Let the app absorb the stream first: the row names the stage the run
        # is in, and before anything is drained it can only say "starting".
        await pilot.pause(0.3)
        await app.screen.refresh_entries()
        await pilot.pause(0.2)

        text = screen_text(app)
        assert CLEAN in text
        assert "running · " in text

        from holt.tui.widgets.recent import RecentList

        listing = app.screen.query_one("#recent", RecentList)
        listing.focus()
        listing.index = 0
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.3)

        assert app.screen.__class__.__name__ == "LiveScreen"
        assert app.session is session

    drive(body, tmp_path)


def test_arrowing_onto_a_run_in_flight_says_so_and_rejoins_it(tmp_path):
    """Where the two halves of this list meet.

    Runs in flight sit above the stored ones, and ↑↓ move through the whole list
    from the input. A running row is not a stored answer: enter rejoins it
    rather than opening it, ctrl+r must not start a second one, and describing
    it as "assessed N minutes ago" would be wrong twice over — it is not
    finished, and nothing is being reused.
    """

    async def body(app, pilot):
        session = attach(app, CLEAN, unfinished(CLEAN))
        await pilot.pause(0.3)
        await app.screen.refresh_entries()
        await pilot.pause(0.2)

        # The input keeps focus; the arrow key is handled by the screen.
        assert app.focused.id == "repo-input"
        await pilot.press("down")
        await pilot.pause(0.2)

        text = screen_text(app)
        assert f"enter rejoins the run on {CLEAN}" in text
        assert "ctrl+x stops it" in text
        # Never the stored-answer wording, which would claim it had finished.
        assert "enter opens" not in text

        # ctrl+r on it would be paying twice for one question.
        await pilot.press("ctrl+r")
        await pilot.pause(0.2)
        assert "still running" in screen_text(app)
        assert app.screen.__class__.__name__ == "HomeScreen"
        assert len(app.runs) == 1

        await pilot.press("enter")
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "LiveScreen"
        assert app.session is session

    drive(body, tmp_path)


def test_asking_for_a_repository_already_running_rejoins_rather_than_pays_twice(
    tmp_path,
):
    async def body(app, pilot):
        session = attach(app, CLEAN, unfinished(CLEAN))
        await pilot.pause(0.1)

        app.screen.run_repo(CLEAN)
        await pilot.pause(0.3)

        assert app.screen.__class__.__name__ == "LiveScreen"
        assert app.session is session
        assert len(app.runs) == 1

    drive(body, tmp_path)


def test_stopping_asks_first_and_only_then_stops(tmp_path):
    async def body(app, pilot):
        session = attach(app, CLEAN, unfinished(CLEAN))
        await watch(app, pilot)

        await pilot.press("ctrl+x")
        await pilot.pause(0.2)
        assert app.screen.__class__.__name__ == "ConfirmScreen"
        assert "stop home-assistant/core?" in screen_text(app)

        await pilot.press("n")
        await pilot.pause(0.2)
        assert app.screen.__class__.__name__ == "LiveScreen"
        assert not session._cancel.is_set(), "declining stopped the run anyway"

        await pilot.press("ctrl+x")
        await pilot.pause(0.2)
        await pilot.press("y")
        await pilot.pause(0.2)
        assert session._cancel.is_set()

    drive(body, tmp_path)


def test_quitting_with_a_run_in_flight_says_what_it_would_stop(tmp_path):
    async def body(app, pilot):
        attach(app, CLEAN, unfinished(CLEAN))
        await pilot.pause(0.2)

        app.action_quit()
        await pilot.pause(0.2)

        text = screen_text(app)
        assert app.screen.__class__.__name__ == "ConfirmScreen"
        assert "still in flight" in text
        assert CLEAN in text

        await pilot.press("n")
        await pilot.pause(0.2)
        assert app.screen.__class__.__name__ == "HomeScreen"

    drive(body, tmp_path)


def test_quitting_with_nothing_running_does_not_ask(tmp_path):
    async def body(app, pilot):
        assert app.in_flight == []
        app.action_quit()
        await pilot.pause(0.2)
        assert app.screen.__class__.__name__ != "ConfirmScreen"

    drive(body, tmp_path)


def test_a_stopped_run_reads_as_stopped_and_not_as_a_failure(tmp_path):
    from holt.tui import events as _events

    async def body(app, pilot):
        session = attach(app, CLEAN, unfinished(CLEAN))
        await watch(app, pilot)

        session._queue.put(
            _events.RunCancelled(completed_stages=("classify", "opportunity"))
        )
        await pilot.pause(0.3)

        text = screen_text(app)
        assert "stopped" in text
        assert "classify" in text
        assert session.cancelled
        assert session.error is None, "a stop must not be recorded as a failure"
        assert app.store.all() == [], "a partial run must not be stored"

    drive(body, tmp_path)


# ─── the command palette ────────────────────────────────────────────────────


async def palette_commands(app) -> list[tuple[str, str]]:
    """Every command the palette would offer right now, in order."""
    from holt.tui.commands import HoltCommands

    provider = HoltCommands(app.screen)
    return [(name, help_text) for name, help_text, _ in provider._commands()]


def test_the_palette_leads_with_holt_and_keeps_the_framework(tmp_path):
    """holt's own commands first, then Textual's, in a written order.

    `App.COMMANDS` is a set and providers are searched concurrently, so two
    providers interleave differently between launches. One provider yielding in
    order is what makes this assertable at all.
    """

    async def body(app, pilot):
        names = [name for name, _ in await palette_commands(app)]

        assert "assess a repository" in names
        assert "find a repository" in names
        assert "models" in names
        assert "profile" in names

        # The framework's are kept, and come after.
        assert "Theme" in names, "the built-in commands were dropped"
        assert names.index("assess a repository") < names.index("Theme")

    drive(body, tmp_path)


def test_the_palette_offers_what_is_true_right_now(tmp_path):
    """Runs in flight and stored assessments are commands while they exist."""
    from holt.tui import store

    keep = store.Store(root=tmp_path)
    keep.save(fake_run.stored_entry(repo="vercel/next.js", age=120))

    async def body(app, pilot):
        session = attach(app, CLEAN, unfinished(CLEAN))
        await app.screen.refresh_entries()
        await pilot.pause(0.2)

        names = [name for name, _ in await palette_commands(app)]
        assert f"watch {CLEAN}" in names
        assert f"stop {CLEAN}" in names
        assert "open vercel/next.js" in names
        # Live things first: they are the only ones that stop being true.
        assert names.index(f"stop {CLEAN}") < names.index("open vercel/next.js")

        # And once the run is over, it stops being offered as one you can stop.
        session._queue.put(
            _run_finished(fake_run.assessment(CLEAN)),
        )
        await pilot.pause(0.4)
        after = [name for name, _ in await palette_commands(app)]
        assert f"stop {CLEAN}" not in after
        assert f"open {CLEAN}" in after

    drive(body, tmp_path)


def _run_finished(assessment):
    from holt.tui import events as _events

    return _events.RunFinished(assessment=assessment, trace=None)


def test_the_palette_opens_and_is_styled_as_one_surface(tmp_path):
    """Opened, it shows holt's commands and none of Textual's default chrome."""

    async def body(app, pilot):
        await pilot.press("ctrl+p")
        await pilot.pause(0.6)

        assert app.screen.__class__.__name__ == "CommandPalette"
        text = screen_text(app)
        assert "assess a repository" in text
        # The emoji sat on its own line, out of line with the input it labelled.
        assert "🔎" not in text
        # The heavy full-width bars Textual frames the input with.
        assert "▔" not in text and "▁" not in text

    drive(body, tmp_path)


def highlighted_rows(app) -> list[tuple[int, str]]:
    """Rows in the command list carrying the cursor, by rendered background.

    Read off the composited output rather than off the widget's index, because
    the defect being pinned is precisely that an index moved while nothing on
    screen changed. Only rows below the search box are considered: the input
    has a background of its own and is not a candidate.
    """

    def background(segment):
        style = segment.style
        rich = getattr(style, "rich_style", style)
        return str(getattr(rich, "bgcolor", None))

    strips = list(app.screen._compositor.render_strips())
    rendered = ["".join(seg.text for seg in strip) for strip in strips]
    box = next(
        (i for i, text in enumerate(rendered) if "Search for commands" in text), None
    )
    if box is None:
        return []

    listed = range(box + 2, len(strips))
    weight: dict[str, int] = {}
    for index in listed:
        for segment in strips[index]:
            if segment.text.strip():
                key = background(segment)
                weight[key] = weight.get(key, 0) + len(segment.text)
    if not weight:
        return []
    surface = max(weight, key=weight.get)

    rows: list[tuple[int, str]] = []
    for index in listed:
        for segment in strips[index]:
            if segment.text.strip() and background(segment) != surface:
                rows.append((index, rendered[index].strip()))
                break
    return rows


def test_the_palette_cursor_is_visible_and_moves(tmp_path):
    """Up and down have to move something a person can see.

    Textual falls back to its *blurred* cursor colours here, because the input
    keeps focus the whole time the palette is open, and blurred on this surface
    is indistinguishable from no cursor at all.
    """

    async def body(app, pilot):
        await pilot.press("ctrl+p")
        await pilot.pause(0.6)

        first = highlighted_rows(app)
        assert first, "no option is visibly highlighted when the palette opens"
        assert "assess a repository" in first[0][1]

        await pilot.press("down")
        await pilot.pause(0.3)
        second = highlighted_rows(app)
        assert second, "the cursor disappeared instead of moving"
        assert second[0][0] > first[0][0], "the cursor did not move down"

        await pilot.press("up")
        await pilot.pause(0.3)
        back = highlighted_rows(app)
        assert back and back[0][0] == first[0][0], "up did not come back"

    drive(body, tmp_path)


# ─── choosing a model you can actually find ─────────────────────────────────


OPENAI_IDS = [
    "babbage-002",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4o-transcribe",
    "gpt-5",
    "gpt-5-2025-08-07",
    "gpt-5-mini",
    "gpt-5-mini-2025-08-07",
    "text-embedding-3-small",
]


async def open_openai_models(app, pilot, monkeypatch, ids=None):
    """The models screen, on a scripted OpenAI listing. No network.

    Everything it changes goes through `monkeypatch`. Setting `OPENAI_API_KEY`
    directly leaked into every later test in the session — home reads it to
    decide between live and replay, so a models test silently flipped the mode
    of tests that ran after it.
    """
    from holt.tui import models as models_layer

    monkeypatch.setattr(
        models_layer, "_list_openai_wire", lambda provider, key: sorted(ids or OPENAI_IDS)
    )
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv(models_layer.NO_NETWORK_ENV, "0")

    await pilot.press("ctrl+l")
    await pilot.pause(0.4)
    screen = app.screen
    screen.chosen = next(p for p in screen.providers if p.name == "openai")
    await screen._show_models(models_layer.list_models(screen.chosen))
    await pilot.pause(0.3)
    return screen


def listed_ids(screen):
    from textual.widgets import ListView

    return [row.entry.id for row in screen.query_one("#models", ListView).children]


def test_the_model_list_leads_with_what_holt_can_price(tmp_path, monkeypatch):
    """Alphabetical opened on `babbage-002`, and buried `gpt-5` under speech
    models. The ones with a known rate come first; nothing is hidden for it."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    async def body(app, pilot):
        screen = await open_openai_models(app, pilot, monkeypatch)
        shown = listed_ids(screen)

        assert shown[0].startswith("gpt-5")
        assert shown.index("gpt-5") < shown.index("gpt-4o")
        assert shown[-1] == "babbage-002", "legacy sinks rather than vanishing"
        # The non-chat ids never make the list, and the screen says how many.
        assert "gpt-4o-transcribe" not in shown
        assert "text-embedding-3-small" not in shown
        assert "are not chat models" in screen_text(app)

    drive(body, tmp_path, size=(110, 40))


def test_a_rate_is_shown_rather_than_the_word_priced(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    async def body(app, pilot):
        await open_openai_models(app, pilot, monkeypatch)
        text = screen_text(app)
        assert "per M tokens" in text
        assert "$1.25 in / $10.00 out" in text
        # gpt-5 is an alias for the pinned snapshot, and says so with ≈.
        assert "≈ $1.25 in / $10.00 out" in text

    drive(body, tmp_path, size=(110, 40))


def test_typing_narrows_the_model_list_without_losing_the_box(tmp_path, monkeypatch):
    """A provider can offer eighty ids. Scrolling all of them is not a choice."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    async def body(app, pilot):
        screen = await open_openai_models(app, pilot, monkeypatch)
        assert app.focused.id == "model-filter"

        for char in "mini":
            await pilot.press(char)
        await pilot.pause(0.4)

        shown = listed_ids(screen)
        assert shown and all("mini" in i for i in shown)
        assert "3 of " in screen_text(app)
        # Typing must not cost you the box, and ↑↓ must not either.
        assert app.focused.id == "model-filter"

        await pilot.press("down")
        await pilot.pause(0.2)
        assert screen.query_one("#models").index == 1
        assert app.focused.id == "model-filter"

    drive(body, tmp_path, size=(110, 40))


def test_a_filter_that_matches_nothing_says_so(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    async def body(app, pilot):
        screen = await open_openai_models(app, pilot, monkeypatch)
        for char in "zzz":
            await pilot.press(char)
        await pilot.pause(0.4)
        assert listed_ids(screen) == []
        assert "Nothing here matches" in screen_text(app)

    drive(body, tmp_path, size=(110, 40))


def test_enter_in_the_filter_box_chooses_the_highlighted_model(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    async def body(app, pilot):
        screen = await open_openai_models(app, pilot, monkeypatch)
        for char in "mini":
            await pilot.press(char)
        await pilot.pause(0.4)
        chosen = listed_ids(screen)[0]

        await pilot.press("enter")
        await pilot.pause(0.3)
        assert f"{chosen} now answers every stage" in screen_text(app)

    drive(body, tmp_path, size=(110, 40))


# ─── getting out ────────────────────────────────────────────────────────────


def test_the_front_screen_has_a_way_out_that_survives_the_input(tmp_path):
    """`q` quits every screen with no text box on it. Home has one, so the key
    never arrives — which left the front screen with no visible way out."""

    async def body(app, pilot):
        assert app.screen.__class__.__name__ == "HomeScreen"
        # It is advertised, not just present.
        assert "ctrl+q quit" in screen_text(app)

        await pilot.press("ctrl+q")
        await pilot.pause(0.3)
        assert app._exit or not app.is_running

    drive(body, tmp_path)
