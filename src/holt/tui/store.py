"""Assessments that outlive the process.

Two jobs, one file on disk per assessment:

* **History.** The interface opens on what you have already looked at, because
  the first question is almost never "assess something new" — it is "what did it
  say about the thing I ran this morning".
* **Cache.** Assessing a repository costs a minute and real money. Asking for
  one that was assessed four minutes ago should hand back that answer rather
  than spend again, and should say plainly that is what it did.

Design rules that matter here:

* **Never lie about freshness.** A reused assessment is labelled with its age
  everywhere it appears, and re-running is always one key away. A cache that
  hides its age is indistinguishable from a stale answer.
* **A corrupt file is skipped, never fatal.** History is a convenience; losing
  it must not stop you assessing something. Every read is defensive.
* **Writes are atomic.** Temp file then `os.replace`, so a process killed
  mid-write leaves the previous entry intact rather than a truncated one.
* **The engine's types are converted here, not taught to serialise themselves.**
  `holt.report` is frozen; this module knows how to write an `Assessment` down
  and read one back, and that knowledge lives on this side of the boundary.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from holt.report import Assessment, Claim, EntryPoint, Verdict

#: Bumped when the on-disk shape changes in a way older readers cannot handle.
#: Entries with a different version are ignored rather than guessed at.
SCHEMA_VERSION = 1

#: Where history lives. Outside `fixtures/`, outside the reproduction path, and
#: in `.gitignore` — this is a convenience for one machine, not project content.
DEFAULT_ROOT = Path(".holt/assessments")

#: How long an assessment is considered fresh enough to reuse without asking.
#: Ten minutes: long enough to cover re-opening the tool while still working on
#: the same repository, short enough that nobody mistakes it for live data.
DEFAULT_MAX_AGE_SECONDS = 10 * 60


@dataclass(slots=True)
class Entry:
    """One stored assessment, plus how it was produced."""

    repo: str
    mode: str  # replay | recorded | live
    created_at: float
    assessment: Assessment
    contributor_days: int = 7
    duration_seconds: float = 0.0
    cost_usd: float = 0.0
    path: Path | None = None

    @property
    def age_seconds(self) -> float:
        # Clamped: a clock change or a file copied from another machine must not
        # produce a negative age that renders as "in 3 minutes".
        return max(0.0, time.time() - self.created_at)

    def fresh(self, max_age: float = DEFAULT_MAX_AGE_SECONDS) -> bool:
        return self.age_seconds <= max_age

    @property
    def key(self) -> tuple[str, str, int]:
        """What makes two assessments the same question.

        The day budget is part of it because `verdict.py` reads it: the same
        repository can be worth a fortnight and not worth an afternoon, and
        serving one answer for the other would be wrong.
        """
        return (self.repo, self.mode, self.contributor_days)


def describe_age(seconds: float) -> str:
    """Human, and never more precise than it is."""
    seconds = max(0.0, seconds)
    if seconds < 45:
        return "just now"
    minutes = seconds / 60
    if minutes < 60:
        n = round(minutes)
        return f"{n} min ago" if n != 1 else "1 min ago"
    hours = minutes / 60
    if hours < 24:
        n = round(hours)
        return f"{n} hours ago" if n != 1 else "1 hour ago"
    days = hours / 24
    n = round(days)
    return f"{n} days ago" if n != 1 else "1 day ago"


# ─── serialisation ──────────────────────────────────────────────────────────


def to_dict(entry: Entry) -> dict[str, Any]:
    a = entry.assessment
    return {
        "schema_version": SCHEMA_VERSION,
        "repo": entry.repo,
        "mode": entry.mode,
        "created_at": entry.created_at,
        "contributor_days": entry.contributor_days,
        "duration_seconds": entry.duration_seconds,
        "cost_usd": entry.cost_usd,
        "assessment": {
            "repo": a.repo,
            "verdict": a.verdict.value,
            "summary": a.summary,
            "bottom_line": getattr(a, "bottom_line", ""),
            "limits": getattr(a, "limits", ""),
            "rules": list(getattr(a, "rules", []) or []),
            "landing": list(getattr(a, "landing", []) or []),
            "contributor_days": getattr(a, "contributor_days", 7),
            "models": list(getattr(a, "models", []) or []),
            "method": a.method,
            "replayed": a.replayed,
            "claims": [
                {"text": c.text, "evidence_id": c.evidence_id} for c in a.claims
            ],
            "entry_points": [
                {
                    "evidence_id": p.evidence_id,
                    "first_step": p.first_step,
                    "why": p.why,
                }
                for p in (getattr(a, "entry_points", []) or [])
            ],
        },
    }


def from_dict(raw: dict[str, Any], path: Path | None = None) -> Entry | None:
    """Rebuild an entry, or `None` if the file is not one we understand.

    Returns rather than raises: a single unreadable file must not take the
    history list down with it.
    """
    try:
        if raw.get("schema_version") != SCHEMA_VERSION:
            return None
        body = raw["assessment"]
        try:
            verdict = Verdict(body["verdict"])
        except ValueError:
            # A verdict this build has never heard of. Keeping the entry out of
            # history is safer than inventing a member for it.
            return None

        assessment = Assessment(
            repo=body["repo"],
            verdict=verdict,
            summary=body.get("summary", ""),
            claims=[
                Claim(text=c.get("text", ""), evidence_id=c.get("evidence_id"))
                for c in body.get("claims", [])
            ],
            method=body.get("method", "holt"),
            replayed=bool(body.get("replayed", False)),
        )
        # Fields the engine has added over time. Set only when this build's
        # `Assessment` actually carries them, so an older or newer engine does
        # not turn a cached file into an AttributeError.
        for name, value in (
            ("bottom_line", body.get("bottom_line", "")),
            ("limits", body.get("limits", "")),
            ("rules", list(body.get("rules", []) or [])),
            ("landing", list(body.get("landing", []) or [])),
            ("contributor_days", body.get("contributor_days", 7)),
            ("models", list(body.get("models", []) or [])),
        ):
            if hasattr(assessment, name):
                setattr(assessment, name, value)
        if hasattr(assessment, "entry_points"):
            assessment.entry_points = [
                EntryPoint(
                    evidence_id=p.get("evidence_id", ""),
                    first_step=p.get("first_step", ""),
                    why=p.get("why", ""),
                )
                for p in body.get("entry_points", [])
            ]

        return Entry(
            repo=raw["repo"],
            mode=raw.get("mode", "replay"),
            created_at=float(raw.get("created_at", 0.0)),
            assessment=assessment,
            contributor_days=int(raw.get("contributor_days", 7)),
            duration_seconds=float(raw.get("duration_seconds", 0.0)),
            cost_usd=float(raw.get("cost_usd", 0.0)),
            path=path,
        )
    except (KeyError, TypeError, ValueError):
        return None


# ─── the store ──────────────────────────────────────────────────────────────


@dataclass
class Store:
    root: Path = DEFAULT_ROOT
    #: Set when the directory cannot be written. The interface stays usable and
    #: says so once, rather than failing every time an assessment finishes.
    read_only: bool = False
    _memory: list[Entry] = field(default_factory=list)

    def save(self, entry: Entry) -> Entry:
        """Write an assessment down. Always succeeds from the caller's view."""
        self._memory = [e for e in self._memory if e.key != entry.key]
        self._memory.insert(0, entry)
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            path = self.root / _filename(entry)
            _atomic_write(path, to_dict(entry))
            entry.path = path
            self.read_only = False
        except OSError:
            # Kept in memory for this session; history simply will not survive
            # the process. Not worth interrupting anyone over.
            self.read_only = True
        return entry

    def all(self) -> list[Entry]:
        """Every stored assessment, newest first. Unreadable files are skipped."""
        found: dict[tuple[str, str, int], Entry] = {}
        for entry in self._memory:
            found.setdefault(entry.key, entry)

        try:
            paths = sorted(self.root.glob("*.json"))
        except OSError:
            paths = []
        for path in paths:
            try:
                raw = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            entry = from_dict(raw, path)
            if entry is None:
                continue
            existing = found.get(entry.key)
            if existing is None or entry.created_at > existing.created_at:
                found[entry.key] = entry

        return sorted(found.values(), key=lambda e: e.created_at, reverse=True)

    def latest(self, repo: str, mode: str, contributor_days: int = 7) -> Entry | None:
        """The most recent assessment of exactly this question, if any."""
        key = (repo, mode, contributor_days)
        for entry in self.all():
            if entry.key == key:
                return entry
        return None

    def fresh(
        self,
        repo: str,
        mode: str,
        contributor_days: int = 7,
        max_age: float = DEFAULT_MAX_AGE_SECONDS,
    ) -> Entry | None:
        """A reusable answer, or `None`. The caller must still show its age."""
        entry = self.latest(repo, mode, contributor_days)
        return entry if entry is not None and entry.fresh(max_age) else None

    def forget(self, entry: Entry) -> None:
        self._memory = [e for e in self._memory if e.key != entry.key]
        if entry.path is not None:
            try:
                entry.path.unlink()
            except OSError:
                pass


def _filename(entry: Entry) -> str:
    slug = entry.repo.replace("/", "__")
    return f"{slug}__{entry.mode}__{entry.contributor_days}d.json"


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    """Temp file then rename, so a kill mid-write cannot truncate history."""
    handle = tempfile.NamedTemporaryFile(
        "w", dir=path.parent, prefix=".tmp-", suffix=".json", delete=False
    )
    try:
        with handle:
            json.dump(payload, handle, indent=1)
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
