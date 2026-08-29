"""Every model call goes through here.

One seam, three jobs. It is where trajectories are recorded, which is a required
deliverable and a qualification-gate item. It is what makes replay possible, so
a judge can reproduce the headline result with no API key and no spend. And it
is the single place a provider swap would touch, which is why the codebase pins
one model rather than shipping adapters nobody scored.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

MODEL = "claude-opus-5"
TRAJECTORY_DIR = Path("fixtures/trajectories")


def call_key(label: str, system: str, prompt: str) -> str:
    """Stable identity for a call, so a replay can be matched to a recording.

    Includes the prompt text: if a prompt is edited, the recording no longer
    matches and replay fails loudly instead of quietly serving a stale answer
    for a question that is no longer being asked.
    """
    blob = json.dumps([label, system, prompt], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


@dataclass(slots=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def cost_usd(self) -> float:
        # claude-opus-5: $5 per Mtok in, $25 per Mtok out.
        return self.input_tokens / 1e6 * 5 + self.output_tokens / 1e6 * 25


class ModelClient(Protocol):
    replayed: bool

    def complete(self, *, label: str, system: str, prompt: str, schema: dict) -> dict: ...


@dataclass
class AnthropicModel:
    """Live calls, recorded as they go."""

    trajectory_path: Path
    replayed: bool = False
    usage: Usage = field(default_factory=Usage)
    _client: Any = None

    def __post_init__(self) -> None:
        import anthropic

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Use --replay to reproduce recorded "
                "results with no key and no spend."
            )
        self._client = anthropic.Anthropic()
        self.trajectory_path.parent.mkdir(parents=True, exist_ok=True)

    def complete(self, *, label: str, system: str, prompt: str, schema: dict) -> dict:
        response = self._client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        text = next(b.text for b in response.content if b.type == "text")
        parsed = json.loads(text)
        self.usage.input_tokens += response.usage.input_tokens
        self.usage.output_tokens += response.usage.output_tokens

        with self.trajectory_path.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "key": call_key(label, system, prompt),
                        "label": label,
                        "model": MODEL,
                        "system": system,
                        "prompt": prompt,
                        "response": parsed,
                        "usage": {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens,
                        },
                    }
                )
                + "\n"
            )
        return parsed


@dataclass
class ReplayModel:
    """Serves recorded responses. No network, no key, no spend.

    A miss is an error rather than a silent live call: replay that quietly falls
    back to the API is not reproduction, and would bill a judge who asked for the
    free path.
    """

    trajectory_path: Path
    replayed: bool = True
    usage: Usage = field(default_factory=Usage)
    _recorded: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.trajectory_path.exists():
            raise FileNotFoundError(
                f"No trajectory at {self.trajectory_path}. Replay needs a recorded run."
            )
        for line in self.trajectory_path.read_text().splitlines():
            if line.strip():
                entry = json.loads(line)
                self._recorded[entry["key"]] = entry

    def complete(self, *, label: str, system: str, prompt: str, schema: dict) -> dict:
        key = call_key(label, system, prompt)
        entry = self._recorded.get(key)
        if entry is None:
            raise KeyError(
                f"No recorded response for {label} (key {key}). The prompt has "
                "changed since the recording, so replaying it would answer a "
                "question that is no longer being asked. Re-record with a key."
            )
        usage = entry.get("usage", {})
        self.usage.input_tokens += usage.get("input_tokens", 0)
        self.usage.output_tokens += usage.get("output_tokens", 0)
        return entry["response"]


def build(repo_slug: str, replay: bool) -> ModelClient:
    path = TRAJECTORY_DIR / (repo_slug.replace("/", "__") + ".jsonl")
    return ReplayModel(path) if replay else AnthropicModel(path)
