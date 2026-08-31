"""Where outsider work landed — a count, not a claim.

This section makes no prediction, so nothing here is about accuracy. It is about
not misleading: an attempt counted once per pull request rather than once per
file, a directory named "never landed" only when enough people tried for the
statement to mean anything, and silence when there is nothing to report.
"""

from __future__ import annotations

from datetime import timedelta

from holt.agent.landing import MIN_ATTEMPTS, area_of, compute, render
from holt.agent.signals import Thread
from holt.types import T_CUTOFF

BEFORE = T_CUTOFF - timedelta(days=10)


def thread(n: int, author: str, files: list[str], merged: bool, day: int = 0) -> Thread:
    return Thread(
        key=f"pr:a/b#{n}", number=n, author=author, author_is_bot=False,
        opened_at=BEFORE + timedelta(days=day), files=files, merged=merged,
    )


def landing_for(threads: list[Thread]):
    return compute({t.key: t for t in threads})


def test_a_path_is_cut_to_two_segments():
    assert area_of("pkgs/by-name/fo/foo/package.nix") == "pkgs/by-name"
    assert area_of("README.md") == "(root)"
    assert area_of("tests/conftest.py") == "tests/conftest.py"


def test_a_wide_pull_request_counts_once_per_area():
    """Forty files in one directory is one attempt at it, not forty."""
    wide = thread(1, "newcomer", [f"src/core/f{i}.py" for i in range(40)], merged=True)
    # Padding so the area-to-thread ratio does not trip the regrouping fallback,
    # which is a different behaviour tested separately.
    others = [thread(10 + i, f"new{i}", ["src/core/x.py"], merged=False, day=i)
              for i in range(4)]
    result = landing_for([wide, *others])
    assert [(a.path, a.landed, a.attempted) for a in result.landed] == [("src/core", 1, 5)]


def test_an_author_stops_being_an_outsider_after_their_first_merge():
    """Their second landing says nothing about whether a stranger could land.

    Outsider status is decided per thread in time order, so the same person's
    first pull request counts and their later ones do not. Without this, a repo
    where one prolific newcomer merged forty times would look wide open.
    """
    threads = [
        thread(1, "regular", ["core/one/first.py"], merged=True, day=0),
        thread(2, "regular", ["core/one/second.py"], merged=True, day=1),
        thread(3, "regular", ["core/one/third.py"], merged=True, day=2),
        thread(4, "regular", ["core/one/fourth.py"], merged=True, day=3),
        # Other newcomers in the same area, so the regrouping fallback (tested
        # separately) does not fire on a one-thread sample.
        *[thread(10 + i, f"new{i}", ["core/one/x.py"], merged=False, day=4 + i)
          for i in range(3)],
    ]
    landed = landing_for(threads).landed
    assert [(a.path, a.landed, a.attempted) for a in landed] == [("core/one", 1, 4)]


def test_a_directory_nobody_landed_in_is_reported_separately():
    threads = [thread(i, f"new{i}", ["hard/area/x.py"], merged=False, day=i)
               for i in range(MIN_ATTEMPTS)]
    result = landing_for(threads)
    assert result.landed == []
    assert [(a.path, a.attempted) for a in result.never] == [("hard/area", MIN_ATTEMPTS)]


def test_one_lone_failure_is_not_called_a_dead_end():
    """A single unmerged attempt is not evidence that a door is shut."""
    result = landing_for([thread(1, "newcomer", ["hard/area/x.py"], merged=False)])
    assert result.never == []


def test_nothing_to_say_renders_nothing():
    """No heading over an empty section, and no section over an empty repository."""
    assert render(landing_for([])) == []


def test_the_rendered_section_states_what_it_is_not():
    threads = [thread(i, f"new{i}", ["shut/door/x.py"], merged=False, day=i)
               for i in range(MIN_ATTEMPTS)]
    out = "\n".join(render(landing_for(threads)))
    assert "not a rule" in out
    assert "only a couple of people ever tried" in out


def test_a_split_that_groups_nothing_falls_back_to_one_segment():
    """A registry where every entry is its own directory.

    At two segments this produced ninety single-merge rows that looked like
    insight and carried none. It must collapse to the one true statement:
    everything lands in `plugins`.
    """
    threads = [thread(i, f"new{i}", [f"plugins/thing-{i}/manifest"], merged=True, day=i)
               for i in range(20)]
    landed = landing_for(threads).landed
    assert [(a.path, a.landed) for a in landed] == [("plugins", 20)]


def test_a_split_that_does_group_is_kept():
    """The fallback must not fire on a repository with real structure."""
    threads = [thread(i, f"new{i}", [f"pkgs/by-name/x{i}.nix"], merged=True, day=i)
               for i in range(10)]
    threads += [thread(50 + i, f"other{i}", [f"nixos/modules/y{i}.nix"], merged=True, day=i)
                for i in range(10)]
    paths = {a.path for a in landing_for(threads).landed}
    assert paths == {"pkgs/by-name", "nixos/modules"}


def test_tied_areas_are_ordered_the_same_way_in_every_process():
    """Ties used to be broken by the interpreter's hash seed.

    `_tally` walked a set of areas, so the order two equally-attempted
    directories were first counted in varied per process, and
    `Counter.most_common` breaks ties by exactly that order. The same command
    on the same evidence printed three different reports across eight runs.
    Ranking on the path as well as the count makes the tie a decision.
    """
    # Four areas, every one landed once of two attempts: nothing but the path
    # can order them.
    threads = []
    n = 0
    for area in ("d/four", "a/one", "c/three", "b/two"):
        for merged in (True, False):
            n += 1
            threads.append(
                thread(n, f"new{n}", [f"{area}/f.py"], merged=merged, day=n)
            )
    ranked = [a.path for a in landing_for(threads).landed]
    assert ranked == ["a/one", "b/two", "c/three", "d/four"]


def test_a_tied_dead_end_is_ordered_by_path_too():
    """The `never` list is ranked by the same rule as the landed one."""
    threads = []
    n = 0
    for area in ("z/last", "m/mid", "a/first"):
        for _ in range(MIN_ATTEMPTS):
            n += 1
            threads.append(
                thread(n, f"new{n}", [f"{area}/f.py"], merged=False, day=n)
            )
    # One landed area so the report has something to show alongside the rest,
    # plus padding: enough threads that the area-to-thread ratio does not trip
    # the regrouping fallback, which is a different behaviour tested above.
    n += 1
    threads.append(thread(n, f"new{n}", ["got/in/f.py"], merged=True, day=n))
    for _ in range(6):
        n += 1
        threads.append(thread(n, f"pad{n}", ["got/in/f.py"], merged=False, day=n))
    assert [a.path for a in landing_for(threads).never] == [
        "a/first", "m/mid", "z/last",
    ]
