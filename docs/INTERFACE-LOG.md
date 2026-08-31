# Interface log

The terminal interface, iteration by iteration. These are kept out of
[CHANGELOG.md](../CHANGELOG.md) on purpose: that file answers the brief's
question — one entry per experiment, each with the result it was measured
by — and none of the work below moved a benchmark number. It changed what
a person sees. Entries are verbatim and in the order they happened.

They keep the iteration numbers they were written under, so the references
inside them still resolve. The two sequences are independent: "Iteration 27"
below is this file's, not that one's.

---

## Iteration 22 — a terminal interface, built without the engine noticing (2026-08-30)

**Tried.** A Textual TUI over the existing pipeline: a live view that streams the
run, and an assessment view that makes the finished report navigable. The
requirement that shaped every decision was that the headless path stays
authoritative — the interface must be a way of *watching* a stage, never a second
way of *running* one.

**Why.** The orchestration's central behaviour is invisible in the CLI output.
Stage D drops a claim whose evidence id does not resolve, and today that shows up
only as a stderr comment behind `--show-verification`. The thing the project is
actually about is the least visible thing it does.

**The design question was where the event stream comes from.** The obvious move
is a callback threaded through `pipeline.analyze`. That puts a UI concern in the
reproduction path and hands the eval harness a parameter it has no use for.

**What was built instead: the interface wraps the pipeline's two inputs.**
`ObservingModel` and `ObservingProvider` are pure delegates around the
`ModelClient` and `EvidenceProvider` that `analyze` already takes. Stage
transitions come from the labels passed to `complete`. And Stage D's drop needs no
hook at all, because the drop *is* `provider.resolve()` returning `None` — watching
resolution is enough to see it happen.

**Zero engine edits.** `holt/agent/`, `holt/report.py`, `holt/evidence/` and
`eval/` are byte-identical. A test asserts the point directly: the assessment
produced with the observers in place renders identically to the one produced
without them.

**The one honest coupling is pinned.** `observe.py` reads each stage's structured
response so the live view can show a claim appear *before* Stage D judges it, which
means it mirrors key names owned by `stages.py`. A test replays real recorded
trajectories and fails if any expected key stops being produced — because a live
view that silently renders nothing looks like a working interface with a quiet
repository behind it, which is the worst failure mode available to this feature.

**Evidence, from real replays rather than constructed fixtures.** A sweep of all
60 recorded trajectories found exactly two repositories where Stage D actually
drops something. `Sistema-de-certificacion-academica` is the one the interface is
demonstrated on: the model asserted `onboarding = absent` and cited
`no_contributing_file`, an id it invented. The lookup fails, the claim is dropped,
and it does not reach the reader — 15 findings in, 14 out.

**Design.** Colour does three jobs and no others: verdict state, evidence
resolution, Stage D drops. No background is painted, so the app sits on the
terminal's own ground and reads correctly on a light or dark profile without a
theme switch. `not_viable` is clay rather than red — it is a finding about a
repository, not a failure of the tool. `insufficient_evidence` is grey, because an
absence of evidence has not earned a colour. There are no progress bars: a bar
would need a denominator the pipeline does not know, and the count of threads read
is a real number.

**The reading order's negative result is given more room than the ranking it
qualifies.** No warning colour, no collapsing behind a keystroke, and the four
precision figures are a table rather than a sentence, because the point is that
they sit on top of each other. Every number is read from `entry.MEASURED`, so the
interface cannot drift from the measurement.

**Textual is an optional extra and nothing else imports it.** `uv sync` with no
extra: **79 passed, 1 skipped** — the skip is the screen tests, reporting
themselves absent rather than failing. `uv sync --extra tui`: 5 screen tests pass
on top. `holt tui` without the extra prints how to install it and exits 2. The
observation layer's 8 tests run either way, because it does not import Textual.

---

## Iteration 27 — the interface was mouse-only, and a stylesheet typo was why (2026-08-31)

