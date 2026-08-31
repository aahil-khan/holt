# Submission checklist — what the brief asks for, and where we stand

Checked against `docs/Problem Statement.pdf` (Final deliverables p.07, Ground
rules p.06, How to evaluate p.04, How judging works p.05) and the submission
form itself.

Verified on 2026-08-31 against `main`. Everything marked **verified** was
actually run, not read off a document.

---

## The four required deliverables

| # | Deliverable | Status |
|---|---|---|
| 01 | Complete solution code + **Improvement Changelog** | **Done.** `CHANGELOG.md` is titled *Improvement Changelog* and opens with *The story in one table* — 14 rows, baseline through final, each giving what was tried, the evidence and the decision, in exactly the shape the brief's example asks for. Iterations 1–28 follow in full, including five removed experiments. Failure mode and hot take are at the end, as the brief asks. |
| 02 | Reproduction guide | **Done.** `REPRODUCTION.md` — clean machine, exact commands, versions, runtimes, costs. Verified: full suite is **364 passed** in 113 s. |
| 03 | Solution video, ≤ 5 min | **Not started.** Script and shot list: [`VIDEO-SCRIPT.md`](VIDEO-SCRIPT.md). |
| 04 | Agent trajectories for **every agent you used** | **Substantially done, one gap.** See §3 below. |

---

## 1. BLOCKER — the source-code zip is over the 50 MB limit

The form says *"Upload your source code (e.g. zip or apk). **Max 50MB**."*

Measured, not estimated:

| Archive | Size |
|---|---|
| all 920 tracked files, `zip -9` | **54 MB** — over the cap |
| `git archive --format=zip HEAD` | 54.5 MB |
| the same, minus `fixtures/post_t/` | **22 MB** |

`fixtures/post_t/` is 74 files and about 32 MB of the compressed total. It is
the **label-side** evidence — the post-cutoff records ground truth is computed
from.

**What actually needs it.** The headline result does not:
`eval/harness.py --replay` scores against the committed
`eval/results_labels*.json`, and reads no `post_t` fixture. What does read it:

- `eval/run_labels.py` — REPRODUCTION §6, recomputing L0 and L1
- `eval/sensitivity.py` — the ground-truth sensitivity table
- `eval/run_l0.py`, `eval/pathfinder_harness.py`, `eval/progression_harness.py`

**Recommendation: upload the 22 MB zip and point at the public repository for
the rest.** `github.com/aahil-khan/holt` is **public** (verified) and `main` is
fully pushed, so ground rule 10 — *give judges enough access to run the project
and reproduce the main result* — is satisfied by the clone regardless of what
the zip contains. But do these two things or the omission reads as an accident:

1. Add a short note at the top of `REPRODUCTION.md` naming exactly which
   commands need the full clone and why the zip omits those fixtures. A stated
   omission is a decision; a silent one is a broken repro step.
2. Put the repository URL in the submission's Description field, above the fold.

Build the zip with:

```sh
git ls-files | grep -v '^fixtures/post_t/' | zip -9 -X holt-submission.zip -@
```

Verify it lands under 50 MB before you upload, and unzip it into a scratch
directory and run `uv sync && uv run pytest -rs` there once. The whole project's
argument is that a claim you did not test is a claim you do not have.

---

## 2. BLOCKER — human time per task has no number

The brief's evaluation table (p.04) has three rows. Two are measured and
published; this one is not.

| Row | Status |
|---|---|
| Primary outcome | **Measured.** MCC, two pools, three runs each. |
| **Human time per task** | **Missing.** Protocol written, never executed. |
| Cost per task | **Measured.** $0.012/repo live, $0.00 replay, in `REPRODUCTION.md`. |

`eval/HUMAN-TIME-PROTOCOL.md` fixes the design and was committed before any
timing. It has never been run, so nothing in the project answers *how much time
does this save*, which is the question the brief names.

Mechanics: [`../eval/HUMAN-TIME-RUNBOOK.md`](../eval/HUMAN-TIME-RUNBOOK.md).
About 50 minutes, and only you can do it.

