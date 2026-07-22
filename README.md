# AI Slop Guard

A 6-stage code review pipeline for AI coding agents. `check.py` (stage 3/6)
is the static-analysis piece; see below for the whole sequence.

![python](https://img.shields.io/badge/python-3.9+-blue) ![dependencies](https://img.shields.io/badge/dependencies-0-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green)

Turns your AI coding agent from "generate code, hope it's fine" into a
6-stage self-review pipeline: **generate → mentally compile → lint → review
→ refactor → final audit**. That sequence - not any individual rule - is
this project's actual distinctive part; see
[`docs/adr/0001-six-stage-pipeline.md`](docs/adr/0001-six-stage-pipeline.md)
for why it's structured this way instead of as a flat checklist.

`scripts/check.py` is real static analysis (Python's `ast`, stdlib-only,
zero installs, zero network calls) that reports findings with a rule ID,
reason, and suggested fix. It exists to support the pipeline: stage 6
re-runs stage 3's exact check specifically to catch
regressions the refactor step (stage 5) itself introduces — see
[`docs/adr/0002-stage6-reruns-stage3.md`](docs/adr/0002-stage6-reruns-stage3.md).
Stages 2 and 4 have no tool at all; they're pure reasoning steps the
pipeline still requires.

## Why a pipeline instead of a flat rule list

A linter tells you what's wrong. It doesn't tell you *when* to check, or
what to do about the things it structurally can't see. Sequencing generate,
verify, review, and re-verify — so an agent's own refactor doesn't quietly
undo the verification — is the actual point here. `check.py` and the rule
registry below support stages 3 and 6; they're intentionally the least
novel part of this repository.

## Sample run

A `check.py --json` run, before and after applying its own suggestions to
`examples/violations_demo.py` — reproduce with the two commands in
[`benchmarks/README.md`](benchmarks/README.md):

| Rule | Before | After |
|---|---|---|
| ASG001 Unused imports | 2 | 0 |
| ASG002 Dead code candidate | 2 | 0 |
| ASG003 Catch-all exception handling | 1 | 0 |
| ASG007 Leftover debug output | 1 | 0 |
| **Total** | **6** | **0** |

And against real, independently-written code — not a fixture — the tool's
own false-positive rate, measured, fixed, and re-measured:

| Benchmark run | Findings | False positives |
|---|---|---|
| Flask tutorial app, before scope fix | 34 | 34 (100%) |
| Flask tutorial app, after scope fix | 4 | 4 (pre-existing cross-file cases, see `benchmarks/README.md`) |

Full story: [`benchmarks/README.md`](benchmarks/README.md). The 34→4 fix
happened during this project's own development — see `CHANGELOG.md`.

## Language support

| Language | Status |
|---|---|
| Python | ✓ implemented (`ast`-based, all 4 script-verified rules) |
| TypeScript / JavaScript | partial (regex-based for unused named imports, empty catch, debug output — see `docs/known-limitations.md`) |
| Java | planned |
| Go | planned |
| Rust | planned |

## What's inside

```
ai-slop-guard/
├── SKILL.md                    # entry point — frontmatter + 6-stage pipeline
├── data/rules.json             # source of truth: rule IDs, status, philosophy
├── scripts/
│   ├── check.py                 # real static analysis, stdlib only
│   └── generate_registry.py     # regenerates references/registry.md from rules.json
└── references/
    ├── rules.md                 # full reasoning + before/after per rule
    └── registry.md              # generated: coverage table + full per-rule philosophy
docs/
├── philosophy.md                # project-wide: why these rules and not others
├── known-limitations.md         # every known false positive/negative, with examples
└── adr/                         # architecture decision records
    ├── 0001-six-stage-pipeline.md
    ├── 0002-stage6-reruns-stage3.md
    ├── 0003-why-stdlib-only.md
    └── 0004-why-no-autofix.md
benchmarks/
└── README.md                    # methodology + real numbers from a real project
examples/
├── violations_demo.py            # before
├── violations_demo_fixed.py      # after
├── real-world/                   # patterns from real, independently-written code
├── false-positive/                # current, documented false positives
└── edge-cases/                    # inputs exercising a specific code path
tests/
├── golden/<case>/                # input.py + expected.json per case
└── test_golden.py                # unittest — fails if check.py's output drifts
.github/workflows/ci.yml          # self-check, golden tests, registry-sync check
CHANGELOG.md
```

`ai-slop-guard/` is a self-contained [Claude Skill](https://docs.claude.com) —
copy that one folder anywhere Claude Code looks for skills and it activates
automatically. Everything else in this repo (`.cursor/`, root `CLAUDE.md`) is
a thin adapter pointing at that same folder for other tools.

## Installation

**Claude Code** (native Skill support):

```bash
mkdir -p .claude/skills
cp -r ai-slop-guard .claude/skills/
```

**Cursor:**

```bash
mkdir -p .cursor/rules
cp .cursor/rules/ai-slop-guard.mdc <your-project>/.cursor/rules/
cp -r ai-slop-guard <your-project>/
```

**Any other agent that reads a root `CLAUDE.md` / system prompt:**

```bash
cp CLAUDE.md <your-project>/
cp -r ai-slop-guard <your-project>/
```

**Just want the checker, no agent integration:**

```bash
python3 ai-slop-guard/scripts/check.py path/to/your/code          # human-readable
python3 ai-slop-guard/scripts/check.py --json path/to/your/code   # machine-readable
```

## The pipeline

| Stage | What happens | Tool-verified? |
|---|---|---|
| 1. Generate | Write the solution | — |
| 2. Compile mentally | Trace the code by reading it — names resolve, arities match, branches return the right thing | No — reasoning only |
| 3. Lint | Run `check.py` on the diff | Yes |
| 4. Review | Senior-level pass: duplicated logic, unneeded defensive checks, comments that restate code | No — needs project/type context |
| 5. Refactor | Fix what 3–4 found, structure only, behavior preserved | — |
| 6. Final audit | Re-run `check.py` — finding count must not exceed stage 3's | Yes |

Full stage-by-stage instructions: [`ai-slop-guard/SKILL.md`](ai-slop-guard/SKILL.md).

## Rule registry

Rule set v1.0.0 (`ai-slop-guard/data/rules.json`) — see `CHANGELOG.md` for
why this version number moves independently from the project version.

| ID | Name | Status | Script-verified |
|---|---|---|---|
| ASG001 | Unused imports | stable | yes |
| ASG002 | Dead code (module-level, undecorated, non-`test_*`) | experimental | partial |
| ASG003 | Catch-all / empty exception handling | stable | yes |
| ASG004 | Duplicated logic | planned | no — manual |
| ASG005 | Unnecessary defensive checks | planned | no — manual |
| ASG006 | Comments that restate the code | planned | no — manual |
| ASG007 | Leftover debug output | stable | yes |
| ASG008 | Hallucinated API usage | planned | not implemented |

Print any rule's full reasoning on demand:

```bash
python3 ai-slop-guard/scripts/check.py --explain ASG002
```

Generated, always-current version with the coverage table and full
per-rule philosophy: [`ai-slop-guard/references/registry.md`](ai-slop-guard/references/registry.md).
Full reasoning and before/after examples: [`ai-slop-guard/references/rules.md`](ai-slop-guard/references/rules.md).
Why these rules and not others: [`docs/philosophy.md`](docs/philosophy.md).
Why the pipeline is structured the way it is: [`docs/adr/`](docs/adr/README.md).
Known false positives and edge cases: [`docs/known-limitations.md`](docs/known-limitations.md).

## Suppressing a false positive

Put `# slop-guard: ignore` (Python) or `// slop-guard: ignore` (JS/TS) on the
line, and say why in a nearby comment or commit message rather than silencing
a finding you haven't actually looked at — the script's own CLI output uses
this for its one legitimate `print()` call, see `ai-slop-guard/scripts/check.py`.

## Prerequisites

Python 3.9+. Nothing else — no packages to install, no network access
required or used, for the tool or for its tests.

```bash
python3 --version
```

## Try it

```bash
python3 ai-slop-guard/scripts/check.py examples/violations_demo.py         # should report 6 findings
python3 ai-slop-guard/scripts/check.py examples/violations_demo_fixed.py   # should report none
python3 ai-slop-guard/scripts/check.py examples/real-world/flask_route_handler.py     # should report none
python3 ai-slop-guard/scripts/check.py examples/false-positive/cross_file_call.py     # should report 1 (documented false positive)
python3 -m unittest tests.test_golden -v                                    # should pass, 8/8
```

## Contributing

New rule proposals need: a concrete, reproducible pattern (not "write better
code"), an entry in `data/rules.json`, a before/after example in
`references/rules.md`, and — if it's mechanically detectable — a
corresponding check in `scripts/check.py` with a golden test that doesn't
false-positive on the script's own code. See `CONTRIBUTING.md`.

## License

MIT
