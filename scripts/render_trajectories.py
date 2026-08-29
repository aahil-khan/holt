"""Render recorded runs into trajectories a person can follow.

The raw JSONL is the record; this is the reading copy. It interleaves what the
agent asked its tools, what came back, what each stage concluded, what
verification removed, and how the rules turned that into a verdict -- in the
order it happened.

Runs entirely from committed fixtures and trajectories. No key, no spend.

Run:  PYTHONPATH=. uv run python scripts/render_trajectories.py
"""

from __future__ import annotations

import json
from pathlib import Path

from holt.agent.pipeline import analyze
from holt.evidence.fixtures import FixtureProvider
from holt.model import PRICES, ReplayModel, TRAJECTORY_DIR
from holt.types import Window

OUT = Path("trajectories")
FEATURED = ["is-a-dev/register", "NixOS/nixpkgs", "SecureBananaLabs/bug-bounty"]


def load_calls(slug: str) -> list[dict]:
    path = TRAJECTORY_DIR / (slug.replace("/", "__") + ".jsonl")
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def render(slug: str) -> str:
    provider = FixtureProvider(Window.PRE_T)
    model = ReplayModel(TRAJECTORY_DIR / (slug.replace("/", "__") + ".jsonl"))
    assessment, trace = analyze(slug, provider, model)
    calls = {c["label"]: c for c in load_calls(slug)}

    fetches = [c for c in provider.call_log if c[0] == "fetch"]
    resolves = [c for c in provider.call_log if c[0] == "resolve"]
    hit = sum(1 for c in resolves if c[2])

    out = [
        f"# Trajectory — {slug}",
        "",
        f"**Verdict:** `{assessment.verdict.value}`  ",
        f"**Rule that decided it:** {trace.rules[0] if trace.rules else '(none)'}",
        "",
        "Replayed from committed fixtures and recorded model output. No model ran.",
        "",
        "## 1. Evidence retrieved (tool call)",
        "",
        f"`provider.fetch(\"{slug}\")` → **{fetches[0][2] if fetches else 0} records**, "
        f"every one asserted to be dated at or before the cutoff 2026-06-01.",
        "",
        "## 2. Signals computed — arithmetic, no model",
        "",
        "```",
        json.dumps(trace.signals.as_dict(), indent=1),
        "```",
        "",
    ]

    stage_titles = {
        "classify": "3. Stage A — what kind of repository is this?",
        "opportunity": "4. Stage B — is there a real route in?",
        "outcomes": "5. Stage C — what happened to people who tried?",
    }
    for label, title in stage_titles.items():
        call = calls.get(label)
        if not call:
            continue
        u = call.get("usage", {})
        ri, ro = PRICES.get(call["model"], (0, 0))
        cost = u.get("input_tokens", 0) / 1e6 * ri + u.get("output_tokens", 0) / 1e6 * ro
        out += [
            f"## {title}",
            "",
            f"*Model:* `{call['model']}` · *{u.get('input_tokens',0)} in / "
            f"{u.get('output_tokens',0)} out tokens · ${cost:.4f}*",
            "",
            "<details><summary>Instructions given to the model</summary>",
            "",
            "```",
            call["system"].strip(),
            "```",
            "</details>",
            "",
            "<details><summary>Evidence it was shown (first 1500 chars)</summary>",
            "",
            "```",
            call["prompt"][:1500].strip(),
            "```",
            "</details>",
            "",
            "**What it answered:**",
            "",
            "```json",
            json.dumps(call["response"], indent=1)[:1800],
            "```",
            "",
        ]

    unresolved = [c[1] for c in resolves if not c[2]]
    out += [
        "## 6. Stage D — verification (tool calls, no model)",
        "",
        f"Every evidence id cited by every finding was looked up against the provider: "
        f"**{len(resolves)} lookups, {hit} resolved, {len(resolves) - hit} did not.**",
        "",
        "Verification works at two levels. An id that does not resolve is stripped "
        "from the finding that cited it. A finding left with *no* resolving id at "
        "all is dropped entirely — not softened, not hedged, removed.",
        "",
        f"Findings before verification: **{trace.before_verification}**  ",
        f"Findings after verification: **{trace.after_verification}**  ",
        f"Findings dropped outright: **{len(trace.dropped)}**  ",
        f"Individual citations stripped: **{len(unresolved)}**",
        "",
    ]
    if unresolved:
        out += ["Ids that did not resolve, and were removed from the claims citing them:", ""]
        out += [f"- `{u}`" for u in unresolved[:10]]
        if len(unresolved) > 10:
            out += [f"- …and {len(unresolved) - 10} more"]
        out += [""]
    if trace.dropped:
        out += ["Findings dropped outright, with the ids they cited:", ""]
        out += [f"- `{d.field}` citing `{list(d.evidence_ids)}`" for d in trace.dropped]
        out += [""]
    else:
        out += [
            "No finding lost every one of its citations on this run, so none was "
            "dropped outright.",
            "",
        ]

    out += [
        "",
        "## 7. Verdict — a plain function, no model",
        "",
        "`verdict.py` turned the surviving findings and the signals into a verdict.",
        "The model was not consulted and could not have overridden it.",
        "",
        "```",
        *[f"{r}" for r in trace.rules],
        f"=> {assessment.verdict.value}",
        "```",
        "",
        "## 8. Stage E — narration",
        "",
        "The verdict above was passed to Stage E as an input it cannot change.",
        "",
        "---",
        "",
        assessment.render(),
    ]
    return "\n".join(out)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    written = []
    for slug in FEATURED:
        try:
            (OUT / (slug.replace("/", "__") + ".md")).write_text(render(slug) + "\n")
            written.append(slug)
            print(f"  rendered {slug}")
        except Exception as exc:
            print(f"  SKIPPED {slug}: {type(exc).__name__}: {exc}")

    (OUT / "README.md").write_text(
        "# Agent trajectories\n\n"
        "Each file walks one complete run from the instructions the agent was given "
        "to the verdict it produced, in the order it happened: the evidence it "
        "retrieved, what each stage was asked and answered, which findings "
        "verification removed, and how the rules turned what survived into a "
        "verdict.\n\n"
        "All of it replays from committed fixtures and recorded model output, so "
        "nothing here needs a key.\n\n"
        "| Trajectory | Verdict | Why it is worth reading |\n|---|---|---|\n"
        "| [`is-a-dev/register`](is-a-dev__register.md) | `not_viable` | A registry with "
        "hundreds of merged outsider pull requests. The baseline solution calls it viable. |\n"
        "| [`NixOS/nixpkgs`](NixOS__nixpkgs.md) | `viable` | A genuine opportunity that the "
        "naive label ranked 17th of 22. |\n"
        "| [`SecureBananaLabs/bug-bounty`](SecureBananaLabs__bug-bounty.md) | `not_viable` | "
        "A thousand inbound attempts, nothing merged. |\n\n"
        "Raw records for every repository, one JSON object per model call with the "
        "full request, response and token usage, are in "
        "[`../fixtures/trajectories/`](../fixtures/trajectories/).\n\n"
        "Regenerate with `PYTHONPATH=. uv run python scripts/render_trajectories.py`.\n"
    )
    print(f"\nwrote {len(written)} trajectories + index to {OUT}/")


if __name__ == "__main__":
    main()
