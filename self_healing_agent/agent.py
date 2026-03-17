from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from self_healing_agent.fixers import propose_fix
from self_healing_agent.llm_client import suggest_fix_from_log_with_meta


class AgentState(TypedDict):
    repo_root: str
    log_text: str
    attempt: int
    max_attempts: int
    root_cause: str
    fix: dict[str, Any] | None
    fix_applied: bool
    validation_ok: bool
    notes: str


def collect_failure(state: AgentState) -> AgentState:
    lines = state["log_text"].splitlines()
    tail = "\n".join(lines[-80:])
    return {
        **state,
        "notes": f"Collected failure trace ({len(lines)} log lines).\n{tail[:2500]}",
    }


def analyze_root_cause(state: AgentState) -> AgentState:
    log_text = state["log_text"]
    root_cause = "Unknown CI failure"

    if "AssertionError" in log_text or ("FAILED" in log_text and "assert" in log_text):
        root_cause = "Unit test assertion failure"
    elif "SyntaxError" in log_text:
        root_cause = "Python syntax error"
    elif "ruff" in log_text or "F401" in log_text:
        root_cause = "Linting error"
    elif "ModuleNotFoundError" in log_text:
        root_cause = "Missing dependency or import path issue"

    return {**state, "root_cause": root_cause}


def propose_code_fix(state: AgentState) -> AgentState:
    repo_root = Path(state["repo_root"])
    llm_suggestion, llm_meta = suggest_fix_from_log_with_meta(state["log_text"])
    candidate = propose_fix(
        log_text=state["log_text"],
        repo_root=repo_root,
        llm_suggestion=llm_suggestion,
    )
    suggestion_keys = []
    if isinstance(llm_suggestion, dict):
        suggestion_keys = sorted(llm_suggestion.keys())

    extra_notes = (
        state.get("notes", "")
        + "\nLLM suggestion present: "
        + str(llm_suggestion is not None)
        + "; llm_meta: "
        + llm_meta
        + "; keys: "
        + ",".join(suggestion_keys)
        + "; candidate selected: "
        + str(candidate is not None)
    )
    return {**state, "fix": candidate, "notes": extra_notes}


def apply_code_fix(state: AgentState) -> AgentState:
    fix = state["fix"]
    if not fix:
        return {**state, "fix_applied": False}

    target = Path(state["repo_root"]) / fix["file_path"]
    text = target.read_text(encoding="utf-8")

    old_code = str(fix["old_code"])
    new_code = str(fix["new_code"])

    if old_code in text:
        updated = text.replace(old_code, new_code, 1)
        target.write_text(updated, encoding="utf-8")
        return {**state, "fix_applied": True}

    # Fallback for model output that misses indentation or trailing spaces.
    stripped_old = old_code.strip()
    if not stripped_old:
        return {**state, "fix_applied": False}

    lines = text.splitlines(keepends=True)
    match_indexes = [i for i, line in enumerate(lines) if line.strip() == stripped_old]
    if len(match_indexes) != 1:
        return {**state, "fix_applied": False}

    idx = match_indexes[0]
    old_line = lines[idx]
    old_indent = old_line[: len(old_line) - len(old_line.lstrip(" "))]
    line_ending = "\n" if old_line.endswith("\n") else ""

    replacement = new_code
    if replacement and replacement == replacement.lstrip(" "):
        replacement = old_indent + replacement

    lines[idx] = replacement.rstrip("\n") + line_ending
    updated = "".join(lines)
    target.write_text(updated, encoding="utf-8")
    return {**state, "fix_applied": True}


def validate_fix(state: AgentState) -> AgentState:
    if not state["fix_applied"]:
        return {**state, "validation_ok": False}

    result = subprocess.run(
        ["python", "-m", "pytest", "-q"],
        cwd=state["repo_root"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    ok = result.returncode == 0
    latest_log = result.stdout + "\n" + result.stderr
    return {
        **state,
        "validation_ok": ok,
        "attempt": state["attempt"] + 1,
        "log_text": latest_log,
        "notes": (
            state.get("notes", "")
            + "\nValidation output:\n"
            + latest_log[-3000:]
        ),
    }


def next_after_apply(state: AgentState) -> str:
    if not state["fix_applied"]:
        return END
    return "validate_fix"


def next_after_validate(state: AgentState) -> str:
    if state["validation_ok"]:
        return END
    if state["attempt"] >= state["max_attempts"]:
        return END
    return "propose_code_fix"


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("collect_failure", collect_failure)
    graph.add_node("analyze_root_cause", analyze_root_cause)
    graph.add_node("propose_code_fix", propose_code_fix)
    graph.add_node("apply_code_fix", apply_code_fix)
    graph.add_node("validate_fix", validate_fix)

    graph.set_entry_point("collect_failure")
    graph.add_edge("collect_failure", "analyze_root_cause")
    graph.add_edge("analyze_root_cause", "propose_code_fix")
    graph.add_edge("propose_code_fix", "apply_code_fix")
    graph.add_conditional_edges("apply_code_fix", next_after_apply)
    graph.add_conditional_edges("validate_fix", next_after_validate)

    return graph.compile()


def run_self_heal(log_text: str, repo_root: str) -> AgentState:
    agent = build_agent()
    initial: AgentState = {
        "repo_root": repo_root,
        "log_text": log_text,
        "attempt": 0,
        "max_attempts": 3,
        "root_cause": "",
        "fix": None,
        "fix_applied": False,
        "validation_ok": False,
        "notes": "",
    }
    return agent.invoke(initial)