**Tried.** Four fixes to the terminal interface, all from using it: copy the
report out as markdown, reach every list from the keyboard, stop a pasted URL
hiding an assessment we already have, and stop offering models that cannot hold
a conversation.

**The keyboard fault was one character.** Every list in the app is a Textual
`ListView`, which marks the row the keyboard is on with a CSS class. The
stylesheet styled `.--highlight`. Textual sets `-highlight`. So **no list in the
interface has ever shown a selection** — not recent, not the claims, not the
providers, not the discovered candidates — and the only way to pick anything was
to click it.

**And fixing the selector was not enough.** The rule it enabled was
`background: $boost`, and boost is a translucent overlay. `theme.py` paints no
background anywhere on purpose, so it composites over `transparent` to exactly
nothing. The interface's own best property — that it sits on the terminal's
ground and reads on a light or a dark profile — is what made Textual's idiom for
selection unavailable to it.

**So selection is a rail, not a fill**: `border-left: outer` in `CITE`, the same
colour and shape already used to mark a focused input, with the column reserved
on every row so moving the selection does not shift the text sideways. It is now
the same vocabulary in all four lists.

**A test that reads text could not have caught any of this**, which is why
`rail_colour()` in `test_tui_screens.py` reads the compositor's *styles* and
asserts the rail is on the highlighted row and absent from its neighbour. Both
class names are listed on every rule, because Textual renamed it between
versions this project supports and naming one silently stops highlighting again.

**Three more places the keyboard dead-ended.** Home never set an index, so there
was nothing to move from — ↑↓ now move the selection while the input keeps
focus, so typing never stops working, and the notice says what enter means now
that it has changed meaning. Discover focused the scroll box rather than the
list inside it, so enter did nothing. And on the report, tab reaches the claims
but `ListView` then takes enter for itself and posts a message the screen did
not handle — a list you could move around in and never open.

**The pasted-URL bug was the interface contradicting itself.** Typing filters
recent by raw substring; enter runs the text through `normalise`. So
`https://github.com/astral-sh/uv` filtered the list to nothing and printed
"Nothing assessed matches that" about a repository sitting in the store — while
enter on the same text opened the stored answer. Both cannot be right. The
needle is normalised now, and when what you typed names something already
assessed it says so in words, with its age and whether enter will reuse it or
pay for it again.

**Copying is honest about not knowing.** `c` puts `Assessment.render()` — the
artefact, not a transcription of the screen — on the clipboard via a local tool
*and* OSC 52. A local tool confirms; OSC 52 cannot, so the message says "asked
your terminal to copy it" rather than "copied" when that is all that ran. Tools
whose display variable is unset are skipped rather than timed out.

**Embedding models are not choices.** Ollama serves `nomic-embed-text` from the
same `/v1/models` as everything else, and every stage of the engine calls chat
completions — so picking one fails at Stage A. Ollama is now asked what each
model can do (`/api/show`, which reads the manifest and does *not* load the
model into RAM — the one call that does that is still `test_connection`, behind
a keypress). A model it will not describe, or an Ollama too old to report
capabilities, falls back to the name rather than being dropped on no evidence.
What is filtered out is counted and reported: a list shorter than `ollama list`
has to say why it is shorter.

**Evidence.** `uv sync --extra tui`, `HOLT_NO_NETWORK=1 pytest -q -rs`:
**264 passed** in 56s, no skips (259 in `tests/`, 5 in `eval/`). That is 29 new
tests: 20 on the model filter — including one that stubs `/api/show` returning
no `capabilities` field at all, the case that would otherwise hide every model
on an older Ollama — and 9 on the keyboard, the pasted URL and the clipboard.

---

## Iteration 28 — a run belongs to the app, not to the screen watching it (2026-08-31)

**Tried.** Three defects in the interface, reported by a reader using it: the
live view claimed a `pre_t ≤ 2026-06-01` holdout on runs that were reading up to
today; leaving a run stopped it; and ctrl+p opened a menu about Textual.

