"""Fixtures are what make the eval reproducible without credentials.

They are also the easiest place to break the holdout by accident, so the loader
re-asserts on every read instead of trusting what is on disk.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from holt.evidence.fixtures import FixtureProvider, content_hash, write_fixture
from holt.evidence.provider import ContaminationError
from holt.types import T_CUTOFF, EvidenceRecord, Window

BEFORE = T_CUTOFF - timedelta(days=1)
AFTER = T_CUTOFF + timedelta(days=1)


def record(evidence_id, timestamp):
    return EvidenceRecord(evidence_id, "github", "https://x", timestamp, {"k": "v"})


def test_capture_and_reload_round_trips(tmp_path):
    original = [record("pr:a/b#1:opened", BEFORE), record("pr:a/b#1:comment:0", BEFORE)]
    write_fixture("a/b", Window.PRE_T, original, root=tmp_path)

    reloaded = FixtureProvider(Window.PRE_T, root=tmp_path).fetch("a/b")
    assert [r.evidence_id for r in reloaded] == [r.evidence_id for r in original]
    assert [r.timestamp for r in reloaded] == [r.timestamp for r in original]
    assert reloaded[0].payload == {"k": "v"}


def test_content_hash_ignores_capture_order():
    a, b = record("pr:x#2:opened", BEFORE), record("pr:x#1:opened", BEFORE)
    assert content_hash([a, b]) == content_hash([b, a])


def test_hand_edited_fixture_is_rejected(tmp_path):
    """A fixture whose evidence changed after capture must not silently load."""
    path = write_fixture("a/b", Window.PRE_T, [record("pr:a/b#1:opened", BEFORE)], root=tmp_path)
    data = json.loads(path.read_text())
    data["records"][0]["payload"]["k"] = "tampered"
    path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="content hash mismatch"):
        FixtureProvider(Window.PRE_T, root=tmp_path).fetch("a/b")


def test_post_cutoff_record_in_a_pre_cutoff_fixture_still_raises(tmp_path):
    """The window assertion runs on load, so a bad capture cannot reach the agent."""
    write_fixture("a/b", Window.PRE_T, [record("pr:a/b#1:merged", AFTER)], root=tmp_path)
    with pytest.raises(ContaminationError):
        FixtureProvider(Window.PRE_T, root=tmp_path).fetch("a/b")


def test_misfiled_fixture_is_refused(tmp_path):
    """A capture bug that writes post-T evidence into the pre-T directory.

    The file's own `window` field disagrees with where it sits, which the loader
    catches before any record is handed on.
    """
    written = write_fixture("a/b", Window.POST_T, [record("pr:a/b#1:merged", AFTER)], root=tmp_path)
    misfiled = tmp_path / Window.PRE_T.value / written.name
    misfiled.parent.mkdir(parents=True, exist_ok=True)
    misfiled.write_text(written.read_text())

    with pytest.raises(ValueError, match="must not be mixed"):
        FixtureProvider(Window.PRE_T, root=tmp_path).fetch("a/b")


def test_missing_fixture_says_what_to_do(tmp_path):
    with pytest.raises(FileNotFoundError, match="never reaches the network"):
        FixtureProvider(Window.PRE_T, root=tmp_path).fetch("nope/nope")
