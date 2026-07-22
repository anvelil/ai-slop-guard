---
name: ai-slop-guard
description: Runs a 6-stage quality pipeline on code you write or edit — generate, mentally compile, lint, senior-level review, refactor, final audit — to catch common AI-agent code smells (dead code, empty/catch-all exceptions, unused imports, duplicated logic, unnecessary defensive checks, comments that restate the code, leftover debug output) before calling a task done. Use this throughout a coding session, any time you finish writing or editing code in any language.
---

# AI Slop Guard

Agent-written code usually passes tests and still accumulates small,
recognizable mistakes — dead functions, exceptions caught and silently
ignored, imports nobody uses, logic copy-pasted instead of reused. None of
them individually breaks anything. Together they turn reviewing an agent's
diff into archaeology.

This skill is a 6-stage pipeline you walk through before calling a coding
task done. Each stage has one job — don't skip ahead or merge stages, the
value is in doing them in order.

## The pipeline

### 1. Generate
Write the solution as you normally would. Nothing special here — this stage
just marks the starting point the rest of the pipeline checks against.

### 2. Compile mentally
Before running anything, trace through what you wrote by reading it, not
executing it. Check: every name you reference is actually defined or
imported, every function is called with the right number/type of arguments,
every branch returns what the caller expects, no obviously mismatched types.
This is a reasoning step — no tool does this for you. If you can't convince
yourself it holds together by reading it, don't move on to lint yet, fix it
first.

### 3. Lint
Run the checker on the files you touched:
```bash
python3 ai-slop-guard/scripts/check.py <file_or_dir> [<file_or_dir> ...]
```
Stdlib-only, no network calls, nothing installed — safe to run without
asking. It catches: unused imports, catch-all/empty exception handling,
leftover debug output, and file-local dead-code candidates. Fix everything it
reports, or be able to state in one sentence why a specific finding is a
false positive.

### 4. Review
Do a senior-engineer pass the script can't do for you — it needs
whole-project or type context the script doesn't have:
- **Duplicated logic** — search the project for a similar function signature
  before you decide your new function is actually new.
- **Unnecessary defensive checks** — don't guard against a `null`/`undefined`
  a type already rules out.
- **Comments that restate the code** — a comment should say "why", not
  "what". If you can't state a "why", delete it.

### 5. Refactor
Apply what stages 3 and 4 found — structure only, behavior unchanged. If the
project has tests, they must still pass after this stage with no changes to
their expected outputs. If it doesn't have tests, restrict yourself to
changes you can justify are behavior-preserving line by line (renames,
deletions of things stage 3/4 flagged, deduplication). This is not the stage
to also improve the algorithm or fix an unrelated bug — do that as a
separate, explicit change so it's reviewable on its own.

### 6. Final audit
Re-run the same checks, on the refactored code, to make sure stage 5 didn't
introduce a regression:
```bash
python3 ai-slop-guard/scripts/check.py <file_or_dir> [<file_or_dir> ...]
```
The finding count here should be lower than or equal to stage 3's, never
higher. If it's higher, the refactor introduced new slop — fix it before
calling the task done, don't carry it forward.

## Rule IDs

Every check has a stable ID (`ASG001`–`ASG007`; `ASG008` is registered but
not yet implemented). Findings from `check.py` include the ID, a `Reason`,
and a `Suggested fix`. Add `--json` to the command in stages 3 and 6 for
machine-readable output.

## Reference

Full rule catalog with before/after examples: `references/rules.md`.
Full registry with script-verification status per rule: `references/registry.md`.
Known false positives and edge cases: `../docs/known-limitations.md`.
Why these specific rules exist: `../docs/philosophy.md`.