**The window label was a literal, and the fix it needed had already shipped.**
`f0beaa4` made `LiveGitHubProvider` default its cutoff to `datetime.now(UTC)` —
T is an evaluation device, and a live reader wants everything up to today. That
commit touched `github_graphql.py`, `capture_fixtures.py`, its test and this
file. It did not touch the TUI, where `screens/live.py` printed the date as a
string constant and `events.EvidenceLoaded` carried only a count and a window
name. The engine was right and the screen could not have known.

`EvidenceLoaded` now carries the `cutoff` the provider actually applied, read
off the provider in `ObservingProvider.fetch`. The screen renders that date and
never a constant: `holdout window, ≤ 2026-06-01` when the cutoff really is T,
`read through 2026-08-31` when it is not, and no window claim at all when the
provider reports no cutoff. **A field added with a default, not changed** — the
schema's rule is that events are added to, and a caller written before this
field existed still constructs a valid one.

**Leaving a run did not stop it — it discarded the run's result, which looked
the same.** The worker thread was already a daemon and carried on. But
`LiveScreen._pump` was the only caller of `session.drain()` in the whole app,
and `LiveScreen._on_finished` was the only caller of `app.remember()`. Popping
the screen killed the interval that consumed the run's events: the thread kept
spending, `RunFinished` sat unread in a queue, and the assessment it produced
was never absorbed and never stored. `app.session` was also a single slot, so
starting a second run orphaned the first silently.

**The fix is one move: the pump belongs to the app.** `HoltApp` keeps
`runs: dict[str, Session]` and one interval that drains every registered
session, stores what finished, and unregisters it — ticking whether or not any
screen exists. The live screen renders from `session.log` behind a cursor
instead of draining the queue itself, which buys the rejoin behaviour for free:
a run opened again replays from index 0, so you see what happened while you were
away rather than only what happens next.

**Stopping is cooperative, and the engine still knows nothing about it.** A
Python thread cannot be killed, so `Session.cancel()` sets an event and the run
is interrupted at its next chokepoint. Those chokepoints already exist —
`ObservingModel.complete` and `ObservingProvider.fetch/resolve` are the only
ways a stage reaches a model or a record — so no file under `holt/agent/`
changed again. The check is placed *before* the delegated call rather than
inside `complete`'s existing try, because raising in there emits `RunFailed` on
the way out and would report a stop the reader asked for as a defect.

**The cost of that choice is latency, and the interface says so.** A stop lands
when the call in flight returns: instant on a replay, up to a model timeout on a
live run. The row reads `stopping…` until the worker exits rather than claiming
the run has already ended. `RunCancelled` is its own event, not a `RunFailed`
with a nicer message — a stopped run stores nothing, and nothing about it should
read like something going wrong.

**The command palette was the framework's, not holt's.** ctrl+p listed `Keys`,
`Maximize`, `Screenshot` and `Theme` — and `Theme` would have overridden the
verdict colours `theme.py` deliberately fixes. It now leads with holt's own
commands, including two kinds that *cannot* be keybindings because they are
state: `stop home-assistant/core` exists only while that run does, and
`open vercel/next.js` only once there is something stored. Textual's commands
are kept and yielded last.

**And the cursor was invisible.** Textual falls back to its *blurred* block-cursor
colours for an `OptionList` that does not hold focus, and the palette's input
holds focus the entire time it is open — so up and down moved a selection
nobody could see. Reported as two bugs, one cause. The focused cursor tokens are
used instead: they are the theme's own, so this stays right on a light terminal
as well as a dark one. The test reads the cursor off the composited output
rather than off the widget's index, because an index that moves while nothing on
screen changes is exactly the defect.

**They are yielded from holt's provider rather than registered beside it.**
`App.COMMANDS` is a set and providers are searched concurrently with hits
collected as they arrive, so two providers produced a different order on each
launch — measured directly: holt's commands on top in one run, Textual's in the
next. One provider yielding in a written order is what makes the order a
decision rather than a hash.

**Evidence.**

