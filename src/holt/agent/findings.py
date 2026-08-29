"""Typed findings: what the stages produce, before anything becomes a verdict."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Finding:
    """One field, its value, and the evidence that supports it.

    A finding with no resolvable evidence is dropped by Stage D rather than
    softened, so `evidence_ids` is what keeps a claim alive.
    """

    field: str
    value: Any
    evidence_ids: tuple[str, ...] = ()
    note: str = ""


@dataclass(slots=True)
class Findings:
    items: list[Finding] = field(default_factory=list)

    def add(self, field_name: str, value: Any, evidence_ids=(), note: str = "") -> None:
        self.items.append(Finding(field_name, value, tuple(evidence_ids), note))

    def get(self, field_name: str, default: Any = None) -> Any:
        for item in self.items:
            if item.field == field_name:
                return item.value
        return default

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)
