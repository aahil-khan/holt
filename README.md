# Holt

![Holt](assets/holt.png)

**Is this repository worth an outside contributor's week?**

Holt reads a GitHub repository the way a careful developer would after an
afternoon in its pull request threads, and produces an evidence-backed written
assessment. Every claim it makes carries an evidence id that resolves to a real
pull request, review or comment.

Named after Captain Holt: procedure, and refusing to state anything the evidence
does not support.

---

## Try it — no API key, no GitHub token, no spend

```sh
uv sync
PYTHONPATH=. uv run holt analyze NixOS/nixpkgs --replay              # one assessment
PYTHONPATH=. uv run python eval/harness.py --replay --run-tag run1   # the headline result, ~30s
```

Both run from committed evidence and committed model trajectories. Nothing is
fetched and no model runs.

To point it at a repository *you* care about, [USAGE.md](USAGE.md) is the whole
product in one page. The rest of this file is the argument and the measurement.

## Where everything is

| | |
|---|---|
| [USAGE.md](USAGE.md) | **start here if you want to use it**: install, ask about a repository, read the answer |
| [REPRODUCTION.md](REPRODUCTION.md) | every command, from a clean machine: tests, the headline result, both solutions, the pool draw, the labels |
| [docs/COMMANDS.md](docs/COMMANDS.md) | what each command does, and what the report says that GitHub does not |
| [docs/DESIGN.md](docs/DESIGN.md) | why this is a pipeline and not a prompt — and, measured, what that does *not* buy |
| [docs/EVALUATION.md](docs/EVALUATION.md) | the holdout, the pool, the labels, the sensitivities, the limitations |
| [CHANGELOG.md](CHANGELOG.md) | every iteration, including the experiments that were removed and the results that went against us — the whole story in one table at the top |
| [docs/CHANGELOG-FULL.md](docs/CHANGELOG-FULL.md) | the same log unabridged, with every evidence table as it was written on the day |
| [docs/INTERFACE-LOG.md](docs/INTERFACE-LOG.md) | the terminal interface's design history |

---

## Who this is for, and what it costs them today

A developer who wants to contribute to open source and has a week to spend.
Usually early in their career, for whom a wasted week is expensive.

Every signal GitHub surfaces measures **project health**, not **outsider
experience**, and those are different things. A domain registry with 40,000
merged pull requests, a curated links list, a read-only corporate mirror and a
genuinely welcoming software project are indistinguishable on stars, recency,
contributor count and open issues.

The only way to tell them apart today is to read twenty pull request threads per
repository, at roughly fifteen minutes each. Nobody does that, so people pick by
stars. **Stars are not useless** — on this pool the ten most-starred repositories
are 80% viable against a 51% base rate, and we say so because we measured it.
What stars cannot do is separate the registry, the mirror and the links list from
the software project, and that is exactly the population this tool exists for.
On the trap repositories — 100+ inbound attempts, zero qualifying
contributions — Holt rejects **4 of 5 in every run we have ever recorded**; the
baseline has scored anywhere from 0 to 3 of 5 depending on the day it was asked.

Two closed pull requests are the same integer in every GitHub statistic:

> "Thanks for this! Merged in #4821 — could you also look at the sibling case?"

> "We're rewriting this module internally, closing."

One says a newcomer can land work here. The other says don't bother.

---

## "Why not just paste it into ChatGPT?"

The fair answer is that **we measured that, and it is a scored arm in the
evaluation.** `baseline` is one prompt over the README and the repository
metadata, which is what a person actually pastes. `probe` is the repository name
alone with no evidence at all, which is what asking a chat model from memory
gets you.

| What you did | MCC (pool 1) | MCC (pool 2, out of sample) |
|---|---|---|
| Asked a model that already knows the repo, name only | 0.16 | 0.10 |
| **Pasted the README and the numbers into one prompt** | **0.09** | **0.21** |
| Ran Holt | **0.61** | **0.63** |