```
$ uv run pytest -rs -q
238 passed in 51.45s
```

216 before this iteration, so twenty-two tests added and nothing skipped. The
one that pins the reported defect: a run whose live screen is popped, finishing
while home is up, and asserting the assessment reaches the store and the session
leaves `app.runs`. Reverting only `src/holt/` and re-running the two new
window-label tests fails them (`EvidenceLoaded.__init__() got an unexpected
keyword argument 'cutoff'`), which is what says they would have caught it.

**Decision.** Kept. The interface now has one rule about runs — a run ends
because it finished, it failed, or someone stopped it — and escape is not one of
those reasons.

**Landed after the keyboard work, so the two had to be reconciled.** This branch
was cut from `89c8014` and sat unmerged while Iteration 27 rebuilt the same
screen; rebasing it produced real conflicts in `home.py`, not textual ones.
Three decisions came out of that:

* **The selection index counts rows, not stored entries.** Iteration 27 set
  `listing.index` from `len(self._entries)`. Running rows sit above the stored
  ones in the same list, so counting only the stored ones left the last rows
  unreachable by keyboard — a highlight that stops short of the bottom of the
  list it is in.
* **Enter has three meanings now, and they are resolved in one place.** In the
  box it assesses what you typed; on a stored row it opens that answer; on a
  running row it rejoins the run. `_open_highlighted()` is the single function
  that decides which, so the ↑↓ path and the empty-box path cannot drift apart.
* **A running row is never described as a stored one.** "assessed 2 min ago"
  about a run in flight would be wrong twice: it has not finished, and nothing
  is being reused. It says `enter rejoins the run on …  ctrl+x stops it`, and
  ctrl+r on it refuses rather than starting a second run of one question.

**Evidence.** `uv sync --extra tui`, `HOLT_NO_NETWORK=1 pytest -q -rs`:
**288 passed**, no skips. One test is new here rather than from either branch —
`test_arrowing_onto_a_run_in_flight_says_so_and_rejoins_it` covers exactly the
seam the rebase created, which neither side's tests reached on their own.

---

## Iteration 29 — the model list was a dump, not a choice (2026-08-31)

**Observed, from a screenshot of the real screen.** Under an OpenAI key the
model list opened on `gpt-4o-mini-transcribe`, ran alphabetically through four
speech-to-text models, and showed `gpt-5` as **unpriced — cost recorded as 0**
one row above `gpt-5-2025-08-07` showing **priced**. Every visible row but one
claimed holt could not cost it.

**The pricing was a real bug, and a narrow one.** `PRICES` is keyed on dated
snapshots — deliberately, because `STAGE_MODELS` pins dated ids so a recorded
run cannot drift underneath a reproduction claim. But *display* was reading the
same table, so the floating alias `gpt-5` matched nothing and reported zero.
Two ids for one model, disagreeing on screen about what it costs.

**Fixed with a second table, not by loosening the first.** `MODEL_ALIASES` maps
each floating alias to the snapshot it currently points at, and `resolve_price`
reads through it. They are kept apart because the two facts have different
lifetimes: a snapshot's price is fixed for as long as the snapshot exists, and
where an alias points is true only until the provider repoints it. A rate
reached through an alias renders with `≈` and the cost accounting uses it —
recording $0 for a run on `gpt-5` understates a real bill, which is worse than
declining to guess.

**The rate is now the row, because "priced" answers nobody's question.** A
reader choosing a model is deciding what a run will cost; "priced" told them a
number existed somewhere else. Rows read `$1.25 in / $10.00 out per M tokens`.
`holt models` on the command line prints the same figure.

**Speech, image and realtime ids were leaking through the chat filter.**
Iteration 27 caught embeddings; `transcribe`, `diarize`, `realtime`, `sora` and
`gpt-image` were not on the list and every one of them was being offered as a
model to run the pipeline on. Ten of the twenty-five ids on a stock OpenAI key
are not chat models.

