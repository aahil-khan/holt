# Pre-registration 4 — contesting `repo_kind`

Written **before** the rule below was run against any repository. Pool 1 was
used to choose the thresholds and that fitting is disclosed here; pool 2 is
out-of-sample and is not consulted until the predictions below are recorded.

## The problem

`repo_kind` is the only model-derived field that can decide a verdict on its
own. Two rules in `verdict.py` act on it before anything else is considered:

    repo_kind in CLOSED_KINDS       -> not_viable  ("outside pull requests are
                                                    not the contribution path")
    repo_kind in NON_SOFTWARE_KINDS -> not_viable  ("merged work here is not a
                                                    software contribution")

Stage D cannot check either. It verifies that a cited id *resolves*; a
classification is not a quotation, and a model that says `mirror` while citing a
real README has produced a claim that verifies perfectly and is false.

Observed on 2026-08-31, running under `llama3.2` via Ollama:

* `aden-hive/hive`, a software project, was classified `registry`.
* `pytorch/pytorch` was classified a *mirror of pytorch/pytorch*, with the
  advice to "contribute upstream at github.com/pytorch/pytorch".

Both produced a confident `not_viable`. Neither is a threshold problem or a
prompt problem: they are the absence of any check at all on a field that decides
the answer by itself.

## The rule

Both verdict-flipping kinds justify themselves with a claim about something we
already crawl. Contest the *consequence*, not the label — do not adjudicate what
a repository "really is", only whether the reason the rule gives for refusing it
survives contact with the evidence.

**K1 — catalogue kinds** (`registry`, `awesome_list`). The stated reason is that
merged work here is a catalogue entry rather than software. A catalogue entry is
one file in one place. The claim is contested when, over merges that carry a
file list:

    merged_with_files    >= 5      (below this there is no shape to speak of)
    and (merged_files_median >= 3  or  merged_dirs_median >= 2)

`portfolio` and `course_material` are deliberately **excluded**: their reason is
about whose project it is, not about the shape of a diff, and file lists cannot
refute it. A portfolio is usually real code — that is not a contradiction.

**K2 — `mirror`.** The stated reason is that outside pull requests are not the
contribution path. It is contested when the repository's own GitHub metadata
reports `is_mirror = false` **and** outsiders' pull requests were merged in the
window (`outsider_merged >= 2` by `distinct_merged_authors >= 2`). Metadata
alone is not enough: `is_mirror` is only set for repositories created as
mirrors, so a genuine mirror can report false. Requiring the merges as well
means the rule only fires when the claimed consequence is directly disproved.

**On a contested kind the field is dropped, not overridden.** No verdict is
asserted in its place; `classify` falls through to the arithmetic rules, and the
disagreement is printed in the rule trace where the reader can see it. This is
the project's standing rule for contradictory sources
(`CLAUDE.md`, "Evidence"), applied to the one field that had been exempt.

### Thresholds, and where they come from

Chosen on pool 1's 27 recorded classifications. The three repositories the model
called `registry` — `Homebrew/homebrew-cask`, `is-a-dev/register`,
`runelite/plugin-hub` — all sit at a median of **1 file in 1 directory**, and
every repository called `real_software` with a comparable merge volume sits at 2
or more files. The thresholds are the midpoint of that gap and were not tuned
past their first value.

## Predictions

1. **P1 (in-sample specificity).** The rule fires on **0 of 27** recorded pool-1
   repositories. Every verdict-flipping kind in pool 1 is correct, so any firing
   is a false accusation.
2. **P2 (out-of-sample specificity).** The rule fires on **0 of 45** pool-2
   repositories. This is the number that matters; it is measured after this file
   is committed.
3. **P3 (reproduction survives).** Because the rule fires nowhere, every frozen
   replay reproduces its committed MCC exactly: pool 1 `run1/run2/run3` at 0.61
   and pool 2 `p2r1/p2r2/p2r3` at 0.63. A firing anywhere invalidates this
   prediction and breaks replay for that repository, because the rule trace
   feeds the narration prompt.
4. **P4 (sensitivity).** On evidence whose merged work is plainly software
   (`NixOS/nixpkgs`: median 1 file — *not* contested; `AlvarOnce/rancho`: median
   9.5 files across 3 directories — contested), the rule fires exactly where the
   shape contradicts the label. Sensitivity is demonstrated on the shape, not on
   the two live repositories that prompted this, which are outside the pool and
   cannot be crawled at T.

## What would falsify this, and what happens then

If the rule fires on any pool repository whose kind is correct, it is wrong and
is not shipped — a guard that removes true classifications is worse than the
failure it prevents, because the kind rules are load-bearing for the
rubber-stamp result.

If it fires on a pool repository whose kind is *incorrect*, that is a genuine
catch, and the affected frozen replay must be re-recorded and the benchmark
re-run rather than the finding suppressed.

**Note the limit this rule does not remove.** `nixpkgs` merges one file in one
directory and is real software. K1 protects a repository from being *called* a
registry when its merges are software-shaped; it cannot protect one whose merges
look like a catalogue's. The remaining exposure is stated rather than closed.
