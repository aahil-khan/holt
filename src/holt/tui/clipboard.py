"""Getting the report out of the terminal and into somewhere it can be used.

The assessment is markdown before it is anything else — `Assessment.render()`
writes the file that `holt assess` produces — so what leaves here is that exact
text, evidence ids and all. Copying a re-typeset version of a report would mean
the thing you paste into an issue is not the thing the tool committed.

Copying from a terminal is genuinely uncertain, and this module refuses to
pretend otherwise. Two mechanisms, tried together:

* **A local clipboard tool** (`wl-copy`, `pbcopy`, `xclip`, …). When one runs
  successfully the text is definitely on the clipboard, and we can say so.
* **OSC 52**, the escape sequence that asks the terminal emulator itself to take
  the text. It is the only thing that works over ssh or inside tmux without a
  local display, and it is also *unacknowledged* — the terminal may honour it,
  ignore it, or have it switched off, and nothing comes back either way.

So the caller is handed a sentence describing what actually happened rather than
a boolean, and that sentence is shown to the user. "Copied" when a tool
confirmed it; "asked your terminal to copy it" when only OSC 52 was available.
Claiming success we cannot observe is the one thing not on offer.
"""

from __future__ import annotations

import os
import shutil
import subprocess

#: How long a clipboard tool may take before we give up on it and try the next.
#: Generous for a local process, short enough that a wedged one does not hold
#: the interface while somebody waits for a keypress to do something.
TIMEOUT_S = 2.0


#: name, argv, and the environment variable that has to be set for the tool to
#: have anything to talk to. `wl-copy` outside a Wayland session and `xclip`
#: with no `DISPLAY` both exist on a lot of machines and fail on all of them;
#: skipping those is faster than timing them out.
COMMANDS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("pbcopy", ("pbcopy",), ""),
    ("wl-copy", ("wl-copy",), "WAYLAND_DISPLAY"),
    ("xclip", ("xclip", "-selection", "clipboard"), "DISPLAY"),
    ("xsel", ("xsel", "--clipboard", "--input"), "DISPLAY"),
    ("clip.exe", ("clip.exe",), ""),
)


def native(text: str) -> str:
    """Write to the system clipboard. Returns the tool that did it, or `""`."""
    for name, argv, needs in COMMANDS:
        if needs and not os.environ.get(needs):
            continue
        if shutil.which(argv[0]) is None:
            continue
        try:
            subprocess.run(
                argv,
                input=text.encode(),
                timeout=TIMEOUT_S,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        return name
    return ""


def copy(app, text: str) -> str:
    """Put `text` on the clipboard, and say in words what actually happened.

    Both mechanisms are used, not one as a fallback for the other. A local tool
    reports success but only reaches the machine holt is running on; OSC 52
    reports nothing but is the one that reaches the terminal you are sitting in
    front of when that is somewhere else.
    """
    tool = native(text)
    try:
        app.copy_to_clipboard(text)
    except Exception:  # noqa: BLE001 - never let a copy attempt close the report
        pass
    if tool:
        return f"Copied as markdown ({tool})."
    return (
        "Asked your terminal to copy it as markdown (OSC 52). "
        "Not every terminal honours that, and none of them say."
    )
