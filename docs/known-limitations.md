# Known limitations

Any static analyzer produces false positives and false negatives. This file
documents the known ones for `src/ai_slop_guard/cli.py`, so you know what to double
check instead of trusting the tool blindly.

## ASG002 — dead code candidate

- **Scope-narrowed by design, twice.** Only module-level, undecorated
  functions are checked, and pytest's `test_*` naming convention is
  excluded too. Both exclusions came from real false positives, not
  hypothetical ones:
  - Class methods: an early version flagged every method of this project's
    own `Finding` class (`to_dict`, `render`) as dead code, because they're
    called as `finding.to_dict()` — an attribute access the script didn't
    track as a "use".
  - Decorated functions and `test_*` functions: running against a real
    external project (Flask's own tutorial app, see `benchmarks/README.md`)
    flagged **34** findings, all false positives — every Flask route handler
    (`@bp.route(...)`) and every pytest test function, both invoked by a
    framework via decorator registration or name-based discovery, never by
    a direct call in the file. After excluding both patterns, the same run
    produced **4** findings. See `benchmarks/README.md` for the full
    before/after.
- **Decorators without parentheses count as a use.** `@foo` (no call
  syntax) used to not register `foo` as used, because it's a bare `ast.Name`
  in the decorator list rather than an `ast.Call`. Fixed — decorator
  references are now collected separately and count as uses.
- **False negative:** a module-level function passed as a callback
  (`on_click=my_handler`) without ever being called with `my_handler(...)`
  syntax in the same file won't be recognized as used, and will be flagged
  even though it's genuinely referenced. Verify manually before deleting.
- **False negative (the opposite risk):** a function *is* called only from
  another file (like Flask's `create_app`, looked up by name from outside
  the file). The script has no project-wide view, so this always needs a
  human check — treat every ASG002 finding as "verify", never "confirmed dead".
  Live, runnable reproduction: `examples/false-positive/cross_file_call.py`.
- **Fixed in 0.3.1:** a function that only calls itself (recursion) used to
  always count as "used". A recursive function never called from anywhere
  else in the file is now flagged.

## ASG001 — unused imports (Python)

- Correct for standard `import` / `from ... import ...` usage detected via
  `ast`, which is reliable — it's not a text/regex match.
- **Fixed in 0.2.0:** a module-level `__all__ = [...]` (or `__all__ +=
  [...]`, or an annotated `__all__: list[str] = [...]`) is now read, and
  any string literal it contains counts as a use — a name imported purely
  to re-export it via `__all__` is no longer flagged. Only plain string
  literals inside a list/tuple/set are understood; nothing is evaluated.
- **Fixed in 0.3.1:** name usage now only counts `Load` context. Previously
  `import json` followed by `json = 5`, never read afterward, still counted
  as used, because the reassignment target is an `ast.Name` node too.
- **Still not scope-aware.** The check asks "is this identifier read
  anywhere in the file", not "is this specific import read where it's in
  scope". A same-named local variable, parameter, loop variable, or
  `except ... as` binding still masks a genuinely unused module-level
  import as long as it's read somewhere in the file. Fixing this properly
  needs a symbol table, which the stdlib-only, single-pass design
  deliberately skips — see `docs/adr/0003-why-stdlib-only.md`.
- Still **not** understood: an `__all__` built dynamically — a list
  comprehension, a call to `.extend(...)`, names computed at runtime — is
  left exactly as before (false positive on the re-exported name). Mark
  such lines with `# slop-guard: ignore` for now.
- Does not understand `TYPE_CHECKING`-guarded imports used only in string
  type annotations — same workaround applies.

## ASG001 — unused imports (JS/TS)

- Best-effort only: matches named imports (`import { x } from '...'`) via
  regex rather than a real JS/TS parser. Default imports, namespace imports
  (`import * as x`), and dynamic imports are not checked at all — that means
  a false negative for any of those, never a finding at all.
- Counts raw occurrences of the identifier text in the file. A local
  variable that happens to share the imported name will suppress a true
  finding (false negative), and, in principle, one in a string or comment
  could too — this hasn't come up in the demo/golden fixtures, but the
  underlying method makes it possible.

## ASG003 — catch-all / empty exception handling

- Only recognizes bare `except:`, `except Exception:` (Python) and any
  `catch` block (JS/TS) whose body is trivially empty, `pass`/`continue`, or
  a single call expression (usually a log call). A catch block with two
  statements where the second is still just logging will not be flagged —
  the check is intentionally conservative to avoid false positives on real
  error handling.
- Does not evaluate whether the specific exception type caught is
  appropriate — only whether the body looks like it's doing nothing with
  the error.
- **Can't tell logging from real recovery.** A single-call body is flagged
  either way, whether the call is `logger.warning(...)` or
  `rollback_transaction()`. Since 0.3.1 the message reflects that
  uncertainty instead of asserting the error was silently swallowed.

## ASG007 — leftover debug output

- AST-based for Python — it matches real `print(...)` calls only, so it
  won't be fooled by the word "print" appearing in a string or docstring.

## General

- **Fixed in 0.3.1:** `# slop-guard: ignore` used to only suppress ASG007
  and the JS/TS checks — ASG001, ASG002, and ASG003 in Python ignored it.
  It now suppresses any finding on the marked line, for every rule. Say
  why you're using it — in a commit message or a trailing comment — so a
  future reader can tell it was a deliberate call rather than a finding
  silenced to quiet the tool.
- The script analyzes **one file at a time**. Anything that requires
  cross-file knowledge (ASG004 duplicated logic, whether an ASG002 candidate
  is really dead, whether an ASG005 guard is really unnecessary given the
  full type picture) is explicitly out of scope for automation and stays a
  human review step — see stage 7 (Review) in the pipeline.
- No attempt is made to resolve imports, follow the actual call graph, or
  understand decorators/metaclasses/dependency injection that might call a
  function indirectly. Treat every finding as "here's something to look at",
  not as ground truth.

Found a false positive not listed here? Open an issue with the exact
snippet — see `CONTRIBUTING.md`.
