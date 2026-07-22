# Changelog

Two version numbers move independently here:

- **Project version** — the pipeline/tooling as
  a whole.
- **Rule set version** (`ai-slop-guard/data/rules.json` → `rule_set_version`,
  semver) — bumps only when a rule is added, removed, or has a breaking
  change to what it flags. A false-positive fix within a rule's existing
  scope does not bump it.

## 0.3.0 — rule set v1.0.0

### Changed
- **9-Stage Pipeline**: Restructured the development and verification pipeline from 6 stages to 9 stages to introduce explicit Analyze, Plan, Syntax Check, and Testing phases.
- Updated ADR-0001 ("Nine-stage pipeline") and ADR-0002 ("Stage 9 re-runs stage 6's exact check") to align with the new structure.

## 0.2.0 — rule set v1.0.0

### Added
- **Python Packaging**: The project is now a standard Python package (`pyproject.toml`) and can be installed via `pip install .`.
- **CLI Command**: Exposed `slop-guard` command globally after installation.
- **Pre-commit integration**: Added `.pre-commit-hooks.yaml` for easy integration into pre-commit workflows.
- 6-stage pipeline (generate → mentally compile → lint →
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

- Standardized package structure by moving code to `src/ai_slop_guard`.
- Removed all "AI slop" from the project itself (excessive explaining comments, AI-agent instructions like `CLAUDE.md`, `SKILL.md`). The project is now a clean, standalone linter.
- `check.py` (now `cli.py`) findings now carry a rule ID, `Reason`, and `Suggested fix`,
  not a one-line message.
- README repositioned around the pipeline as the main idea, with
  `slop-guard` and the rule set framed as what supports stages 3 and 6.

### Fixed

- ASG001 no longer flags an import used only to re-export it via a
  module-level `__all__` (e.g. `from .helpers import public_helper` with
  `__all__ = ["public_helper"]` and no other reference in the file).
  String literals inside `__all__ = [...]`, `__all__ += [...]`, and an
  annotated `__all__: list[str] = [...]` are now read and counted as uses.
  A dynamically built `__all__` (list comprehension, `.extend(...)`, etc.)
  is still not understood — see `docs/known-limitations.md`.
- Added `tests/golden/dunder_all_reexport/` and corrected a stale test
  count in `CONTRIBUTING.md`.
- `tests/test_golden.py` no longer compares the exact line/reason text of
  `PARSE` findings: CPython's own `SyntaxError` message and line number
  for the same malformed file differ between the pre-3.10 parser and the
  PEG parser introduced in 3.10.

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

- Initial release: 7 rules as a flat checklist. `check.py` covered unused imports, catch-all
  exception handling, leftover debug output, and file-local dead-code
  candidates.

### Known issues

- The dead-code check had no scope narrowing yet — flagged class methods,
  decorated functions, and test functions. Fixed in 0.2.0.
