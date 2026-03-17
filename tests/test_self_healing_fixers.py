from pathlib import Path

from self_healing_agent.fixers import propose_fix


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_propose_fix_handles_incomplete_assignment_before_multiply(tmp_path: Path) -> None:
    _write_file(
        tmp_path / "src" / "math_utils.py",
        """def factorial(number: int) -> int:
    result =
    for value in range(2, number + 1):
        result *= value
    return result
""",
    )

    log_text = """src/math_utils.py:2:14: SyntaxError: Expected an expression"""
    fix = propose_fix(log_text=log_text, repo_root=tmp_path, llm_suggestion=None)

    assert fix is not None
    assert fix["file_path"] == "src/math_utils.py"
    assert fix["old_code"] == "    result ="
    assert fix["new_code"] == "    result = 1"


def test_propose_fix_handles_incomplete_assignment_before_add(tmp_path: Path) -> None:
    _write_file(
        tmp_path / "src" / "math_utils.py",
        """def sum_upto(limit: int) -> int:
    total =
    for value in range(limit + 1):
        total += value
    return total
""",
    )

    log_text = """src/math_utils.py:2:12: SyntaxError: Expected an expression"""
    fix = propose_fix(log_text=log_text, repo_root=tmp_path, llm_suggestion=None)

    assert fix is not None
    assert fix["file_path"] == "src/math_utils.py"
    assert fix["old_code"] == "    total ="
    assert fix["new_code"] == "    total = 0"
