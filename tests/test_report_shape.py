"""The report is a deliverable, so its shape is tested like one.

Everything here is about what a reader sees. The failures being guarded against
are the ones that make generated output look generated: a quotation mark with
nothing inside it, a sentence that stops mid-word, a heading over an empty
section, and a verdict word printed without saying what it means for the reader.
"""

from __future__ import annotations

import pytest

from holt.agent.pipeline import MAX_CLAIM_CHARS, clip
from holt.report import Assessment, Claim, Verdict


def build(**kw) -> str:
    base = dict(repo="a/b", verdict=Verdict.VIABLE, summary="Prose.")
    return Assessment(**{**base, **kw}).render()


@pytest.mark.parametrize(
    "verdict,expected",
    [(Verdict.VIABLE, "Worth your time"),
     (Verdict.NOT_VIABLE, "Not worth your time"),
     (Verdict.INSUFFICIENT_EVIDENCE, "Not enough evidence to say")],
)
def test_the_headline_says_what_the_verdict_means_for_the_reader(verdict, expected):
    assert expected in build(verdict=verdict)


def test_the_time_budget_is_stated_because_the_answer_depends_on_it():
    assert "with 3 days" in build(contributor_days=3)
    assert "with 1 day." in build(contributor_days=1)


def test_empty_sections_do_not_get_headings():
    out = build(bottom_line="", limits="", rules=[], claims=[])
    for heading in ("What decided it", "What could not be determined", "Evidence"):
        assert heading not in out


def test_the_deciding_rule_is_shown_not_described():
    """A chat answer cannot be asked which rule fired. This one can."""
    out = build(rules=["rubber_stamp: reviewed_share 0.04 < 0.20"])
    assert "## What decided it" in out
    assert "reviewed_share 0.04 < 0.20" in out


def test_clip_never_cuts_mid_word():
    text = "The maintainer asked for a smaller diff before they would look at it again"
    out = clip(text, 40)
    assert out.endswith("…")
    assert text.startswith(out[:-1])
    assert out[-2] != " "
    # what survives is whole words
    assert all(w in text.split() for w in out[:-1].split())


def test_clip_leaves_short_text_untouched():
    assert clip("  already   short ", 100) == "already short"


def test_a_long_note_is_clipped_before_it_reaches_the_reader():
    note = "word " * 200
    assert len(clip(note, MAX_CLAIM_CHARS)) <= MAX_CLAIM_CHARS + 1


def test_a_claim_keeps_its_evidence_id_next_to_it():
    out = build(claims=[Claim("merged after review", "pr:a/b#1:opened")])
    assert "- merged after review — `pr:a/b#1:opened`" in out
