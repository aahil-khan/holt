"""Entry points: which open issue an outsider should attempt first.

**Not shipped. Kept as the prototype that showed what not to build.**

It was designed, pre-registered and then measured against the comparators that
could make it unnecessary (`eval/PATHFINDER-DESIGN.md`, written before any of it
existed). It did not beat them. The measurement is a module constant here, not a
line in a document the reader will never open, because a ranking whose evaluation
lives only in the README is an unsupported ranking with the caveat filed where
nobody looks.

**Why it failed is more useful than the fact that it did.** This ranker never
sees the contributor. It produces one ranking for everybody, which means it is
answering "which issues here are generally approachable" -- exactly what a
`good first issue` label already encodes. It did not lose because the model is
weak. It lost because it was solving the label's problem, and a tie with the
label is the expected outcome of that.

Available behind `holt analyze --entry-points`, off by default, and it still
prints its own measurement when asked for. The successor question -- which issue
is a sensible next step *for this person, given what they have already merged
here* -- is a different question, and one no label answers.
"""

from __future__ import annotations

from holt.agent.signals import build_threads, compute
from holt.agent.stages import find_paths
from holt.issues import open_at_cutoff
from holt.model import ModelClient
from holt.types import EvidenceRecord

# The signals the ranker is shown. Kept as a constant because the evaluation and
# the shipped path must build byte-identical prompts, or the recorded trajectories
# stop replaying and the published number stops describing what users run.
RANKER_SIGNALS = ("outsider_merged", "outsider_threads", "median_first_response_hours")

#: Measured on both pools. Regenerate with:
#:     uv run python eval/pathfinder_harness.py --replay
#:     uv run python eval/pathfinder_harness.py --replay --pool eval/pool2.json \
#:         --labels eval/results_labels_pool2.json
MEASURED = {
    "repositories": 25,
    "issues_ranked": 3613,
    "precision_at_3": {"holt": 0.173, "good_first_issue": 0.187, "recency": 0.160, "random": 0.151},
    "paired_ci_vs_label": (-0.133, 0.120),
    "sign_test_p": 0.51,
    "repos_with_no_labelled_issue": 13,
}

DISCLAIMER = (
    "> **This ranking is not measurably better than picking at random.** Measured\n"
    "> over 25 repositories and 3,613 issues held out before the cutoff:\n"
    "> precision@3 was **0.173** for this ranking, **0.187** for GitHub's\n"
    "> `good first issue` label and **0.151** for a random pick — differences well\n"
    "> inside noise (paired 95% CI [−0.13, +0.12], sign test p = 0.51).\n"
    ">\n"
    "> It is printed anyway because **13 of those 25 repositories had no\n"
    "> beginner-labelled issue at all**, so on half of them there is no free signal\n"
    "> to lose to. Read it as a reading order, not a recommendation.\n"
    ">\n"
    "> Check it yourself: `uv run python eval/pathfinder_harness.py --replay`"
)


def rank(
    repo: str,
    issue_records: list[EvidenceRecord],
    pull_records: list[EvidenceRecord],
    model: ModelClient,
) -> list[dict]:
    """Rank the issues open at the cutoff. `[]` when there are none.

    Called by both `eval/pathfinder_harness.py` and the CLI, so the ranking a
    user sees is produced by the same code path as the ranking that was scored.
    """
    candidates = open_at_cutoff(issue_records)
    if not candidates:
        return []
    signals = compute(build_threads(pull_records)).as_dict()
    return find_paths(
        repo,
        list(candidates.values()),
        {k: signals[k] for k in RANKER_SIGNALS},
        model,
    )
