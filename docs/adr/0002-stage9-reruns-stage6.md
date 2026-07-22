# 0002. Stage 9 re-runs stage 6's exact check

## Status

Accepted (0.3.0) - Supersedes 0.2.0 (Stage 6 re-runs stage 3's exact check)

## Context

Stage 8 (Refactor) is the one stage in the pipeline that touches code a second time, on the agent's own initiative, after stage 6 (Lint) / 7 (Review) already found issues. Refactoring is also exactly the kind of edit most likely to introduce a *new* instance of the same problems it's fixing — a rename that leaves a stale import, a restructured `try` that accidentally swallows an exception it used to propagate, a helper extracted from duplicated code that itself goes unused in one of the two call sites. Without a check after refactoring, the pipeline could report success while quietly making things worse than stage 6 found them.

## Decision

Stage 9 (Final audit) runs the identical command as stage 6 (Lint):
`slop-guard <file_or_dir>`.
The pipeline is explicit: the finding count at stage 9 must not exceed the finding count at stage 6. If it does, the refactor introduced new slop, and the task is not done — fix it before finishing, don't carry it forward.

This was deliberately kept as a *count* comparison rather than a requirement that the finding sets be identical or empty. A codebase can have pre-existing, accepted findings (e.g. a documented ASG002 false positive on a framework-registered function) that neither stage is expected to fix. What matters is that the number doesn't go up.

## Consequences

- This is the only place in the pipeline where the same tool call happens twice with an explicit numeric comparison — every other stage is single-pass.
- It gives the pipeline exactly one automatically checkable regression gate.
- It does not catch regressions in stages 7's manual-only rules (ASG005–006, ASG008) — those still rely on the agent (or a human reviewer) applying the same judgment twice, which is a real gap this ADR doesn't close.
