"""The only path from findings to a verdict, and it is a plain function.

No model runs here. Three reasons, all of which matter:

* a judge who reruns Holt gets our numbers, not a resample of them
* scoring across a pool is not polluted by model variance
* "is this just a wrapper around a prompt?" is answered by a file rather than
  an argument

Stage E writes prose *around* this decision and is handed the result as an input
it cannot change. A test asserts the rendered report and this function agree.
"""

from __future__ import annotations

from holt.agent.findings import Findings
from holt.agent.signals import Signals
from holt.report import Verdict

# Kinds where a merged pull request is not a software contribution. Landing work
# in these is easy and means nothing for the question being asked.
NON_SOFTWARE_KINDS = {"registry", "awesome_list", "portfolio", "course_material"}

# Kinds where outside contribution is not accepted regardless of activity.
CLOSED_KINDS = {"mirror"}

# --- contesting the one field that can decide alone -------------------------
#
# `repo_kind` is the only model-derived input either of the rules above reads,
# and Stage D cannot check it: it verifies that a cited id resolves, and a
# classification is not a quotation. A model that answers `mirror` while citing
# a real README has made a claim that verifies perfectly and is false -- which
# is exactly what happened to `pytorch/pytorch` under a 3B local model, and to
# `aden-hive/hive`, which was called a registry.
#
# So the two kinds that can flip a verdict are checked against the evidence they
# implicitly claim something about. What is contested is the rule's stated
# *reason*, never what the repository "really is": a catalogue entry is one file
# in one place, and a mirror does not merge outsiders' pull requests. Where the
# evidence disagrees the field is dropped rather than overridden -- no verdict
# is asserted in its place, `classify` falls through to the arithmetic, and the
# disagreement is printed for the reader.
#
# Pre-registered with its predictions in eval/PREREGISTRATION-4.md; thresholds
# chosen on pool 1 and that fitting disclosed there.
CATALOGUE_KINDS = {"registry", "awesome_list"}

# `portfolio` and `course_material` are deliberately not contested this way.
# Their reason is about whose project it is, not the shape of a diff, and a
# portfolio being real code is not a contradiction.
MIN_MERGES_FOR_SHAPE = 5

# One directory. Not "few enough files": that criterion was pre-registered,
# failed out-of-sample, and is gone. `microsoft/winget-pkgs` is a real registry
# whose every entry is three YAML manifests -- installer, locale, version -- in
# one package directory, so a median-files test called a correct classification
# a hallucination on all four of its recordings. What survived is the criterion
# that did not misfire: a catalogue entry lands in one place, whatever it
# weighs. The narrowing was chosen after seeing that failure and is disclosed as
# such in eval/PREREGISTRATION-4.md; it has no untouched holdout behind it.
CATALOGUE_DIRS_MAX = 2

# How long the contributor has. Everything time-shaped scales from this, because
# "is this repository worth my time" has no answer independent of how much time
# you have: a maintainer who replies in five days is fine if you have three
# months and useless if you have three days.
DEFAULT_CONTRIBUTOR_DAYS = 7

# Rubber-stamp rejection. Validated out-of-sample on pool 2 -- specificity 0.58
# to 0.83 with all three pre-registered predictions holding. Thresholds were
# chosen on pool 1 and that fitting is disclosed in eval/PREREGISTRATION-2.md.
#
# Both halves are required. Landing easily alone describes a welcoming project;
# going unreviewed alone describes a project whose review happens elsewhere,
# which is what killed the first rejection rule when nixpkgs was withheld. It is
# the conjunction that describes work being waved through unread.
RUBBER_STAMP_REVIEWED_MAX = 0.20
RUBBER_STAMP_MERGE_RATE_MIN = 0.60

# One merge from one person is an anecdote; two people is a pattern.
MIN_MERGES = 2
MIN_DISTINCT_AUTHORS = 2

# Below this share of ignored attempts, silence is noise rather than a policy.
IGNORED_SHARE = 0.7

# ...and below this many attempts there is no share worth speaking of. Four
# ignored pull requests out of four is not evidence of hostility, it is four
# data points. tensorflow/tensorflow reaches exactly that shape: 97% of its pull
# request traffic is automation, leaving a handful of outsider threads. Without
# this guard the rule turns a thin sample into a confident accusation.
MIN_ATTEMPTS_FOR_HOSTILE = 8


