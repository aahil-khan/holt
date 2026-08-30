"""The TUI's observation layer, and the coupling it is allowed to have.

Three things are held here:

* Watching a run does not change it. The assessment produced with the observers
  in place is identical to the one produced without them, because a second way
  of running a stage is exactly what this feature must not become.
* The keys `holt.tui.observe` reads off each stage's response still exist. That
  file mirrors `holt.agent.stages` so the live view can show a claim before
  Stage D judges it; the mirror is pinned here so a schema change breaks a test
  instead of silently emptying a panel.
* The Stage D drop reaches the event stream, from a repository where a drop
  really happens rather than a constructed one.

None of these import Textual. The observation layer is useful without a
terminal, and the tests run on a checkout that never installed the extra.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from holt import model
from holt.agent import pipeline
from holt.evidence.fixtures import FixtureProvider
from holt.tui import events
from holt.tui.observe import EXPECTED_KEYS, ObservingModel, ObservingProvider
from holt.tui.session import RunOptions, Session
from holt.types import Window

# A repository whose recorded run drops a finding: the model cited
# `no_contributing_file`, an id it invented, which does not resolve.
DROPS = "Sistema-de-certificacion-academica/Sistema-de-certificacion-academica"
CLEAN = "home-assistant/core"

pytestmark = pytest.mark.skipif(
    not Path("fixtures/trajectories").is_dir(),
    reason="recorded trajectories are not present in this checkout",
)


def _run(repo: str, emit=None):
    events_seen: list = []
    emit = emit or events_seen.append
    provider = ObservingProvider(FixtureProvider(Window.PRE_T), emit)
    client = ObservingModel(model.build(repo, replay=True), emit, repo)
    assessment, trace = pipeline.analyze(repo, provider, client)
    return assessment, trace, events_seen


def test_observing_does_not_change_the_result():
    """The wrappers are pure delegates, and this is what that has to mean."""
    watched, watched_trace, _ = _run(DROPS)

    plain_assessment, plain_trace = pipeline.analyze(
        DROPS, FixtureProvider(Window.PRE_T), model.build(DROPS, replay=True)
    )

    assert watched.verdict == plain_assessment.verdict
    assert watched.summary == plain_assessment.summary
    assert watched.render() == plain_assessment.render()
    assert [(c.text, c.evidence_id) for c in watched.claims] == [
        (c.text, c.evidence_id) for c in plain_assessment.claims
    ]
    assert watched_trace.before_verification == plain_trace.before_verification
    assert watched_trace.after_verification == plain_trace.after_verification
    assert [d.field for d in watched_trace.dropped] == [
        d.field for d in plain_trace.dropped
    ]


@pytest.mark.parametrize("repo", [CLEAN, DROPS])
def test_stage_responses_still_carry_the_keys_the_live_view_reads(repo):
    """`observe.py` mirrors `stages.py`. If the mirror cracks, fail loudly.

    A live view that renders nothing because a key was renamed looks like a
    working interface with a quiet repository behind it, which is the worst
    failure mode available to this feature.
    """
    _, _, seen = _run(repo)
    responses = {e.stage: e.payload for e in seen if isinstance(e, events.ToolResponse)}

    for stage, keys in EXPECTED_KEYS.items():
        assert stage in responses, f"no recorded response for stage {stage!r}"
        for key in keys:
            assert key in responses[stage], (
                f"stage {stage!r} no longer returns {key!r}; "
                "holt.tui.observe reads it to build the live view"
            )


def test_every_finding_the_engine_records_is_also_emitted():
    """The stream shows the same number of claims the engine actually built."""
    _, trace, seen = _run(DROPS)
    emitted = [e for e in seen if isinstance(e, events.FindingEmitted)]
    assert len(emitted) == trace.before_verification


def test_the_drop_reaches_the_event_stream():
    session = Session(RunOptions(repo=DROPS, replay=True))
    session.start()
    session.wait(120)

    assert session.error is None, session.error
    dropped = [e for e in session.log if isinstance(e, events.FindingDropped)]
    assert len(dropped) == 1
    assert dropped[0].field == "onboarding"
    assert dropped[0].cited == ("no_contributing_file",)

    # The same moment seen from the provider's side: the id was looked up and
    # did not resolve. Stage D needs no hook in the engine to be visible.
    failed = [
        e.evidence_id
        for e in session.log
        if isinstance(e, events.EvidenceResolved) and not e.resolved
    ]
    assert "no_contributing_file" in failed

    # And the claim does not reach the reader.
    assert all(
        c.evidence_id != "no_contributing_file" for c in session.assessment.claims
    )


def test_a_clean_run_drops_nothing_and_still_reports_resolution():
    session = Session(RunOptions(repo=CLEAN, replay=True))
    session.start()
    session.wait(120)

    assert session.error is None, session.error
    assert not [e for e in session.log if isinstance(e, events.FindingDropped)]
    assert [e for e in session.log if isinstance(e, events.EvidenceResolved)]
    assert session.assessment.verdict.value == "viable"


def test_describe_survives_an_event_it_has_never_seen():
    """Unknown events degrade to a line. Nothing in the UI may raise on one."""

    class Invented:
        __slots__ = ("stage", "detail")

        def __init__(self):
            self.stage, self.detail = "new_stage", "something added later"

    line = events.describe(Invented())
    assert "Invented" in line
    assert "new_stage" in line


def test_verdict_colour_tolerates_a_member_the_tui_has_never_seen():
    from holt.tui import theme

    assert theme.verdict_colour("viable") == theme.VIABLE
    assert theme.verdict_colour("a_verdict_added_later") == theme.VERDICT_FALLBACK
    assert theme.verdict_label("not_viable") == "not viable"
