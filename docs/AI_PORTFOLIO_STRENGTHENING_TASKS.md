# AI Portfolio Strengthening Tasks — Executed Plan

This document is both the implementation task pack and the verification checklist for the public portfolio repository. The goal is to demonstrate defensible AI-workflow engineering skills without presenting the project as enterprise production AI.

## Reusable implementation prompt

> Act as a senior AI workflow/control-plane engineer and adversarial portfolio reviewer. Improve `governed-agent-workflow-demo` only with capabilities that are either already evidenced by the author's broader personal R&D or can be fully implemented and tested inside this repository. Prefer deterministic, inspectable Python over framework complexity. For every capability, implement code, add a failure-path test, document the non-claim/limitation, and map the capability to exact source/test files. Do not add RAG, LangChain, LangGraph, embeddings, vector databases, Azure OpenAI, Kubernetes, or commercial/production claims. A task is not complete until code exists, tests pass, demos reproduce, secret scans pass, and the acceptance report identifies evidence.

## Executed tasks

### S01 — Make the task contract explicit and fail closed

**Skill signal:** structured outputs, schema discipline, deterministic orchestration.

**Files:** `src/governed_agent/models.py`, `planning.py`.

**Implementation:** strict task parsing; unknown fields rejected; task includes objective, required artifacts, explicit tool allowlist, provider preference, retry/timeout budget, approval requirement, idempotency key, and optional parent task identity.

**Tests:** `tests/test_planning.py`.

**Completion gate:** malformed/unknown input cannot silently enter execution; explicit allowlist is represented in the task schema.

**Status:** COMPLETE.

### S02 — Implement least-privilege tool execution

**Skill signal:** MCP/tool governance concepts, safety boundaries, fail-closed execution.

**Files:** `src/governed_agent/tools.py`, `engine.py`.

**Implementation:** registered tool metadata contains risk and side-effect flags; every task must explicitly allow the tool selected by the provider; a non-allowlisted action is blocked before side effects.

**Tests:** `test_tool_not_allowlisted_is_blocked` plus path-containment behavior in the artifact tool.

**Completion gate:** provider output alone cannot grant tool access.

**Status:** COMPLETE.

### S03 — Upgrade approvals from a boolean to a bounded authorization artifact

**Skill signal:** human-in-the-loop design, action binding, replay prevention.

**Files:** `src/governed_agent/approvals.py`, `engine.py`.

**Implementation:** approvals carry an ID, actor, task ID, SHA-256 of the exact proposed action, creation time, expiry time, and one-time-use state. The engine validates and consumes approval before executing the side effect.

**Tests:** `tests/test_approval_controls.py`, approval-denied workflow test.

**Completion gate:** modified action, expired approval, replayed approval, or denied approval is rejected.

**Status:** COMPLETE.

### S04 — Implement provider-health state and circuit breaking

**Skill signal:** provider resilience, quota/failure-aware routing, model/provider operations.

**Files:** `src/governed_agent/providers.py`, `router.py`, `engine.py`.

**Implementation:** provider health is `HEALTHY`, `DEGRADED`, or `DOWN`; repeated provider-class failures open a bounded circuit; open circuits are excluded from routing until cooldown; success restores health.

**Tests:** `tests/test_provider_health.py`, provider/rate/timeout tests.

**Completion gate:** an unhealthy provider is demonstrably skipped on a subsequent task while another eligible provider can proceed.

**Status:** COMPLETE.

### S05 — Keep fallback safe and failure-class aware

**Skill signal:** failure taxonomy, safe retries/fallback, side-effect awareness.

**Files:** `src/governed_agent/engine.py`, `providers.py`.

**Implementation:** fallback is permitted only for provider-class failures: unavailable, rate limited, timeout, malformed provider output. Tool failure does not trigger blind cross-provider replay because side effects may have partially occurred.

**Tests:** fallback, tool-failure, timeout, malformed-output and provider-unavailable tests.

**Completion gate:** provider failure can reach the fallback provider; tool failure cannot silently replay.

**Status:** COMPLETE.

### S06 — Add restart-safe idempotency and crash-state detection

**Skill signal:** durable state concepts, restart/recovery engineering, duplicate prevention.

**Files:** `src/governed_agent/state.py`, `engine.py`.

**Implementation:** standard-library SQLite state store records task claims and terminal states. Duplicate idempotency keys survive process restart. A task left in a non-terminal state is not silently replayed after restart; it returns `RECOVERY_REQUIRED` for explicit operator handling.

**Tests:** `tests/test_state_recovery.py`.

**Completion gate:** a second engine process using the same database cannot re-run a completed logical task, and an incomplete prior claim does not auto-replay.

**Status:** COMPLETE.

### S07 — Add tamper-evident execution audit

**Skill signal:** auditability, evidence integrity, security-minded engineering.

**Files:** `src/governed_agent/audit.py`, `engine.py`.

