# Contributing

## Adding a new rule

1. Open an issue or PR with a **concrete, reproducible** pattern — not a
   vague wish like "make the code cleaner". If you can't write a one-line
   before/after diff for it, it's not specific enough yet.
2. Add an entry to `ai-slop-guard/data/rules.json` with the next free
   `ASGxxx` ID — that file is the single source of truth for rule content.
   Include a `status` (`stable` only once it's been checked against real,
   non-fixture code with an acceptable false-positive rate — start new
   rules at `experimental` or `planned`) and a `philosophy` object (`why`,
   `example`, `counterexample`, `tradeoffs`) — this is what
   `--explain ASGxxx` and the generated registry both read directly from.
3. Regenerate the table:
   ```bash
   python3 ai-slop-guard/scripts/generate_registry.py
   ```
   and commit the resulting `ai-slop-guard/references/registry.md` — CI
   checks this file is in sync with `rules.json` and fails the build if not.
4. Add the full reasoning and a before/after diff to
   `ai-slop-guard/references/rules.md`, following the format of the
   existing entries.
5. Add the one-line summary to the checklist table in
   `ai-slop-guard/SKILL.md`.
6. If the pattern is mechanically detectable in a single file (no
   whole-project context needed), add a check to
   `ai-slop-guard/scripts/check.py`:
   - stdlib only — no new dependencies, no network calls
   - add a fixture under `tests/golden/<case>/input.py`, generate its
     `expected.json` with `python3 ai-slop-guard/scripts/check.py --json
     input.py > expected.json` from inside that directory, and run
     `python3 -m unittest tests.test_golden -v` — it must pass
   - run the checker against itself
     (`python3 ai-slop-guard/scripts/check.py ai-slop-guard/scripts/check.py`)
     — it must report zero findings; the tool has to pass its own rules
   - ideally, run it against one real external project (see
     `benchmarks/README.md` for the methodology) before considering the
     check done — fixtures alone tend to hide false-positive classes that
     only show up on code nobody wrote to please the linter, the way the
     ASG002 decorator/pytest exclusion was found
7. If the pattern needs project-wide context (like duplicated logic), leave
   it `"script_verified": false` in `rules.json` and say so explicitly in
   both `SKILL.md` and `references/rules.md` — don't imply script coverage
   that doesn't exist.
8. Add a categorized entry (Added/Changed/Fixed/Known issues) to
   `CHANGELOG.md`. Bump `rule_set_version` (semver: `MAJOR.MINOR.PATCH`)
   in `data/rules.json` for an added/removed/breaking-changed rule — a
   false-positive fix within a rule's existing stated scope doesn't bump it.
9. If the change touches how the pipeline itself is structured (not just a
   rule), consider whether it needs a new ADR under `docs/adr/` — see
   `docs/adr/README.md` for the format and when an existing ADR should be
   superseded instead of silently contradicted.

## Reporting a false positive

Include the exact snippet that triggered it and which rule ID fired. If
it's genuine, either the detection logic needs to be narrower (see
`docs/philosophy.md` for how this project prefers to narrow scope over
adding heuristics that guess), or the case needs documenting in
`docs/known-limitations.md` — both are useful outcomes.

## Local testing

```bash
python3 ai-slop-guard/scripts/check.py examples/violations_demo.py       # should find 6 issues
python3 ai-slop-guard/scripts/check.py examples/violations_demo_fixed.py # should find 0
python3 ai-slop-guard/scripts/check.py ai-slop-guard/scripts/check.py    # should find 0 (self-check)
python3 -m unittest tests.test_golden -v                                  # should pass, 6/6
```
