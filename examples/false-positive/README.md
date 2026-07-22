# Known, current false positives

Real cases where `check.py` still produces a false positive today, kept as
fixtures so the limitation is demonstrated rather than just asserted in
prose. Cross-reference: `docs/known-limitations.md`.

## cross_file_call.py

```bash
slop-guard examples/false-positive/cross_file_call.py
```

Flags `init_app` as ASG002 dead code. In the real project this is adapted
from (Flask's tutorial app), `init_app` is genuinely called — from
`flaskr/__init__.py`'s `create_app()`, a different file. The checker only
sees one file at a time, so it has no way to know that (see
`docs/philosophy.md` for the reasoning behind that tradeoff). ADR 0003
covers why cross-file resolution isn't something the project reaches for
just to close this one gap.
