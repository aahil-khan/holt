"""Live GitHub evidence, via GraphQL.

REST needs roughly four calls per pull request (the PR, its reviews, its
comments, its files). At 5,000 requests/hour that exhausts the budget well
before the pool is crawled. One GraphQL query returns a page of PRs with all
four, so the same crawl costs a couple of hundred points instead.

A pull request is decomposed into *events*, not stored whole. A PR opened in
April and merged in July is two facts with two timestamps: the agent may see
the first and must not see the second. Storing the PR as a single record with
a single timestamp would force a choice between leaking the merge and hiding
the thread. Event decomposition removes the choice.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator
from datetime import datetime
from typing import Any

import httpx

from holt.evidence.provider import EvidenceProvider
from holt.types import T_CUTOFF, EvidenceRecord, Window

API = "https://api.github.com/graphql"

REPO_META = """
query($owner:String!, $name:String!) {
  rateLimit { remaining resetAt }
  repository(owner:$owner, name:$name) {
    createdAt pushedAt isArchived isMirror isFork stargazerCount
    description homepageUrl primaryLanguage { name }
  }
}
"""

# Date filtering happens server-side. Ordering by newest and paging until the
# timestamps fall past the cutoff would burn most of the rate-limit budget on
# records the window filter then discards.
PR_SEARCH = """
query($q:String!, $cursor:String) {
  rateLimit { remaining resetAt }
  search(query:$q, type:ISSUE, first:25, after:$cursor) {
    issueCount
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        number title createdAt mergedAt closedAt merged
        additions deletions changedFiles
        author { login __typename }
        files(first:20) { nodes { path additions deletions } }
        reviews(first:20) { nodes { createdAt state body author { login __typename } } }
        comments(first:30) { nodes { createdAt body author { login __typename } } }
      }
    }
  }
}
"""


def _ts(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _login(actor: dict[str, Any] | None) -> str:
    """Deleted accounts come back as null; bots carry a distinct __typename."""
    if not actor:
        return "(ghost)"
    return actor.get("login") or "(ghost)"


def _is_bot(actor: dict[str, Any] | None) -> bool:
    if not actor:
        return False
    if actor.get("__typename") == "Bot":
        return True
    login = (actor.get("login") or "").lower()
    return login.endswith("[bot]") or login in {"dependabot", "renovate", "greenkeeper"}


class GitHubGraphQL:
    """Thin transport. Knows about auth, pagination and the rate-limit budget."""

    def __init__(self, token: str | None = None, client: httpx.Client | None = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError(
                "GITHUB_TOKEN is not set. Live mode needs a token; "
                "use fixture or replay mode to run without one."
            )
        self._client = client or httpx.Client(timeout=30.0)
        self.remaining: int | None = None

    def query(self, document: str, **variables: object) -> dict[str, Any]:
        response = self._client.post(
            API,
            headers={"Authorization": f"bearer {self.token}"},
            json={"query": document, "variables": variables},
        )
        response.raise_for_status()
        body = response.json()
        if "errors" in body:
            raise RuntimeError(f"GraphQL error: {body['errors']}")
        data = body["data"]
        if limit := data.get("rateLimit"):
            self.remaining = limit["remaining"]
        return data

    def repo_meta(self, owner: str, name: str) -> dict[str, Any]:
        repo = self.query(REPO_META, owner=owner, name=name)["repository"]
        if repo is None:
            raise RuntimeError(f"{owner}/{name} not found or not public")
        return repo

    def search_pull_requests(self, q: str, max_pages: int = 8) -> Iterator[dict[str, Any]]:
        cursor: str | None = None
        for _ in range(max_pages):
            search = self.query(PR_SEARCH, q=q, cursor=cursor)["search"]
            yield from (n for n in search["nodes"] if n)
            page = search["pageInfo"]
            if not page["hasNextPage"]:
                return
            cursor = page["endCursor"]


def search_query(repo_slug: str, window: Window, cutoff: datetime) -> str:
    """Bound the crawl by date server-side, on the side of the holdout we are on."""
    day = cutoff.date().isoformat()
    bound = f"created:<{day}" if window is Window.PRE_T else f"created:>={day}"
    return f"repo:{repo_slug} is:pr {bound} sort:created-desc"


def project(repo_slug: str, nodes: Iterable[dict[str, Any]]) -> Iterator[EvidenceRecord]:
    """Turn pull requests into timestamped, individually-addressable evidence."""
    for pr in nodes:
        number = pr["number"]
        base = f"pr:{repo_slug}#{number}"
        url = f"https://github.com/{repo_slug}/pull/{number}"
        shared = {"author": _login(pr["author"]), "author_is_bot": _is_bot(pr["author"])}

        yield EvidenceRecord(
            evidence_id=f"{base}:opened",
            source="github",
            url=url,
            timestamp=_ts(pr["createdAt"]),
            payload={
                **shared,
                "title": pr["title"],
                "additions": pr["additions"],
                "deletions": pr["deletions"],
                "changed_files": pr["changedFiles"],
                "files": [f["path"] for f in pr["files"]["nodes"]],
            },
        )

        if merged_at := _ts(pr["mergedAt"]):
            yield EvidenceRecord(
                evidence_id=f"{base}:merged",
                source="github",
                url=url,
                timestamp=merged_at,
                payload={**shared, "merged": True},
            )
        elif (closed_at := _ts(pr["closedAt"])) and not pr["merged"]:
            yield EvidenceRecord(
                evidence_id=f"{base}:closed",
                source="github",
                url=url,
                timestamp=closed_at,
                payload={**shared, "merged": False},
            )

        for i, review in enumerate(pr["reviews"]["nodes"]):
            yield EvidenceRecord(
                evidence_id=f"{base}:review:{i}",
                source="github",
                url=url,
                timestamp=_ts(review["createdAt"]),
                payload={
                    "author": _login(review["author"]),
                    "author_is_bot": _is_bot(review["author"]),
                    "state": review["state"],
                    "body": review["body"],
                },
            )

        for i, comment in enumerate(pr["comments"]["nodes"]):
            yield EvidenceRecord(
                evidence_id=f"{base}:comment:{i}",
                source="github",
                url=url,
                timestamp=_ts(comment["createdAt"]),
                payload={
                    "author": _login(comment["author"]),
                    "author_is_bot": _is_bot(comment["author"]),
                    "body": comment["body"],
                },
            )


def project_repo_meta(repo_slug: str, repo: dict[str, Any]) -> EvidenceRecord:
    """Repository-level facts.

    Mutable counters (stars) are as-of-fetch, not as-of-T: GitHub does not expose
    a historical star count, so they cannot be reconstructed at the cutoff. The
    payload says so. Holt's own reasoning must not lean on them; the popularity
    diagnostic does, and that limitation is published rather than hidden.
    """
    return EvidenceRecord(
        evidence_id=f"repo:{repo_slug}:meta",
        source="github",
        url=f"https://github.com/{repo_slug}",
        timestamp=_ts(repo["createdAt"]),
        payload={
            "pushed_at": repo["pushedAt"],
            "is_archived": repo["isArchived"],
            "is_mirror": repo["isMirror"],
            "is_fork": repo["isFork"],
            "description": repo["description"],
            "homepage_url": repo["homepageUrl"],
            "primary_language": (repo["primaryLanguage"] or {}).get("name"),
            "stargazer_count": repo["stargazerCount"],
            "_counters_are_as_of_fetch_not_cutoff": True,
        },
    )


class LiveGitHubProvider(EvidenceProvider):
    """Crawls GitHub, then hands every record to the base-class window check."""

    def __init__(
        self,
        window: Window,
        cutoff: datetime = T_CUTOFF,
        transport: GitHubGraphQL | None = None,
        max_pages: int = 8,
    ) -> None:
        super().__init__(window, cutoff)
        self.transport = transport or GitHubGraphQL()
        self.max_pages = max_pages
        self._seen: dict[str, EvidenceRecord] = {}

    def _fetch_raw(self, request: str, /, **params: object) -> Iterable[EvidenceRecord]:
        owner, _, name = request.partition("/")
        records: list[EvidenceRecord] = [
            project_repo_meta(request, self.transport.repo_meta(owner, name))
        ]
        nodes = self.transport.search_pull_requests(
            search_query(request, self.window, self.cutoff), self.max_pages
        )
        records.extend(project(request, nodes))

        # Slice at the source; the base-class assertion is the safety net, not
        # the filter. A PR created before T can still carry a merge after it.
        kept = [r for r in records if self._in_window(r)]
        self._seen.update({r.evidence_id: r for r in kept})
        return kept

    def _in_window(self, record: EvidenceRecord) -> bool:
        if self.window is Window.PRE_T:
            return record.timestamp <= self.cutoff
        return record.timestamp > self.cutoff

    def _resolve_raw(self, evidence_id: str) -> EvidenceRecord | None:
        return self._seen.get(evidence_id)
