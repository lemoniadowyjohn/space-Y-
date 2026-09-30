# AI Portfolio CV Block

## Governed Agent Workflow Demo — Evidence-Gated AI Task Orchestration

Built a local Python prototype that demonstrates governed agent-style workflow execution with deterministic routing, provider-health/fallback controls, explicit tool permissions, human approval boundaries, restart-safe idempotency and evidence-based completion.

### CV bullets

- Implemented a dependency-light Python workflow control plane with structured task state, provider abstraction, health-aware routing/circuit breaking, bounded retries/fallback, dry-run execution and explicit per-task tool allowlists.
- Added action-bound human approvals with expiry/replay protection plus SQLite-backed idempotency and fail-closed restart handling to reduce duplicate or ambiguous side-effect execution.
- Built evidence-gated completion using artifact/receipt SHA-256 verification and a tamper-evident audit chain; validated success and adversarial failure paths with 35 automated tests and reproducible zero-secret demos.

### Skills

Python · AI workflow automation · agent orchestration concepts · structured task state · deterministic routing · provider health · circuit breakers · retries/fallback · human-in-the-loop approvals · least-privilege tool execution · idempotency · restart/recovery controls · evidence verification · SHA-256 integrity · audit trails · automated testing · Git/GitHub Actions · Docker

### Interview positioning

Implemented in the public repository: local deterministic providers, provider-health/circuit state, tool permissions, approvals, local SQLite idempotency, artifact verification, tamper-evident audit, parent/child evidence gate, metrics and tests.

Broader personal R&D experience may be discussed separately: Hermes task queues, model/provider routing, bounded sub-agent delegation, provider quota/deprecation handling, MCP-style integrations, scheduled audits and recovery work.

Do **not** describe this repository as enterprise production AI, commercial deployment, distributed multi-agent infrastructure, production MLOps or a production LLM platform.
