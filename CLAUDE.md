# Holt — working rules

Holt determines whether a GitHub repository is a genuine opportunity for an
*external* contributor, and produces an evidence-backed written assessment.
Read-only: Holt never writes to GitHub, opens PRs, or contacts maintainers.

## Commits

- Commit messages state **behaviour**, not files. The log becomes the changelog.
- **Do not add `Co-Authored-By` trailers, "Generated with Claude Code" lines, or
  any other attribution footer** to commit messages or PR descriptions.

## Evidence

- Every fact the agent sees passes through `EvidenceProvider`. No direct network
  calls from stages.
- Every user-visible claim carries a `file:line` or an evidence ID that resolves.
- Where sources disagree, drop the contested field rather than picking a side.
  Never write an instruction that forbids re-checking a claim.

## Temporal holdout

- **T = 2026-06-01.** The agent sees only records with `timestamp <= T`; labels
  are computed only from records with `timestamp > T`.
- This is enforced by assertion in the provider, not by convention.
- `eval/labels/` must not import from `src/holt/agent/`. A test enforces this.

## Evaluation

- Never edit `eval/pool.json` after seeing results. It is hash-committed first.
- Anything synthetic or replayed is labelled as such in the tool's own output,
  not only in the docs.
- Definition of done includes pasted test output. Skipped is not passed —
  confirm with `pytest -rs`.

## Changelog

`CHANGELOG.md` is a graded deliverable. Write entries **at the moment of the
experiment**, including experiments that were removed. It cannot be convincingly
reconstructed at the end.
