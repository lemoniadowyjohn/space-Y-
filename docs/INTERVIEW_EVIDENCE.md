# Interview Evidence Guide

## 30-second explanation

I built a small Python control-plane prototype for agent-style automation. The core idea is that a model or worker saying “done” is not enough. Tasks have explicit tool permissions, provider failures are classified and may fall back, side effects can require a one-time action-bound approval, execution is idempotency-guarded across restarts, and completion requires fresh artifact evidence with hashes. I added tests for both success and failure paths rather than only a happy-path demo.

## Technically strongest points

### Evidence-based completion

**Implemented here:** artifact SHA-256/size/time receipts, receipt digest, freshness check and current-file verification.

**Failure to explain:** a tool can return success while writing the wrong file. The engine still fails because the required artifact is absent.

### Safe fallback

**Implemented here:** only provider-class failures are eligible for cross-provider fallback.

**Tradeoff:** tool failure does not automatically replay, because a side effect may have partially succeeded and duplicate execution could be worse than stopping.

### Human approval

**Implemented here:** approval ID, actor, exact-action hash, task binding, expiry and one-time consumption.

**Tradeoff:** the demo uses a local deterministic policy rather than a production identity/approval service.

### Restart/idempotency

**Implemented here:** local SQLite claims survive a new engine process. Reused idempotency keys are blocked; non-terminal prior claims become `RECOVERY_REQUIRED` rather than auto-replaying.

**Tradeoff:** this is local single-node durability, not distributed locking or consensus.

### Provider health

**Implemented here:** `HEALTHY/DEGRADED/DOWN`, failure threshold, cooldown circuit and routing exclusion.

**Tradeoff:** the adapters are deterministic fakes so the repo remains zero-secret and reproducible.

### Multi-agent completion semantics

**Implemented here:** a parent completion group accepts only required children that are actually `COMPLETE` and carry evidence receipts.

**Broader R&D context:** bounded delegation, model/provider routing, queue operations and independent review were explored in a larger personal Hermes/automation environment. Do not claim that the compact public demo is a distributed multi-agent platform.

## Questions to expect

**Why not use LangGraph/LangChain?**  
The portfolio objective is to make control semantics inspectable. The core routing, approval, failure, idempotency and verification behavior is intentionally explicit Python. A framework could later provide orchestration primitives, but it would not remove the need to define these policies.

**Why is fallback not universal?**  
Provider failure occurs before the side effect in this demo and is therefore safe to reroute. A tool failure may be ambiguous; replaying it can duplicate a write/action. I prefer explicit recovery/idempotency over blind retry of side effects.

**Is this production-ready?**  
No. It is a locally runnable portfolio prototype. Production would require real provider adapters, authentication/authorization, durable distributed coordination, secure secrets, production telemetry, stronger sandboxing, and operational SLO/runbook work.

**What is the most important design principle?**  
Separate worker/model claims from authoritative system state. Completion is a deterministic decision made from policy and evidence, not prose returned by the worker.