**"Popular first" is not a fact this tool can know, so it is not claimed.**
Ordering is four tiers: the two models holt is pinned to, then the ones it can
state a cost for, then everything else, then legacy and preview ids — with
alphabetical order inside each tier so the list is stable between looks. The
last tier is *sunk, not hidden*: `babbage-002` is a real chat model and the
provider offers it, so the list says so, at the bottom. The count line explains
the order rather than leaving a reader to infer it.

**And the list is filterable.** Substring, case-insensitive, deliberately not
fuzzy — you are looking for a name you already partly know, and a fuzzy match
surfacing `gpt-4o` for "o1" would make the list less trustworthy. The filter box
keeps focus while ↑↓ move the cursor, the same arrangement home uses, so
narrowing and choosing are one gesture.

**A separate report from the same session: the front screen had no visible way
out.** `q` quits every screen with no text box on it, and home has one, so the
key is consumed as a character and never arrives. `ctrl+q` is now an app-level
binding — it therefore appears on every footer, and it survives a focused input.

**Test pollution found while adding the tests, and worth recording.** The first
version of the models-screen helper set `OPENAI_API_KEY` in `os.environ`
directly. Home reads that variable to choose between live and replay, so a
models test silently flipped the mode of every test that ran after it and broke
an unrelated assertion about the evidence window. Everything the helper touches
now goes through `monkeypatch`.

**Evidence.** `uv sync --extra tui`, `HOLT_NO_NETWORK=1 pytest -q -rs`:
**305 passed**, no skips. 17 new tests, driven against a scripted listing of the
25 ids a stock OpenAI key actually returns — the alias pricing, the four
ordering tiers, the six id families that are not chat models, the filter, and
`ctrl+q` on home.

---

## Iteration 30 — `ctrl+f` was showing somebody else's search results (2026-08-31)

**The report.** Pressing `ctrl+f` opened a page of twenty-five repositories.
They were real, they were screened correctly, and they had nothing to do with
the person looking at them: they came from the `demo` session committed to this
repository — one profile, run once, on a date in the past. Nothing on the screen
was false. The screen was still lying, because a list of repositories presented
where a result goes reads as *your* result, and no caption undoes that.

**Why it was built that way, and why that stopped being a good reason.** The
recording exists so the interface demos with no token and no key, and so the
screening rule can be exercised in tests without network. Both are still worth
having. What was wrong was making the demo the default: it turned a feature that
finds you repositories into a feature that shows you a canned list, and the
better it looked the worse the problem was.

**`ctrl+f` now opens on a choice.** Search GitHub, change what you are looking
for, or replay the recorded example search — that last one described as what it
is and offered only when the manifest is actually on disk. The recording is one
keystroke away and still free. It is no longer what the feature claims to be.

**Live search needs a token and nothing else, and the screen says exactly
that.** `screen_records` runs no model, so a sweep costs GitHub API quota and
about a minute of waiting. The check is on `GITHUB_TOKEN` alone; demanding an
OpenAI key to *find* candidates would have made a free feature look paid. A
missing token is reported on the start screen with the choice still under the
cursor, not as a dead end.

**Rows are drawn as they land.** Sourcing twenty-five repositories and reading a
page of pull-request threads from each is a minute of network, and a minute of
blank screen is indistinguishable from a hang. The engine grew `source_live`,
which does the one search call and returns a `LiveSearch` whose `screen()`
yields one `ScreenedStep` per candidate; `run_live` now walks that same
generator, so the command line and the interface cannot drift on what survives.
The interface wraps it in a worker thread that appends, with a cursor on the
reading side — the arrangement the run stream already uses, no lock and no
message schema.

**Rows are not re-sorted as they arrive.** The recorded view puts survivors
first because it has all of them before it draws anything. A live sweep does
not, and rearranging the list under the cursor as each verdict landed would
assert a ranking screening never computed. They stay in the order the search
returned them, cut ones included, reasons attached.

**"Could not read" is kept separate from "rejected".** A candidate GitHub
refuses is listed as unread, never counted as a cut. A sweep that quietly merged
the two would report a rejection it never made.

