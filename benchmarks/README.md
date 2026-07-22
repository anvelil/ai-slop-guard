# Benchmarks

Methodology: clone a real, independently-written codebase and run
`check.py` against it. What matters isn't "0 findings" — a clean run on
code nobody wrote to please a linter is the useful signal. What matters is
the false-positive count, since that's what decides whether the tool
survives a week of actual use.

## Small fixture: violations_demo.py

`check.py --json` on `examples/violations_demo.py`, before and after
applying its own suggested fixes. Reproduce:

```bash
python3 ai-slop-guard/scripts/check.py examples/violations_demo.py
python3 ai-slop-guard/scripts/check.py examples/violations_demo_fixed.py
```

| Rule | Before | After |
|---|---|---|
| ASG001 Unused imports | 2 | 0 |
| ASG002 Dead code candidate | 2 | 0 |
| ASG003 Catch-all exception handling | 1 | 0 |
| ASG007 Leftover debug output | 1 | 0 |
| **Total** | **6** | **0** |

ASG004 and ASG005 aren't in this table — they're manual (stage 4 in
`SKILL.md`), and this file doesn't happen to exercise them; a `0` here
doesn't mean everything was checked. ASG008 isn't implemented (see
`docs/philosophy.md`). And this is one small file — the number below, from
independently-written code, is the one that says something about
false-positive rate.

## flask/examples/tutorial

Source: [pallets/flask](https://github.com/pallets/flask), `examples/tutorial/`
— Flask's own tutorial app (`flaskr`): routes, a db layer, a pytest test
suite. Cloned shallow, checked as-is.

```bash
git clone --depth 1 https://github.com/pallets/flask.git
python3 ai-slop-guard/scripts/check.py --json flask/examples/tutorial
```

### Run 1 — before this benchmark existed

| Rule | Findings |
|---|---|
| ASG002 Dead code candidate | 34 |

All 34 were false positives: every Flask route handler (`@bp.route(...)`)
and every pytest `test_*` function, both invoked by a framework — via
decorator registration or name-based discovery — rather than a direct call
in the file. The heuristic at the time only recognized `name(...)` call
syntax, so it had no way to know either pattern counted as "used".

### Fix

`check.py` now excludes, from ASG002, any module-level function that has a
decorator (`@app.route`, `@click.command`, `@pytest.fixture`, ...) or
matches the `test_*` naming convention — the same reasoning class methods
were already excluded for.

### Run 2 — after the fix

| Rule | Findings |
|---|---|
| ASG002 Dead code candidate | 4 |

The remaining 4 (`create_app`, `login_required`, `close_db`, `init_app`)
are each called from a different file than the one they're defined in:
`create_app` is looked up by name by Flask's own CLI, `login_required` is
imported as a decorator in `blog.py`, and `close_db`/`init_app` are
registered with `app.teardown_appcontext(...)` elsewhere. Single-file
analysis has no way to see any of that — see `docs/known-limitations.md`.

34 → 4 on the same codebase, found by running against real code instead of
only fixtures built to demonstrate the tool working.

## Planned

| Project | Status |
|---|---|
| django (small app) | planned |
| react / typescript project | planned — exercises the regex-based JS/TS path |
| a Rust or Go project | blocked — no checker for these languages yet |

Contributions running this methodology against a new project are welcome —
see `CONTRIBUTING.md`.
