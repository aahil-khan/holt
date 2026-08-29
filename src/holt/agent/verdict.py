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

# A week. Past this, a newcomer has moved on before anyone replied.
SLOW_RESPONSE_HOURS = 168.0

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


def classify(findings: Findings, signals: Signals) -> tuple[Verdict, list[str]]:
    """Return a verdict and the rule trace that produced it."""
    trace: list[str] = []
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
        trace.append("no outsider attempts before the cutoff: nothing to judge from")
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
        and signals.median_first_response_hours > SLOW_RESPONSE_HOURS
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
        return Verdict.VIABLE, trace

    if slow:
        trace.append(
            f"median first response {signals.median_first_response_hours}h "
            f"exceeds {SLOW_RESPONSE_HOURS}h"
        )
    if signals.outsider_merged == 0 and ignored_share > IGNORED_SHARE:
        trace.append(
            f"{signals.outsider_ignored}/{signals.outsider_threads} attempts ignored, "
            f"but fewer than {MIN_ATTEMPTS_FOR_HOSTILE} attempts is too thin to call hostile"
        )
    elif signals.outsider_merged < MIN_MERGES:
        trace.append(f"only {signals.outsider_merged} outsider merges before the cutoff")
    return Verdict.INSUFFICIENT_EVIDENCE, trace
