# 0003. Python standard library only, no dependencies

## Status

Accepted (0.1.0), reaffirmed (0.2.0)

## Context

`scripts/check.py` could be more powerful with real parsers for TypeScript
(e.g. via a Node-based AST) or a proper multi-language framework. It could
also lean on existing linters (`ruff`, `eslint`) and just wrap their output.
Both options were considered and rejected.

## Decision

`scripts/check.py` and `scripts/generate_registry.py` use only the Python
standard library (`ast`, `json`, `re`, `pathlib`). No `pip install`, no
`npm install`, no network access, at any point.

In order of weight:

1. **Trust.** An agent — or a human — running this tool is told, in
   `SKILL.md` and the README, that it's "safe to run without asking". That
   claim is only true because there is nothing to install and nothing that
   phones home. Adding a dependency, even a well-known one, breaks that
   guarantee: now running the checker means trusting a supply chain, not
   just reading ~300 lines of stdlib Python.
2. **Zero-friction adoption.** The entire pitch of the project (see the
   README's installation section) is `cp` the folder and run one command.
   A `requirements.txt` or `package.json` step is exactly the kind of
   friction that determines whether a tool gets tried once or adopted.
3. **Forces honest scope.** Not having a real TS/JS parser available is
   *why* the JS/TS path is regex-based and documented as best-effort in
   `docs/known-limitations.md`, rather than silently pretending to be as
   reliable as the Python `ast` path. The constraint keeps the project
   honest about what it can verify.

## Consequences

- The JS/TS checks are permanently weaker than the Python checks unless a
  future decision explicitly revisits this ADR — there is no stdlib JS/TS
  parser to reach for.
- Any contributed rule must be implementable without a new dependency, per
  `CONTRIBUTING.md` — a hard constraint on rule design, beyond being a mere
  style preference.
- `ASG008` (hallucinated API usage) stays unimplemented in part *because*
  of this constraint — reliable detection needs resolved type information
  or a real library API surface, neither of which stdlib alone can provide
  without either a type checker dependency or network calls to fetch
  package metadata. See `docs/philosophy.md`.
