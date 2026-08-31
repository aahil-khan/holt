"""Choosing which model answers, and finding out whether it can.

`holt models` on the command line takes a provider and a model id and trusts you
to know both. An interface can do better: ask the provider what it actually has,
and try a real call before you find out mid-run that the endpoint is down.

Everything here is Textual-free and synchronous, so it can be tested without a
terminal and run on a worker thread by the screen that uses it. Nothing in this
file decides *what a model costs* or *what the defaults are* — `holt.model` owns
both, and this asks it.

Two facts this module exists to keep in front of the user:

* **A non-default configuration breaks replay of the committed recordings.**
  Those were recorded under the pinned ids, and the engine fails loudly rather
  than serving another model's answers. That is correct behaviour and it is not
  a surprise anybody should get later.
* **An unpriced model records cost as zero.** Not "free" — unknown. The
  interface says so wherever a price would otherwise appear.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from holt import model as model_module

#: How long any network call here may take. Short: this is an interactive
#: screen, and a provider that cannot answer in this long is a provider you
#: want to be told about rather than wait for.
TIMEOUT_S = 12.0

#: Hard stop on every outbound call in this module.
#:
#: Listing a provider is cheap, but testing a connection is a real inference
#: request, and against a local endpoint that means loading a model into RAM on
#: the user's machine. That must only ever happen because someone pressed the
#: key for it — never from a test, a script, or a screen doing it eagerly. The
#: tests set this, so the suite physically cannot reach a provider.
NO_NETWORK_ENV = "HOLT_NO_NETWORK"


def network_allowed() -> bool:
    return os.environ.get(NO_NETWORK_ENV, "") in ("", "0", "false", "False")


_BLOCKED = "Network calls are disabled here (HOLT_NO_NETWORK)."

#: Shown when a provider cannot be listed. Curated rather than invented: these
#: are ids the SDKs document, used only as a starting point the user can edit,
#: and always labelled as not having come from the provider.
FALLBACK_MODELS: dict[str, tuple[str, ...]] = {
    "anthropic": ("claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5-20251001"),
    "openai": (model_module.SMALL, model_module.LARGE),
}


@dataclass(slots=True)
class Provider:
    name: str
    key_env: str
    base_url: str

    @property
    def key_set(self) -> bool:
        return bool(os.environ.get(self.key_env))

    @property
    def needs_base_url(self) -> bool:
        """`openai-compatible` is only meaningful once you say where."""
        return self.name == "openai-compatible" and not self.base_url

    def status(self) -> str:
        """One line about whether this provider could be used right now."""
        if self.needs_base_url:
            return "set a base url first"
        if self.name == "ollama":
            # Local, and usually keyless. Whether it is running is a question
            # only a connection test can answer, so do not imply either way.
            return self.base_url
        if self.key_set:
            return f"{self.key_env} is set"
        return f"{self.key_env} is not set"

    @property
    def usable(self) -> bool:
        if self.needs_base_url:
            return False
        return self.key_set or self.name == "ollama"


def providers(config: model_module.ModelsConfig | None = None) -> list[Provider]:
    """Every provider the engine knows, with the current config filled in."""
    config = config or model_module.load_models_config()
    out = []
    for name, preset in model_module.PROVIDER_PRESETS.items():
        # The configured values win, but only for the provider they belong to.
        key_env = preset.get("api_key_env", "OPENAI_API_KEY")
        base_url = preset.get("base_url", "")
        if config.provider == name:
            key_env = config.resolved_key_env()
            base_url = config.resolved_base_url()
        out.append(Provider(name=name, key_env=key_env, base_url=base_url))
    return out


@dataclass(slots=True)
class Model:
    id: str
    priced: bool = False
    #: True when the provider told us about it, False when it came from
    #: `FALLBACK_MODELS`. The screen labels the difference.
    from_provider: bool = True

    @property
    def pricing(self) -> str:
        return "priced" if self.priced else "unpriced — cost recorded as 0"


@dataclass(slots=True)
class Listing:
    models: list[Model] = field(default_factory=list)
    error: str = ""
    #: Set when the list is `FALLBACK_MODELS` rather than the provider's answer.
    guessed: bool = False

    @property
    def ok(self) -> bool:
        return not self.error


def list_models(provider: Provider) -> Listing:
    """Ask the provider what it has. Never raises; the error is the result.

    Runs on a worker thread. A provider that is unreachable, unauthorised or
    simply not running produces a sentence, not a traceback.
    """
    if not network_allowed():
        return _fallback(provider, _BLOCKED)
    if provider.needs_base_url:
        return Listing(error="Set a base url for this provider first.")

    key = os.environ.get(provider.key_env, "")
    if not key and provider.name != "ollama":
        return _fallback(provider, f"{provider.key_env} is not set.")

    try:
        if provider.name == "anthropic":
            ids = _list_anthropic(key)
        else:
            ids = _list_openai_wire(provider, key)
    except Exception as exc:  # noqa: BLE001 - reported to the user as prose
        return _fallback(provider, explain(exc, provider))

    if not ids:
        return _fallback(provider, "The provider returned no models.")

    return Listing(models=[_model(i) for i in ids])


def _model(model_id: str) -> Model:
    return Model(id=model_id, priced=model_id in model_module.PRICES)


def _fallback(provider: Provider, error: str) -> Listing:
    """What we know without asking, clearly labelled as exactly that."""
    known = FALLBACK_MODELS.get(provider.name, ())
    return Listing(
        models=[Model(id=i, priced=i in model_module.PRICES, from_provider=False)
                for i in known],
        error=error,
        guessed=bool(known),
    )


def _list_openai_wire(provider: Provider, key: str) -> list[str]:
    from openai import OpenAI

    client = OpenAI(
        api_key=key or "not-needed",
        base_url=provider.base_url or None,
        timeout=TIMEOUT_S,
        max_retries=0,
    )
    return sorted({m.id for m in client.models.list()})


def _list_anthropic(key: str) -> list[str]:
    from anthropic import Anthropic

    client = Anthropic(api_key=key, timeout=TIMEOUT_S, max_retries=0)
    return sorted({m.id for m in client.models.list(limit=100)})


@dataclass(slots=True)
class Probe:
    ok: bool
    detail: str
    seconds: float = 0.0


def test_connection(provider: Provider, model_id: str) -> Probe:
    """Make the smallest real call this provider allows, and time it.

    Listing models proves the endpoint is reachable and the key is accepted.
    This proves the *chosen model* answers, which is a different question and
    the one that bites during a run.
    """
    if not network_allowed():
        return Probe(False, _BLOCKED)
    key = os.environ.get(provider.key_env, "")
    if provider.needs_base_url:
        return Probe(False, "Set a base url for this provider first.")
    if not key and provider.name != "ollama":
        return Probe(False, f"{provider.key_env} is not set.")
    if not model_id:
        return Probe(False, "Choose a model first.")

    started = time.monotonic()
    try:
        if provider.name == "anthropic":
            from anthropic import Anthropic

            Anthropic(api_key=key, timeout=TIMEOUT_S, max_retries=0).messages.create(
                model=model_id,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
        else:
            from openai import OpenAI

            OpenAI(
                api_key=key or "not-needed",
                base_url=provider.base_url or None,
                timeout=TIMEOUT_S,
                max_retries=0,
            ).chat.completions.create(
                model=model_id,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
    except Exception as exc:  # noqa: BLE001 - the point is to report it
        return Probe(False, explain(exc, provider), time.monotonic() - started)

    elapsed = time.monotonic() - started
    return Probe(True, f"{model_id} answered in {elapsed:.1f}s", elapsed)


def explain(exc: BaseException, provider: Provider) -> str:
    """An error a person can act on.

    The failures that actually happen when pointing a tool at a model endpoint
    get a sentence saying what to do. Anything else is reported as itself: a
    confident wrong guess is worse than the raw text.
    """
    text = str(exc)
    lowered = text.lower()
    name = type(exc).__name__

    if "connection" in lowered or "connect" in lowered or "refused" in lowered:
        if provider.name == "ollama":
            return (
                f"Nothing is listening on {provider.base_url}. "
                "Start Ollama with `ollama serve`."
            )
        return f"Could not reach {provider.base_url or provider.name}."
    if "timeout" in lowered or "timed out" in lowered:
        return f"{provider.name} did not answer within {TIMEOUT_S:.0f}s."
    if "401" in text or "unauthorized" in lowered or "authentication" in lowered:
        return f"{provider.key_env} was rejected by {provider.name}."
    if "403" in text or "permission" in lowered:
        return f"{provider.key_env} is not permitted to do this."
    if "404" in text or "not_found" in lowered or "does not exist" in lowered:
        return "That model does not exist for this provider or key."
    if "429" in text or "rate" in lowered and "limit" in lowered:
        return f"{provider.name} is rate limiting. Wait a moment."
    return f"{name}: {text[:160]}"


# ─── applying a choice ──────────────────────────────────────────────────────


def apply(provider: Provider, model_id: str) -> model_module.ModelsConfig:
    """Save the choice and opt this process into it.

    Writes the same `models.toml` the command line writes, so choosing here and
    choosing with `holt models` are the same act.
    """
    config = model_module.load_models_config()
    config.provider = provider.name
    config.model = model_id
    config.base_url = provider.base_url if provider.base_url else ""
    config.api_key_env = provider.key_env
    model_module.save_models_config(config)
    model_module.enable_user_models_config(config)
    return config


def reset() -> model_module.ModelsConfig:
    """Back to the pinned defaults the benchmark was measured on."""
    path = model_module.models_config_path()
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass
    default = model_module.ModelsConfig()
    model_module.enable_user_models_config(default)
    return default


def replay_warning(config: model_module.ModelsConfig) -> str:
    """What a non-default configuration costs you. Empty when on the defaults.

    Not phrased as an error, because it is not one — it is the reproducibility
    guarantee doing its job. But it is never hidden either: finding out that
    `--replay` no longer works, during a demo, would be the worse outcome.
    """
    if config.is_default():
        return ""
    return (
        "Not the defaults. The committed recordings were made with the pinned "
        "models, so replaying them under this configuration fails loudly rather "
        "than serving another model's answers. Recordings you make now replay "
        "under this configuration."
    )
