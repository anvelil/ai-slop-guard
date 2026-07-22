#!/usr/bin/env python3
"""
tests/test_golden.py
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK_PY = ROOT / "src" / "ai_slop_guard" / "cli.py"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def discover_cases():
    return sorted(p for p in GOLDEN_DIR.iterdir() if p.is_dir())


class GoldenTests(unittest.TestCase):
    pass


def _normalize(findings: list) -> list:
    normalized = []
    for f in findings:
        if f.get("rule_id") == "PARSE":
            f = {**f, "line": None, "reason": None}
        normalized.append(f)
    return normalized


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
            _normalize(actual),
            _normalize(expected),
            f"\nslop-guard output for {case_dir.name}/input.py drifted from "
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