**Also missing: the three-row summary table itself.** The brief offers that
format and says to propose your own rubric if it fits poorly. The project's
tables are richer and better suited — but a reader looking for the brief's
format finds no single place with all three numbers side by side. Add one to
`README.md` near the Result section, five lines, pointing at the detailed tables
below it. The runbook has the skeleton.

---

## 3. Trajectories — complete in raw form, incomplete in readable form

Deliverable 04: *representative trajectories for **every agent you used**, easy
to follow from the agent instructions to the final result.*

**Coverage is complete.** Verified across `fixtures/trajectories/run1/` — all
seven model-driven arms are recorded with full system prompt, prompt, response
and token usage:

```
baseline 22   baseline_matched 22   name_only 22
classify 22   opportunity 22        outcomes 22   narrate 22
```

**Readability is not.** The three rendered walkthroughs in `trajectories/` cover
the five pipeline stages end to end — evidence retrieved, each stage's question
and answer, what verification dropped, how the rule produced the verdict. They
cover **none of** `baseline`, `baseline_matched` or `name_only`, which are
scored arms in the headline table and, in the baseline's case, the thing the
video opens on.

**Fix, ~20 minutes.** Render one baseline trajectory for `is-a-dev/register` —
the disagreement case, where the baseline says viable and Holt says not viable.
`scripts/render_trajectories.py` already exists; the records are already
committed. It is the single most persuasive trajectory in the repository and it
is currently only readable as JSONL.

While there, add one line to `trajectories/README.md` stating that the raw
records cover all seven arms. Right now a judge checking "every agent" against
the three rendered files concludes two arms are undocumented, and they are not.

---

## 4. Ground rules (p.06)

| | Rule | Status |
|---|---|---|
| 01 | Build with tools you know | ✅ |
| 02 | Clear what existed before vs. what you added | ✅ [`EVALUATION.md`](EVALUATION.md) *Provenance*: everything written during the competition except `docs/Problem Statement.pdf`. |
| 03 | Licenses and service terms | ✅ Public GitHub data, read-only, zero-scope token. |
| 04 | Consequential actions sandboxed / human-approved | ✅ **Structurally**: Holt never writes to GitHub, opens PRs or contacts maintainers, and it is stated in the README and CLAUDE.md. Worth one sentence in the video — a judge scoring this row should not have to hunt. |
| 05 | Qualified human reviewer where it affects someone | ✅ Verdicts are about fit for a contributor's time, not maintainer quality; every negative claim links to evidence a maintainer can contest. Already in the README. |
| 06 | Legal and ethical use case | ✅ |
| 07 | Data you are allowed to share | ✅ Public data only. |
| 08 | **Credentials outside the submission** | ⚠️ **Open.** A scrub runs before the content hash and a test fails on any credential-shaped string in any fixture — good. But `ASSESSMENT.md` records that the PAT and the OpenAI key appeared in working sessions and lists rotating both as open. **Rotate them.** Also record the recording shell for the video with `env -u OPENAI_API_KEY -u GITHUB_TOKEN`. |
| 09 | Every claim connected to evidence | ✅ This is the project. `tests/test_docs_claims.py` recomputes the documented numbers and runs every command the guide prints. |
| 10 | Judges can run it and reproduce the main result | ✅ via the public repo — see §1 for the zip caveat. |

---

## 5. Judging rubric (p.05) — where the points are

`ASSESSMENT.md` §5b already walks this honestly. Two notes that bear on what is
left to do rather than on what is written:

- **End to End Quality (20)** — *"would the intended user consider this high
  quality, or does it read as clearly AI generated?"* The one gap `ASSESSMENT.md`
  names as not ours to close is that **nobody outside the project has read a
  report**. If you can get one developer to read one assessment and say whether
  they would act on it, that is a bigger marginal gain than any remaining code
  change. It costs one message to one person.
- **Measured Improvement (15)** — the brief asks for *"ten or more cases"*, *"one
  challenging case"*, and an explanation of what it revealed. 22 and 33 gradable
  cases ✅. Challenging cases are documented and unresolved in our favour, which
  is the right way to have them: `hermes-agent` (the trap Holt has never caught)
  and `Homebrew/homebrew-cask` (a genuine disagreement with the label, neither
  side tuned to agree) — both in [`EVALUATION.md`](EVALUATION.md) *Known
  limitations*. Make sure at least one of these is spoken aloud in the video — a
  project that names the case it still gets wrong reads differently from one
  that does not.

