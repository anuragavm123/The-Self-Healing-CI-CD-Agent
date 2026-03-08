# Self-Healing CI/CD Agent (LangGraph + GitHub Actions)

This demo shows an autonomous CI/CD agent that:
1. Detects a failed test/lint run,
2. Reads pipeline logs,
3. Finds root cause,
4. Applies a fix,
5. Opens a GitHub PR automatically.

## Core Value

Reduce **Mean Time to Repair (MTTR)** for routine failures by moving from alert-only CI to corrective CI.

## Stack

- **LangGraph** for stateful reasoning loops
- **GitHub Actions** for CI trigger/orchestration
- **GPT-4o** (OpenAI) or **DeepSeek-Coder** (OpenAI-compatible endpoint)
- **Python + pytest + ruff** sample project

## Project Layout

- `.github/workflows/ci.yml` — CI + self-heal automation
- `self_healing_agent/agent.py` — LangGraph agent graph
- `self_healing_agent/fixers.py` — deterministic + model-assisted fix proposal
- `self_healing_agent/llm_client.py` — model provider abstraction
- `scripts/run_self_heal.py` — entry script used by workflow
- `src/math_utils.py` + `tests/test_math_utils.py` — sample app/tests

## Setup

1. Add repository secrets/variables:
   - `OPENAI_API_KEY` (for GPT-4o), or
   - `DEEPSEEK_API_KEY` (for DeepSeek)
   - Optional repo vars:
     - `LLM_PROVIDER` = `openai` or `deepseek`
     - `OPENAI_MODEL` (default: `gpt-4o`)
     - `DEEPSEEK_MODEL` (default: `deepseek-coder`)

2. Ensure default branch is one of: `main` / `develop` (or trigger via `workflow_dispatch`).

## Demo Script (what to show live)

1. Start with green pipeline on current code.
2. **Manually break code** in `src/math_utils.py`:
   - Change `return a + b` to `return a + b + 1`
3. Push commit to GitHub.
4. Show CI failure in Actions.
5. Show self-heal job reading `ci_failure.log`, identifying assertion failure, applying fix.
6. Show auto-created PR (`self-heal/<run_id>`) with corrected code.
7. Merge PR and show pipeline back to green.

## Optional local run

```bash
pip install -r requirements.txt
pytest -q
ruff check .

# after producing a failure log
python scripts/run_self_heal.py --log-file ci_failure.log --repo-root .
```

## Notes

- The agent uses deterministic safety-first rules first, then optional model suggestion.
- PR is created only if a fix is applied **and** checks pass after the fix.
- Workflow skips self-heal for PR events and self-heal branches to avoid loops.