def contested_kind(
    findings: Findings, signals: Signals, meta: dict | None = None
) -> str | None:
    """Why the claimed `repo_kind` disagrees with the evidence, or None.

    Returns the sentence a reader should see, not a boolean: a field being
    dropped is a thing that happened to their report and it is printed.
    """
    kind = findings.get("repo_kind")

    if kind in CATALOGUE_KINDS:
        if (
            signals.merged_with_files >= MIN_MERGES_FOR_SHAPE
            and signals.merged_dirs_median is not None
            and signals.merged_dirs_median >= CATALOGUE_DIRS_MAX
        ):
            return (
                f"repo_kind={kind} was claimed, but merged work here spans a "
                f"median of {signals.merged_dirs_median:g} top-level directories "
                "rather than landing in one place, which is not a catalogue "
                "entry; the field is dropped and decided nothing"
            )

    if kind in CLOSED_KINDS:
        # `is_mirror` alone would not be enough -- GitHub sets it only for
        # repositories created as mirrors, so a genuine mirror can report
        # false. The merges are what disprove the claim being made.
        if (
            (meta or {}).get("is_mirror") is False
            and signals.outsider_merged >= MIN_MERGES
            and signals.distinct_merged_authors >= MIN_DISTINCT_AUTHORS
        ):
            return (
                f"repo_kind={kind} was claimed, but GitHub does not report this "
                f"repository as a mirror and {signals.outsider_merged} outside "
                f"pull requests by {signals.distinct_merged_authors} people were "
                "merged in the period read; the field is dropped and decided nothing"
            )

    return None


def classify(
    findings: Findings,
    signals: Signals,
    contributor_days: int = DEFAULT_CONTRIBUTOR_DAYS,
) -> tuple[Verdict, list[str]]:
    """Return a verdict and the rule trace that produced it.

    `contributor_days` is the time the person actually has. Re-running this
    function with a different budget costs nothing and calls no model, because
    the findings are already computed -- which is a thing a single prompt cannot
    do without paying for the whole assessment again.
    """
    trace: list[str] = []
    slow_response_hours = contributor_days * 24.0
    kind = findings.get("repo_kind")

    if findings.get("is_archived"):
        trace.append("archived: no longer accepting work")
        return Verdict.NOT_VIABLE, trace

    if kind in CLOSED_KINDS:
        trace.append(f"repo_kind={kind}: outside pull requests are not the contribution path")
        return Verdict.NOT_VIABLE, trace

    if kind in NON_SOFTWARE_KINDS:
        trace.append(f"repo_kind={kind}: merged work here is not a software contribution")
        return Verdict.NOT_VIABLE, trace

    if signals.outsider_threads == 0:
        # "In the period read", not "before the cutoff": the cutoff is an
        # evaluation device, and this line is printed verbatim to users.
        trace.append("no outsider attempts in the period read: nothing to judge from")
        return Verdict.INSUFFICIENT_EVIDENCE, trace

    ignored_share = signals.outsider_ignored / signals.outsider_threads
    if (
        signals.outsider_merged == 0
        and ignored_share > IGNORED_SHARE
        and signals.outsider_threads >= MIN_ATTEMPTS_FOR_HOSTILE
    ):
        trace.append(
            f"{signals.outsider_ignored}/{signals.outsider_threads} outsider attempts "
            "drew no response and none merged"
        )
        return Verdict.NOT_VIABLE, trace

    slow = (
        signals.median_first_response_hours is not None
        and signals.median_first_response_hours > slow_response_hours
    )
    if (
        signals.outsider_merged >= MIN_MERGES
        and signals.distinct_outsider_authors >= MIN_DISTINCT_AUTHORS
        and not slow
    ):
        trace.append(
            f"{signals.outsider_merged} first-time merges by "
            f"{signals.distinct_merged_authors} distinct people, out of "
            f"{signals.outsider_threads} attempts by "
            f"{signals.distinct_outsider_authors}; median first response "
            f"{signals.median_first_response_hours}h"
        )
        if (
            signals.reviewed_share is not None
            and signals.merge_rate is not None
            and signals.reviewed_share < RUBBER_STAMP_REVIEWED_MAX
            and signals.merge_rate > RUBBER_STAMP_MERGE_RATE_MIN
        ):
            trace.append(
                f"but only {signals.reviewed_share:.0%} of merges drew any human "
                f"reply while {signals.merge_rate:.0%} of attempts landed: work is "
                "being waved through unread, so a contribution here buys no review"
            )
            return Verdict.NOT_VIABLE, trace
        return Verdict.VIABLE, trace

    if slow:
        trace.append(
            f"median first response {signals.median_first_response_hours}h "
            f"exceeds the {slow_response_hours:.0f}h a {contributor_days}-day "
            "budget allows"
        )
    if signals.outsider_merged == 0 and ignored_share > IGNORED_SHARE:
        trace.append(
            f"{signals.outsider_ignored}/{signals.outsider_threads} attempts ignored, "
            f"but fewer than {MIN_ATTEMPTS_FOR_HOSTILE} attempts is too thin to call hostile"
        )
    elif signals.outsider_merged < MIN_MERGES:
        trace.append(f"only {signals.outsider_merged} outsider merges in the period read")
    return Verdict.INSUFFICIENT_EVIDENCE, trace
