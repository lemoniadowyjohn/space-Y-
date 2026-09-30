from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Metrics:
    tasks_total: int = 0
    tasks_complete: int = 0
    tasks_failed: int = 0
    provider_attempts: int = 0
    provider_failures: int = 0
    circuit_open_events: int = 0
    fallback_successes: int = 0
    tool_calls: int = 0
    tool_failures: int = 0
    tool_authorization_failures: int = 0
    verification_failures: int = 0
    retries: int = 0
    approvals_requested: int = 0
    approvals_denied: int = 0
    approvals_invalid: int = 0
    duplicate_executions_blocked: int = 0
    recovery_blocks: int = 0
    audit_events: int = 0
    total_latency_ms: float = 0.0

    def snapshot(self) -> dict:
        data = asdict(self)
        data["task_success_rate"] = (
            self.tasks_complete / self.tasks_total if self.tasks_total else 0.0
        )
        data["fallback_success_rate"] = (
            self.fallback_successes / self.provider_failures if self.provider_failures else 0.0
        )
        data["tool_call_success_rate"] = (
            (self.tool_calls - self.tool_failures) / self.tool_calls if self.tool_calls else 0.0
        )
        data["approval_frequency"] = (
            self.approvals_requested / self.tasks_total if self.tasks_total else 0.0
        )
        data["average_latency_ms"] = (
            self.total_latency_ms / self.tasks_total if self.tasks_total else 0.0
        )
        return data
