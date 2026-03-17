from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _resolve_repo_relative_path(raw_path: str) -> str | None:
    normalized = raw_path.replace("\\", "/")
    if normalized.startswith("src/"):
        return normalized

    marker = "/src/"
    if marker in normalized:
        return "src/" + normalized.split(marker, 1)[1]

    return None


def _extract_syntax_location(log_text: str) -> tuple[str, int] | None:
    ruff_style = re.search(
        r"(?P<path>src/.+?\.py):(?P<line>\d+):\d+:\s+SyntaxError:\s+Expected an expression",
        log_text,
    )
    if ruff_style:
        path = _resolve_repo_relative_path(ruff_style.group("path"))
        if path:
            return path, int(ruff_style.group("line"))

    pytest_style = re.search(
        r"File\s+\"(?P<path>[^\"]+?\.py)\",\s+line\s+(?P<line>\d+)",
        log_text,
    )
    if pytest_style and "SyntaxError" in log_text:
        path = _resolve_repo_relative_path(pytest_style.group("path"))
        if path:
            return path, int(pytest_style.group("line"))

    return None


def _syntax_expected_expression_fix(log_text: str, repo_root: Path) -> dict[str, Any] | None:
    location = _extract_syntax_location(log_text)
    if not location:
        return None

    target_path, line_number = location
    file_path = repo_root / target_path
    if not file_path.exists():
        return None

    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    index = line_number - 1
    if index < 0 or index >= len(lines):
        return None

    broken_line = lines[index]
    assign_match = re.match(r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=\s*$", broken_line)
    if not assign_match:
        return None

    var_name = assign_match.group("name")
    indent = assign_match.group("indent")

    # Infer a safe initializer from nearby update patterns.
    nearby = "\n".join(lines[index + 1 : index + 5])
    if re.search(rf"\b{re.escape(var_name)}\s*\*=", nearby):
        replacement = f"{indent}{var_name} = 1"
    elif re.search(rf"\b{re.escape(var_name)}\s*\+=", nearby):
        replacement = f"{indent}{var_name} = 0"
    else:
        return None

    return {
        "reason": "SyntaxError from incomplete assignment (missing expression)",
        "file_path": target_path,
        "old_code": broken_line,
        "new_code": replacement,
    }


def _rule_based_fix(log_text: str, repo_root: Path) -> dict[str, Any] | None:
    syntax_fix = _syntax_expected_expression_fix(log_text=log_text, repo_root=repo_root)
    if syntax_fix:
        return syntax_fix

    if "test_math_utils.py" in log_text and "add(2, 2)" in log_text and "== 4" in log_text:
        file_path = repo_root / "src" / "math_utils.py"
        if not file_path.exists():
            return None

        text = file_path.read_text(encoding="utf-8")
        off_by_one_match = re.search(r"return\s+a\s*\+\s*b\s*\+\s*1\b", text)
        if off_by_one_match:
            return {
                "reason": "Off-by-one bug in add() implementation",
                "file_path": "src/math_utils.py",
                "old_code": off_by_one_match.group(0),
                "new_code": "return a + b",
            }

    if "test_word_count_handles_irregular_spacing" in log_text and "word_count(" in log_text:
        file_path = repo_root / "src" / "math_utils.py"
        if not file_path.exists():
            return None

        text = file_path.read_text(encoding="utf-8")
        off_by_one_match = re.search(r"return\s+count\s*\+\s*1\b", text)
        if off_by_one_match:
            return {
                "reason": "Off-by-one bug in word_count() implementation",
                "file_path": "src/math_utils.py",
                "old_code": off_by_one_match.group(0),
                "new_code": "return count",
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
