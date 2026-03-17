# Self-Healing CI/CD Agent — Demo Deck (10 Slides)

## Slide 1 — Title
**Title:** Self-Healing CI/CD Agent
**Subtitle:** From failed pipeline to auto-fix PR
**Footer:** Anurag VM | LangGraph + GitHub Actions + LLM

**Speaker notes (15s):**
- This demo shows how a failed CI run can trigger an autonomous agent that proposes and opens a fix PR.

---

## Slide 2 — Problem Statement
**Title:** Why This Matters
- CI failures are frequent and often repetitive
- Engineers spend time on diagnosis + small fixes
- Mean Time To Repair (MTTR) impacts release velocity

**Speaker notes (20s):**
- Most failures are routine: off-by-one errors, lint failures, import issues.
- The goal is to reduce manual triage for these common patterns.

---

## Slide 3 — Proposed Solution
**Title:** Self-Healing Pipeline
- Detect CI failure automatically
- Parse and analyze failure logs
- Propose + apply minimal fix
- Re-run checks
- Create auto-fix PR only when validated

**Speaker notes (20s):**
- The system is safe-by-default: no PR if validation fails.

---

## Slide 4 — Architecture
**Title:** High-Level Architecture
- GitHub Actions workflow (`CI + Self-Heal`)
- LangGraph state machine (`collect → analyze → propose → apply → validate`)
- Rule-based fixers + optional LLM suggestion
- Auto-PR via `peter-evans/create-pull-request`
- Diagram source: `docs/self_heal_architecture.mmd`

**Speaker notes (30s):**
- Rule-based fixes handle known classes quickly.
- LLM is fallback/assist for broader issues.

---

## Slide 5 — LangGraph Flow
**Title:** Stateful Agent Loop
- `AgentState`: log text, attempts, root cause, fix, validation status
- Conditional loop supports multi-step healing (`max_attempts=3`)
- Uses latest validation output as next-iteration context

**Speaker notes (25s):**
- This is key for complex scenarios where one fix reveals the next failure.

---

## Slide 6 — Demo Scenarios
**Title:** Scenarios We Can Demonstrate
- Basic: `simulate_failure` (unit-test fail)
- Basic: `simulate_lint_failure` (F401 lint fail)
- Advanced: `simulate_scenario=nonmath_wordcount`
- Advanced: `simulate_scenario=multi_failure`
- Advanced: `simulate_scenario=lint_and_test`

**Speaker notes (20s):**
- Multi-failure scenario proves sequential healing behavior.

---

## Slide 7 — Live Demo Script
**Title:** What We Show Live
1. Trigger workflow with failing scenario
2. `ci` turns red and uploads failure log
3. `self_heal` analyzes logs + applies fix
4. Recheck passes
5. Auto-PR is created (`self-heal/<run_id>-<attempt>`)

**Speaker notes (40s):**
- Open Actions run summary (`Run Mode` + `Self-Heal PR Decision`) to explain exactly why PR is or isn’t created.

---

## Slide 8 — Safety & Governance
**Title:** Guardrails
- PR only if: token available + changed files + recheck passed
- Skip/No-op path when conditions are not met
- Clear run-time summary for decision transparency
- Branch naming avoids rerun collisions

**Speaker notes (25s):**
- This prevents unsafe or noisy automation.

---

## Slide 9 — Results / Value
**Title:** Expected Impact
- Faster recovery for routine failures
- Lower MTTR
- Less developer interruption
- Better CI reliability and throughput

**Speaker notes (20s):**
- Start with routine failures, then expand patterns over time.

---

## Slide 10 — Roadmap
**Title:** What’s Next
- Add more fix patterns (imports, formatting, type errors)
- Add confidence scoring + approval policy
- Add metrics dashboard (success rate, MTTR reduction)
- Integrate notifications (Slack/Teams)

**Speaker notes (20s):**
- Position this as phase 1 of autonomous DevOps operations.

---

## Appendix A — Backup Talking Points
- Why `AUTO_PR_TOKEN` is needed in restricted repos
- Why `ci` can be red while `self_heal` still runs
- How to debug PR creation conditions from summary

## Appendix B — Presenter Checklist
- Verify `main` is green before demo
- Confirm `AUTO_PR_TOKEN` secret exists
- Keep one prepared fail-case branch ready
- Keep Actions page and PR tab open in separate tabs

## Appendix C — Diagram
- Use `docs/self_heal_architecture.mmd` as the architecture visual in Slide 4.
