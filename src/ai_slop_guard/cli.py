#!/usr/bin/env python3
"""
ai_slop_guard/cli.py

Static, single-file checks for common AI-agent code smells. Rule IDs match
ai_slop_guard/data/rules.json (see ai_slop_guard/references/registry.md for the full list).

Standard library only. No network calls. No files are written or installed.

Usage:
    slop-guard <file_or_dir> [<file_or_dir> ...]
    slop-guard --json <file_or_dir> [<file_or_dir> ...]
    slop-guard --explain ASG002

Exit code is non-zero if any finding was reported, so this is safe to use
as a CI gate.
"""

import ast
import json
import re
import sys
from pathlib import Path

RULES_JSON = Path(__file__).resolve().parent / "data" / "rules.json"

PY_SUFFIXES = {".py"}
JS_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}
SUPPORTED = PY_SUFFIXES | JS_SUFFIXES

DEBUG_JS_RE = re.compile(r"\bconsole\.(log|debug|info)\s*\(")
EMPTY_CATCH_JS_RE = re.compile(
    r"catch\s*(\([^)]*\))?\s*\{\s*(console\.\w+\([^)]*\)\s*;?\s*)?\}"
)

IGNORE_MARKER = "slop-guard: ignore"


def _is_ignored(source_lines: list[str], lineno: int) -> bool:
    if 1 <= lineno <= len(source_lines):
        return IGNORE_MARKER in source_lines[lineno - 1]
    return False


def _out(*args, **kwargs) -> None:
    print(*args, **kwargs)


class Finding:
    __slots__ = ("path", "line", "rule_id", "title", "reason", "fix")

    def __init__(self, path, line, rule_id, title, reason, fix):
        self.path = path
        self.line = line
        self.rule_id = rule_id
        self.title = title
        self.reason = reason
        self.fix = fix

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "line": self.line,
            "rule_id": self.rule_id,
            "title": self.title,
            "reason": self.reason,
            "fix": self.fix,
        }

    def render(self) -> str:
        return (
            f"{self.rule_id}  {self.title}  ({self.path}:{self.line})\n"
            f"  Reason: {self.reason}\n"
            f"  Suggested fix: {self.fix}"
        )


