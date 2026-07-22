# Rule philosophy

Why these seven rules and not others, and why each one is drawn where it is.

## The filter every rule has to pass

A rule gets into this project only if it passes three tests:

1. **Concrete and reproducible.** "Write cleaner code" is not a rule — you
   can't write a before/after diff for it. "A bare `except:` whose body is
   just `pass`" is a rule — you can point at the exact line.
2. **Low false-positive cost.** A linter that cries wolf gets ignored, then
   disabled. Every rule here is deliberately conservative: ASG003 only fires
   on exception handlers whose entire body is empty/pass/continue or a
   single log call — not on any broad `except Exception`, because plenty of
   those are legitimate (see below).
3. **The fix is obvious.** If a rule fires and the right fix isn't clear
   from the message, the rule isn't done yet — that's why every finding
   carries a `Reason` and a `Suggested fix` alongside the name.

Rules that fail test 2 (like flagging *all* `except Exception`, or all
functions over N lines) were deliberately left out even though they're
common in other linters — see "What's deliberately not a rule" below.

## Why `except Exception: pass` specifically — broad excepts aren't banned outright

`except Exception:` is not banned outright. A broad except that re-raises
with context, converts the error to a domain-specific one, or does real
cleanup (closing a resource, rolling back a transaction) is fine — often
better than a narrow except that misses a related error type.

What's flagged is narrower: a broad except whose entire body does nothing
observable (`pass`, `continue`) or only logs. That specific shape has one
job — make the error disappear without anyone deciding whether that's safe.
That's the dangerous part. Broadness alone isn't.

## Why unused imports and not unused variables

Unused imports (ASG001) are flagged; unused local variables are not, even
though both are "unused things". The reason is asymmetry of cost and
signal: an unused import is unambiguous (Python's `ast` resolves it exactly,
no false positives) and always safe to remove. An unused local variable is
frequently intentional — destructuring where you only need some fields,
a variable kept for a debugger, a placeholder in a tuple unpack — and
flagging it reliably needs scope analysis this project doesn't have yet.
Rather than ship a noisy heuristic, the rule stays out until it can be done
without guessing.

## Why dead-code detection is scoped to module-level functions only

Originally ASG002 walked the whole file including class bodies. It flagged
every method of this project's own `Finding` class as dead code, because
methods are called via `obj.method()` — an attribute access — and the
script only tracked calls to bare names. Extending it to resolve attribute
calls back to class definitions needs real type inference (which instance
is `obj`? which class defines `method`?) — exactly the kind of guesswork
rule 2 above rules out. So the check was narrowed instead of made cleverer:
module-level functions only, where "is this name called anywhere in the
file" is unambiguous. See `docs/known-limitations.md` for the full story.

This is the project's general answer when a rule can only be made more
powerful by guessing: narrow the scope, don't guess.

The same reasoning applied a second time, from running against real code
rather than fixtures: a benchmark against Flask's own tutorial app (see
`benchmarks/README.md`) flagged 34 route handlers and test functions as
"dead", all false positives, because both are invoked by a framework via
decorator registration or name-based discovery — rather than a direct
call in the file. Rather than try to model what every possible framework convention
means, the scope was narrowed again — decorated functions and `test_*`
functions excluded — cutting the same run to 4 findings, all legitimately
explainable as cross-file calls the tool has never claimed to see.

## Why duplicated logic, unnecessary defensive checks, and restating
## comments stay manual (ASG004–006)

All three need context a single-file static check doesn't have — whether
similar logic exists *elsewhere in the project*, whether a type *elsewhere
in the codebase* really rules out `null`, whether a comment's "why" is
already obvious from surrounding code a script can't see. Rather than
approximate these with a heuristic that will be wrong often enough to
distrust, they're kept as an explicit manual step (stage 4, Review, in
`SKILL.md`) with the reasoning spelled out so an agent — or a person — can
apply judgment instead of a false sense of automated coverage.

## Why "hallucinated API usage" is listed but not implemented (ASG008)

It's real, it's common with agent-generated code, and it belongs in the
registry so it isn't forgotten. But detecting it reliably needs resolved
type information or the actual installed library's API surface — neither
of which single-file static analysis has. A regex guess at "does this
method name look plausible" would produce enough noise to violate rule 2
above. It stays `planned` until there's a way to do it that doesn't guess.

## What's deliberately not a rule

- **Line-length / formatting** — solved problems with mature tools
  (`black`, `prettier`, `ruff format`). Duplicating them here would be
  scope creep with no advantage.
- **Cyclomatic complexity / function length thresholds** — genuinely useful,
  but the "right" threshold is project-specific and arguing about the
  number is its own time sink. That call is left to the team.
- **Naming conventions** — subjective enough that a wrong call here costs
  more trust than the rule is worth.
