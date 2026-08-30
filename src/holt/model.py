"""Every model call goes through here.

One seam, four jobs. It records trajectories, which are a required deliverable
and a qualification-gate item. It makes replay possible, so a judge reproduces
the headline result with no key and no spend. It pins a model per *stage* rather
than globally. And it is the only file that touches an LLM at all, which is why
swapping provider took one rewrite instead of a refactor.

Model choice is per stage and evidence-led. Counting and verification run no
model; classification, opportunity and prose run the small one; thread
interpretation is the stage that may need the larger one, and whether it does is
measured rather than assumed.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

# Dated ids, not floating aliases: `gpt-5-mini` can be repointed underneath a
# recorded run, and a reproduction claim that drifts is not a claim.
SMALL = "gpt-5-mini-2025-08-07"
LARGE = "gpt-5-2025-08-07"

# USD per million tokens, (input, output).
PRICES = {
    SMALL: (0.25, 2.00),
    LARGE: (1.25, 10.00),
}

# The per-stage assignment under test. Everything starts on the small model; a
# stage is promoted only if the pilot shows it needs to be.
STAGE_MODELS: dict[str, str] = {
    "baseline": SMALL,
    "baseline_matched": SMALL,
    "classify": SMALL,
    "opportunity": SMALL,
    "outcomes": SMALL,
    "narrate": SMALL,
    "pathfinder": SMALL,
    "profile": SMALL,
    "describe": SMALL,
}

TRAJECTORY_DIR = Path("fixtures/trajectories")


def model_for(label: str) -> str:
    return STAGE_MODELS.get(label, SMALL)


def call_key(label: str, system: str, prompt: str) -> str:
    """Stable identity for a call, so a replay matches its recording.

    Covers the prompt text and the model. An edited prompt or a swapped model
    fails loudly instead of quietly serving an answer to a question nobody asked.
    """
    blob = json.dumps(
        [label, model_for(label), system, prompt], sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


@dataclass(slots=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

    def add(self, model: str, inp: int, out: int) -> None:
        rate_in, rate_out = PRICES.get(model, (0.0, 0.0))
        self.input_tokens += inp
        self.output_tokens += out
        self.cost_usd += inp / 1e6 * rate_in + out / 1e6 * rate_out


class ModelClient(Protocol):
    replayed: bool
    usage: Usage

    def complete(self, *, label: str, system: str, prompt: str, schema: dict) -> dict: ...


@dataclass
class OpenAIModel:
    """Live calls, recorded as they go."""

    trajectory_path: Path
    replayed: bool = False
    usage: Usage = field(default_factory=Usage)
    _client: Any = None

    def __post_init__(self) -> None:
        from openai import OpenAI

        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Use --replay to reproduce recorded "
                "results with no key and no spend."
            )
        self._client = OpenAI()
        self.trajectory_path.parent.mkdir(parents=True, exist_ok=True)

    def complete(self, *, label: str, system: str, prompt: str, schema: dict) -> dict:
        model = model_for(label)
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": label, "schema": schema, "strict": True},
            },
        )
        parsed = json.loads(response.choices[0].message.content)
        u = response.usage
        self.usage.add(model, u.prompt_tokens, u.completion_tokens)

        with self.trajectory_path.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "key": call_key(label, system, prompt),
                        "label": label,
                        "model": model,
                        "system": system,
                        "prompt": prompt,
                        "response": parsed,
                        "usage": {
                            "input_tokens": u.prompt_tokens,
                            "output_tokens": u.completion_tokens,
                        },
                    }
                )
                + "\n"
            )
        return parsed


@dataclass
class ReplayModel:
    """Serves recorded responses. No network, no key, no spend.

    A miss raises rather than falling back to a live call: replay that silently
    bills a judge who asked for the free path is not reproduction.
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
                f"No recorded response for {label} (key {key}). The prompt or the "
                "stage's model has changed since the recording, so replaying it "
                "would answer a question that is no longer being asked."
            )
        u = entry.get("usage", {})
        self.usage.add(entry["model"], u.get("input_tokens", 0), u.get("output_tokens", 0))
        return entry["response"]


def build(repo_slug: str, replay: bool) -> ModelClient:
    path = TRAJECTORY_DIR / (repo_slug.replace("/", "__") + ".jsonl")
    return ReplayModel(path) if replay else OpenAIModel(path)
