# 0002. Stage 6 re-runs stage 3's exact check

## Status

Accepted (0.2.0)

## Context

Stage 5 (Refactor) is the one stage in the pipeline that touches code a
second time, on the agent's own initiative, after stage 3/4 already found
issues. Refactoring is also exactly the kind of edit most likely to
introduce a *new* instance of the same problems it's fixing — a rename that
leaves a stale import, a restructured `try` that accidentally swallows an
exception it used to propagate, a helper extracted from duplicated code
that itself goes unused in one of the two call sites. Without a check
after refactoring, the pipeline could report success while quietly making
things worse than stage 3 found them.

## Decision

Stage 6 (Final audit) runs the identical command as stage 3 (Lint):
`python3 ai-slop-guard/scripts/check.py <file_or_dir>`. The rule in
`SKILL.md` is explicit: the finding count at stage 6 must not exceed the
finding count at stage 3. If it does, the refactor introduced new slop, and
the task is not done — fix it before finishing, don't carry it forward.

This was deliberately kept as a *count* comparison rather than a requirement
that the finding sets be identical or empty. A codebase can have pre-existing,
accepted findings (e.g. a documented ASG002 false positive on a
framework-registered function) that neither stage is expected to fix.
What matters is that the number doesn't go up.

## Consequences

- This is the only place in the pipeline where the same tool call happens
  twice with an explicit numeric comparison — every other stage is
  single-pass.
- It gives the pipeline exactly one automatically checkable regression
  gate, which is also what CI enforces for the project's own
  `examples/violations_demo_fixed.py` fixture (see `.github/workflows/ci.yml`)
  — the fixed example must produce zero findings, a stricter version of the
  same "stage 6 ≤ stage 3" rule.
- It does not catch regressions in stages 4's manual-only rules (ASG004–006)
  — those still rely on the agent (or a human reviewer) applying the same
  judgment twice, which is a real gap this ADR doesn't close.
