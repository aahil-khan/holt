"""Static mockup of the proposed Holt TUI. Not the TUI — a picture of it.

Run it to see the screens rendered at real width with the real palette:

    uv run python mockups/tui_mockup.py            # every frame
    uv run python mockups/tui_mockup.py 3          # one frame

Content is pulled from a real `--replay` run, so what you are looking at is
actual assessment text, actual evidence ids and actual Stage D drops rather than
invented sample strings. Nothing here imports Textual and nothing here is
imported by the engine. Delete this directory once the real TUI lands.
"""

from __future__ import annotations

import sys
import textwrap
from dataclasses import dataclass

sys.path.insert(0, "src")

from pathlib import Path

from holt import model
from holt.agent import entry, pipeline
from holt.agent.entry import MEASURED
from holt.evidence.fixtures import FixtureProvider
from holt.report import EntryPoint
from holt.types import Window

# ─── palette ────────────────────────────────────────────────────────────────
#
# Colour carries meaning or it is not used. Three jobs only:
#   1. verdict state          2. evidence resolution        3. Stage D drops
# Everything else is the terminal's own foreground, or one of two greys.

W = 84  # content width — long enough for prose, short enough to stay readable


def _c(n: int) -> str:
    return f"\033[38;5;{n}m"


RESET = "\033[0m"
BOLD = "\033[1m"
UL = "\033[4m"
STRIKE = "\033[9m"

TEXT = ""  # inherit the terminal's foreground; never hardcode white
DIM = _c(245)  # labels, chrome, secondary prose
FAINT = _c(240)  # counts, timings, things you read only if you look
RULE = _c(238)  # hairlines
RAIL = _c(243)  # the disclaimer rail — quiet, but meant to be seen

VIABLE = _c(72)  # muted green
NOT_VIABLE = _c(173)  # clay — a finding about the world, not an error
INSUFFICIENT = _c(245)  # deliberately colourless: no evidence earns no colour
DROP = _c(131)  # muted red, reserved for Stage D
CITE = _c(73)  # desaturated teal, reserved for evidence ids

VERDICT_COLOUR = {
    "viable": VIABLE,
    "not_viable": NOT_VIABLE,
    "insufficient_evidence": INSUFFICIENT,
}
# Unknown verdicts render in the neutral tone rather than raising. The engine
# owns the enum; the TUI must not encode a fixed list of its members.
VERDICT_FALLBACK = DIM


# ─── primitives ─────────────────────────────────────────────────────────────


def line(s: str = "") -> None:
    print("  " + s)


def rule(indent: int = 0) -> None:
    line(RULE + " " * indent + "─" * (W - indent) + RESET)


def wrap(s: str, indent: int = 0, colour: str = TEXT, width: int | None = None) -> None:
    body = textwrap.wrap(s, (width or W) - indent) or [""]
    for row in body:
        line(colour + " " * indent + row + RESET)


def gutter(mark: str, label: str, right: str = "", colour: str = TEXT) -> None:
    """The two-column stage line: a mark in the gutter, a label, a status."""
    left = f"{FAINT}{mark:<2}{RESET} {DIM}{label:<16}{RESET}{colour}{right}{RESET}"
    pad = W - 2 - 1 - 16 - _len(right)
    line(left + " " * max(pad, 0))


def _len(s: str) -> int:
    """Printable length, ignoring escape sequences."""
    out, i = 0, 0
    while i < len(s):
        if s[i] == "\033":
            i = s.index("m", i) + 1
            continue
        out += 1
        i += 1
    return out


def chrome(left: str, right: str) -> None:
    """The one persistent line of app chrome. Name, subject, mode."""
    gap = W - _len(left) - _len(right)
    line(DIM + left + RESET + " " * max(gap, 1) + FAINT + right + RESET)


def evidence_id(eid: str, resolves: bool = True, width: int = 46) -> str:
    """An evidence id, styled by whether it resolves. This is the project's
    whole thesis in one glyph run, so it gets the only underline in the app."""
    short = eid if len(eid) <= width else eid[: width - 1] + "…"
    if resolves:
        return f"{CITE}{UL}{short}{RESET}"
    return f"{DROP}{STRIKE}{short}{RESET}"


def clip(s: str, n: int) -> str:
    """Truncate on a word boundary. Mid-word cuts read as a bug, not a summary."""
    s = " ".join(s.split())
    if len(s) <= n:
        return s
    cut = s[: n - 1]
    if " " in cut:
        cut = cut[: cut.rindex(" ")]
    return cut + "…"


