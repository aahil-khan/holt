"""Choosing a model, and the ways that goes wrong.

**Nothing here touches the network.** `HOLT_NO_NETWORK` is set for the whole
module, and one of the tests asserts that the guard actually holds — listing a
provider is a request to somebody's server, and testing a connection is a real
inference call that, against a local endpoint, loads a model into RAM on the
machine running the suite. A test run must never do either.

No Textual either. This is the layer the screen sits on, and its edge cases —
a missing key, an endpoint that is not up, an unpriced model, a configuration
that breaks replay — are all reachable without a terminal.
"""

from __future__ import annotations

import pytest

from holt import model as model_module
from holt.tui import models


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setenv(models.NO_NETWORK_ENV, "1")


@pytest.fixture(autouse=True)
def private_config(tmp_path, monkeypatch):
    """Never read or write the developer's real `models.toml`."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    model_module.enable_user_models_config(model_module.ModelsConfig())


def provider(name: str) -> models.Provider:
    return next(p for p in models.providers() if p.name == name)


# ─── the guard itself ───────────────────────────────────────────────────────


def test_the_network_guard_actually_blocks_both_calls():
    """The one test that matters most in this file."""
    assert not models.network_allowed()

    listing = models.list_models(provider("ollama"))
    assert models.NO_NETWORK_ENV in listing.error

    probe = models.test_connection(provider("ollama"), "anything")
    assert probe.ok is False
    assert models.NO_NETWORK_ENV in probe.detail


def test_the_guard_is_off_by_default(monkeypatch):
    """It exists to be set deliberately, not to disable the feature."""
    monkeypatch.delenv(models.NO_NETWORK_ENV, raising=False)
    assert models.network_allowed()


# ─── providers ──────────────────────────────────────────────────────────────


def test_every_provider_the_engine_knows_is_offered():
    offered = {p.name for p in models.providers()}
    assert offered == set(model_module.PROVIDER_PRESETS)


def test_a_provider_says_whether_its_key_is_set_before_you_pick_it(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    anthropic = provider("anthropic")
    assert not anthropic.usable
    assert "is not set" in anthropic.status()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    anthropic = provider("anthropic")
    assert anthropic.usable
    assert "is set" in anthropic.status()


def test_ollama_is_usable_without_a_key_but_claims_nothing_about_being_up():
    """Local and keyless. Whether it is running is a question only a connection
    test can answer, so the row must not imply either way."""
    ollama = provider("ollama")
    assert ollama.usable
    assert "11434" in ollama.status()
    assert "set" not in ollama.status()


def test_an_openai_compatible_endpoint_needs_a_url_first():
    compatible = provider("openai-compatible")
    assert compatible.needs_base_url
    assert not compatible.usable
    assert models.list_models(compatible).error


# ─── listing ────────────────────────────────────────────────────────────────


def test_a_fallback_list_is_labelled_as_not_coming_from_the_provider():
    """A guessed list presented as the provider's answer would be a lie about
    what the tool knows."""
    listing = models.list_models(provider("anthropic"))

    assert listing.error, "the reason for falling back must be stated"
    assert listing.guessed
    assert listing.models
    assert all(not m.from_provider for m in listing.models)


def test_an_unpriced_model_says_unknown_rather_than_free():
    priced = models.Model(id=model_module.SMALL, priced=True)
    unpriced = models.Model(id="some-local-model", priced=False)

    assert priced.pricing == "priced"
    assert "cost recorded as 0" in unpriced.pricing
    assert "free" not in unpriced.pricing.lower()


def test_pricing_is_read_from_the_engine_not_restated():
    listing = models.list_models(provider("openai"))
    for entry in listing.models:
        assert entry.priced == (entry.id in model_module.PRICES)


# ─── only models you can actually talk to ───────────────────────────────────


@pytest.mark.parametrize(
    "model_id",
    [
        "nomic-embed-text:latest",
        "mxbai-embed-large",
        "text-embedding-3-small",
        "bge-reranker-v2-m3",
        "whisper-1",
        "dall-e-3",
        "tts-1-hd",
        "omni-moderation-latest",
    ],
)
def test_a_model_that_cannot_hold_a_conversation_is_not_offered(model_id):
    """Every stage calls chat completions. These are not choices."""
    assert not models.looks_like_chat(model_id)


@pytest.mark.parametrize(
    "model_id",
    [
        "qwen3:8b",
        "llama3.2:latest",
        "gpt-5-mini-2025-08-07",
        "claude-opus-5",
        "deepseek-r1:14b",
        "gemma3:12b",
    ],
)
def test_a_chat_model_is_left_alone(model_id):
    """The filter's failure mode that matters is hiding a model that works."""
    assert models.looks_like_chat(model_id)


def test_ollama_is_asked_what_each_model_can_do_rather_than_guessed_at(monkeypatch):
    """Names are the fallback. Ollama publishes capabilities, so it is asked.

    `pixtral` here is the point: nothing in its name says what it is, and the
    only reason it is kept is that Ollama said `completion`.
    """
    monkeypatch.setattr(
        models,
        "_ollama_capabilities",
        lambda provider, ids: {
            "pixtral:latest": ("completion", "vision"),
            "snowflake-arctic:latest": ("embedding",),
            "nomic-embed-text:latest": ("embedding",),
        },
    )
    kept = models._chat_only(
        provider("ollama"),
        ["pixtral:latest", "snowflake-arctic:latest", "nomic-embed-text:latest"],
    )
    assert kept == ["pixtral:latest"]


