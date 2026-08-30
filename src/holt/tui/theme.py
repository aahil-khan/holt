"""Every colour in the interface, and what each one is for.

Colour is used to mean something or it is not used. Three jobs:

1. **verdict state** — viable, not viable, insufficient evidence
2. **evidence resolution** — an id that resolves against the provider, or one
   that does not
3. **Stage D drops** — the one place red appears

Everything else is the terminal's own foreground and two greys. There is no
background colour anywhere in the stylesheet: the app sits on whatever ground
the user's terminal already has, which is both the restrained choice and the
reason it reads correctly on a light and a dark profile without a theme switch.

`not_viable` is clay rather than red on purpose. It is a finding about a
repository, not a failure of the tool, and colouring it like an error would
misreport it. `insufficient_evidence` is grey on purpose too: an absence of
evidence has not earned a colour.
"""

from __future__ import annotations

# ─── tokens ─────────────────────────────────────────────────────────────────

DIM = "#8a8a8a"  # labels, chrome, secondary prose
FAINT = "#585858"  # counts, timings, read only if you look for them
RULE = "#444444"  # hairlines
RAIL = "#767676"  # the measured-result rail: quiet, but meant to be seen

VIABLE = "#5faf87"
NOT_VIABLE = "#d7875f"
INSUFFICIENT = "#8a8a8a"
DROP = "#af5f5f"
CITE = "#5fafaf"

#: Verdicts are looked up, never matched exhaustively. `holt.report.Verdict`
#: owns the enum; a member added there renders in the neutral tone instead of
#: raising, so the TUI never has to be edited in lockstep with the engine.
VERDICT_COLOURS: dict[str, str] = {
    "viable": VIABLE,
    "not_viable": NOT_VIABLE,
    "insufficient_evidence": INSUFFICIENT,
}
VERDICT_FALLBACK = DIM


def verdict_colour(value: str) -> str:
    return VERDICT_COLOURS.get(value, VERDICT_FALLBACK)


def verdict_label(value: str) -> str:
    """`not_viable` reads as "not viable". Spelled out, never abbreviated."""
    return value.replace("_", " ")


CSS = f"""
Screen {{
    background: transparent;
    color: $foreground;
}}

/* chrome ------------------------------------------------------------------ */

#chrome {{
    height: 1;
    color: {DIM};
    padding: 0 1;
}}
#chrome-left {{
    width: 1fr;
}}
#chrome-right {{
    width: auto;
    color: {FAINT};
    text-align: right;
}}
.rule {{
    height: 1;
    color: {RULE};
}}
Footer {{
    background: transparent;
    color: {FAINT};
}}
Footer > .footer--key {{
    background: transparent;
    color: {DIM};
}}
Footer > .footer--description {{
    background: transparent;
    color: {FAINT};
}}

/* stages ------------------------------------------------------------------ */

StageRow {{
    height: 1;
    padding: 0 1;
}}
.stage-mark {{ color: {FAINT}; width: 3; }}
.stage-name {{ color: {DIM}; width: 16; }}
.stage-pending {{ color: {FAINT}; }}
.stage-running {{ color: {DIM}; }}

/* findings as they stream -------------------------------------------------- */

.finding {{
    padding: 0 1 0 6;
    height: auto;
}}
.finding-note {{ color: {FAINT}; }}

/* the drop ---------------------------------------------------------------- */

DroppedFinding {{
    height: auto;
    padding: 1 1 1 6;
}}
.drop-mark {{ color: {DROP}; }}
.drop-reason {{ color: {FAINT}; padding-left: 2; }}
.drop-id {{ color: {DROP}; text-style: strike; }}

/* evidence ---------------------------------------------------------------- */

.cite {{ color: {CITE}; text-style: underline; }}
.cite-broken {{ color: {DROP}; text-style: strike; }}

EvidenceDetail {{
    height: auto;
    padding: 0 1;
}}
.record-meta {{ color: {FAINT}; }}
.record-key {{ color: {DIM}; width: 17; }}

/* claims ------------------------------------------------------------------ */

ClaimList {{
    /* `auto`, not `1fr`. Inside the scrolling page, a fractional height
       resolves against whatever space a long summary has left over, which on a
       verbose repository collapses the whole list to a single row. The page
       scrolls; the list should be as tall as it has claims. */
    height: auto;
    background: transparent;
    border: none;
    scrollbar-size: 1 1;
}}
ClaimList > ListItem {{
    background: transparent;
    padding: 0 1;
}}
ClaimList > ListItem.--highlight {{
    background: $boost;
}}
ClaimList:focus > ListItem.--highlight {{
    background: $boost;
}}

/* verdict ----------------------------------------------------------------- */

#verdict {{
    height: auto;
    padding: 1 1 0 1;
    text-style: bold;
}}
#verdict-budget {{
    height: auto;
    padding: 0 1 1 1;
}}
#bottom-line {{
    height: auto;
    padding: 0 1 1 1;
}}
.prose {{
    height: auto;
    padding: 0 1 1 1;
}}
.rule-line {{
    height: auto;
    padding: 0 1 0 2;
}}
.landing-line {{
    height: auto;
    padding: 0 1 0 2;
}}
#report {{
    height: 1fr;
    scrollbar-size: 1 1;
}}

/* home --------------------------------------------------------------------- */

#home-body {{
    height: 1fr;
    padding: 0 1;
}}
#repo-input {{
    /* The one focusable box on the screen, so it is marked by its border
       rather than by a label telling you to type in it. */
    background: transparent;
    border: none;
    border-left: outer {RULE};
    padding: 0 1;
    height: 1;
    margin: 0 0 0 0;
}}
#repo-input:focus {{
    border-left: outer {CITE};
}}
#home-notice {{
    height: auto;
    padding: 1 1 0 2;
}}
#recent-scroll {{
    height: 1fr;
    scrollbar-size: 1 1;
}}
RecentList {{
    height: auto;
    background: transparent;
    border: none;
}}
RecentList > ListItem {{
    background: transparent;
    padding: 0 1;
}}
RecentList > ListItem.--highlight {{
    background: $boost;
}}
RecentList:focus > ListItem.--highlight {{
    background: $boost;
}}

/* the measured result ------------------------------------------------------ */

MeasuredResult {{
    height: auto;
    padding: 0 1;
    border-left: outer {RAIL};
}}
.measured-lede {{ text-style: bold; }}
.measured-row {{ color: {DIM}; }}
.measured-row-ours {{ color: $foreground; }}
.measured-check {{ color: {DIM}; }}

/* reading order ------------------------------------------------------------ */

EntryPointRow {{
    height: auto;
    padding: 1 1 0 1;
}}
.entry-index {{ color: {FAINT}; width: 4; }}
.entry-why {{ color: {FAINT}; padding-left: 4; }}

.section-label {{
    color: {DIM};
    padding: 1 1 0 1;
}}
.empty {{
    color: {FAINT};
    padding: 1 1;
}}
"""