def frame(title: str) -> None:
    print()
    print(f"{FAINT}  ┄┄ {title} {'┄' * max(0, W - len(title) - 5)}{RESET}")
    print()


# ─── real data ──────────────────────────────────────────────────────────────


@dataclass
class Run:
    assessment: object
    trace: object
    records: list


def load(repo: str) -> Run:
    provider = FixtureProvider(Window.PRE_T)
    records = provider.fetch(repo)
    assessment, trace = pipeline.analyze(
        repo, provider, model.build(repo, replay=True)
    )
    # Same path the CLI uses, so the ranking shown is the ranking that was scored.
    try:
        issues = FixtureProvider(Window.PRE_T, root=Path("fixtures/issues")).fetch(repo)
        path = model.TRAJECTORY_DIR / "pathfinder" / (repo.replace("/", "__") + ".jsonl")
        ranked = entry.rank(repo, list(issues), list(records), model.ReplayModel(path))
        assessment.entry_points = [
            EntryPoint(r["evidence_id"], r["first_step"], r.get("why", "")) for r in ranked
        ]
    except FileNotFoundError:
        pass
    return Run(assessment, trace, records)


HEALTHY = "home-assistant/core"
DROPPED = "Sistema-de-certificacion-academica/Sistema-de-certificacion-academica"


def short(repo: str, n: int = 34) -> str:
    return repo if len(repo) <= n else repo[: n - 1] + "…"


# ─── frame 1 — live, mid-run ────────────────────────────────────────────────


def frame_live_midrun(run: Run) -> None:
    frame("1 · live investigation, mid-run")
    chrome("holt · analyze", f"{short(HEALTHY)}   replay")
    rule()
    line()

    gutter("A", "classify", "real_software", TEXT)
    gutter("B", "opportunity", "substantive", TEXT)
    gutter("C", "outcomes", "reading 13 threads", DIM)
    line()

    # Findings stream in beneath the stage that produced them, indented once.
    # No progress bar: the count of threads read is the progress.
    for eid, outcome in [
        ("pr:home-assistant/core#172481:opened", "changes_requested"),
        ("pr:home-assistant/core#172384:opened", "ignored"),
        ("pr:home-assistant/core#172460:opened", "ignored"),
        ("pr:home-assistant/core#172500:opened", "merged_after_review"),
    ]:
        line(f"     {evidence_id(eid)}  {DIM}{outcome}{RESET}")
    line(f"     {FAINT}▍{RESET}")
    line()

    gutter("D", "verify", "—", FAINT)
    gutter(" ", "verdict", "—", FAINT)
    gutter("E", "narrate", "—", FAINT)
    line()
    rule()
    sig = run.trace.signals.as_dict()
    chrome(
        f"{len(run.records)} evidence records · {sig['total_threads']} threads"
        "  ·  window ≤ 2026-06-01",
        "gpt-5-mini   ^C cancel",
    )


# ─── frame 2 — the Stage D drop ─────────────────────────────────────────────


def frame_stage_d(run: Run) -> None:
    frame("2 · the Stage D moment — a claim removed for want of evidence")
    chrome("holt · analyze", f"{short(DROPPED)}   replay")
    rule()
    line()

    gutter("A", "classify", "real_software", TEXT)
    gutter("B", "opportunity", "absent", TEXT)
    gutter("C", "outcomes", "13 outcomes", TEXT)
    line()

    t = run.trace
    gutter(
        "D",
        "verify",
        f"{t.before_verification} findings → {t.after_verification} kept, "
        f"{len(t.dropped)} dropped",
        TEXT,
    )
    line(f"   {FAINT}{'':<16}no model runs here; resolution is a lookup{RESET}")
    line()

    # The drop gets the space. It is the only red on the screen.
    for d in t.dropped:
        line(f"     {DROP}✗{RESET} {TEXT}{d.field} = {d.value!r}{RESET}")
        cited = list(d.evidence_ids)
        if cited:
            for eid in cited:
                line(
                    f"       {DIM}cited{RESET}  {evidence_id(eid, resolves=False)}"
                    f"   {DROP}does not resolve{RESET}"
                )
        else:
            line(f"       {DIM}cited{RESET}  {DROP}nothing{RESET}")
        wrap(
            "Dropped, not softened. The model asserted this and could not point at "
            "a record that carries it, so the claim does not reach the reader.",
            indent=7,
            colour=FAINT,
        )
        line()

    line(f"     {DIM}kept{RESET}   {TEXT}{t.after_verification}{RESET}")
    line()
    rule()
    chrome("d  detail    ↑↓ move    enter open record", "1 dropped")