---

## 6. Ready to paste into the form

**Title**

```
Holt — is this repository worth an outside contributor's week?
```

**Description** (the field takes formatting and links)

> **Who has the problem.** A developer with one week to spend on open source,
> usually early in their career, for whom a wasted week is expensive.
>
> **The bottleneck.** Every signal GitHub surfaces — stars, recency, contributor
> count, open issues — measures *project health*, not *outsider experience*. A
> domain registry with 40,000 merged pull requests, a read-only corporate mirror
> and a genuinely welcoming project are indistinguishable on all of them. The
> only way to tell them apart is to read ~20 pull request threads per repository
> at ~15 minutes each, so nobody does, and people pick by stars.
>
> **What Holt does.** Assembles a median of 642 evidence records and 253,000
> characters across 200 pull-request conversations per repository — 44× what a
> person can realistically paste into a chat window — then runs five stages over
> it: classify, find the route in, read what happened to people who tried,
> verify every citation, narrate. The verdict itself is a plain function over
> verified evidence and runs no model.
>
> **Result.** Two pools, hash-committed before any method ran, ground truth
> computed only from evidence after a temporal holdout neither method could see,
> three independent runs each.
>
> | Method | MCC (pool 1) | MCC (pool 2, out of sample) |
> |---|---|---|
> | one prompt over README + metadata (the baseline) | 0.09 | 0.21 |
> | **Holt** | **0.61** | **0.63** |
>
> Holt returned identical verdicts on 55 of 55 repositories across every run;
> the baseline changed its answer on 16. Measured over repositories rather than
> runs, the 95% interval still touches zero, and we print that rather than round
> it up.
>
> **The change that contributed most** is a pre-registered rejection rule — a
> repository where contributions land *easily* and nobody reviews them is a
> place a stranger's work gets waved through into something unmaintained.
> Written down with three numeric predictions, tested once on the second pool:
> specificity 0.58 → 0.83 out of sample, all three predictions held.
>
> **Our hot take** is that Holt is not a smarter analyst, and we measured that
> four separate times: one prompt handed the same evidence nearly matches our
> model stages. What separates it from a chat window is duller and harder to
> fake — an evidence assembly nobody will do by hand, every claim carrying an id
> that resolves, a verdict that is a function rather than an opinion, and the
> ability to say *no*.
>
> **Reproduce the headline result with no API key, no GitHub token and no
> money**, in about 30 seconds:
>
> ```
> git clone https://github.com/aahil-khan/holt && cd holt && uv sync
> PYTHONPATH=. uv run python eval/harness.py --replay --run-tag run1
> ```
>
> Full repository (including the label-side evidence fixtures omitted from the
> zip for the 50 MB limit): https://github.com/aahil-khan/holt

Read it once before pasting. Every number in it is in the README and reproduces;
if any of them has moved by submission time, fix it here too.

---

## 7. Do these in this order

1. **Rotate both tokens.** Independent of everything else, and easy to forget
   once the deadline pressure starts.
2. **Commit the in-flight TUI work**, or stash it. Ten files are modified in the
   working tree; the zip and any fresh clone will not contain them, and a
   half-committed interface is the kind of thing that makes a repro step fail
   for a judge and nobody else.
3. **Human-time study** (~50 min) — [`../eval/HUMAN-TIME-RUNBOOK.md`](../eval/HUMAN-TIME-RUNBOOK.md).
4. **Three-row metric table** into `README.md` (~10 min, needs step 3).
5. **Render the baseline trajectory** (~20 min) — §3.
6. **Build and test the 22 MB zip** (~15 min) — §1.
7. **Record the video** — [`VIDEO-SCRIPT.md`](VIDEO-SCRIPT.md).
8. **Re-run `uv run pytest -rs`** after all doc edits. `test_docs_claims.py`
   recomputes README numbers, so new tables can break the build. That is the
   guard working.
9. Paste §6 into the form, upload the zip, submit.
