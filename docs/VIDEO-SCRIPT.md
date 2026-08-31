# Solution video — script and shot list

**Target: 4:50. Hard cap: 5:00.** The brief (Final deliverables, item 03) asks
for five things, in this order:

1. the problem, and the simple baseline
2. one realistic execution, start to finish
3. the final comparison
4. a brief explanation of the changelog
5. **the change that contributed most**, and **one experiment you removed**

Each is a numbered beat below, in that order. If you run long, cut from §2,
never from §5.

**This cut is driven from the terminal interface — `holt tui` — not from the
command line.** Everything in §2 happens inside one running interface, with no
command typed on camera after it launches. The three beats that are not the
interface (§3, §4, §5) are documents, because they are measurements and a
record, not screens.

Narration is written to be read at ~150 words per minute. Word counts are given
per beat so you can check pace without a stopwatch.

> **What is not in this cut.** The previous script closed on the hot take. The
> brief's five items do not include it, and it lives in `CHANGELOG.md` where the
> brief asks for it. Dropping it buys the 15 seconds §2 needs to show a real
> execution rather than a summary of one. Do not add it back to hit five
> minutes.

---

## Two things the interface cannot do

Read these before you plan a shot, because both shaped the beats below.

**There is no baseline arm in the TUI.** `--baseline` is a command-line flag on
`holt analyze`. `ctrl+t` on the home screen toggles replay against live, and
nothing else. So §1's baseline is a captured still, not a live screen — see the
two options in §1.

**There is no `compare` view in the TUI.** The side-by-side shortlist is
`holt compare` on the command line. What the interface has instead is the
**RECENT** list on the home screen, which carries a verdict, an age and a mode
per row — and that is what §2 uses. It is the honest substitute: same verdicts,
one repository per row, and it does not sort, because sorting is a claim.

Neither of these is a gap you should apologise for on camera. Do not mention
them.

---

## Before you record

| | |
|---|---|
| Extra | `uv sync --extra tui`. The interface is an optional extra; every other command and the whole eval harness work without it. |
| Terminal | **110×40 minimum**, font ≥ 18pt. Driven and checked at that size: the report, the trace and the ranked-issues screen all fit without truncation. Below ~100 columns the RECENT rows start eliding. Judges watch this at 720p in a browser tab. |
| Environment | `env -u OPENAI_API_KEY -u GITHUB_TOKEN` in the recording shell for the primary path. Nothing needs a key, and no credential should ever be on screen (**ground rule 08**). |
| Store | The interface keeps what you have assessed in `.holt/assessments`. **Seed it with exactly one entry** — see below — and nothing else, so RECENT is legible rather than a wall. |
| Pre-warm | Launch the interface once and quit before recording. `uv` resolves the environment on first invocation and that pause is dead air. |
| Screen | Editor closed. One terminal for the interface, one browser tab for §3–§5. |

**Seed the store, then capture the baseline still, then clear the screen:**

```sh
rm -rf .holt/assessments                      # start from a known list

# one entry in RECENT, so §1 is a single keystroke
env -u OPENAI_API_KEY -u GITHUB_TOKEN PYTHONPATH=. uv run holt tui
#   type: is-a-dev/register   enter   (report appears)   ctrl+q

# the still frame §1 needs — screenshot this output, do not film it
env -u OPENAI_API_KEY -u GITHUB_TOKEN PYTHONPATH=. \
  uv run holt analyze is-a-dev/register --baseline --replay
```

Then launch the interface for the take and leave it running for the whole of
§1–§2:

```sh
env -u OPENAI_API_KEY -u GITHUB_TOKEN PYTHONPATH=. uv run holt tui
```

Every keystroke from here is a key, not a command. The keys are written as
**`bold`** in the shot lists so you can rehearse from the left column alone.

---

## §1 — The problem, and the baseline (0:00 → 1:00, ~150 words)

**Screen:** two GitHub PR threads side by side, then the baseline still, then
the interface.