**The premise is where the work hides.** "The same GitHub information" is not
pasteable. Per repository, Holt assembles a median of **642 evidence records and
253,000 characters** across **200 pull-request conversations** — a **44×** ratio
against the ~11,900 characters of README, CONTRIBUTING and landing-page numbers a
person can realistically copy. Seeing it by hand means opening about **202
github.com pages**; across this evaluation, **11,636**. Reproduce with
`PYTHONPATH=. uv run python eval/evidence_volume.py`.

And the pasteable material is not a smaller sample of the same thing. It contains
**no review states, no reply latencies, and no record of what happened to anyone
who tried** — which is the entire question.

Four properties follow from being a pipeline rather than a conversation, none of
which a chat transcript has:

- **Provable claims.** Every statement carries an evidence id that resolves to a
  real thread, and every quotation is words that thread actually said — 9 claims
  across the committed runs quoted something it did not, and were dropped rather
  than softened (`eval/evidence_integrity.py`). A chat answer cannot be checked
  without redoing the work.
- **A bounded, honest horizon.** Every fact passes a cutoff assertion, so the
  answer cannot come from what the model remembers. We also bound what memory
  alone buys: **MCC 0.16**.
- **The same answer twice.** On the frozen runs Holt returned identical
  verdicts on **55 of 55** repositories across three runs per pool. The
  one-prompt baseline changed its answer on 16 of 55.
- **It says no.** A written, versioned rejection rule rather than an agreeable
  paragraph — and it is the one change that measurably improved accuracy
  (specificity 0.58 → 0.83, out of sample).

**What Holt is not is a better analyst.** We have measured four separate times
that the model layer adds little or nothing over arithmetic *on the verdict*,
and [docs/DESIGN.md](docs/DESIGN.md) publishes each one — with the correction
that on pool 2 removing it entirely costs 8 points of MCC, not the 1 the
in-sample ablation suggested. The value is in assembly, provability, determinism
and refusal: on the report rather than the verdict, the arithmetic writes
nothing at all.

---

## Result

Measured over two pools drawn and hash-committed **before any method ran**,
against ground truth computed only from evidence *after* a temporal holdout
neither method could see. Three independent live runs per pool, frozen
2026-08-31 on the shipped prompts and rules; every number below reproduces
from the committed recordings with no key and no spend. The design behind it —
holdout, sampling, labels — is in [docs/EVALUATION.md](docs/EVALUATION.md).

**Pool 1** (30 repositories, 22 gradable):

| Method | MCC | Balanced acc. | F1 | Sensitivity | Specificity |
|---|---|---|---|---|---|
| always answer "viable" | 0.00 ±0.00 | 0.50 | **0.78** | 1.00 | 0.00 |
| name-only probe (memorisation control) | 0.16 ±0.03 | 0.58 | 0.52 | 0.40 | 0.75 |
| baseline solution (one prompt over README + metadata) | 0.09 ±0.09 | 0.55 | 0.63 | 0.60 | 0.50 ±0.12 |
| **Holt** | **0.61 ±0.00** | **0.80 ±0.00** | 0.86 ±0.00 | 0.86 ±0.00 | 0.75 ±0.00 |

**Pool 2** (45 repositories, 33 gradable — drawn, labelled and held out *after*
every rule was written; genuine out-of-sample replication):

| Method | MCC | Balanced acc. | F1 | Sensitivity | Specificity |
|---|---|---|---|---|---|
| name-only probe | 0.10 ±0.02 | 0.55 | 0.47 | 0.35 | 0.75 |
| baseline solution | 0.21 ±0.02 | 0.61 | 0.60 | 0.49 | 0.72 ±0.04 |
| evidence-matched ablation (same evidence, one prompt) | 0.32 ±0.07 | 0.65 | 0.78 | 0.83 | 0.47 ±0.04 |
| **Holt** | **0.63 ±0.00** | **0.82 ±0.00** | 0.85 ±0.00 | 0.81 ±0.00 | **0.83 ±0.00** |

Mean and half-range over the three runs. **Holt's half-range is ±0.00 because
its verdicts were identical on all 55 repositories in all three runs** — the
verdict is a plain function over verified evidence, so re-running it moves
nothing. Per pool: identical verdicts on **22 of 22** pool-1 repositories, where
the baseline — which puts the whole decision inside one model call — manages
**17 of 22**.

