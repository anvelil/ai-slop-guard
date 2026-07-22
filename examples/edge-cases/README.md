# Edge cases

Inputs chosen to exercise a specific code path in `check.py` rather than
to demonstrate a rule in the normal sense.

## decorator_without_parens.py

```bash
slop-guard examples/edge-cases/decorator_without_parens.py
# -> no findings
```

`@route_registry` (no call parentheses) counts as a use of
`route_registry`. An earlier version of `check.py` only tracked
`ast.Call` nodes as "uses"; a bare decorator reference is an `ast.Name`
instead, so `route_registry` was flagged as dead code until this was
fixed. This fixture is also a golden test:
`tests/golden/decorated_and_test_functions/`.

## syntax_error.py

```bash
slop-guard examples/edge-cases/syntax_error.py
```

Deliberately invalid Python. Confirms the checker reports a `PARSE`
finding with a line number and exits non-zero, instead of crashing with an
unhandled traceback — a static analysis tool that crashes on bad input is
worse than useless in a pipeline stage that's supposed to run
unconditionally.
