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

# USD per million tokens, (input, output). A model not listed here is charged
# at zero and `holt models` says so, rather than inventing a price.
PRICES = {
    SMALL: (0.25, 2.00),
    LARGE: (1.25, 10.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-fable-5": (10.00, 50.00),
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

# Long enough for a large reasoning response, short enough that a dead connection
# surfaces as an error in the same session rather than as an unexplained silence.
REQUEST_TIMEOUT_S = 300.0
MAX_RETRIES = 4


# --- provider configuration -------------------------------------------------
#
# The default is the pinned OpenAI models above, and the *library* never reads
# the user's model configuration on its own: every benchmark number, committed
# trajectory and replay was produced under the defaults, and an eval script
# silently inheriting somebody's Ollama config would be the exact reproducibility
# failure this file exists to prevent. Only the CLI (and any front end that
# makes the same deliberate call) opts in, via `enable_user_models_config()`.

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    # provider -> filled-in defaults; anything the user sets explicitly wins.
    "openai": {"api_key_env": "OPENAI_API_KEY"},
    "anthropic": {"api_key_env": "ANTHROPIC_API_KEY", "model": "claude-opus-5"},
    "ollama": {"base_url": "http://localhost:11434/v1", "api_key_env": "OLLAMA_API_KEY"},
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
    },
    "openai-compatible": {"api_key_env": "OPENAI_API_KEY"},
}

# Providers that speak the OpenAI wire protocol; everything except anthropic.
_OPENAI_WIRE = {"openai", "ollama", "gemini", "openai-compatible"}


@dataclass(slots=True)
class ModelsConfig:
    provider: str = "openai"
    model: str = ""  # applied to every stage when set; stage overrides win
    base_url: str = ""
    api_key_env: str = ""
    stages: dict[str, str] = field(default_factory=dict)

    def resolved_key_env(self) -> str:
        return self.api_key_env or PROVIDER_PRESETS.get(self.provider, {}).get(
            "api_key_env", "OPENAI_API_KEY"
        )

    def resolved_base_url(self) -> str:
        return self.base_url or PROVIDER_PRESETS.get(self.provider, {}).get("base_url", "")

    def is_default(self) -> bool:
        return self == ModelsConfig()


def models_config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "holt" / "models.toml"


def load_models_config(path: Path | None = None) -> ModelsConfig:
    import tomllib

    path = path or models_config_path()
    if not path.exists():
        return ModelsConfig()
    data = tomllib.loads(path.read_text())
    return ModelsConfig(
        provider=data.get("provider", "openai"),
        model=data.get("model", ""),
        base_url=data.get("base_url", ""),
        api_key_env=data.get("api_key_env", ""),
        stages={k: str(v) for k, v in (data.get("stages") or {}).items()},
    )


def save_models_config(config: ModelsConfig, path: Path | None = None) -> Path:
    path = path or models_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f'provider = "{config.provider}"',
        f'model = "{config.model}"',
        f'base_url = "{config.base_url}"',
        f'api_key_env = "{config.api_key_env}"',
    ]
    if config.stages:
        lines.append("")
        lines.append("[stages]")
        lines += [f'{k} = "{v}"' for k, v in sorted(config.stages.items())]
    path.write_text("\n".join(lines) + "\n")
    return path


_user_config: ModelsConfig | None = None


def enable_user_models_config(config: ModelsConfig | None = None) -> ModelsConfig:
    """Opt this process into the user's model configuration.

    Called by the CLI entry point (and deliberately by any front end that wants
    the same behavior). Library and eval code never call it, so recorded runs
    and replays always resolve against the pinned defaults.
    """
    global _user_config
    _user_config = config if config is not None else load_models_config()
    return _user_config


def active_config() -> ModelsConfig:
    return _user_config if _user_config is not None else ModelsConfig()


def model_for(label: str) -> str:
    config = active_config()
    if label in config.stages:
        return config.stages[label]
    if config.model:
        return config.model
    preset_model = PROVIDER_PRESETS.get(config.provider, {}).get("model")
    if preset_model and not config.is_default():
        return preset_model
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

        config = active_config()
        key_env = config.resolved_key_env()
        base_url = config.resolved_base_url()
        api_key = os.environ.get(key_env)
        if not api_key:
            if base_url:
                # Local OpenAI-compatible servers (Ollama, vLLM, LM Studio)
                # accept any key; a missing variable must not block them.
                api_key = "unused"
            else:
                raise RuntimeError(
                    f"{key_env} is not set. Use --replay to reproduce recorded "
                    "results with no key and no spend."
                )
        # A request with no timeout can hang for hours on a half-open socket, and
        # a recording run that stalls silently is worse than one that fails: the
        # log simply stops and nothing says why. Bounded and retried instead.
        self._client = OpenAI(
            timeout=REQUEST_TIMEOUT_S,
            max_retries=MAX_RETRIES,
            api_key=api_key,
            base_url=base_url or None,
        )
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
class AnthropicModel:
    """Live calls against Claude, recorded exactly like the OpenAI ones.

    Structured output goes through `output_config.format` with the same JSON
    schema every stage already declares, so the `complete()` contract -- a dict
    matching the schema -- holds regardless of provider. Safety classifiers can
    decline a request with `stop_reason: "refusal"`; that surfaces as a loud
    error rather than an empty finding.
    """

    trajectory_path: Path
    replayed: bool = False
    usage: Usage = field(default_factory=Usage)
    _client: Any = None

    MAX_TOKENS = 16000  # thinking counts toward this on current Claude models

    def __post_init__(self) -> None:
        if self._client is None:
            import anthropic

            key_env = active_config().resolved_key_env()
            if not os.environ.get(key_env):
                raise RuntimeError(
                    f"{key_env} is not set. Use --replay to reproduce recorded "
                    "results with no key and no spend."
                )
            self._client = anthropic.Anthropic(
                timeout=REQUEST_TIMEOUT_S, max_retries=MAX_RETRIES
            )
        self.trajectory_path.parent.mkdir(parents=True, exist_ok=True)

    def complete(self, *, label: str, system: str, prompt: str, schema: dict) -> dict:
        model = model_for(label)
        response = self._client.messages.create(
            model=model,
            max_tokens=self.MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        if response.stop_reason == "refusal":
            raise RuntimeError(
                f"{model} declined the {label} request (stop_reason=refusal); "
                "nothing was recorded for it"
            )
        text = next(b.text for b in response.content if b.type == "text")
        parsed = json.loads(text)
        u = response.usage
        self.usage.add(model, u.input_tokens, u.output_tokens)

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
                            "input_tokens": u.input_tokens,
                            "output_tokens": u.output_tokens,
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


def live_client(path: Path) -> ModelClient:
    """The provider dispatch. One place, so nothing else needs to know."""
    if active_config().provider == "anthropic":
        return AnthropicModel(path)
    return OpenAIModel(path)


def build(repo_slug: str, replay: bool) -> ModelClient:
    path = TRAJECTORY_DIR / (repo_slug.replace("/", "__") + ".jsonl")
    return ReplayModel(path) if replay else live_client(path)
