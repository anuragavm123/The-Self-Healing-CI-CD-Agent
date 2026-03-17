from pathlib import Path

from self_healing_agent.fixers import propose_fix


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_propose_fix_uses_llm_for_syntax_expected_expression(tmp_path: Path) -> None:
    _write_file(
        tmp_path / "src" / "math_utils.py",
        """def factorial(number: int) -> int:
    result =
    for value in range(2, number + 1):
        result *= value
    return result
""",
    )

    log_text = """E     File \"/home/runner/work/The-Self-Healing-CI-CD-Agent/The-Self-Healing-CI-CD-Agent/src/math_utils.py\", line 2
E       result =
E                ^
E   SyntaxError: invalid syntax
"""
    llm_suggestion = {
        "reason": "Initialize accumulator",
        "file_path": "src/math_utils.py",
        "old_code": "result =",
        "new_code": "result = 1",
    }

    fix = propose_fix(log_text=log_text, repo_root=tmp_path, llm_suggestion=llm_suggestion)

    assert fix is not None
    assert fix["file_path"] == "src/math_utils.py"
    assert fix["old_code"] == "result ="
    assert fix["new_code"] == "result = 1"


def test_propose_fix_returns_none_for_syntax_error_without_llm(tmp_path: Path) -> None:
    _write_file(
        tmp_path / "src" / "math_utils.py",
        """def find_first_even(values: list[int]) -> int | None:
    for value in values:
        if value % 2 == 0
            return value
    return None
""",
    )

    log_text = """E   SyntaxError: expected ':'"""
    fix = propose_fix(log_text=log_text, repo_root=tmp_path, llm_suggestion=None)

    assert fix is None


def test_propose_fix_keeps_rule_based_non_syntax_fallback(tmp_path: Path) -> None:
    _write_file(
        tmp_path / "src" / "math_utils.py",
        """def add(a: int, b: int) -> int:
    return a + b + 1
""",
    )

    log_text = """FAILED tests/test_math_utils.py::test_add_two_positive_numbers
assert add(2, 2) == 4
"""

    fix = propose_fix(log_text=log_text, repo_root=tmp_path, llm_suggestion=None)

    assert fix is not None
    assert fix["file_path"] == "src/math_utils.py"
    assert fix["new_code"] == "return a + b"