def test_a_model_ollama_will_not_describe_falls_back_to_its_name(monkeypatch):
    """Silence is not evidence that a model is unusable."""
    monkeypatch.setattr(
        models,
        "_ollama_capabilities",
        lambda provider, ids: {"qwen3:8b": None, "nomic-embed-text": None},
    )
    assert models._chat_only(provider("ollama"), ["qwen3:8b", "nomic-embed-text"]) == [
        "qwen3:8b"
    ]


def test_an_old_ollama_that_reports_no_capabilities_hides_nothing(monkeypatch):
    """Empty capabilities means "would not say", not "can do nothing".

    Reading it the other way would hide every model on an Ollama predating the
    field, which is a total failure that no other test in this file would see.
    """
    import httpx

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"model_info": {}}  # no `capabilities` key at all

    class Client:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, url, json):
            return Response()

    monkeypatch.setattr(httpx, "Client", Client)
    found = models._ollama_capabilities(provider("ollama"), ["qwen3:8b"])
    assert found == {"qwen3:8b": None}
    assert models._chat_only(provider("ollama"), ["qwen3:8b"]) == ["qwen3:8b"]


def test_the_native_api_is_addressed_without_the_openai_suffix():
    assert models._ollama_native("http://localhost:11434/v1") == "http://localhost:11434"
    assert models._ollama_native("http://box:11434/") == "http://box:11434"
    assert models._ollama_native("") == "http://localhost:11434"


def test_what_was_filtered_out_is_counted_not_silently_dropped(monkeypatch):
    """A list shorter than `ollama list` has to say why it is shorter."""
    monkeypatch.delenv(models.NO_NETWORK_ENV)
    monkeypatch.setattr(
        models,
        "_list_openai_wire",
        lambda p, key: ["qwen3:8b", "nomic-embed-text:latest", "mxbai-embed-large"],
    )
    monkeypatch.setattr(models, "_ollama_capabilities", lambda p, ids: {})

    listing = models.list_models(provider("ollama"))
    assert [m.id for m in listing.models] == ["qwen3:8b"]
    assert listing.hidden == 2


def test_a_provider_with_nothing_but_embedding_models_says_so(monkeypatch):
    """An empty list under a working connection otherwise reads as a bug."""
    monkeypatch.delenv(models.NO_NETWORK_ENV)
    monkeypatch.setattr(
        models, "_list_openai_wire", lambda p, key: ["nomic-embed-text:latest"]
    )
    monkeypatch.setattr(models, "_ollama_capabilities", lambda p, ids: {})

    listing = models.list_models(provider("ollama"))
    assert not listing.models
    assert "none of them can hold a conversation" in listing.error
    assert "ollama pull" in listing.error


# ─── errors a person can act on ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "raised,expected",
    [
        (ConnectionError("connection refused"), "ollama serve"),
        (TimeoutError("request timed out"), "did not answer"),
        (RuntimeError("Error code: 401 - unauthorized"), "rejected"),
        (RuntimeError("Error code: 404 - model not_found"), "does not exist"),
    ],
)
def test_failures_are_explained_in_terms_of_what_to_do(raised, expected):
    assert expected in models.explain(raised, provider("ollama"))


def test_an_unrecognised_failure_is_reported_as_itself():
    """A confident wrong guess about a cause is worse than the raw text."""
    detail = models.explain(ValueError("something nobody predicted"), provider("openai"))
    assert "ValueError" in detail
    assert "something nobody predicted" in detail


# ─── applying a choice ──────────────────────────────────────────────────────


def test_choosing_writes_the_same_file_the_command_line_writes():
    chosen = models.apply(provider("anthropic"), "claude-opus-5")

    assert chosen.provider == "anthropic"
    assert chosen.model == "claude-opus-5"
    assert model_module.models_config_path().is_file()
    # And it takes effect for this process, as the CLI's opt-in does.
    assert model_module.model_for("classify") == "claude-opus-5"

    reloaded = model_module.load_models_config()
    assert reloaded.provider == "anthropic"
    assert reloaded.model == "claude-opus-5"


def test_a_non_default_choice_warns_that_replay_will_fail():
    """The reproducibility guarantee doing its job is not a surprise anybody
    should get later, during a demo."""
    assert models.replay_warning(model_module.ModelsConfig()) == ""

    models.apply(provider("anthropic"), "claude-opus-5")
    warning = models.replay_warning(model_module.active_config())
    assert "fails loudly" in warning
    assert "pinned models" in warning
    # And it says what still works, not only what broke.
    assert "Recordings you make now" in warning


def test_reset_restores_the_pinned_defaults():
    models.apply(provider("anthropic"), "claude-opus-5")
    assert not model_module.active_config().is_default()

    back = models.reset()

    assert back.is_default()
    assert not model_module.models_config_path().exists()
    assert model_module.model_for("classify") == model_module.SMALL
    assert models.replay_warning(back) == ""
