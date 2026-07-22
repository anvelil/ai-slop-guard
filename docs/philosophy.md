# Why these rules, and not others

I didn't want to just port over whatever other linters check. Every rule
here had to earn its place, and I used roughly the same three questions
each time:

1. Can I point at the exact line and say "this is the problem"? "Write
   cleaner code" isn't a rule. "A bare `except:` whose body is just `pass`"
   is — you can show a before and after.
2. If it's wrong, how much does that cost? A check that cries wolf gets
   ignored, then turned off. I'd rather leave a rule out than ship one that
   fires on legitimate code often enough that people stop trusting it.
3. If it fires, is the fix obvious? If the message doesn't tell you what to
   do, the rule isn't finished.

A few common linter rules — flagging every broad `except Exception`,
flagging every function over N lines — fail question 2 badly enough that I
left them out on purpose, even though other tools include them. More on
that below.

## Why `except: pass` and not "all broad excepts"

Catching `Exception` broadly isn't inherently wrong — sometimes it's the
right call, if you re-raise with more context or actually clean something
up (close a connection, roll back a transaction). What I flag is narrower:
an except block whose entire body does nothing observable, or just logs.
That specific shape has one function — making an error disappear without
anyone deciding that's okay. Broadness by itself isn't the problem; silence
is.

## Why unused imports but not unused variables

Both are "things nobody uses," but they're not the same kind of finding.
An unused import is unambiguous — Python's `ast` resolves exactly where a
name is used, no guessing — and always safe to delete. An unused local
variable is much more often intentional: you destructured an object and
only need two of five fields, you kept a variable around for a debugger
session, you have a placeholder in a tuple unpack. Flagging that reliably
needs scope analysis I haven't built. Rather than guess and be wrong a lot,
I left it out.

## Why dead-code detection only looks at module-level functions

The first version of this check walked the whole file, including classes.
It immediately flagged every method on this project's own `Finding` class
as dead — because they're called as `finding.to_dict()`, an attribute
access, and the script was only tracking calls to bare names. Rather than
teach it to resolve attribute calls back to a class (which needs real type
inference — whose instance is this, which class defines the method), I
narrowed the check instead: module-level functions only, where "is this
name called anywhere in the file" has one unambiguous answer.

That wasn't the last narrowing, either. Running it against Flask's own
tutorial app — real code I didn't write to please the linter — flagged 34
functions as dead. All 34 were false positives: every route handler and
every pytest test, both called by the framework through decorators or
name-based discovery, never by a direct call in the file. So the scope got
narrowed again: decorated functions and `test_*` names are now excluded.
Same run, same codebase, down to 4 findings — all genuinely cross-file
calls the tool has no way to see and never claimed to.

The pattern I keep coming back to: when a rule can only get smarter by
guessing, narrow it instead.

## Why duplicated logic, defensive checks, and restating comments stay manual

All three need context a single file doesn't have — whether similar logic
already exists somewhere else in the project, whether a type defined
elsewhere really rules out `null`, whether a comment's reasoning is
actually obvious from code the script can't see beyond this file. I could
approximate all of this with heuristics, but they'd be wrong often enough
that I'd rather keep them as an explicit manual step (stage 4 in
`README.md`) — with the reasoning written down so whoever's doing the
review, human or agent, can apply real judgment instead of trusting a
heuristic that only looks automated.

## Why "hallucinated API usage" is listed but doesn't exist yet

It's real — agents invent methods that don't exist on a library often
enough that it deserves a rule ID, so it's in the registry instead of
forgotten. But catching it reliably needs resolved type information or the
actual installed library's API surface, and single-file static analysis
has neither. A regex guess at "does this method name sound plausible"
would be noisy enough to break rule 2 above. It stays on the list, unbuilt,
until there's a way to do it without guessing.

## What I decided not to check at all

- Formatting and line length — `black`, `prettier`, and `ruff format`
  already solve this well; duplicating it here adds nothing.
- Function length / cyclomatic complexity thresholds — genuinely useful,
  but the "right" number is project-specific, and arguing about it is a
  time sink I didn't want to import into this tool.
- Naming conventions — too subjective; getting it wrong here costs more
  trust than the rule is worth.