> A developer with one week to spend on open source has to pick a repository.
> Every signal GitHub gives them — stars, recency, contributor count, open
> issues — measures *project health*. What they actually need to know is
> whether an outsider can land work there, and those are different things.
>
> These two closed pull requests are the same integer in every GitHub
> statistic. One says "merged, could you look at the sibling case?" The other
> says "we're rewriting this internally, closing." One means a newcomer can
> contribute here. The other means don't bother.
>
> The only way to tell them apart today is to read about twenty pull request
> threads per repository, at roughly fifteen minutes each. Nobody does that, so
> people pick by stars.

**Cut to the baseline still.** This is the thing a person actually does: one
prompt over the README and the repository metadata. `is-a-dev/register` — a
domain registry, forty thousand merged pull requests, none of them software.

> The baseline says **worth your time**. It is a text file where you add one
> line with your name on it.

**Cut to the interface, on home.**

| Key | On screen | Say |
|---|---|---|
| — | Chrome reads `1 assessed   replay   no OPENAI_API_KEY`. RECENT holds one row: `is-a-dev/register`. | Nothing yet — let the frame land. |
| **`↑`** | The row highlights. The line under the input changes to `enter opens is-a-dev/register — assessed just now, replay.` | "Here is the same repository, assessed properly." |
| **`enter`** | The report: **Not worth your time**, *for a contributor with 7 days*. | Read the verdict aloud, then stop. |

**Beat.** Let *Not worth your time* sit against the baseline's *worth your time*
for a full second before you move. That contradiction is the whole first minute.

> **Fully-terminal-free variant.** If you would rather no terminal output
> appeared at all: skip the still, and narrate the baseline's answer over the
> two PR threads instead — "one prompt over the README says *worth your
> time*" — then cut straight to the interface. You lose the evidence that the
> baseline really runs. §3 shows the baseline's numbers either way, so this is
> defensible; it is just weaker. Do not run `--baseline` on camera to fix it.

---

## §2 — One realistic execution, start to finish (1:00 → 2:55, ~250 words)

This is the required execution. One interface, no commands, one contributor's
arc: no shortlist → screened for free → one repository read properly → the run
behind the report → the evidence behind a claim.

**Do not change repository more than once in this beat.** The arc is the point.

### 2a. The mode is a choice (1:00 → 1:10)

| Key | On screen | Say |
|---|---|---|
| **`esc`** | Back to home from the report. | — |
| — | Chrome still reads `replay   no OPENAI_API_KEY`. | "Everything you are about to see is free, reads committed evidence, and the interface says so in the corner rather than letting you find out from a bill." |

### 2b. No shortlist yet, which is the real starting position (1:10 → 1:35)

| Key | On screen | Say |
|---|---|---|
| **`ctrl+f`** | The finder. It opens on a **choice**, not a list: *Search GitHub for repositories* / *Change what you are looking for* / *Replay the recorded example search*. Above them, your own profile. | "Usually you cannot name the repository — that is the actual starting position. This sources candidates against a stated profile and screens them." |
| **`↓` `↓`** then **`enter`** | The results pane. Chrome: `demo   recorded 2026-08-31`. Header: `Looking for python + cli, 7 days, tests`, then `25 candidates screened at no model cost · 16 worth a closer look · 9 cut`. Survivors first: `yt-dlp/yt-dlp`, `tqdm/tqdm`, `fastapi/typer`, `pallets/click`, `beetbox/beets`… each `survived screening`. | "I'm replaying a recorded search, so this costs nothing — and it says so, with the date it was taken." |
| hold **`↓`** to the cut rows | `sherlock-project/sherlock  90,661★  outsider attempts went unanswered` · `Textualize/textual  37,098★  outsider attempts went unanswered` · `soxoj/maigret  37,163★  work merged without review (the rubber-stamp rule)` · `pypa/hatch  nobody outside has landed work in` · `kellyjonbrazil/jc  replies too slow for the day budget` | "Nine of twenty-five cut, and the reason is on the row. Ninety thousand stars, cut. Thirty-seven thousand, cut. Every one of those rejections is free — the verdict rule needs exactly one model-derived input, so screening is arithmetic at zero cost. Remember the third one; we come back to the rule that cut it." |

