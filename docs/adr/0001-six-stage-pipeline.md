# 0001. Six-stage pipeline instead of a flat rule list

## Status

Accepted (0.2.0)

## Context

The project started (0.1.0) as a flat checklist of 7 rules in a single
`CLAUDE.md`. In practice, an agent given a flat list applies it
inconsistently — some rules get checked, some get forgotten, and there's no
natural point at which "the task is done" versus "I should go back and
check again". There was also no distinction between things a static script
can verify and things that genuinely need judgment; both were mixed into
one list.

## Decision

Restructure the skill as an ordered, six-stage pipeline: **generate → mentally
compile → lint → review → refactor → final audit**. Each stage has exactly
one job. Stages 3 and 6 both run the same script (`check.py`) — see
[ADR 0002](0002-stage6-reruns-stage3.md) for why that specific pairing
matters. Stages 2, 4 are pure-reasoning steps with no tool support, by
design — see [ADR 0004](0004-why-no-autofix.md) for the related decision not
to auto-fix.

## Consequences

- The skill's `SKILL.md` frontmatter and structure now describe a sequence,
  not a bag of rules — an agent following it can't as easily skip a step
  without it being visible in what it produces (e.g., no stage-3 output to
  compare stage 6 against).
- Every new rule has to be placed in exactly one stage (`"stage":
  "lint" | "review"` in `data/rules.json`), which forces an explicit answer
  to "can a script check this, or does it need judgment" at the time the
  rule is added, rather than leaving it ambiguous.
- The rule-first framing ("7 rules") is now secondary in the project's own
  positioning to the pipeline framing ("6 stages") — the pipeline is what's
  distinctive; the rules are what stage 3/6 happen to check today, and that
  set can grow independently (see [ADR 0003](0003-why-stdlib-only.md) is
  unrelated, but rule set growth is tracked separately from pipeline
  changes via `rule_set_version` in `data/rules.json`).