# ─── frame 3 — the assessment ───────────────────────────────────────────────


def frame_assessment(run: Run) -> None:
    frame("3 · assessment view")
    a = run.assessment
    v = a.verdict.value
    colour = VERDICT_COLOUR.get(v, VERDICT_FALLBACK)

    chrome("holt", f"{short(a.repo)}   replay")
    rule()
    line()

    # The verdict is the largest thing on the screen, and the only thing that
    # gets both bold and colour. It is spelled out, not abbreviated.
    line(f"{colour}{BOLD}{v.replace('_', ' ')}{RESET}")
    line()
    for r in run.trace.rules:
        wrap(r, indent=0, colour=DIM, width=W)
    line()

    para = a.summary.split("\n")[0]
    wrap(para[:520] + ("…" if len(para) > 520 else ""), colour=TEXT)
    line()
    rule()

    n = len(a.claims)
    chrome(f"EVIDENCE   {n} claims, every one carrying an id that resolved", "↑↓  enter")
    line()
    for i, claim in enumerate(a.claims[:7]):
        mark = f"{TEXT}▸{RESET}" if i == 0 else " "
        text = clip(claim.text.split(" (")[0], 44)
        line(f"{mark} {TEXT}{text:<45}{RESET} {evidence_id(claim.evidence_id, width=34)}")
    if n > 7:
        line(f"  {FAINT}… {n - 7} more{RESET}")
    line()
    rule()
    chrome(f"method  {a.method[:52]}", "replayed" if a.replayed else "live")


# ─── frame 4 — evidence inspector ───────────────────────────────────────────


def frame_inspector(run: Run) -> None:
    frame("4 · evidence inspector — enter on a claim resolves its id")
    a = run.assessment
    claim = a.claims[0]
    rec = next(r for r in run.records if r.evidence_id == claim.evidence_id)

    chrome("holt", f"{short(a.repo)}   replay")
    rule()
    line()
    line(f"{TEXT}▸ {clip(claim.text.split(' (')[0], 44):<45}{RESET} "
         f"{evidence_id(claim.evidence_id, width=34)}")
    line()
    rule(indent=2)
    line()
    line(f"  {evidence_id(rec.evidence_id, width=W - 4)}")
    line(f"  {FAINT}{rec.source} · {rec.timestamp.isoformat()}{RESET}")
    line(f"  {FAINT}{rec.url[:W - 4]}{RESET}")
    line()
    for k, val in list(rec.payload.items())[:6]:
        if isinstance(val, list):
            shown = val[:3]
            line(f"  {DIM}{k:<15}{RESET}{TEXT}{shown[0][:56]}{RESET}")
            for extra in shown[1:]:
                line(f"  {'':<15}{TEXT}{extra[:56]}{RESET}")
            if len(val) > 3:
                line(f"  {'':<15}{FAINT}+{len(val) - 3} more{RESET}")
        else:
            line(f"  {DIM}{k:<15}{RESET}{TEXT}{str(val)[:56]}{RESET}")
    line()
    rule()
    chrome("esc  back    o  open on github", "record 1 of 1 cited")


# ─── frame 5 — where to start, and its own negative result ──────────────────


