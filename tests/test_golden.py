#!/usr/bin/env python3
"""
tests/test_golden.py

Runs ai-slop-guard/scripts/check.py --json against every fixture in
tests/golden/<case>/input.py and compares it byte-for-byte against
tests/golden/<case>/expected.json. If the checker's output ever changes
for these fixtures — a new finding, a changed message, a fixed false
positive — this test fails and shows exactly what changed, on purpose:
that's the point of a golden test, catching drift you didn't mean to
introduce.

Uses only the standard library (unittest, json, subprocess) — no pytest,
no dependencies to install, consistent with the rest of this project.

Usage:
    python3 -m unittest tests.test_golden -v
    # or just:
    python3 tests/test_golden.py
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK_PY = ROOT / "ai-slop-guard" / "scripts" / "check.py"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def discover_cases():
    return sorted(p for p in GOLDEN_DIR.iterdir() if p.is_dir())


class GoldenTests(unittest.TestCase):
    pass


def _make_test(case_dir: Path):
    def test(self):
        input_file = case_dir / "input.py"
        expected_file = case_dir / "expected.json"
        self.assertTrue(input_file.exists(), f"missing fixture: {input_file}")
        self.assertTrue(expected_file.exists(), f"missing golden file: {expected_file}")

        result = subprocess.run(
            [sys.executable, str(CHECK_PY), "--json", "input.py"],
            cwd=case_dir,
            capture_output=True,
            text=True,
        )
        actual = json.loads(result.stdout)
        expected = json.loads(expected_file.read_text(encoding="utf-8"))
        self.assertEqual(
            actual,
            expected,
            f"\ncheck.py output for {case_dir.name}/input.py drifted from "
            f"expected.json.\nIf this drift is intentional (e.g. you fixed a "
            f"false positive or improved a message), regenerate the golden "
            f"file with:\n"
            f"  cd {case_dir} && python3 {CHECK_PY} --json input.py > expected.json\n"
            f"and review the diff before committing it.",
        )

    return test


for _case_dir in discover_cases():
    _test_name = f"test_{_case_dir.name}"
    setattr(GoldenTests, _test_name, _make_test(_case_dir))


if __name__ == "__main__":
    unittest.main()