**Those intervals measure the wrong thing, and we are saying so.** ±0.00 is how
much the model wobbles between runs; it is not how much a 22-repository sample
can tell you. Measured over repositories instead — bootstrap resampling, 20,000
draws, pool 1 — the Holt−baseline difference is **+0.42 to +0.59 with
`P(difference ≤ 0)` = 0.04–0.08, and a 95% interval that still touches zero**.
Exact McNemar gives p = 0.15–0.23. At this sample size the aggregate gap is
large but not formally distinguishable, and we print that rather than round it
up. Run `PYTHONPATH=. uv run python eval/stats.py` to see it.

- **Trap rejection — including the part that got worse for us.** Repositories
  with 100+ inbound outsider attempts and zero qualifying contributions: Holt
  rejects **4 of 5 in every run** (it has never caught `hermes-agent`). When
  this was first measured, the baseline rejected 0 of 5 (Fisher exact
  p = 0.048); on the frozen re-runs the baseline rejected **2–3 of 5**, so that
  significance claim did not survive re-measurement and we are retiring it
  rather than citing the old number. What remains is the stable version: Holt
  4/5 every time, a baseline that wanders between 0 and 3 depending on the day.
- **Positive control.** Three verified-genuine repositories outside the pool:
  Holt recovers 3 of 3, the baseline 1 of 3.

**The constant answers are in that table on purpose.** F1 was this project's
original primary metric, and on a pool that is 64% positive it is degenerate:
answering "viable" to everything scores **F1 0.78**, beating our own baseline
solution. We found that by attacking our own metric before shipping it, and the
row stays in so a reader can see the floor rather than take our word for it.

Matthews correlation is the honest headline, because it is **0.00 for any
constant strategy**. Holt reaches 0.61 against the baseline's 0.09 in sample
and **0.63 against 0.21 out of sample** — and the out-of-sample gap is the
wider one, because pool 2 skews toward quieter repositories where a README
tells you nothing.

**Where the advantage is now.** Earlier versions of this table showed Holt
over-recommending: specificity 0.50, a coin flip on ordinary repositories. The
pre-registered rubber-stamp rule — *contributions land easily and nobody
reviews them* — was written against pool 1, predicted numerically, then tested
once on pool 2: specificity moved to **0.75 in sample and 0.83 out of sample**
at a cost of a few points of sensitivity (0.86/0.81 against 0.90 before),
exactly the trade the pre-registration predicted. The ablation row shows what
it is worth: given the identical evidence in one prompt, specificity is 0.47.
The rule is the difference between flagging a registry and recommending it.

**Positive control.** A detector that answers "not viable" to everything would
reject every trap in the table above and look excellent doing it. So three
repositories nobody would dispute — `home-assistant/core` (152 qualifying
contributions from 62 people after the cutoff), `rust-lang/rust` (66 from 44) and
`astral-sh/uv` (35 from 13) — are assessed as a declared, hand-picked control,
separate from the scored pool.

| | Recovered |
|---|---|
| **Holt** | **3 / 3** |
| baseline solution | 1 / 3 |

The baseline calls `home-assistant/core` and `astral-sh/uv` *insufficient
evidence*, because their READMEs do not advertise how contributable they are.
That is the failure this project is about, in the positive direction.

**What the result depends on.** Ground truth counts an outsider merge only if the
diff is *substantive* and a human *reviewed* it. Both filters are ours, and
dropping the diff-shape one narrows Holt's lead from +0.61 to +0.39 — against a
baseline that rises to +0.28. The full sensitivity table, and the limitations
that go with it, are in [docs/EVALUATION.md](docs/EVALUATION.md).

---

## How it works

```
pre-cutoff evidence ──┬─► signals          arithmetic, no model
                      ├─► A classify       what kind of repository is this?
                      ├─► B opportunity    is there a real route in?
                      ├─► C outcomes       what happened to people who tried?
                      │        │
                      │   typed findings, each carrying evidence ids
                      │        │
                      │   D verify         drop any finding whose evidence
                      │        │           does not resolve
                      └────────┴─► verdict.py   a plain function, no model
                                       │
                                  E narrate     prose around a verdict it
                                                cannot change
```