> `soxoj/maigret` is cut by **the rubber-stamp rule** — the change §5 names as
> the biggest contributor, visibly firing in the product. That callback is worth
> the eight words it costs.
>
> Rehearsing this beat is what found the bug fixed in interface-log iteration
> 35: `↓` used to move the highlight without scrolling the pane, so the cut rows
> were mouse-only. If you are recording from a checkout that predates that fix,
> use the wheel instead.

### 2c. Read one properly (1:35 → 2:05)

| Key | On screen | Say |
|---|---|---|
| **`esc`** | Home. The box still holds `is-a-dev/register` from §1. | — |
| **`esc`** | The box clears. *(The box is not cleared by going home — this second escape is what empties it. Rehearse this; typing into a dirty box is how you get `is-a-dev/registerrunelite/plugin-hub` and a "not an owner/name" notice on camera.)* | — |
| type `runelite/plugin-hub`, **`enter`** | The report, effectively instantly: **Not worth your time**. | "Replay is instant, which is also why a judge reproduces every number in this video with no key at all." |
| — | Read the bottom line: contributions here are metadata entries pointing at external plugin repositories, not runnable code. Maintainers reply in about 4.2 hours. | "Seventy of a hundred and one outsiders merged here, first reply in four hours. It is the best-looking project on that list, and it is rejected." |
| scroll to **WHAT DECIDED IT** | One line: the rule that fired. | "The verdict is not the model's. It is a plain function over verified evidence, and the report prints the rule that decided it." |

### 2d. The run behind the report (2:05 → 2:30)

| Key | On screen | Say |
|---|---|---|
| **`esc`** | Home. Chrome now reads `2 assessed`. `runelite/plugin-hub  Not worth your time  just now  replay` is the top row. | — |
| **`↑`** then **`enter`** | The same report, this time out of the store. Chrome: `just now · replay   ctrl+r to re-run`. | "Reopened from the store — and a stored assessment carries the run's own event stream, so the run behind it is not lost with the process that produced it." |
| **`t`** | The **trace**. Chrome reads `trace`. Five stages with their results: `A classify registry` · `B opportunity substantive` · `C outcomes welcoming · 12 threads read` · `D verify 15 findings → 15 kept, 0 dropped` · `verdict not_viable` · `E narrate 1359 characters`. Below: `830 evidence records · holdout window, ≤ 2026-06-01`, then every evidence id the run emitted. | "The whole execution on one screen. Eight hundred and thirty evidence records, stopping at a holdout the run cannot see past. Five stages. Stage D resolves every evidence id a finding cites and drops what does not resolve. Then the verdict, computed from what survived." |

> **Why the report first and the trace second.** Pressing `t` on a run you
> just watched goes *back down* to the live screen, whose chrome still says
> `assessing` and whose footer still offers `esc leave running` and `^x stop`.
> Reopening from RECENT first gives you the screen titled `trace`, with the
> footer `esc back · a report · q quit`. Two extra keystrokes for a frame that
> does not contradict your narration.

### 2e. The claim, and the record under it (2:30 → 2:55)

| Key | On screen | Say |
|---|---|---|
| **`esc`** | Back to the report. | — |
| scroll to **EVIDENCE** | Fifteen claims, each with an id under it — `pr:…#12259:opened`, `pr:…#12283:opened`. | "Every claim carries an id." |
| **`tab`**, then **`↓`** until a `pr:` id is highlighted, then **`enter`** | The inspector. Chrome reads `resolved`. `pr:runelite/plugin-hub#12259:opened`, its source and timestamp, the URL `https://github.com/runelite/plugin-hub/pull/12259`, then the record's own fields — author, additions, the thread. | "That id opens the real thread it came from. Not a citation — the record." |
| **`esc`** | Report. Scroll to **WHAT COULD NOT BE DETERMINED**. | "And where the evidence could not answer something, that is a section with a heading, in the position the engine puts it — not a footnote." |

