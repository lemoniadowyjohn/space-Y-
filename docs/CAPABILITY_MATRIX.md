# Capability Evidence Matrix

`IMPLEMENTED` means executable code exists in this repository. `DEMONSTRATED` means a runnable example or test exercises the behavior. `NOT CLAIMED` means the repository intentionally does not present the capability as implemented.

| Capability | Status | Implementation evidence | Verification evidence |
|---|---|---|---|
| Structured task contract | IMPLEMENTED | `models.py`, `planning.py` | `test_planning.py` |
| Deterministic decomposition | IMPLEMENTED | `TaskDecomposer` | `test_parser_and_rule_based_decomposition` |
| Provider adapter interface | IMPLEMENTED | `ProviderAdapter` | workflow tests use multiple adapters |
| Deterministic routing | IMPLEMENTED | `router.py` | fallback/provider-health tests |
| Provider health state | IMPLEMENTED | `ProviderHealthRegistry` | `test_provider_health.py` |
| Circuit breaker | IMPLEMENTED | `ProviderHealthRegistry.record_failure` | circuit-open/skip tests |
| Retry budget | IMPLEMENTED | `WorkflowEngine` | provider failure tests |
| Provider fallback | IMPLEMENTED | `WorkflowEngine` | `test_fallback` |
| Failure classification | IMPLEMENTED | `FailureKind`, typed provider exceptions | workflow matrix |
| Transport-level real LLM timeout | NOT CLAIMED | demo providers are local fakes | README limitation |
| Tool registry | IMPLEMENTED | `tools.py` | workflow tests |
| Explicit tool allowlist | IMPLEMENTED | `ToolRegistry.authorize` | `test_tool_not_allowlisted_is_blocked` |
| Workspace path containment | IMPLEMENTED | artifact tools | tests/demos exercise bounded paths |
| Dry-run execution | IMPLEMENTED | `WorkflowEngine` | `test_dry_run_does_not_execute_tool` |
| Human approval gate | IMPLEMENTED | `approvals.py`, `engine.py` | approval workflow test |
| Approval action binding | IMPLEMENTED | `action_digest` | action-mismatch test |
| Approval expiry | IMPLEMENTED | `expires_at` validation | expiry test |
| Approval replay protection | IMPLEMENTED | used-ID registry | one-time-use test |
| Durable idempotency | IMPLEMENTED | SQLite `ExecutionStateStore` | restart test |
| Crash/incomplete-state detection | IMPLEMENTED | claim-state classification | recovery-required test |
| Automatic crash replay | NOT CLAIMED | deliberately fail-closed | recovery test/README |
| Artifact evidence receipt | IMPLEMENTED | `evidence.py` | normal completion test |
| Receipt integrity digest | IMPLEMENTED | `receipt_sha256` | receipt-tamper test |
| Stale-evidence detection | IMPLEMENTED | `verification.py` | stale-evidence test |
| False-completion prevention | IMPLEMENTED | completion verifier | missing/required-artifact tests |
| Repository state inspection | IMPLEMENTED | `repository.py` | `test_repository.py` |
| Tamper-evident audit chain | IMPLEMENTED | `audit.py` | `test_audit.py` |
| Parent/child acceptance separation | IMPLEMENTED | `CompletionGroup` | `test_completion_groups.py` |
| Distributed multi-agent scheduler | NOT CLAIMED | no distributed workers here | README limitation |
| MCP server/client implementation | NOT CLAIMED | tool governance is MCP-style only | README limitation |
| Persistent distributed queue | NOT CLAIMED | SQLite state is local | README limitation |
| Process-local metrics | IMPLEMENTED | `metrics.py` | metrics test + demos |
| Production observability stack | NOT CLAIMED | no OpenTelemetry/Prometheus stack | README limitation |
| Docker artifact | IMPLEMENTED | `Dockerfile` | structurally included; build depends on Docker availability |
| CI verification | IMPLEMENTED | GitHub Actions workflow | runs acceptance command |
| RAG / embeddings / vector DB | NOT CLAIMED | absent by design | README limitation |
| LangChain / LangGraph | NOT CLAIMED | absent by design | README limitation |
| Enterprise/customer deployment | NOT CLAIMED | prototype only | README + portfolio review |
