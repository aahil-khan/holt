"""Keeping the highlighted row where somebody can see it.

Every list in the interface is laid out the same way: a `ListView` at
`height: auto` inside an ancestor that scrolls. That is deliberate — the list
should be as tall as it has rows, and the page around it should scroll — but it
breaks the scrolling Textual gives a `ListView` for free. A `ListView` scrolls
*itself* to keep its cursor visible, and one sized to its own content has
nothing to scroll. So the highlight moved and the view did not: the cursor
walked off the bottom of the pane and kept going, invisibly.

It was worst on the finder, where the nine rejected candidates sit below the
sixteen survivors. Rejections are the interesting result, the screen says so in
its own docstring, and they were unreachable by keyboard — twenty presses of ↓
left the list index at 20 and the scroll offset at 0. The only way to read them
was a mouse wheel, in an interface whose whole claim is that it does not need
one.

The fix is to scroll the *ancestor*, which is what `scroll_visible` does. Mixed
in rather than repeated, because all three lists have the layout and so would
all three have the bug.
"""

from __future__ import annotations

from textual.widgets import ListView


class KeepsHighlightVisible:
    """Scroll the highlighted row into view in whatever ancestor scrolls.

    Mixed in *before* `ListView` so this handler runs on the widget itself.
    Motion is off: the highlight is being driven by a key repeat, and animating
    each step means the view lags several rows behind the cursor.
    """

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is not None:
            event.item.scroll_visible(animate=False)
