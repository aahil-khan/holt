"""The discovery layer, and the coupling it is allowed to have.

`holt.tui.discovery` reassembles the screening step from `discover`'s own public
parts rather than parsing the markdown `run_replay` prints. That is a real
dependency on the engine, so it is pinned here: the manifest shape, the
functions it calls, and the fact that screening still decides what it decided.

No Textual. The layer is useful without a terminal and these run on a checkout
that never installed the extra.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from holt.tui import discovery

pytestmark = pytest.mark.skipif(
    not discovery.manifest_path_exists(),
    reason="the recorded discovery session is not present in this checkout",
)


def test_the_shipped_session_loads_with_no_credentials():
    """The demo session is the free path. It must need nothing at all."""
    session = discovery.load()

    assert session.name == discovery.DEFAULT_SESSION
    assert session.rows, "the recorded search found no candidates"
    assert session.queries, "a search with no query is not a search"
    assert session.profile_description


def test_screening_keeps_what_it_rejected():
    """A discovery tool that shows only its survivors is asking to be trusted
    about the ones it hid."""
    session = discovery.load()
    cut = [r for r in session.rows if not r.survived]

    assert cut, "this session is expected to cut some candidates"
    assert all(r.category for r in cut)
    # Every cut carries a reason a person can read.
    assert all(discovery.cut_reason(r.category) for r in cut)


def test_survivors_come_first_and_keep_the_search_order():
    """Screening says 'worth a look', never 'better than'. Sorting survivors
    among themselves would assert a ranking screening does not make."""
    session = discovery.load()
    flags = [r.survived for r in session.rows]
    assert flags == sorted(flags, reverse=True)

    import json

    from holt import discover

    manifest = json.loads(discover.manifest_path(session.name).read_text())
    order = [c["slug"] for c in manifest["candidates"]]
    survivors = [r.slug for r in session.rows if r.survived]
    assert survivors == [s for s in order if s in set(survivors)]


def test_the_screening_verdict_is_the_engines_not_ours():
    """`screen_records` holds the rule. This asks it; it does not restate it."""
    import json

    from holt import discover
    from holt.evidence.fixtures import FixtureProvider
    from holt.profile import Profile
    from holt.types import Window

    session = discovery.load()
    manifest = json.loads(discover.manifest_path(session.name).read_text())
    profile = Profile(**manifest["profile"])
    provider = FixtureProvider(
        Window.PRE_T, root=discover.screen_root(session.name), cutoff=session.as_of
    )

    by_slug = {r.slug: r for r in session.rows}
    checked = 0
    for raw in manifest["candidates"]:
        candidate = discover.Candidate(**raw)
        if candidate.slug not in by_slug:
            continue
        expected = discover.screen_records(candidate, provider.fetch(candidate.slug),
                                           profile.days)
        row = by_slug[candidate.slug]
        assert row.category == expected.category
        assert row.verdict == expected.verdict.value
        checked += 1
    assert checked == len(by_slug)


def test_a_session_that_is_not_there_raises_rather_than_inventing_one():
    with pytest.raises(FileNotFoundError):
        discovery.load("no-such-session")


def test_counts_add_up():
    session = discovery.load()
    assert len(session.survivors) + len(
        [r for r in session.rows if not r.survived]
    ) == len(session.rows)


def test_available_lists_the_shipped_session():
    assert discovery.DEFAULT_SESSION in discovery.available()
