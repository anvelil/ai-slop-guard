# 0004. No autofix

## Status

Accepted (0.1.0), reaffirmed (0.2.0)

## Context

Every rule `check.py` verifies has an obvious mechanical fix in the common
case — delete the unused import, delete the dead function, remove the
`print()`. It would be straightforward to add a `--fix` flag that applies
these edits automatically, the way `ruff --fix` or `eslint --fix` do. This
was considered and rejected, at least for now.

## Decision

`check.py` only reports findings — path, line, rule ID, reason, suggested
fix as text. It never edits a file. Applying the fix is stage 5 (Refactor)
in the pipeline, done by the agent (or a human) reading stage 3's/6's
output. The script itself never edits a file.

Reasons:

1. **The suggested fix is sometimes wrong on inspection.** An ASG002
   "dead code candidate" might be called from another file — the script
   cannot know that (see `docs/known-limitations.md`). Auto-deleting it
   would be a correctness bug, unlike deleting an unused import — the
   "obvious" fix here isn't guaranteed safe. Since some rules' fixes need a
   human/agent judgment call and others don't, having the tool
   auto-fix only the "safe" ones would create an inconsistent experience
   and hide exactly the cases (ASG002, and any future rule with the same
   shape) where checking twice actually matters.
2. **The pipeline's structure depends on refactoring being a distinct,
   deliberate step.** Stage 5 exists precisely so that applying fixes is
   separated from finding them, and so stage 6 has something meaningful to
   verify against stage 3 (see [ADR 0002](0002-stage6-reruns-stage3.md)). A
   `--fix` flag that silently applies changes during stage 3 would collapse
   that separation.
3. **Consistent with [ADR 0003](0003-why-stdlib-only.md)'s trust posture.**
   A tool that only reads files and prints text is a much smaller thing to
   trust than one that rewrites files on your behalf, especially for a tool
   whose whole pitch is "safe to run without asking".

## Consequences

- Every fix, even the mechanically obvious ones, requires a human or agent
  in the loop, which is slightly more friction than a one-shot `--fix` run.
- This keeps the "Suggested fix" field in every finding doing real work —
  it has to be clear enough in prose to act on, since there's no
  alternative automated path.
- This may be revisited for the subset of rules that are unconditionally
  safe (arguably ASG001, unused imports, since Python's `ast` resolves them
  exactly) — but as of this ADR, no rule has an autofix, to keep the
  behavior uniform and avoid the "why does this rule autofix but not that
  one" confusion.