> **`tab` first, or you get the wrong claim.** Focus sits on the report's scroll
> container, so `↓` scrolls the page and `enter` opens whatever the claim list
> is *already* on — claim one, which for `runelite/plugin-hub` is
> `repo:…:readme`. That resolves fine, at a pinned commit, but it is a README
> blob and your line is about a thread. `tab` moves focus into the claim list;
> from there `↓` walks the claims and `enter` opens the highlighted one.
> Verified: `tab`, three `↓`, `enter` lands on `#12259`. Count your presses in
> rehearsal — the claim order is fixed, so the number is stable.

> **Optional variant: watch the pipeline run for real (~$0.012, ~40 s).**
> Replay finishes in about 0.15 s, so §2c shows a report rather than a run
> happening. If you want the stage stream — spinners, elapsed clocks, findings
> landing, Stage D dropping one — launch the interface with a repository and no
> mode flag, with `OPENAI_API_KEY` set and `GITHUB_TOKEN` unset:
>
> ```sh
> PYTHONPATH=. uv run holt tui runelite/plugin-hub
> ```
>
> That is *recorded* mode: real model calls over the same committed holdout
> fixtures, so the evidence and the verdict are the ones quoted above and the
> prose is freshly generated. It opens straight onto the run and hands off to
> the report when it finishes, so §2d's `t` is unnecessary — you have already
> watched it.
>
> Costs: about 40 seconds and about $0.012. Three consequences to accept
> knowingly: you start inside a run instead of on home, so §1's last shot and
> §2a move to the end of the beat; the home chrome will read `live` rather than
> `replay`, so you must press **`ctrl+t`** once on camera before typing
> anything else (it answers with *"replay reads a committed recording: free, and
> only where one exists"*, which is a better line than the fallback notice
> anyway); and a stage that errors means re-recording. **Rehearse this path
> once with your key before you commit to it.**

---

## §3 — The final comparison (2:55 → 3:45, ~125 words)

**Screen:** the README result tables, in a browser. Not the interface — this is
a measurement, and there is no screen in the product that claims it. Running
`eval/harness.py --replay` live takes about 30 s, which you do not have.
**Show the tables.**

> Two pools, both hash-committed before any method ran. Ground truth computed
> only from evidence after a temporal holdout neither method could see. Three
> independent runs per pool.
>
> Matthews correlation, because it is zero for any constant answer — and that
> matters here: this pool is sixty-four percent positive, so answering "viable"
> to everything scores F1 0.78 and beats our own baseline. We found that by
> attacking our own metric, and the row stays in the table so you can see the
> floor.
>
> Baseline 0.09 in sample, 0.21 out of sample. Holt 0.61 and 0.63. Holt's
> interval is ±0.00 because its verdicts were identical on all fifty-five
> repositories across every run; the baseline changed its answer on sixteen.
>
> And the honest part: measured over *repositories* rather than runs, the
> ninety-five percent interval still touches zero. We print that rather than
> round it up.

---

## §4 — The changelog, briefly (3:45 → 4:05, ~50 words)

**Screen:** `CHANGELOG.md` → **"The story in one table"**, at the top of the
file. Do not scroll the whole changelog; this one table is the deliverable the
brief describes, and it fits on a screen. Two of its rows — *Thread sentiment →
verdict* (**Removed**) and *The rubber-stamp rule* (**Shipped**) — are adjacent,
which sets up §5 without a scene change.

> Fourteen stages, from the baseline to the shipped tool. Every row is what we
> tried, the evidence it produced, and what we decided — written on the day,
> including five capabilities we cut and a significance claim we retired when it
> failed to re-measure. Two of these rows matter most, and they are the same
> method with opposite results.

Highlight the two rows with the cursor as you say the last sentence.

---

## §5 — The change that contributed most, and the one we removed (4:05 → 4:50, ~115 words)

**Do not cut this beat.** The brief names both items explicitly.

**Screen:** `eval/PREREGISTRATION-2.md` beside the specificity table.

