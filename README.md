# AI Slop Guard

![python](https://img.shields.io/badge/python-3.9+-blue) ![dependencies](https://img.shields.io/badge/dependencies-0-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green)

A month ago I got tired of the same pattern with AI coding agents: they
generate something, it runs, it looks fine — and then a week later I find a
stray `print()`, an import nobody uses, or a `try/except: pass` quietly
eating an error I actually needed to see. Not because the agent is bad at
writing code. It's bad at *checking its own work*, and most workflows never
ask it to.

So instead of writing another linter, I built a small pipeline that makes
an agent review itself before calling a task done:

**generate → mentally compile → lint → review → refactor → final audit.**

`src/ai_slop_guard/cli.py` — real static analysis, `ast`-based, stdlib only, no
installs, no network — is stage 3. It's the least interesting part of this
repo, honestly. The sequencing is the actual point: an agent that fixes
what the linter found is *also* the agent most likely to break something
else while doing it — a rename that leaves a dead import, a "cleaned up"
except block that now swallows an error it used to raise. Stage 6 catches
that by re-running stage 3's exact check and requiring the finding count
not to go up. Nobody else's README for this kind of tool mentions that
failure mode, as far as I've seen — see `docs/adr/0002-stage6-reruns-stage3.md`
if you want the full reasoning.

## Why not just add more rules

There are already several AI-slop scanners out there with 50+ rules across
half a dozen languages. I'm not trying to out-rule them. This project
checks three things reliably (unused imports, dead module-level functions,
exception handlers that swallow errors silently) and is upfront that three
more (duplicated logic, unnecessary null checks, restating comments) are
listed but deliberately left manual, because doing them automatically means
guessing — and a rule that guesses wrong often enough gets disabled, which
is worse than not having it. `docs/philosophy.md` goes through the
reasoning per rule if you're curious, including the ones I decided *not*
to build.

## What actually happened when I ran this on real code

Small fixture, before/after applying its own suggestions
(`examples/violations_demo.py`):

| Rule | Before | After |
|---|---|---|
| ASG001 Unused imports | 2 | 0 |
| ASG002 Dead code candidate | 2 | 0 |
| ASG003 Catch-all exception handling | 1 | 0 |
| ASG007 Leftover debug output | 1 | 0 |
| **Total** | **6** | **0** |

More useful: running it against code I didn't write, Flask's own tutorial
app. First pass flagged 34 "dead functions" — every one was a false
positive, because route handlers and pytest tests get called by the
framework, not by a direct name in the file, and the script had no way to
know that yet. I fixed the scope (exclude decorated functions and `test_*`
names) and re-ran it: 4 findings left, all explainable, all cross-file
calls the tool has never claimed to see. Full writeup in
`benchmarks/README.md` — I'd rather show you where it was wrong than just
tell you it works.

## Language support

| Language | Status |
|---|---|
| Python | full — `ast`-based, all script-verified rules |
| TypeScript / JavaScript | partial — regex-based for named imports, empty catch, debug output (see `docs/known-limitations.md`) |
| Java / Go / Rust | not yet |

## What's inside

```
src/ai_slop_guard/
├── cli.py                       # the actual static analysis
├── generate_registry.py         # regenerates references/registry.md
├── data/rules.json              # rule IDs, status, reasoning per rule
└── references/
    ├── rules.md                 # before/after per rule
    └── registry.md              # generated coverage table
docs/
├── philosophy.md                # why these rules, and not others
├── known-limitations.md         # every known false positive, with examples
└── adr/                         # a few decisions worth explaining
benchmarks/
└── README.md                    # the Flask run, in full
examples/ · tests/ · .github/workflows/main.yml
```

## The pipeline itself

| Stage | What happens | Checked by a script? |
|---|---|---|
| 1. Generate | Write the solution | — |
| 2. Compile mentally | Read it back before running it — names resolve, arities match, branches return what's expected | No, pure reasoning |
| 3. Lint | Run `slop-guard` on the diff | Yes |
| 4. Review | Duplicated logic, defensive checks a type already rules out, comments that just restate the code | No, needs project context |
| 5. Refactor | Fix what 3–4 found, structure only | — |
| 6. Final audit | Re-run stage 3's command — the count must not go up | Yes |

## The rules, as of now

| ID | Name | Status |
|---|---|---|
| ASG001 | Unused imports | stable |
| ASG002 | Dead module-level function (undecorated, non-`test_*`) | experimental |
| ASG003 | Catch-all / empty exception handling | stable |
| ASG004 | Duplicated logic | planned — manual |
| ASG005 | Unnecessary defensive checks | planned — manual |
| ASG006 | Comments that restate the code | planned — manual |
| ASG007 | Leftover debug output | stable |
| ASG008 | Hallucinated API usage | planned — not implemented |

```bash
slop-guard --explain ASG002   # full reasoning for one rule
```

## If it flags something that isn't actually a problem

Add `# slop-guard: ignore` (Python) or `// slop-guard: ignore` (JS/TS) on
the line, and say why nearby — in a comment or the commit message — rather
than silencing something you haven't actually looked at.

## Requirements

Python 3.9+. Nothing else — no packages, no network access, ever.

## Installation

```bash
# Install directly from github:
pip install git+https://github.com/your-repo/ai-slop-guard.git
```

### Pre-commit hook
You can add `ai-slop-guard` to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/your-repo/ai-slop-guard
    rev: v0.2.0
    hooks:
      - id: slop-guard
```

## Try it yourself

```bash
slop-guard examples/violations_demo.py         # 6 findings
slop-guard examples/violations_demo_fixed.py   # 0
slop-guard examples/real-world/flask_route_handler.py  # 0
slop-guard examples/false-positive/cross_file_call.py  # 1, documented
python3 -m unittest tests.test_golden -v               # 8/8
```

## Contributing

If you want to propose a rule, I need a real reproducible pattern (not
"write cleaner code"), an entry in `data/rules.json`, a before/after in
`references/rules.md`, and — if it can be checked mechanically — a test in
`src/ai_slop_guard/cli.py` that doesn't false-positive on its own code. See
`CONTRIBUTING.md`.

## License

MIT
