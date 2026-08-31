"""The stated profile: round-trip, flag precedence, and the query it builds."""

from argparse import Namespace
from datetime import UTC, datetime

from holt import profile as profile_mod
from holt.discover import build_queries
from holt.profile import Profile

AS_OF = datetime(2026, 8, 1, tzinfo=UTC)


def test_profile_round_trips_through_toml(tmp_path):
    path = tmp_path / "profile.toml"
    stated = Profile(languages=["python", "rust"], topics=["cli"],
                     contributions=["tests"], days=3)
    profile_mod.save(stated, path)
    assert profile_mod.load(path) == stated


def test_missing_profile_loads_as_none(tmp_path):
    assert profile_mod.load(tmp_path / "absent.toml") is None


def test_flags_override_stored_fields_individually():
    stored = Profile(languages=["python"], topics=["cli"], days=7)
    args = Namespace(lang=None, topic="tui", contribution=None, days=None)
    merged = profile_mod.from_args(args, stored)
    assert merged.languages == ["python"]  # kept from the stored profile
    assert merged.topics == ["tui"]  # overridden by the flag
    assert merged.days == 7


def test_one_query_per_language_because_github_ands_qualifiers():
    queries = build_queries(Profile(languages=["python", "rust"], topics=["cli"]), AS_OF)
    assert len(queries) == 2
    assert any("language:python" in q for q in queries)
    assert any("language:rust" in q for q in queries)
    assert all("topic:cli" in q for q in queries)
    assert all("archived:false" in q for q in queries)


def test_no_language_still_produces_a_query():
    (query,) = build_queries(Profile(topics=["game-engine"]), AS_OF)
    assert "topic:game-engine" in query
    assert "language:" not in query
