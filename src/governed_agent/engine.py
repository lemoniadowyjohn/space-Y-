from __future__ import annotations

import logging
import time

from .approvals import ApprovalError, ApprovalPolicy
from .audit import AuditTrail
from .evidence import build_receipt
from .metrics import Metrics
from .models import ExecutionRecord, FailureKind, Task, TaskStatus, ToolRisk, utc_now
from .providers import (
    MalformedProviderOutput,
    ProviderTimeout,
    ProviderUnavailable,
    RateLimited,
)
from .router import Router
from .state import ClaimStatus, ExecutionStateStore
from .tools import ToolAuthorizationError, ToolExecutionError, ToolRegistry
from .verification import VerificationError, verify_completion


LOGGER = logging.getLogger("governed_agent")


class WorkflowEngine:
    def __init__(
        self,
        *,
        router: Router,
        tools: ToolRegistry,
        approval_policy: ApprovalPolicy,
        metrics: Metrics | None = None,
        audit: AuditTrail | None = None,
        state_store: ExecutionStateStore | None = None,
        retry_backoff_base_s: float = 0.0,
    ) -> None:
        self.router = router
        self.tools = tools
        self.approval_policy = approval_policy
        self.metrics = metrics or Metrics()
        self.audit = audit or AuditTrail()
        self.state_store = state_store
        self.retry_backoff_base_s = max(0.0, retry_backoff_base_s)
        self._executed_task_ids: set[str] = set()

    def _audit(self, event_type: str, payload: dict) -> None:
        self.audit.append(event_type, payload)
        self.metrics.audit_events += 1

    def execute(self, task: Task) -> ExecutionRecord:
        record = ExecutionRecord(task=task, status=TaskStatus.RUNNING)
        self.metrics.tasks_total += 1
        started = time.perf_counter()
        claimed = False

        try:
            if self.state_store is not None:
                claim = self.state_store.claim(task)
                if claim.status is ClaimStatus.DUPLICATE_TERMINAL:
                    self.metrics.duplicate_executions_blocked += 1
                    record.status = TaskStatus.FAILED
                    record.failure_kind = FailureKind.DUPLICATE_EXECUTION
                    record.message = (
                        f"persistent idempotency blocked execution; existing task={claim.existing_task_id} "
                        f"status={claim.existing_status}"
                    )
                    return record
                if claim.status is ClaimStatus.INCOMPLETE_PREVIOUS_RUN:
                    self.metrics.recovery_blocks += 1
                    record.status = TaskStatus.FAILED
                    record.failure_kind = FailureKind.RECOVERY_REQUIRED
                    record.message = (
                        f"previous run is incomplete; explicit recovery required for task={claim.existing_task_id}"
                    )
                    return record
                claimed = True
            else:
                if task.task_id in self._executed_task_ids:
                    self.metrics.duplicate_executions_blocked += 1
                    record.status = TaskStatus.FAILED
                    record.failure_kind = FailureKind.DUPLICATE_EXECUTION
                    record.message = "task_id has already been executed"
                    return record
                self._executed_task_ids.add(task.task_id)

            self._audit(
                "task_started",
                {
                    "task_id": task.task_id,
                    "idempotency_key": task.idempotency_key,
                    "parent_task_id": task.parent_task_id,
                },
            )

            routed = self.router.route(task)
            if not routed:
                record.status = TaskStatus.FAILED
                record.failure_kind = FailureKind.CIRCUIT_OPEN
                record.message = "no eligible providers; circuits may be open"
                self._audit("routing_blocked", {"task_id": task.task_id, "reason": record.message})
                return record

            for provider_index, provider in enumerate(routed):
                max_attempts = 1 + max(task.max_retries, 0)
                for attempt in range(max_attempts):
                    record.attempts += 1
                    self.metrics.provider_attempts += 1
                    try:
                        if attempt:
                            record.retry_count += 1
                            self.metrics.retries += 1
                            if self.retry_backoff_base_s:
                                time.sleep(self.retry_backoff_base_s * (2 ** (attempt - 1)))
                        provider_result = self._generate_with_timeout(provider, task)
                        record.provider_used = provider.name
                        self.router.record_success(provider.name)
                        self._audit(
                            "provider_succeeded",
                            {"task_id": task.task_id, "provider": provider.name, "attempt": attempt + 1},
                        )
                    except (ProviderUnavailable, RateLimited, ProviderTimeout, MalformedProviderOutput) as exc:
                        self.metrics.provider_failures += 1
                        opened = self.router.record_failure(provider.name)
                        if opened:
                            self.metrics.circuit_open_events += 1
                        record.failure_kind = self._classify_provider_failure(exc)
                        record.message = str(exc)
                        self._audit(
                            "provider_failed",
                            {
                                "task_id": task.task_id,
                                "provider": provider.name,
                                "attempt": attempt + 1,
                                "failure_kind": record.failure_kind.value,
                                "circuit_opened": opened,
                            },
                        )
                        LOGGER.warning("provider failure", extra={"provider": provider.name})
                        if attempt + 1 < max_attempts:
                            continue
                        break

                    try:
                        tool_spec = self.tools.authorize(
                            provider_result.tool_name, task.allowed_tools
                        )
                    except ToolAuthorizationError as exc:
                        self.metrics.tool_authorization_failures += 1
                        record.status = TaskStatus.FAILED
                        record.failure_kind = FailureKind.TOOL_NOT_ALLOWED
                        record.message = str(exc)
                        self._audit(
                            "tool_authorization_blocked",
                            {"task_id": task.task_id, "tool": provider_result.tool_name},
                        )
                        return record

                    if task.dry_run:
                        record.status = TaskStatus.DRY_RUN
                        record.message = (
                            f"dry-run: authorized {provider_result.tool_name} via {provider.name}; "
                            f"side_effecting={tool_spec.side_effecting} risk={tool_spec.risk.value}"
                        )
                        self._audit("dry_run_complete", {"task_id": task.task_id, "tool": provider_result.tool_name})
                        return record

                    approval_needed = task.approval_required or tool_spec.risk is ToolRisk.HIGH
                    if approval_needed:
                        record.status = TaskStatus.WAITING_APPROVAL
                        record.approval_requested = True
                        self.metrics.approvals_requested += 1
                        decision = self.approval_policy.request(
                            task, provider_result.tool_name, provider_result.arguments
                        )
                        record.approval_id = decision.approval_id
                        self._audit(
                            "approval_requested",
                            {
                                "task_id": task.task_id,
                                "approval_id": decision.approval_id,
                                "actor": decision.actor,
                            },
                        )
                        try:
                            self.approval_policy.validate_and_consume(
                                decision, task, provider_result.tool_name, provider_result.arguments
                            )
                        except ApprovalError as exc:
                            record.approval_granted = False
                            record.status = TaskStatus.FAILED
                            if "denied" in str(exc):
                                self.metrics.approvals_denied += 1
                                record.failure_kind = FailureKind.APPROVAL_DENIED
                            else:
                                self.metrics.approvals_invalid += 1
                                record.failure_kind = FailureKind.APPROVAL_INVALID
                            record.message = str(exc)
                            self._audit(
                                "approval_blocked",
                                {
                                    "task_id": task.task_id,
                                    "approval_id": decision.approval_id,
                                    "reason": str(exc),
                                },
                            )
                            return record
                        record.approval_granted = True
                        record.status = TaskStatus.RUNNING
                        self._audit(
                            "approval_consumed",
                            {"task_id": task.task_id, "approval_id": decision.approval_id},
                        )

                    execution_started_at = utc_now()
                    try:
                        self.metrics.tool_calls += 1
                        tool_result = self.tools.execute(
                            provider_result.tool_name, provider_result.arguments
                        )
                    except ToolExecutionError as exc:
                        self.metrics.tool_failures += 1
                        record.failure_kind = FailureKind.TOOL_FAILURE
                        record.message = str(exc)
                        self._audit(
                            "tool_failed",
                            {"task_id": task.task_id, "tool": provider_result.tool_name, "reason": str(exc)},
                        )
                        break

                    self._audit(
                        "tool_succeeded",
                        {"task_id": task.task_id, "tool": provider_result.tool_name},
                    )
                    receipt = build_receipt(
                        task_id=task.task_id,
                        provider=provider.name,
                        tool_name=provider_result.tool_name,
                        started_at=execution_started_at,
                        artifact_paths=tool_result.artifact_paths,
                        notes=(provider_result.summary,),
                    )
                    record.receipt = receipt
                    try:
                        verify_completion(task, receipt)
                    except VerificationError as exc:
                        self.metrics.verification_failures += 1
                        record.status = TaskStatus.FAILED
                        record.failure_kind = FailureKind.VERIFICATION_FAILED
                        record.message = str(exc)
                        self._audit(
                            "verification_failed",
                            {"task_id": task.task_id, "reason": str(exc)},
                        )
                        return record

                    record.status = TaskStatus.COMPLETE
                    record.failure_kind = None
                    record.message = "verified completion"
                    if provider_index > 0:
                        record.fallback_count = provider_index
                        self.metrics.fallback_successes += 1
                    self.metrics.tasks_complete += 1
                    self._audit(
                        "task_completed",
                        {
                            "task_id": task.task_id,
                            "provider": provider.name,
                            "receipt_sha256": receipt.receipt_sha256,
                        },
                    )
                    return record

                # Only provider-class failures are eligible for fallback.
                if record.failure_kind in {
                    FailureKind.PROVIDER_UNAVAILABLE,
                    FailureKind.RATE_LIMITED,
                    FailureKind.TIMEOUT,
                    FailureKind.MALFORMED_OUTPUT,
                }:
                    continue
                record.status = TaskStatus.FAILED
                return record

            record.status = TaskStatus.FAILED
            if record.failure_kind is None:
                record.failure_kind = FailureKind.UNKNOWN
                record.message = "all providers exhausted"
            return record
        finally:
            record.latency_ms = (time.perf_counter() - started) * 1000.0
            self.metrics.total_latency_ms += record.latency_ms
            if record.status == TaskStatus.FAILED:
                self.metrics.tasks_failed += 1
            if claimed and self.state_store is not None:
                self.state_store.save(record)

    @staticmethod
    def _classify_provider_failure(exc: Exception) -> FailureKind:
        if isinstance(exc, ProviderUnavailable):
            return FailureKind.PROVIDER_UNAVAILABLE
        if isinstance(exc, RateLimited):
            return FailureKind.RATE_LIMITED
        if isinstance(exc, ProviderTimeout):
            return FailureKind.TIMEOUT
        if isinstance(exc, MalformedProviderOutput):
            return FailureKind.MALFORMED_OUTPUT
        return FailureKind.UNKNOWN

    @staticmethod
    def _generate_with_timeout(provider, task):
        delay_s = getattr(provider, "delay_s", 0.0)
        if delay_s > task.timeout_s:
            raise ProviderTimeout(
                f"{provider.name} exceeded timeout budget ({task.timeout_s}s)"
            )
        return provider.generate(task)
