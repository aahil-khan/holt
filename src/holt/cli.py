"""holt — is this repository worth an outside contributor's week?"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from holt import baseline, model
from holt.agent import entry, pipeline
from holt.evidence.fixtures import FixtureProvider
from holt.evidence.provider import EvidenceProvider
from holt.report import EntryPoint
from holt.types import Window

# Issue evidence is captured and replayed separately from pull-request evidence,
# so that adding the ranker did not invalidate a single recorded verdict
# trajectory. The evaluation of the verdict and the evaluation of the ranking stay
# independent of each other.
ISSUE_ROOT = "fixtures/issues"
PATHFINDER_TRAJECTORIES = "pathfinder"


def normalise(repo: str) -> str:
    repo = repo.strip().rstrip("/")
    if "github.com" in repo:
        repo = repo.split("github.com", 1)[1].lstrip("/:")
    return "/".join(repo.split("/")[:2])


def make_issue_provider(live: bool) -> EvidenceProvider:
    if not live:
        return FixtureProvider(Window.PRE_T, root=Path(ISSUE_ROOT))
    from holt.evidence.github_graphql import LiveGitHubIssueProvider

    return LiveGitHubIssueProvider(Window.PRE_T)


def make_provider(live: bool) -> EvidenceProvider:
    if not live:
        return FixtureProvider(Window.PRE_T)
    from holt.evidence.github_graphql import LiveGitHubProvider

    return LiveGitHubProvider(Window.PRE_T)


def add_entry_points(assessment, repo: str, provider, args) -> None:
    """Attach a ranked reading order, or say nothing at all.

    Silent on failure by design: a missing issue fixture means we cannot rank,
    and a tool that invents an entry point when it has no issues is worse than
    one that omits the section.
    """
    try:
        issues = make_issue_provider(args.live).fetch(repo)
    except FileNotFoundError:
        return
    # Recorded under its own directory, so the ranker's calls and the verdict's
    # calls replay independently and adding one never invalidated the other.
    path = model.TRAJECTORY_DIR / PATHFINDER_TRAJECTORIES / (repo.replace("/", "__") + ".jsonl")
    client = model.ReplayModel(path) if args.replay else model.OpenAIModel(path)
    ranked = entry.rank(repo, list(issues), list(provider.fetch(repo)), client)
    assessment.entry_points = [
        EntryPoint(r["evidence_id"], r["first_step"], r.get("why", "")) for r in ranked
    ]


def cmd_analyze(args: argparse.Namespace) -> int:
    repo = normalise(args.repo)
    provider = make_provider(args.live)
    client = model.build(repo, replay=args.replay)

    if args.baseline:
        assessment = baseline.assess(repo, provider, client)
    else:
        assessment, trace = pipeline.analyze(repo, provider, client, contributor_days=args.days)
        if args.show_verification:
            print(
                f"<!-- findings before verification: {trace.before_verification}, "
                f"after: {trace.after_verification}, dropped: {len(trace.dropped)} -->",
                file=sys.stderr,
            )
            for d in trace.dropped:
                print(f"<!-- DROPPED {d.field}={d.value!r} cited {list(d.evidence_ids)} -->",
                      file=sys.stderr)
    if not args.baseline and not args.no_entry_points:
        add_entry_points(assessment, repo, provider, args)
    print(assessment.render())
    if not args.replay:
        u = client.usage
        print(
            f"<!-- {u.input_tokens} in / {u.output_tokens} out tokens, "
            f"${u.cost_usd:.4f} -->",
            file=sys.stderr,
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="holt", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="assess one repository")
    analyze.add_argument("repo", help="owner/name or a github.com URL")
    analyze.add_argument(
        "--baseline",
        action="store_true",
        help="run the baseline solution: a single prompt over README and metadata",
    )
    analyze.add_argument(
        "--replay",
        action="store_true",
        help="replay recorded model output; no API key, no spend",
    )
    analyze.add_argument(
        "--days",
        type=int,
        default=7,
        help="how many days you actually have; everything time-shaped scales from it",
    )
    analyze.add_argument(
        "--no-entry-points",
        action="store_true",
        help="skip the ranked reading order (see its measured precision in the output)",
    )
    analyze.add_argument(
        "--show-verification",
        action="store_true",
        help="print the findings Stage D dropped and why",
    )
    analyze.add_argument(
        "--live",
        action="store_true",
        help="read GitHub directly instead of committed fixtures (needs GITHUB_TOKEN)",
    )
    analyze.set_defaults(func=cmd_analyze)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
