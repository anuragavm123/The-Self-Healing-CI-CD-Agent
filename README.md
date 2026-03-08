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
  - `AUTO_PR_TOKEN` (optional PAT fallback for creating PRs when `GITHUB_TOKEN` is restricted)
   - Optional repo vars:
     - `LLM_PROVIDER` = `openai`, `deepseek`, or `ollama`
     - `OPENAI_MODEL` (default: `gpt-4o`)
     - `DEEPSEEK_MODEL` (default: `deepseek-coder`)
     - `OLLAMA_MODEL` (default: `qwen2.5-coder:7b`)
     - `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434/v1`)

2. Ensure default branch is one of: `main` / `develop` (or trigger via `workflow_dispatch`).
3. In **Settings → Actions → General**, set:
  - **Workflow permissions**: `Read and write permissions`
  - Enable **Allow GitHub Actions to create and approve pull requests**

### Using local Ollama (no paid API key)

- Use a **self-hosted GitHub runner** on the same machine/network as Ollama.
- Set repo variable `LLM_PROVIDER=ollama`.
- Ensure Ollama is running and model is pulled, for example:
  - `ollama pull qwen2.5-coder:7b`
  - `ollama serve`
- If Ollama is on another host, set `OLLAMA_BASE_URL` accordingly.

## Demo Script (what to show live)

1. Start with green pipeline on current code.
2. Trigger **Actions → CI + Self-Heal → Run workflow** and choose one:
  - `simulate_failure = true` for a test failure demo, or
  - `simulate_lint_failure = true` for a lint (`F401`) failure demo.
  - Do not set both to `true` in the same run (workflow will fail fast).
3. (Alternative) Manually break `src/math_utils.py` by changing `return a + b` to `return a + b + 1`, then push.
4. Show CI failure in Actions.
5. Show self-heal job reading `ci_failure.log`, identifying the root cause, applying fix.
6. Show auto-created PR (`self-heal/<run_id>`) with corrected code.
7. Merge PR and show pipeline back to green.

Tip: each run now writes the selected mode to the GitHub job summary (`CI + Self-Heal Run Mode`).

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
- Any small doc-only commit can be used to trigger a fresh demo run safely.
