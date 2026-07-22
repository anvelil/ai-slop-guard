# Rule catalog

Full rationale and before/after examples for each check in the pipeline.
Read this when you want detail on a specific rule — you don't need it for a
routine check.

## ASG002 — Dead code

If a function, class, or branch isn't called anywhere in the project,
delete it — don't comment it out or leave it "just in case".

```diff
- function calculateLegacyDiscount(price) { // no longer used
-   return price * 0.9;
- }
  function calculateDiscount(price) {
    return price * 0.85;
  }
```

Exception: public library API, where the function is part of the contract.
Mark it `@deprecated` with a reason instead of deleting it.

**Script coverage:** `slop-guard` (`cli.py`) flags module-level, undecorated,
non-`test_*` functions that are never referenced anywhere else *in the same
file*. Class methods, decorated functions (`@app.route`, `@pytest.fixture`,
...) and pytest-style `test_*` functions are excluded — they're almost
always invoked indirectly by a framework rather than by name in the file, and
an earlier version flagging them produced a 34/34 false-positive rate on an
independent benchmark (see `../../benchmarks/README.md`). Even after that
exclusion, a flagged function might still be called from another file —
treat its output as candidates to verify, never as confirmed dead code.

## ASG003 — Catch-all / empty exception handling

A catch block should either handle one specific, expected error, or re-raise
with added context. A catch that's empty, or that just logs and continues as
if nothing happened, hides bugs instead of fixing them.

```diff
- try {
-   const user = await db.getUser(id);
-   return user.name;
- } catch (e) {
-   console.log(e);
-   return null;
- }
+ const user = await db.getUser(id);
+ if (!user) throw new NotFoundError(`User ${id} not found`);
+ return user.name;
```

Test: can you name the specific error you're catching and what you do about
it? If not, the catch block probably shouldn't exist.

**Script coverage:** flags `except:` / `except Exception:` with a body of
only `pass`, `continue`, or a single logging call (Python), and `catch` blocks
with an empty or single-log-statement body (JS/TS).

## ASG004 — Duplicated logic

Before writing a new function, check whether something close already exists
in the project. Two near-identical functions with different names is a sign
the agent didn't look at the existing code first.

```diff
- function formatUserDate(date) { return date.toISOString().split('T')[0]; }
- function formatOrderDate(date) { return date.toISOString().split('T')[0]; }
+ function formatDate(date) { return date.toISOString().split('T')[0]; }
```

**Script coverage:** none — this requires seeing the whole project rather
than one file. Search by likely signature/keywords before adding a new function.

## ASG001 — Unused imports

After any edit, every import in the files you touched should be used.
This especially slips through after a refactor that deleted code but left
the import behind.

```diff
- import os
- from .helpers import public_helper, unused_helper
+ from .helpers import public_helper
  __all__ = ["public_helper"]
```

Exception: a name imported only to re-export it via `__all__` is a real
use, even though it's never referenced by name anywhere else in the file —
that's the whole point of `__all__`. Since 0.2.0 the script recognizes
string literals listed in a module-level `__all__` as uses; see
`docs/known-limitations.md` for what's still not understood (a
dynamically built `__all__`).

**Script coverage:** yes, for Python (via `ast`, including `__all__`
re-exports) and best-effort for JS/TS (via static import-statement +
usage-count matching).

## ASG005 — Unnecessary defensive checks

If a type already guarantees a value can't be `null`/`undefined` (TypeScript,
a required parameter with no default, etc.), don't add a check for it anyway.
It protects against nothing, adds noise to the diff, and creates a false
sense of robustness.

```diff
- function getFullName(user: User): string {
-   if (!user) return '';
-   if (!user.firstName) return '';
    return `${user.firstName} ${user.lastName}`;
- }
+ function getFullName(user: User): string {
+   return `${user.firstName} ${user.lastName}`;
+ }
```

**Script coverage:** none — this requires type information the script
doesn't have. Judgment call at review time.

## ASG006 — Comments that restate the code

A comment should explain "why", not "what" — "what" is already visible from
the code itself.

```diff
- // increment counter by one
- counter += 1;
+ // compensate for the off-by-one in the API, which counts from zero
+ counter += 1;
```

If you can't explain "why", the comment probably shouldn't be there at all.

**Script coverage:** none — judgment call.

## ASG007 — Leftover debug output

No `console.log`, `print`, `dbg!`, or similar in a final diff, unless it's
deliberate logging through the project's logger.

**Script coverage:** yes, flags bare `print(...)` (Python) and
`console.log/debug/info(...)` (JS/TS) calls in changed files.