def frame_entry_points(run: Run) -> None:
    frame("5 · where to start — the disclaimer the tool prints about itself")
    chrome("holt", f"{short(HEALTHY)}   replay")
    rule()
    line()
    chrome("WHERE TO START", "5 issues ranked")
    line()

    # Not an error, not a warning, not collapsed behind a key. It is given more
    # room than the ranking it qualifies, and the comparison is a table because
    # the point is that the numbers sit on top of each other.
    bar = f"{RAIL}│{RESET}  "
    line(bar)
    wrap_rule(
        "This ranking is not measurably better than picking at random.", bold=True
    )
    wrap_rule(
        "Measured over %d repositories and %s issues held out before the cutoff:"
        % (MEASURED["repositories"], f"{MEASURED['issues_ranked']:,}")
    )
    line(bar)
    p = MEASURED["precision_at_3"]
    for name, key in [
        ("this ranking", "holt"),
        ("good first issue", "good_first_issue"),
        ("recency", "recency"),
        ("random", "random"),
    ]:
        emph = TEXT if key == "holt" else DIM
        line(f"{bar}    {emph}{name:<20}{p[key]:.3f}{RESET}")
    line(bar)
    lo, hi = MEASURED["paired_ci_vs_label"]
    wrap_rule(
        f"Differences well inside noise — paired 95% CI [{lo:+.2f}, {hi:+.2f}], "
        f"sign test p = {MEASURED['sign_test_p']}."
    )
    line(bar)
    wrap_rule(
        f"Printed anyway because {MEASURED['repos_with_no_labelled_issue']} of those "
        f"{MEASURED['repositories']} repositories had no beginner-labelled issue at "
        "all, so on half of them there is no free signal to lose to. Read it as a "
        "reading order, not a recommendation."
    )
    line(bar)
    line(f"{bar}{DIM}Check it yourself:{RESET}  "
         f"{TEXT}uv run python eval/pathfinder_harness.py --replay{RESET}")
    line(bar)
    line()

    # Numbered because the order *is* the content here — it is a reading order,
    # and nothing else in the app is a sequence, so nothing else gets numbers.
    for i, pt in enumerate(run.assessment.entry_points[:4], 1):
        line(f"  {FAINT}{i}{RESET}  {TEXT}{clip(pt.first_step, W - 6)}{RESET}")
        line(f"     {evidence_id(pt.evidence_id, width=44)}")
        if pt.why:
            wrap(clip(pt.why, 150), indent=5, colour=FAINT)
        line()
    rule()
    chrome("↑↓ move    enter open issue", "ranking · not a recommendation")


# ─── frame 6 — the palette, stated plainly ──────────────────────────────────


def frame_palette(run: Run) -> None:
    frame("6 · every colour the app uses, and what each one means")
    chrome("holt · palette", "colour carries meaning or is not used")
    rule()
    line()
    line(f"{DIM}verdict{RESET}")
    for v, note in [
        ("viable", "worth an outsider's week"),
        ("not_viable", "a finding about the repo, not an error — clay, not red"),
        ("insufficient_evidence", "no evidence earns no colour"),
    ]:
        c = VERDICT_COLOUR.get(v, VERDICT_FALLBACK)
        line(f"  {c}{BOLD}{v.replace('_', ' '):<24}{RESET}{FAINT}{note}{RESET}")
    line(f"  {VERDICT_FALLBACK}{BOLD}{'a verdict added later':<24}{RESET}"
         f"{FAINT}unknown values render neutral; no hardcoded member list{RESET}")
    line()
    line(f"{DIM}evidence{RESET}")
    for eid, ok, note in [
        ("pr:home-assistant/core#172481:opened", True, "resolves — underlined, and openable"),
        ("no_contributing_file", False, "does not resolve — Stage D removed the claim"),
    ]:
        cell = evidence_id(eid, resolves=ok, width=40)
        line(f"  {cell}{' ' * (41 - _len(cell))}{FAINT}{note}{RESET}")
    line()
    line(f"{DIM}everything else{RESET}")
    line(f"  {TEXT}terminal foreground{RESET}{' ' * 5}{FAINT}claims, prose, values{RESET}")
    line(f"  {DIM}dim 245{RESET}{' ' * 17}{FAINT}labels, chrome, secondary prose{RESET}")
    line(f"  {FAINT}faint 240{RESET}{' ' * 15}{FAINT}counts, timings, read-only-if-you-look{RESET}")
    line(f"  {RULE}rule 238{RESET}{' ' * 16}{FAINT}hairlines{RESET}")
    line()
    rule()
    chrome("no progress bars · no boxes · one underline · three colours", "")


def wrap_rule(s: str, bold: bool = False) -> None:
    pre = BOLD if bold else ""
    for row in textwrap.wrap(s, W - 6):
        line(f"{RAIL}│{RESET}  {pre}{TEXT}{row}{RESET}")


# ─── driver ─────────────────────────────────────────────────────────────────


def main() -> int:
    healthy = load(HEALTHY)
    dropped = load(DROPPED)

    frames = [
        (frame_live_midrun, healthy),
        (frame_stage_d, dropped),
        (frame_assessment, dropped),
        (frame_inspector, dropped),
        (frame_entry_points, healthy),
        (frame_palette, healthy),
    ]
    want = sys.argv[1:] and int(sys.argv[1])
    for i, (fn, data) in enumerate(frames, 1):
        if want and want != i:
            continue
        fn(data)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