def _collect_dunder_all_exports(tree: ast.AST) -> set[str]:
    exported: set[str] = set()

    def _names_from(value: ast.AST) -> None:
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            for elt in value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    exported.add(elt.value)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
                _names_from(node.value)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "__all__":
                _names_from(node.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "__all__" and node.value:
                _names_from(node.value)

    return exported


def check_python(path: Path, source: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        return [
            Finding(
                path, e.lineno or 0, "PARSE", "Syntax error",
                str(e), "Fix the syntax error before running further checks.",
            )
        ]

    source_lines = source.splitlines()

    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                imported[name] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                name = alias.asname or alias.name
                imported[name] = node.lineno

    used_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used_names |= _collect_dunder_all_exports(tree)

    for name, lineno in imported.items():
        if name not in used_names:
            findings.append(
                Finding(
                    path, lineno, "ASG001", f'Unused import "{name}"',
                    f"'{name}' is imported on line {lineno} but never referenced.",
                    f"Remove the import of '{name}'.",
                )
            )

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            body = node.body
            is_trivial = len(body) == 1 and isinstance(body[0], (ast.Pass, ast.Continue))
            is_log_only = (
                len(body) == 1
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Call)
            )
            bare_or_broad = node.type is None or (
                isinstance(node.type, ast.Name) and node.type.id == "Exception"
            )
            if bare_or_broad and (is_trivial or is_log_only):
                exc_kind = "bare except" if node.type is None else "except Exception"
                findings.append(
                    Finding(
                        path, node.lineno, "ASG003", f"Catch-all exception handling ({exc_kind})",
                        "This except block only passes, continues, or logs — it silently "
                        "swallows whatever error occurs instead of handling it.",
                        "Catch the specific exception type you expect, handle it, or "
                        "re-raise with added context (e.g. `raise RuntimeError(...) from e`).",
                    )
                )

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
            and not _is_ignored(source_lines, node.lineno)
        ):
            findings.append(
                Finding(
                    path, node.lineno, "ASG007", "Leftover debug output",
                    "print(...) call left in code.",
                    "Remove it, or route through the project's logger if the output is "
                    "deliberate. If it's intentional CLI output, mark the line with "
                    f"`# {IGNORE_MARKER}`.",
                )
            )

    defined = {}
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
            and not node.name.startswith("test_")
            and not node.decorator_list
        ):
            defined[node.name] = node.lineno
    called = {
        n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for dec in node.decorator_list:
                for n in ast.walk(dec):
                    if isinstance(n, ast.Name):
                        called.add(n.id)
    for name, lineno in defined.items():
        if name not in called and name != "main":
            findings.append(
                Finding(
                    path, lineno, "ASG002", f'Dead code candidate: "{name}"',
                    f"'{name}' is never called anywhere else in this file.",
                    "If it's genuinely unused, delete it. If it's called from another "
                    "file, this is a false positive — the script only sees one file at "
                    "a time; verify manually before keeping it.",
                )
            )

    return findings


def check_js(path: Path, source: str) -> list[Finding]:
    findings: list[Finding] = []

    for lineno, line in enumerate(source.splitlines(), start=1):
        if DEBUG_JS_RE.search(line) and IGNORE_MARKER not in line:
            findings.append(
                Finding(
                    path, lineno, "ASG007", "Leftover debug output",
                    "console.log/debug/info(...) call left in code.",
                    "Remove it, or route through the project's logger. If it's "
                    f"intentional, mark the line with `// {IGNORE_MARKER}`.",
                )
            )

    for m in EMPTY_CATCH_JS_RE.finditer(source):
        lineno = source[: m.start()].count("\n") + 1
        findings.append(
            Finding(
                path, lineno, "ASG003", "Catch-all exception handling",
                "This catch block is empty or only logs — it silently swallows "
                "whatever error occurs instead of handling it.",
                "Handle the specific error, or rethrow with added context "
                "(`throw new Error('...', { cause: e })`).",
            )
        )

    import_re = re.compile(r"^\s*import\s*\{([^}]+)\}\s*from\s*['\"][^'\"]+['\"]", re.M)
    for m in import_re.finditer(source):
        names = [n.strip().split(" as ")[-1].strip() for n in m.group(1).split(",") if n.strip()]
        lineno = source[: m.start()].count("\n") + 1
        for name in names:
            occurrences = len(re.findall(r"\b" + re.escape(name) + r"\b", source))
            if occurrences <= 1:
                findings.append(
                    Finding(
                        path, lineno, "ASG001", f'Unused import "{name}"',
                        f"'{name}' is imported on line {lineno} but never referenced.",
                        f"Remove '{name}' from the import statement.",
                    )
                )

    return findings


def check_file(path: Path) -> list[Finding]:
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    if path.suffix in PY_SUFFIXES:
        return check_python(path, source)
    if path.suffix in JS_SUFFIXES:
        return check_js(path, source)
    return []


def iter_targets(args: list[str]):
    for arg in args:
        p = Path(arg)
        if p.is_dir():
            for suffix in SUPPORTED:
                yield from p.rglob(f"*{suffix}")
        elif p.is_file():
            yield p


def explain(rule_id: str) -> int:
    if not RULES_JSON.exists():
        _out(f"rules.json not found at {RULES_JSON}")
        return 2
    payload = json.loads(RULES_JSON.read_text(encoding="utf-8"))
    rule = next((r for r in payload["rules"] if r["id"] == rule_id.upper()), None)
    if rule is None:
        _out(f"Unknown rule ID: {rule_id}")
        return 2

    phil = rule.get("philosophy")
    _out(f"{rule['id']} — {rule['name']} ({rule['status']})")
    _out()
    _out(rule["description"])
    if phil:
        _out()
        _out(f"Why: {phil['why']}")
        _out()
        _out("Example (flagged):")
        _out(f"  {phil['example']}")
        _out()
        _out("Counterexample (not flagged):")
        _out(f"  {phil['counterexample']}")
        _out()
        _out(f"Tradeoffs: {phil['tradeoffs']}")
    return 0


def main(argv: list[str]) -> int:
    if "--explain" in argv:
        idx = argv.index("--explain")
        if idx + 1 >= len(argv):
            _out("Usage: slop-guard --explain ASGxxx")
            return 2
        return explain(argv[idx + 1])

    as_json = "--json" in argv
    targets = [a for a in argv if a != "--json"]

    if not targets:
        _out(__doc__)
        return 2

    all_findings: list[Finding] = []
    for target in iter_targets(targets):
        all_findings.extend(check_file(target))

    all_findings.sort(key=lambda f: (str(f.path), f.line))

    if as_json:
        _out(json.dumps([f.to_dict() for f in all_findings], indent=2))
        return 1 if all_findings else 0

    if not all_findings:
        _out("ai-slop-guard: no findings.")
        return 0

    for f in all_findings:
        _out(f.render())
        _out()
    _out(f"ai-slop-guard: {len(all_findings)} finding(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
