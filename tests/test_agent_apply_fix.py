from pathlib import Path

from self_healing_agent.agent import apply_code_fix


def test_apply_code_fix_fallback_matches_stripped_line(tmp_path: Path) -> None:
    target = tmp_path / "src" / "math_utils.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """def find_first_even(values: list[int]) -> int | None:
    for value in values:
        if value % 2 == 0
            return value
    return None
""",
        encoding="utf-8",
    )

    state = {
        "repo_root": str(tmp_path),
        "log_text": "",
        "attempt": 0,
        "max_attempts": 3,
        "root_cause": "Python syntax error",
        "fix": {
            "reason": "LLM fix",
            "file_path": "src/math_utils.py",
            "old_code": "if value % 2 == 0",
            "new_code": "if value % 2 == 0:",
        },
        "fix_applied": False,
        "validation_ok": False,
        "notes": "",
    }

    updated_state = apply_code_fix(state)

    assert updated_state["fix_applied"] is True
    updated_text = target.read_text(encoding="utf-8")
    assert "        if value % 2 == 0:" in updated_text