**Implementation:** ordered audit events are linked by SHA-256 hashes. The chain can be kept in memory or persisted as JSONL and reloaded. Task start, provider outcome, approval, tool outcome, verification and completion are auditable events.

**Tests:** `tests/test_audit.py`.

**Completion gate:** modifying a historical event causes integrity verification to fail, including after reload from disk.

**Status:** COMPLETE.

### S08 — Strengthen evidence receipts and completion verification

**Skill signal:** evidence-based completion, false-completion detection, artifact verification.

**Files:** `src/governed_agent/evidence.py`, `verification.py`.

**Implementation:** evidence records artifact path, SHA-256, size and modification time. The entire receipt also has a digest. Completion verifies receipt integrity, task identity, required evidence presence, freshness, current size and current file hash.

**Tests:** missing evidence, stale evidence, false-complete, same-size mutation and receipt-tamper tests.

**Completion gate:** a provider/tool cannot cause `COMPLETE` merely by returning success; required current evidence must independently verify.

**Status:** COMPLETE.

### S09 — Encode parent/child completion separation

**Skill signal:** multi-agent workflow governance, sub-agent delegation semantics.

**Files:** `src/governed_agent/completion.py`.

**Implementation:** a `CompletionGroup` accepts only required child task IDs with `COMPLETE` status and a real evidence receipt. Child prose/self-report is insufficient to close the parent group.

**Tests:** `tests/test_completion_groups.py`.

**Completion gate:** `status=COMPLETE` without receipt is rejected; all required verified children are needed before the group is ready.

**Status:** COMPLETE.

### S10 — Expand observability without pretending to have production telemetry

**Skill signal:** measurable engineering, operational awareness.

**Files:** `src/governed_agent/metrics.py`, `engine.py`, demo JSON.

**Implementation:** task success/failure, provider attempts/failures, circuit openings, fallback successes, tool calls/failures/authorization blocks, verification failures, retries, approvals, duplicates/recovery blocks, audit-event count and latency are recorded in process-local metrics.

**Tests:** `tests/test_dry_run_and_metrics.py` and workflow tests.

**Completion gate:** metrics can be inspected from each reproducible scenario; docs explicitly state they are local, not production observability.

**Status:** COMPLETE.

### S11 — Make local demos reproduce the controls

**Skill signal:** developer experience, reproducibility, communication.

**Files:** `src/governed_agent/demo.py`, `examples/run_all.py`, `demo_outputs/`.

**Implementation:** three zero-secret scenarios remain the primary recruiter path: success, provider fallback, and approval. Each returns the record, metrics, provider-health state and audit-integrity result.

**Tests/verification:** `scripts/acceptance_check.py` executes all scenarios in isolated temporary workspaces.

**Completion gate:** every demo ends in verified completion and reports `audit_integrity=true`.

**Status:** COMPLETE.

### S12 — Add automated portfolio acceptance and secret scanning

**Skill signal:** quality gates, CI discipline, security hygiene.

**Files:** `scripts/acceptance_check.py`, `.github/workflows/test.yml`, `SECURITY.md`.

**Implementation:** one command executes the complete test suite, all three scenarios, a common-secret-pattern scan, required-document checks and scope-boundary checks. GitHub Actions runs the same acceptance command on Python 3.11 and 3.12.

**Completion gate:** `python scripts/acceptance_check.py` returns exit code 0 and verdict `PORTFOLIO READY`.

**Status:** COMPLETE when the final acceptance report in `PORTFOLIO_REVIEW.md` is regenerated after all changes.

### S13 — Create an evidence-indexed capability matrix

**Skill signal:** technical communication and factual claim discipline.

**Files:** `docs/CAPABILITY_MATRIX.md`.

**Implementation:** each recruiter-relevant skill is tagged as `IMPLEMENTED`, `DEMONSTRATED`, or `NOT CLAIMED`, with exact code and test references.

**Completion gate:** no important README/CV claim lacks a source/test reference or explicit limitation.

**Status:** COMPLETE.

### S14 — Document security assumptions and non-goals

**Skill signal:** threat modeling and engineering judgment.

**Files:** `docs/THREAT_MODEL.md`, `SECURITY.md`.

**Implementation:** identify protected assets, trust boundaries, handled threats, residual risks and non-goals. Explicitly document that the project lacks production authentication, distributed coordination, secret vaulting and real provider integrations.

**Completion gate:** limitations are discoverable without reading source code.

**Status:** COMPLETE.

### S15 — Tighten recruiter and interview presentation

**Skill signal:** ability to explain engineering tradeoffs without inflation.

**Files:** `README.md`, `AI_PORTFOLIO_CV_BLOCK.md`, `docs/INTERVIEW_EVIDENCE.md`, `PORTFOLIO_REVIEW.md`.

**Implementation:** README explains the problem/solution/demo in the first screen; CV block uses only implemented capabilities; interview guide separates “implemented here” from “broader R&D experience.”

**Completion gate:** a recruiter can identify the project value in about 60 seconds and an engineer can trace claims to tests in about 10 minutes.

**Status:** COMPLETE.
