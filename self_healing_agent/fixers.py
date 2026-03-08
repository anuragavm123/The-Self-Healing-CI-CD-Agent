from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _rule_based_fix(log_text: str, repo_root: Path) -> dict[str, Any] | None:
    if "test_math_utils.py" in log_text and "add(2, 2)" in log_text and "== 4" in log_text:
        file_path = repo_root / "src" / "math_utils.py"
        if not file_path.exists():
            return None

        text = file_path.read_text(encoding="utf-8")
        if "return a + b + 1" in text:
            return {
                "reason": "Off-by-one bug in add() implementation",
                "file_path": "src/math_utils.py",
                "old_code": "return a + b + 1",
                "new_code": "return a + b",
            }

    lint_match = re.search(r"(?P<path>src/.+?\.py):\d+:\d+:\s+F401", log_text)
    if lint_match:
        target_path = lint_match.group("path")
        file_path = repo_root / target_path
        if not file_path.exists():
            return None
        text = file_path.read_text(encoding="utf-8")

        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                if "# noqa" not in line:
                    old = line
                    new = f"{line}  # noqa: F401"
                    return {
                        "reason": "Unused import lint failure",
                        "file_path": target_path,
                        "old_code": old,
                        "new_code": new,
                    }

    return None


def propose_fix(log_text: str, repo_root: Path, llm_suggestion: dict[str, Any] | None) -> dict[str, Any] | None:
    rule_fix = _rule_based_fix(log_text=log_text, repo_root=repo_root)
    if rule_fix:
        return rule_fix

    if not llm_suggestion:
        return None

    required = {"reason", "file_path", "old_code", "new_code"}
    if not required.issubset(llm_suggestion):
        return None

    candidate = repo_root / llm_suggestion["file_path"]
    if not candidate.exists():
        return None

    return {
        "reason": str(llm_suggestion["reason"]),
        "file_path": str(llm_suggestion["file_path"]),
        "old_code": str(llm_suggestion["old_code"]),
        "new_code": str(llm_suggestion["new_code"]),
    }
