from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from self_healing_agent.agent import run_self_heal  # noqa: E402
from self_healing_agent.llm_client import get_llm_runtime_info  # noqa: E402


def _read_log_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-16", errors="ignore")
    return text.replace("\x00", "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run self-healing agent on CI failure logs")
    parser.add_argument("--log-file", required=True, help="Path to CI failure log")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--output", default="self_heal_result.json", help="Result JSON path")
    args = parser.parse_args()

    log_path = Path(args.log_file)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    runtime = get_llm_runtime_info()
    print(
        "LLM runtime:",
        json.dumps(
            {
                "provider": runtime.get("provider"),
                "configured": runtime.get("configured"),
                "model": runtime.get("model"),
                "base_url": runtime.get("base_url"),
                "api_key_present": runtime.get("api_key_present"),
            }
        ),
    )

    state = run_self_heal(
        log_text=_read_log_text(log_path),
        repo_root=str(Path(args.repo_root).resolve()),
    )

    output_path = Path(args.output)
    output_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print("Root cause:", state.get("root_cause"))
    print("Fix applied:", state.get("fix_applied"))
    print("Validation passed:", state.get("validation_ok"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