**Stopping keeps what it already screened.** Those rows were free and they are
still true; discarding them would punish impatience. Cancellation is checked
between candidates, so `ctrl+x` returns within one candidate rather than at the
end of the sweep.

**Found while testing: the footer advertised a key that did nothing.** `ctrl+x
stop searching` was listed on the start screen, where there is no search to
stop, which made the choice look like a sweep already running. The binding is
now conditional on a live search being alive.

**Also corrected: the discovery tests were gated on the recording.** The whole
module was skipped when `demo` was absent. That was defensible when the
recording was the only path; it is not now that live search is the default. The
skip applies to the seven tests that actually read the manifest, and the
live-search tests run everywhere.

**Evidence.** `pytest -q -rs` and `HOLT_NO_NETWORK=1 pytest -q -rs`:
**315 passed**, no skips (was 305). 10 new tests — seven driving the search
worker against a stubbed `source_live` with no token, network or recording
(ordering, unread candidates, cancellation, thread failure, progress before the
first row, the token check), and three driving the screen (it opens on the
choice with no recorded slug on screen, it streams rows while the sweep runs,
and a missing token is reported without leaving the choice).

---

## Iteration 31 — "what next" only ever read the recording (2026-08-31)

**The report.** Assess a repository, press `n`, and the screen answered *"No
committed evidence for canonical/ubuntu-cloud-docs, so there is nothing to rank
from."* The sentence was true and it named the wrong problem. `_rank` called
`session._provider(live=False)` with the flag hardcoded, so the ranking read the
committed fixtures and nothing else — whatever mode the run in front of you had
been in. A repository GitHub would have answered for immediately was reported as
unrankable because we never asked GitHub.

**It matters more now than it did.** Iteration 30 made the finder open on a live
GitHub search. Every repository it hands you is one with no fixture on disk, so
the natural path through the product — find a repository, assess it, ask what to
work on — hit the dead end every time. A screen that only works on the 69
repositories committed to this repository is a demo, not a feature.

**The mode now travels with the report.** `NextScreen` takes the run's `live`
flag and tries that source first, because the ranking should read the evidence
the report in front of you was built from. The other source is tried second: a
committed fixture and a live fetch answer the same question about the same
repository, and stopping at the first miss was the whole bug. Live is dropped
from the list when there is no token rather than attempted and reported as a
failure, which would again name the wrong problem — the message asks for
`GITHUB_TOKEN` instead of blaming a recording nobody made.

**The fetch moved off the event loop.** A live read is a network round trip and
the interface must not freeze for the length of one, so both fetches go through
`asyncio.to_thread` with the notice saying which source is being read.

**The ranking now carries its own measurement, which it should never have shown
an order without.** `render_next` in the engine carries a docstring saying the
measurement is emitted "in the only path that prints the ranking, so no caller
can show the order without the number that says how well it works". That
invariant was already broken: this screen is a second path that prints the
ranking, and it printed the order with a one-line summary and no number. It now
shows `NEXT_MEASUREMENT` verbatim whenever an order is on screen — hit@10 0.234
against 0.172 for chance, 95% interval [-0.003, +0.132], an interval that spans
zero. The interface holds evidence to a `file:line` standard; a ranking is a
claim and it gets the same treatment.

**Provenance on the summary line.** It now says whether it read live from GitHub
or from committed evidence, because with two sources in play "76 of 202 open
issues overlap" is not a complete statement without saying what it read.

**Evidence.** `HOLT_NO_NETWORK=1 pytest -q -rs`: **318 passed**, no skips (was
315). Three new tests — the measured claim appears with any order it shows
(`hit@10 0.234`, `spans zero`), a live-assessed repository with no fixture asks
for the token instead of blaming the recording, and the source order follows the
report's mode with live dropped when there is no token. Verified by hand against
`home-assistant/core` + `@frenck`: 14 merged PRs, 31 files, 76 of 202 open
issues overlap.
