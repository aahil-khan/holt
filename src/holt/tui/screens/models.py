"""Which model answers, in two steps.

Providers first, then the models that provider actually has — asked for over the
wire rather than hardcoded, because a list of model ids goes stale faster than
anything else in a tool like this and a stale list is worse than none.

Every network call runs on a worker thread. The screen stays responsive while a
provider is thinking, and a provider that never answers produces a sentence
after twelve seconds instead of a frozen interface.

Three things are always on screen once they are true, because each is something
you would otherwise discover at the worst moment:

* whether the key for a provider is even set, before you pick it
* whether a chosen model actually answers, on demand
* that a non-default choice stops the committed recordings replaying
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Input, ListItem, ListView

from holt import model as model_module
from holt.tui import animation, mascot, models as models_layer, theme
from holt.tui.visual import Line
from holt.tui.widgets.masthead import Cat


class ProviderRow(ListItem):
    def __init__(self, provider, current: bool, **kwargs) -> None:
        super().__init__(**kwargs)
        self.provider = provider
        self.current = current

    def compose(self):
        row = Text()
        row.append("▸ " if self.current else "  ", style=theme.DIM)
        row.append(f"{self.provider.name:<20}")
        row.append(
            self.provider.status(),
            style=theme.FAINT if self.provider.usable else theme.DROP,
        )
        yield Line(row)


class ModelRow(ListItem):
    def __init__(self, entry, current: bool, **kwargs) -> None:
        super().__init__(**kwargs)
        self.entry = entry
        self.current = current

    def compose(self):
        row = Text()
        row.append("▸ " if self.current else "  ", style=theme.DIM)
        row.append(f"{self.entry.id:<38}")
        row.append(
            self.entry.pricing,
            style=theme.FAINT if self.entry.priced else theme.NOT_VIABLE,
        )
        if not self.entry.from_provider:
            row.append("   not from the provider", style=theme.FAINT)
        yield Line(row)


class ModelsScreen(Screen):
    BINDINGS = [
        # Handled here, not by the list: the filter box holds focus so that
        # typing and choosing are one gesture. Hidden from the footer, which
        # already carries the hint line under the list.
        Binding("down", "browse_down", "choose", show=False),
        Binding("up", "browse_up", "choose", show=False),
        ("ctrl+t", "test", "test connection"),
        ("ctrl+d", "reset", "back to defaults"),
        ("escape", "back", "back"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = model_module.load_models_config()
        self.providers = models_layer.providers(self.config)
        self.chosen = next(
            (p for p in self.providers if p.name == self.config.provider),
            self.providers[0],
        )
        self.listing: models_layer.Listing | None = None
        self.step = "provider"
        #: What is typed in the filter box. Held on the screen rather than read
        #: back off the widget, because the list is rebuilt from it and the
        #: widget does not exist on the provider step.
        self._filter = ""

    # ─── layout ─────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Horizontal(id="chrome"):
            yield Cat("idle", id="cat", classes="chrome-cat")
            yield Line("models", id="chrome-left")
            yield Line(self._summary(), id="chrome-right")
        yield Line("─" * 240, classes="rule")

        yield Vertical(id="models-body")
        yield Footer()

    async def on_mount(self) -> None:
        await self._show_providers()

    # ─── the two steps, each rebuilding the same body ───────────────────────

    async def _body(self) -> Vertical:
        """Empty the body and hand it back.

        The removal is awaited. It returns before the widgets are actually gone
        otherwise, and mounting a replacement with the same id against the old
        one still present fails on a duplicate id — silently, inside a handler,
        which looks exactly like a key that does nothing.
        """
        body = self.query_one("#models-body", Vertical)
        await body.remove_children()
        return body

    def _footer_lines(self, body: Vertical, hint: str) -> None:
        body.mount(Line(Text(hint, style=theme.FAINT), id="models-notice"))
        body.mount(Line("", id="models-warning"))
        self._paint_warning()

    async def _show_providers(self) -> None:
        self.step = "provider"
        self._filter = ""
        body = await self._body()
        body.mount(Line(Text("PROVIDER", style=theme.DIM), classes="section-label"))
        scroll = VerticalScroll(id="provider-scroll")
        body.mount(scroll)
        listed = ListView(
            *[ProviderRow(p, p.name == self.config.provider) for p in self.providers],
            id="providers",
        )
        scroll.mount(listed)
        # The list is the only thing to interact with, so it takes focus. A
        # screen whose enter key does nothing until you guess to press tab is a
        # screen that appears broken.
        listed.focus()
        self._footer_lines(
            body,
            "enter list this provider's models    ctrl+t test    ctrl+d defaults",
        )
        animation.reveal(body)

    def _summary(self) -> Text:
        text = Text()
        text.append(f"{self.config.provider}   ", style=theme.FAINT)
        text.append(
            model_module.model_for("classify"), style=theme.DIM
        )
        return text

    def _notice(self, message: str, tone: str = "") -> None:
        self.query_one("#models-notice", Line).update(
            Text(message, style=tone or theme.FAINT)
        )

    def _paint_warning(self) -> None:
        warning = models_layer.replay_warning(model_module.active_config())
        widget = self.query_one("#models-warning", Line)
        widget.update(Text(warning, style=theme.DIM) if warning else "")
        widget.display = bool(warning)

    # ─── step one: providers ────────────────────────────────────────────────

    def on_list_view_selected(self, event) -> None:
        item = event.item
        if isinstance(item, ProviderRow):
            self.chosen = item.provider
            self._load_models()
        elif isinstance(item, ModelRow):
            self._use(item.entry.id)

    def _load_models(self) -> None:  # noqa: D401
        if self.chosen.needs_base_url:
            self._notice(
                "This provider needs a base url. Set one with "
                "`holt models --provider openai-compatible --base-url <url>`.",
                theme.DROP,
            )
            return
        self._notice(f"Asking {self.chosen.name} what it has…")
        self._fetch(self.chosen)

    def _fetch(self, provider) -> None:
        """On a thread: a provider that hangs must not take the screen with it."""

        def work():
            return models_layer.list_models(provider)

        self.run_worker(
            lambda: self._fetched(work()), thread=True, exclusive=True, group="models"
        )

    def _fetched(self, listing) -> None:
        self.app.call_from_thread(self._show_models, listing)

    async def _show_models(self, listing) -> None:
        self.listing = listing
        self.step = "model"
        # A filter belongs to the provider you are looking at, not to the
        # screen: carrying "gpt" over to Ollama would show an empty list.
        self._filter = ""

        body = await self._body()
        body.mount(
            Line(
                Text(f"MODELS · {self.chosen.name}", style=theme.DIM),
                classes="section-label",
            )
        )

        if listing.error:
            # The failure and whatever we still know, in that order. A short
            # list with no explanation of why it is short is worse than an error.
            body.mount(Line(Text(listing.error, style=theme.DROP), classes="empty"))
        if not listing.models:
            body.mount(
                Line(
                    Text("Nothing to choose from here.", style=theme.FAINT),
                    classes="empty",
                )
            )
        else:
            if listing.guessed:
                body.mount(
                    Line(
                        Text(
                            "Listed from what this build knows, not from the "
                            "provider — it may be wrong or out of date.",
                            style=theme.FAINT,
                        ),
                        classes="empty",
                    )
                )
            if listing.hidden:
                # The list is shorter than `ollama list` and has to say why,
                # otherwise the missing model reads as the interface losing it.
                body.mount(
                    Line(
                        Text(
                            f"{listing.hidden} more "
                            + (
                                "is not a chat model"
                                if listing.hidden == 1
                                else "are not chat models"
                            )
                            + " — embeddings, speech, images. Every stage "
                            "calls chat completions, so they are not choices.",
                            style=theme.FAINT,
                        ),
                        classes="empty",
                    )
                )
            # A provider can offer eighty ids. Typing narrows them, and the
            # box holds focus so narrowing and choosing are the same gesture —
            # ↑↓ are handled by this screen, exactly as on home.
            body.mount(
                Input(placeholder="filter by name", id="model-filter")
            )
            body.mount(Line("", id="model-count", classes="field-note"))
            scroll = VerticalScroll(id="model-scroll")
            body.mount(scroll)
            scroll.mount(ListView(id="models"))
            await self._paint_models()
            self.query_one("#model-filter", Input).focus()

        self._footer_lines(
            body,
            "type to filter    ↑↓ choose    enter use everywhere    "
            "ctrl+t test    esc providers",
        )
        animation.reveal(body)

    async def _paint_models(self) -> None:
        """Refill the list from the current filter, keeping the offer order."""
        listing = self.listing
        if listing is None:
            return
        needle = self._filter
        shown = [m for m in listing.models if models_layer.matches(m, needle)]

        listed = self.query_one("#models", ListView)
        await listed.clear()
        current = model_module.model_for("classify")
        for entry in shown:
            await listed.append(ModelRow(entry, entry.id == current))
        # Always something under the cursor, so ↑↓ has a position to move from.
        listed.index = 0 if shown else None

        count = self.query_one("#model-count", Line)
        total = len(listing.models)
        if not shown:
            count.update(
                Text(f"Nothing here matches “{needle}”.", style=theme.DROP)
            )
        elif len(shown) < total:
            count.update(
                Text(f"{len(shown)} of {total}", style=theme.FAINT)
            )
        else:
            # The pinned models are first, and saying why beats a reader
            # wondering what the order is.
            count.update(
                Text(
                    f"{total} — the ones holt can cost first, then the rest",
                    style=theme.FAINT,
                )
            )

    async def on_input_changed(self, event: Input.Changed) -> None:
        self._filter = event.value
        await self._paint_models()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter in the filter box uses whatever the cursor is on."""
        listed = self.query_one("#models", ListView)
        row = listed.highlighted_child
        if row is not None:
            self._use(row.entry.id)

    def action_browse_down(self) -> None:
        self._browse(1)

    def action_browse_up(self) -> None:
        self._browse(-1)

    def _browse(self, delta: int) -> None:
        """Move the cursor without taking focus off whichever box has it."""
        try:
            listed = self.query_one("#models", ListView)
        except Exception:  # noqa: BLE001 - on the provider step there is no list
            return
        total = len(listed.children)
        if not total:
            return
        current = listed.index
        if current is None:
            listed.index = 0 if delta > 0 else total - 1
        else:
            listed.index = max(0, min(total - 1, current + delta))

    # ─── step two: choosing ─────────────────────────────────────────────────

    def _use(self, model_id: str) -> None:
        try:
            self.config = models_layer.apply(self.chosen, model_id)
        except OSError as exc:
            self._notice(f"Could not save: {exc}", theme.DROP)
            return
        self.providers = models_layer.providers(self.config)
        self.query_one("#chrome-right", Line).update(self._summary())
        self._paint_warning()
        self._notice(f"{model_id} now answers every stage. ctrl+t to test it.")

    def action_test(self) -> None:
        model_id = model_module.model_for("classify")
        self._notice(f"Calling {model_id}…")

        def work():
            return models_layer.test_connection(self.chosen, model_id)

        self.run_worker(
            lambda: self.app.call_from_thread(self._probed, work()),
            thread=True,
            exclusive=True,
            group="probe",
        )

    def _probed(self, probe) -> None:
        self._notice(probe.detail, "" if probe.ok else theme.DROP)

    def action_reset(self) -> None:
        self.config = models_layer.reset()
        self.query_one("#chrome-right", Line).update(self._summary())
        self._paint_warning()
        self._notice("Back to the pinned defaults. Replay works again.")

    async def action_back(self) -> None:
        """One step back, not out. Escape from the models list returns to the
        providers rather than leaving the screen entirely."""
        if self.step == "model":
            await self._show_providers()
            return
        self.app.go_home()
