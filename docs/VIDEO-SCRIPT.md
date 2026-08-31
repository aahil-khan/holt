# Solution video — script and shot list

**Target: 4:45. Hard cap: 5:00.** The brief (Final deliverables, item 03) asks
for five things, in this order: the problem and the simple baseline, one
realistic execution start to finish, the final comparison, a brief walk of the
changelog, and — named explicitly — *the change that contributed most* and *one
experiment you removed*. Every one of those has a labelled beat below. If you
run long, cut from §2, never from §5.

Narration is written to be read at ~150 words per minute. Word counts are given
per beat so you can check pace without a stopwatch.

---

## Before you record

| | |
|---|---|
| Terminal | 110×32 or wider, font ≥ 18pt. Judges watch this at 720p in a browser tab. |
| Environment | `env -u OPENAI_API_KEY -u GITHUB_TOKEN` in the recording shell. Everything below replays; nothing needs a key, and no credential should ever be on screen (**ground rule 08**). |
| Pre-warm | Run every command once before recording. `uv` resolves the environment on first invocation and that pause is dead air. |
| Prompt | Set `PS1='$ '`. A prompt with your hostname and path in it is noise. |
| Working dir | A fresh clone, so what the judges see is what they get. |
| Screen | Editor and browser closed. One terminal, one browser tab for §3 if you show the tables. |

Commands are typed live but **pre-typed into a scratch file and pasted** — typos
cost ten seconds each and you have none to spare.

---

## §1 — The problem, and the baseline (0:00 → 1:05, ~160 words)

**Screen:** two GitHub PR threads side by side, then the terminal.

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
>
> So here is the baseline — the thing a person actually does. One prompt, over
> the README and the repository metadata. This is `is-a-dev/register`: a domain
> registry, forty thousand merged pull requests, none of them software.

**Type:**

```sh
PYTHONPATH=. uv run holt analyze is-a-dev/register --baseline --replay
```

> It says viable. It is a text file where you add one line with your name on it.

**Beat.** Let the word "viable" sit on screen for a second before you move.

---

## §2 — One realistic execution, start to finish (1:05 → 2:50, ~250 words)

This is the required "one realistic execution." Run the whole arc of a
contributor's week, but keep it moving — one sentence per command, and let the
output do the talking.

**Type:**

```sh
PYTHONPATH=. uv run holt discover
```

> Same user, no shortlist yet. `discover` sources candidates from GitHub search
> against a stated profile — languages, topics, how many days you actually
> have — and screens them. Screening is free: the verdict rule needs exactly one
> model-derived input, so every rejection here runs as arithmetic at zero cost.
> Twenty-five candidates in, nine rejected, and it says *why* each one went:
> nobody outside has landed work here, attempts went unanswered, work merged
> without review.

```sh
PYTHONPATH=. uv run holt compare runelite/plugin-hub NixOS/nixpkgs is-a-dev/register stablyai/orca --replay
```

> Four survivors side by side. Look at the first row. `runelite/plugin-hub`:
> seventy of a hundred and one outsiders merged, first reply in four hours. It
> is the best-looking project on this list and it is rejected — and the `why`
> column is the rule that fired, not a summary of the prose.

```sh
PYTHONPATH=. uv run holt analyze runelite/plugin-hub --replay
```

> Now read one properly. Five stages: classify the repository, find the route
> in, read what happened to people who tried, verify, narrate. Verification
> resolves every evidence id a finding cites and drops what does not resolve.
>
> The verdict itself is not the model's. It is a plain function over verified
> evidence — the report prints the rule that decided it, and re-asking at a
> different time budget, `--days 90`, costs zero model calls.
>
> Every claim carries an id. That id opens a real thread. And where the evidence
> could not answer something, there is a section that says so.

```sh
PYTHONPATH=. uv run holt next NixOS/nixpkgs --as mweinelt
```

> And once you have landed something, `next` ranks the open issues by one
> deterministic rule — and prints its own measured accuracy above the ranking,
> including the confidence interval that spans zero.

---

## §3 — The final comparison (2:50 → 3:45, ~140 words)

**Screen:** the README result tables. Running `eval/harness.py --replay` live
takes about 30 s, which you do not have. **Show the tables.**

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

## §4 — The changelog, briefly (3:45 → 4:05, ~55 words)

**Screen:** scroll `CHANGELOG.md` — fast, so the shape registers. Twenty-eight
iterations, each with a date, a table, and a decision.

> Twenty-eight iterations. Every one has the evidence that produced it and the
> decision it led to, written on the day — including five capabilities we cut,
> and a significance claim we retired when it failed to re-measure. Two of those
> entries matter most, and they are the same method with opposite results.

---

## §5 — The change that contributed most, and the one we removed (4:05 → 4:45, ~110 words)

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

---

## §6 — The hot take (4:45 → 5:00, ~40 words)

> Our hot take is that Holt is **not** a smarter analyst, and we measured that
> four separate times. One prompt handed the same evidence nearly matches our
> model stages. What separates this from a chat window is duller and harder to
> fake: an evidence assembly nobody will do by hand — six hundred records per
> repository, forty-four times what a person can paste — and then three
> properties a conversation cannot have. Every claim carries an id that
> resolves. The verdict is a function, not an opinion. And it can say *no*.

**Last frame:** the repository URL and `REPRODUCTION.md`'s headline line —
*no API key, no token, no money.*

---

## Cut list, if you are over

Cut in this order. Everything below is expendable; nothing in §1, §3 or §5 is.

1. `holt next` in §2 (−15 s) — it is the weakest claim in the arc anyway.
2. `holt discover` in §2 (−20 s) — start at `compare` with the shortlist given.
3. The F1-degeneracy aside in §3 (−15 s) — it is in the README either way.
4. The "measured over repositories" caveat in §3 (−12 s). **Cut this last** — it
   is the most honest sentence in the video, and honesty is the project's pitch.

## What must survive at any length

- The baseline runs, on screen, and gets `is-a-dev/register` wrong.
- One full execution that a viewer could re-type.
- Both numbers in the final comparison, with the baseline arm beside them.
- The rubber-stamp rule named as the biggest contributor, with 0.58 → 0.83.
- The removed experiment named, with why it was removed.
