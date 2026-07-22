# Changelog

Two version numbers move independently here:

- **Project version** (`skill.json` → `version`) — the pipeline/tooling as
  a whole.
- **Rule set version** (`ai-slop-guard/data/rules.json` → `rule_set_version`,
  semver) — bumps only when a rule is added, removed, or has a breaking
  change to what it flags. A false-positive fix within a rule's existing
  scope does not bump it.

## 0.2.0 — rule set v1.0.0

### Added

- 6-stage pipeline in `SKILL.md` (generate → mentally compile → lint →
  review → refactor → final audit), replacing the flat 7-rule checklist
  from 0.1.0. See `docs/adr/0001-six-stage-pipeline.md`.
- Stable rule IDs (`ASG001`–`ASG008`), a lifecycle `status` per rule
  (`stable` / `experimental` / `planned`), and structured `philosophy`
  (why / example / counterexample / tradeoffs), all in
  `ai-slop-guard/data/rules.json`. Added `ASG008` (hallucinated API usage)
  as a registered-but-unimplemented rule — see `docs/philosophy.md`.
- `rule_set_version` switched to semver so rule-set changes version
  independently of the tool's own code changes.
- `check.py --json` for machine output, `--explain ASGxxx` to print a
  rule's philosophy on demand.
- 4 ADRs under `docs/adr/`: pipeline structure, why stage 6 re-runs stage
  3, stdlib-only constraint, no-autofix policy.
- `benchmarks/README.md` — methodology plus a real run against Flask's
  tutorial app.
- `tests/golden/` (8 fixtures) + `tests/test_golden.py`, and
  `.github/workflows/ci.yml` (self-check, golden tests, registry-sync).
- `examples/` split into `real-world/`, `false-positive/`, `edge-cases/`.
- `docs/known-limitations.md`, `docs/philosophy.md`,
  `references/registry.md` (generated from `data/rules.json`).

### Changed

- `check.py` findings now carry a rule ID, `Reason`, and `Suggested fix`,
  not a one-line message.
- README repositioned around the pipeline as the main idea, with
  `check.py` and the rule set framed as what supports stages 3 and 6.

### Fixed

- ASG002 flagged class methods as dead code (called via `obj.method()`,
  not tracked as a "use") — scoped the check to module-level functions.
- ASG002 flagged every Flask route handler and pytest `test_*` function as
  dead code — a benchmark run went from 34 findings (all false positives)
  to 4 after excluding decorated and `test_*` functions. See
  `benchmarks/README.md`.
- Bare decorators (`@foo`, no call parens) weren't counted as a use of
  `foo` — fixed.

### Known issues

- ASG002 stays `experimental`: it has no project-wide view, so a function
  called only from another file is still a false positive (reproducible in
  `examples/false-positive/cross_file_call.py`) — an inherent limit of
  single-file analysis that no fix is scoped to close.
- The JS/TS path (`ASG001`, `ASG003`, `ASG007`) is regex-based; see
  `docs/known-limitations.md` for its specific gaps.
- `ASG004`–`ASG006` stay manual by design. `ASG008` isn't implemented.

## 0.1.0 — rule set v1

### Added

- Initial release: 7 rules as a flat checklist in `CLAUDE.md`, with a
  Cursor `.mdc` adapter. `check.py` covered unused imports, catch-all
  exception handling, leftover debug output, and file-local dead-code
  candidates.

### Known issues

- The dead-code check had no scope narrowing yet — flagged class methods,
  decorated functions, and test functions. Fixed in 0.2.0.
