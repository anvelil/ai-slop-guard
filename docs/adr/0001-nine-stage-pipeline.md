# 0001. Nine-stage pipeline instead of a six-stage pipeline

## Status

Accepted (0.3.0) - Supersedes 0.2.0 (Six-stage pipeline)

## Context

The 6-stage pipeline (0.2.0) combined planning, code generation, testing, and regression checking into a compact flow. However, real-world development requires explicit stage division to ensure the agent understands goals, checks duplicate logic beforehand, validates syntax mechanically before linting, and runs comprehensive test suites before the final audit.

## Decision

Restructure the project as an ordered, nine-stage pipeline: **analyze → plan → generate → mentally compile → syntax check → lint → review → refactor → final audit**. 

Each stage has exactly one job. 
- Stage 2 (Plan) explicitly checks for duplicate code (`ASG004`).
- Stage 5 (Syntax check) compiles code mechanically (e.g., using `python -m py_compile` or similar) to ensure it compiles.
- Stage 6 (Lint) runs the static code smell checks (`slop-guard`).
- Stage 9 (Final audit) re-runs the static code smell checks (`slop-guard`) to ensure the count did not go up.

Stages 6 and 9 run the same command (`slop-guard`) — see [ADR 0002](0002-stage9-reruns-stage6.md) for why that specific pairing matters.

## Consequences

- The pipeline is more comprehensive, detailing exactly how planning, syntax checks, and final verification fit into the lifecycle.
- Rules now map to `"plan"`, `"lint"`, or `"review"` stages in `data/rules.json`.
- More explicit separation of mechanical (tool-checked) steps versus pure-reasoning steps.
