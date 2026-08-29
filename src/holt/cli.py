"""holt — is this repository worth an outside contributor's week?"""

from __future__ import annotations

import argparse
import sys

from holt import baseline, model
from holt.agent import pipeline
from holt.evidence.fixtures import FixtureProvider
from holt.evidence.provider import EvidenceProvider
from holt.types import Window


def normalise(repo: str) -> str:
    repo = repo.strip().rstrip("/")
    if "github.com" in repo:
        repo = repo.split("github.com", 1)[1].lstrip("/:")
    return "/".join(repo.split("/")[:2])


def make_provider(live: bool) -> EvidenceProvider:
    if not live:
        return FixtureProvider(Window.PRE_T)
    from holt.evidence.github_graphql import LiveGitHubProvider

    return LiveGitHubProvider(Window.PRE_T)


def cmd_analyze(args: argparse.Namespace) -> int:
    repo = normalise(args.repo)
    provider = make_provider(args.live)
    client = model.build(repo, replay=args.replay)

    if args.baseline:
        assessment = baseline.assess(repo, provider, client)
    else:
        assessment, trace = pipeline.analyze(repo, provider, client)
        if args.show_verification:
            print(
                f"<!-- findings before verification: {trace.before_verification}, "
                f"after: {trace.after_verification}, dropped: {len(trace.dropped)} -->",
                file=sys.stderr,
            )
            for d in trace.dropped:
                print(f"<!-- DROPPED {d.field}={d.value!r} cited {list(d.evidence_ids)} -->",
                      file=sys.stderr)
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
