# Architecture

## Execution flow

```text
User / caller
    |
    v
Strict TaskParser
    |
    v
Rule-based TaskDecomposer
    |
    v
Task contract
(objective, artifacts, allowlisted tools, timeout/retry,
 approval policy, idempotency key, parent ID)
    |
    v
ExecutionStateStore claim
    |---------------------------|
    | claimed                   | duplicate/incomplete prior run
    v                           v
Health-aware Router        BLOCK / RECOVERY_REQUIRED
    |
    +---- Provider A ---- failure ----+
    |                                 |
    +---- Provider B <--- fallback ---+
    |
    v
Structured proposed action
    |
    v
Tool allowlist / risk check
    |
    +---- dry run -> DRY_RUN
    |
    v
Approval gate when required
(action hash + actor + TTL + one-time use)
    |
    v
Tool execution
    |
    v
Evidence receipt
(file hash + size + mtime + receipt digest)
    |
    v
Completion verifier
    |
    +---- missing/stale/changed/tampered -> FAILED
    |
    v
COMPLETE

All major transitions -> tamper-evident AuditTrail
All attempts/outcomes -> process-local Metrics
```

## Authority model

The architecture deliberately separates four authorities:

1. **Provider/model:** may propose an action; cannot authorize itself.
2. **Task policy:** defines allowed tools, retry/timeout limits and whether approval is needed.
3. **Approval policy:** may authorize the exact proposed action for a bounded time.
4. **Verifier:** decides whether completion criteria are actually satisfied.

This separation prevents a provider's natural-language/structured success response from becoming authoritative system state.

## Provider health and fallback

Provider runtime state is one of `HEALTHY`, `DEGRADED`, `DOWN`. Repeated failures can open a circuit until cooldown. Routing excludes providers with an open circuit.

Fallback is intentionally narrow. Only failures that happen in the provider stage are eligible for moving to another provider. A failed side-effecting tool is not blindly replayed because its real-world state may be ambiguous.

## Tool boundary

Tools are registered with explicit metadata and are not globally available by default. The task carries an allowlist. Provider selection of an unlisted tool fails closed before execution.

This models the principle behind least-privilege tool/MCP integration without claiming that the repository itself implements the MCP protocol.

## Approval boundary

An approval is not a generic boolean. It is bound to:

- `approval_id`;
- `task_id`;
- exact action digest;
- actor;
- creation/expiry time;
- one-time consumption state.

Changing arguments after approval, replaying an approval, or using it after expiry is rejected.

## Durable state boundary

`ExecutionStateStore` uses SQLite to demonstrate restart-safe idempotency. It is intentionally local/single-node. A terminal logical task cannot be repeated with the same idempotency key. A non-terminal previous claim does not auto-replay after restart; it requires explicit recovery.

A real distributed agent platform would require stronger leases/fencing/coordination. This repository does not claim those features.

## Evidence and audit

Artifact completion evidence contains SHA-256, size and modification time. The receipt itself has a digest, so receipt mutation is separately detectable.

Audit events form a SHA-256-linked chain. This demonstrates tamper detection and provenance thinking; it is not equivalent to an externally secured append-only production log.

## Multi-agent completion semantics

`CompletionGroup` provides a deliberately small example of parent/child governance. A required child counts only when it has a `COMPLETE` execution record **and** a real evidence receipt. Child prose such as “done” is not accepted as parent completion evidence.

## Prototype boundaries

The project uses deterministic local provider adapters. It intentionally omits real provider credentials, distributed scheduling, tenant security, secret vaulting, production telemetry and autonomous arbitrary-code execution so that the control semantics remain reviewable and reproducible.
