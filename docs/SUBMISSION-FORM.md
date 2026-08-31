# Submission form — everything, in the order the form asks for it

Four fields: **Title**, **Description**, **Video URL**, **Source Code**.
Everything below is final text. Paste it; do not rewrite it under time pressure.

Every number in the Description is in `README.md` and reproduces from the
committed recordings. Verified against `main` on 2026-08-31.

---

## 1. Title *

```
Holt — is this repository worth an outside contributor's week?
```

---

## 2. Description *

The field accepts formatting and links, so paste this as markdown. The
repository URL appears in the first line **and** the last line on purpose — a
judge who reads two lines and a judge who scrolls to the bottom both get it.

> Full repository (public, `main` fully pushed):
> **https://github.com/aahil-khan/holt**
>
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
> The uploaded zip omits `fixtures/post_t/` — the label-side evidence — to fit
> the 50 MB limit. The headline result above does not read it. The five scripts
> that do are named in `REPRODUCTION.md` §6; clone the repository for those.

---

## 3. Video URL *

```
PASTE YOUR VIDEO URL HERE
```

Before pasting, check three things:

- [ ] **It plays in a private window.** Unlisted is fine; "anyone with the link"
      is fine; *restricted* fails silently for judges.
- [ ] **It is 5:00 or under.** The brief caps it.
- [ ] The recording shell had no credentials in it
      (`env -u OPENAI_API_KEY -u GITHUB_TOKEN`).

---

## 4. Source Code * — upload, max 50 MB

Upload this file:

```
holt-submission.zip   (built by the command below; kept outside the repo)
```

**22 MB**, 854 files — under the cap with room to spare. It extracts into a
single `holt/` directory, so a judge who unzips it in Downloads gets one folder
rather than 854 loose files, and `cd holt` in `REPRODUCTION.md` works as written.

Verified from the archive alone, not assumed. Extracted into a clean directory,
then run inside the extracted `holt/`:

| Check | Result |
|---|---|
| `uv sync` | succeeded |
| `uv run pytest -rs` | **298 passed, 1 skipped** — exactly what `REPRODUCTION.md` §2 says to expect after a plain `uv sync` (the skip is the optional `tui` extra, and the doc names it) |
| `PYTHONPATH=. uv run python eval/harness.py --replay --run-tag run1` | **holt MCC 0.61**, balAcc 0.80, F1 0.86, sens 0.86, spec 0.75 — the published pool-1 row, in about a second |
| `fixtures/post_t/` entries | 0 — the deliberate omission |
| `fixtures/pre_t/` entries | 74 — what the headline result actually reads |
| credential-shaped strings in the archive | none — only redacted placeholders (`sk-1af878XXX…`) and the deliberate test fixture |

sha256 `bffe8234d297255c9df5bcc6644a0d39d32222fc4898283008ca2b843f8f3a96`.

To rebuild it if anything changes — note the staging step, which is what puts
everything under a top-level `holt/`:

```sh
git ls-files | grep -v '^fixtures/post_t/' > /tmp/holt-files.txt
rm -rf /tmp/holt-stage && mkdir -p /tmp/holt-stage/holt
rsync -a --files-from=/tmp/holt-files.txt ./ /tmp/holt-stage/holt/
(cd /tmp/holt-stage && zip -9 -X -qr holt-submission.zip holt)
```

**Rebuild it if you commit anything else.** The first build of this archive
predated two doc commits and silently carried a stale checklist; the file count
is the tell.

---

## Before you hit Submit

- [ ] **Rotate the GitHub PAT and the OpenAI key.** Ground rule 08. They
      appeared in working sessions; a scrub keeps them out of the repository,
      but rotation is the only thing that actually closes it. This is the one
      item on the checklist with no code change behind it and no substitute.
- [ ] Video URL opens in a private window.
- [ ] Zip attached and the upload finished (not just queued).

## Known gap, if a judge asks

**Human time per task** — the brief's evaluation table has three rows. Primary
outcome and cost per task are measured and published ($0.012/repo live, $0.00
replay). Human time is not: the protocol is fixed and committed in
`eval/HUMAN-TIME-PROTOCOL.md`, and it has never been run, so the project does
not claim a number. Saying that is better than estimating one — the whole
argument here is that an untested claim is not a claim.
