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
| 01 | Complete solution code + **Improvement Changelog** | **Done.** `CHANGELOG.md` is titled *Improvement Changelog* and opens with *The story in one table* — 14 rows, baseline through final, each giving what was tried, the evidence and the decision, in exactly the shape the brief's example asks for. Iterations 1–32 follow in full, including five removed experiments. Failure mode and hot take are at the end, as the brief asks. |
| 02 | Reproduction guide | **Done.** `REPRODUCTION.md` — clean machine, exact commands, versions, runtimes, costs, and which sections need the full clone rather than the zip. Verified: full suite is **383 passed** in 130 s. |
| 03 | Solution video, ≤ 5 min | **Being recorded.** Script and shot list: [`VIDEO-SCRIPT.md`](VIDEO-SCRIPT.md). |
| 04 | Agent trajectories for **every agent you used** | **Done.** One readable trajectory per prompted agent, plus the raw record for all of them. See §3 below. |

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
the zip contains. Of the two things that had to happen so the omission reads as
a decision rather than an accident:

1. ✅ **Done.** `REPRODUCTION.md` now names, at the top and again at §6, exactly
   which sections need the full clone and why the zip omits those fixtures.
2. ⬜ Put the repository URL in the submission's Description field, above the
   fold. §6 below is written that way already.

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

## 3. Trajectories — one readable file per prompted agent

Deliverable 04: *representative trajectories for **every agent you used**, easy
to follow from the agent instructions to the final result.*

**Coverage is complete in both forms.** `fixtures/trajectories/` holds every
model call the project ever made, with the full system prompt, prompt, response
and token usage. The benchmark directories carry all seven scored labels for all
22 pool-1 repositories:

```
baseline 22   baseline_matched 22   name_only 22
classify 22   opportunity 22        outcomes 22   narrate 22
```

**And each of them now has a reading copy** in `trajectories/`, generated by
`scripts/render_trajectories.py`:

| File | Agents covered |
|---|---|
| three pipeline walkthroughs (`is-a-dev/register`, `NixOS/nixpkgs`, `SecureBananaLabs/bug-bounty`) | `classify`, `opportunity`, `outcomes`, `narrate`, plus Stage D verification and the verdict function |
| `comparison-arms--is-a-dev__register.md` | `name_only`, `baseline`, `baseline_matched` — all three on the case where they part company with Holt |
| `pathfinder--NixOS__nixpkgs.md` | `pathfinder` |
| `profile--home-assistant__core__epenet.md` | `profile` |

The one prompted function with no trajectory is `describe()`
(`src/holt/agent/progression.py`): it has no recorded calls because the model
call it wraps moved 0 of 88 rankings when measured and was cut, so `holt next`
runs no model at all. `trajectories/README.md` says so rather than leaving a
reader to wonder.

**Retries and human checkpoints are answered explicitly**, in
`trajectories/README.md`: output shape is enforced by a strict JSON schema so
there is no re-prompt loop, the only retries are transport-level
(`max_retries = 4`) and never produce a second answer to the same question, and
a finding whose evidence does not resolve is dropped by Stage D rather than
re-asked. There is no mid-run approval step because Holt takes no consequential
action — the human decisions are what to ask, whether to spend anything
(`--replay`, `--no-model`), the cap on full analyses in a discovery session, and
reading the evidence before committing a week.

**Rendering them found a bug**, which is in the changelog as iteration 35: the
*Where outsider work landed* section ordered tied rows by set-iteration order, so
it varied with the process hash seed. Fixed, with a test that renders the tied
case in three subprocesses at different seeds.

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
| 08 | **Credentials outside the submission** | ⚠️ **Open.** A scrub runs before the content hash and a test fails on any credential-shaped string in any fixture — good. But the self-assessment (kept outside the repository) records that the PAT and the OpenAI key appeared in working sessions and lists rotating both as open. **Rotate them.** Also record the recording shell for the video with `env -u OPENAI_API_KEY -u GITHUB_TOKEN`. |
| 09 | Every claim connected to evidence | ✅ This is the project. `tests/test_docs_claims.py` recomputes the documented numbers and runs every command the guide prints. |
| 10 | Judges can run it and reproduce the main result | ✅ via the public repo — see §1 for the zip caveat. |

---

## 5. Judging rubric (p.05) — where the points are

The self-assessment (kept outside the repository) §5b already walks this honestly. Two notes that bear on what is
left to do rather than on what is written:

- **End to End Quality (20)** — *"would the intended user consider this high
  quality, or does it read as clearly AI generated?"* The one gap the
  self-assessment names as not ours to close is that **nobody outside the project has read a
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
2. **Human-time study** (~50 min) — [`../eval/HUMAN-TIME-RUNBOOK.md`](../eval/HUMAN-TIME-RUNBOOK.md).
3. **Three-row metric table** into `README.md` (~10 min, needs step 2).
4. **Build and test the 22 MB zip** (~15 min) — §1.
5. **Record the video** — [`VIDEO-SCRIPT.md`](VIDEO-SCRIPT.md). *(In progress.)*
6. **Re-run `uv run pytest -rs`** after all doc edits. `test_docs_claims.py`
   recomputes README numbers, so new tables can break the build. That is the
   guard working.
7. Paste §6 into the form, upload the zip, submit.

Done since this list was written: the baseline and other-arm trajectories (§3),
the clone-vs-zip note in `REPRODUCTION.md` (§1), and a framing pass over
`README.md` that leads with the measured result and keeps the self-assessment in
the failure-mode and hot-take sections the brief asks for.