Two consequences are worth stating here, because the rest of the argument rests
on them:

- **The model never owns the decision.** `src/holt/agent/verdict.py` is the only
  path from findings to a verdict and runs no model — which is why re-running
  moves nothing, and why asking a different question (`--days 3` against
  `--days 90`) costs zero model calls.
- **Verification can only subtract.** Stage D resolves every evidence id a
  finding cites and drops what does not resolve.

[docs/DESIGN.md](docs/DESIGN.md) gives the four things the split buys, each with
its measurement — and then, at the same length, what it does not: the +0.01 MCC
the model stages add over arithmetic on the verdict, the 11.8 checkable
statements per report they add where arithmetic writes 0, the ablation that
ships as `--no-model`, and Path Finder, which shipped losing to GitHub's own
`good first issue` label.

## What you get out

An assessment for one repository, a shortlist compared side by side
(`holt compare`), a candidate list built from a stated profile
(`holt discover`), and a ranking of open issues for someone who has already
landed work there (`holt next`). Each is shown with real output in
[docs/COMMANDS.md](docs/COMMANDS.md).

The part GitHub cannot give you, in one example — `NixOS/nixpkgs`, counted from
the file lists of the pull requests Holt read:

> - **`pkgs/by-name`** — 13 merged of 62 attempted (21%)
> - **`pkgs/top-level`** — 3 merged of 11 attempted (27%)
>
> Outsiders attempted these and none were merged: `maintainers/maintainer-list.nix`
> (11), `pkgs/applications` (6), `pkgs/build-support` (6), `doc/release-notes` (2).

In a tree of that size, that is where a stranger's week has a chance and where it
does not.

---

## Read-only, and about time rather than people

Holt never writes to GitHub, opens pull requests, or contacts maintainers. It
reads public data only.

Its verdicts are about **fit for a contributor's time**, not maintainer quality.
A repository can be excellent and still be a poor place to spend your first week.
Every negative claim links to the evidence behind it, so a maintainer who
disagrees can point at the same thread and say why. There is no ranking of
projects by how welcoming their maintainers are, and none should be inferred.

---

## The main failure mode, and the hot take

**The failure mode: nothing was watching whether a published claim was still
true.** Every guard in this project points at the agent — the holdout is
asserted on every record, Stage D drops a citation that does not resolve, replay
refuses a recording whose prompt moved — and each is covered by a test. None of
them guarded the prose. So a number stayed on this page after the run behind it
was redone, and this repository stated its own verdict stability three different
ways at once. Worse, `holt analyze <repo> --baseline --replay` — documented, and
the competition's required baseline arm — failed from a clean clone on every
repository, because baseline calls were recorded only where the harness looks
and the benchmark therefore never noticed. The evaluation and the documented
product path had drifted apart, and only the evaluation was tested.
`tests/test_docs_claims.py` now recomputes the numbers on this page from the
committed results and runs every command the guide prints.

**The hot take: Holt is not a smarter analyst, and we measured that four separate
times.** One prompt handed the same evidence matches the model stages almost
exactly; ablating Stage A's kind rules costs +0.01 MCC. What separates this from
a chat window is duller than intelligence and harder to fake — an evidence
assembly nobody will do by hand (642 records and 253,000 characters per
repository, 44× what a person can paste), and then three properties a
conversation structurally cannot have: every claim carries an id that resolves,
the verdict is a plain function that returned the identical answer on 55 of 55
repositories while the baseline moved on 16, and it can say *no* in a rule the
model cannot override — the single change that most improved accuracy
(specificity 0.58 → 0.83 out of sample).

**What we would build differently:** put the decision in code and the model in
front of the evidence, not the other way round — then spend what that saves on
the boring half, because an agent's guarantees are worth exactly as much as the
tests on the claims you make about them.

The full story, iteration by iteration: [CHANGELOG.md](CHANGELOG.md).
