# CLAUDE.md

This project uses the **ai-slop-guard** skill — see `ai-slop-guard/SKILL.md`
for the full 6-stage pipeline (generate → mentally compile → lint → review →
refactor → final audit).

If your tool supports Claude Skills natively, it should discover that file
automatically. If not, follow this manually before treating any coding task
as finished:

1. **Compile mentally** — read what you wrote, don't run it yet. Confirm
   names resolve, arities match, branches return what's expected.
2. **Lint** — run `python3 ai-slop-guard/scripts/check.py <changed_file_or_dir>`.
   Fix everything it reports, or state in one sentence why a finding is a
   false positive.
3. **Review** — by hand, since the script can't see this: don't duplicate
   logic that exists elsewhere in the project, don't guard against
   `null`/`undefined` a type already rules out, don't leave comments that
   just restate the code.
4. **Refactor** — apply what steps 2–3 found, structure only, no behavior
   change.
5. **Final audit** — re-run step 2's command. The finding count must not be
   higher than before the refactor.

Full rule catalog with before/after examples: `ai-slop-guard/references/rules.md`.
Every finding has a rule ID (ASG001–ASG007); add `--json` to either command
for machine-readable output. Known false positives: `docs/known-limitations.md`.