> **The change that contributed most** is a rejection rule: reject a repository
> when contributions land *easily* and nobody reviews them. A stranger's pull
> request waved through into something nobody maintains. It was written down
> with three numeric predictions before it was run, then tested once on the
> second pool, which had never been used to develop it. Specificity 0.58 to
> **0.83**, out of sample. All three predictions held.

**Screen:** `eval/PREREGISTRATION.md`, showing the appended failure.

> **The experiment we removed** was written the same way, one week earlier. Make
> in-thread review ratio decide. Two of three predictions held; the third failed
> — MCC dropped thirty points, and of six changed verdicts, five were genuine
> opportunities withheld, including `nixpkgs`. So we removed it. `verdict.py` is
> byte-identical to before that experiment, and the pre-registration stays in
> the repo with the failure appended, because a pre-registration quietly deleted
> when it fails is worse than none.
>
> What it taught us is the whole project in one line: **a pull request thread
> records the merge, not the conversation that produced it.** Mature projects
> look unreviewed because their review happens elsewhere.

**Last frame:** the repository URL and `REPRODUCTION.md`'s headline line —
*no API key, no token, no money.*

---

## If you run short

Add these back, in this order. Each is verified to work in replay with no key.

1. **What to look at next** (+20 s). From a report, **`n`**, type `epenet`,
   **`enter`**. Use `home-assistant/core`, not `nixpkgs`: `epenet` has five
   merged pull requests there touching 22 files, and the top rows read *names
   `config_flow.py` — work you have already touched*. The screen prints its own
   measured accuracy above the ranking, including the 95% interval
   `[−0.003, +0.132]` that spans zero. On `nixpkgs`, `mweinelt` overlaps **0 of
   198** open issues and every row says "no path overlap" — honest, and a much
   weaker frame.
2. **The models screen** (+12 s). **`ctrl+l`** from home: which provider answers
   for the product, priced by the name you picked it under, and never for a
   reported number.
3. **Copy the report** (+8 s). **`c`** on a report: the same markdown
   `holt analyze` writes to a file, so what you paste into an issue is the
   artefact rather than a transcription of the screen.

## Cut list, if you are over

Cut in this order. Everything below is expendable; nothing in §1, §3 or §5 is.

1. §2e's *what could not be determined* scroll (−10 s).
2. §2b, the finder (−25 s) — open on the plugin-hub assessment instead. This is
   the biggest single saving and the one that costs the most.
3. The F1-degeneracy aside in §3 (−15 s) — it is in the README either way.
4. The "measured over repositories" caveat in §3 (−12 s). **Cut this last** — it
   is the most honest sentence in the video, and honesty is the project's pitch.

## What must survive at any length

- The baseline's answer on `is-a-dev/register`, against Holt's, in the first
  minute.
- One execution a viewer could re-drive from the keyboard: a report, the trace
  behind it, and one evidence id opened.
- Both numbers in the final comparison, with the baseline arm beside them.
- The rubber-stamp rule named as the biggest contributor, with 0.58 → 0.83.
- The removed experiment named, with why it was removed.

## Keys used in this cut

Rehearse from this list alone. Nothing else is pressed on camera.

| Key | Where | Does |
|---|---|---|
| `↑` `↓` | home | move through RECENT; the line under the input says what `enter` will now do |
| `enter` | home | assess what is typed, or open the highlighted row |
| `esc` | home | clear the input **(press twice from a report: once to reach home, once to clear)** |
| `ctrl+t` | home | replay ⇄ live, and it says which |
| `ctrl+f` | home | the finder |
| `ctrl+l` | home | the models screen |
| `↓` `↓` `enter` | finder | choose *Replay the recorded example search* |
| `↓` (held) | finder | walk to the cut rows; the pane follows the highlight |
| `esc` | finder | home |
| `t` | report | the trace behind this report |
| `tab` | report | focus the claim list, so `↓` walks claims instead of scrolling |
| `enter` | report | open the evidence under the highlighted claim |
| `n` | report | what to look at next |
| `c` | report | the report as markdown, on the clipboard |
| `esc` | report / trace / inspector | one screen up |
| `ctrl+q` | anywhere | quit, naming any run still in flight |
