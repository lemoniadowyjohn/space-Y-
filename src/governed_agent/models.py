from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    FAILED = "failed"
    COMPLETE = "complete"
    DRY_RUN = "dry_run"


class FailureKind(str, Enum):
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    RATE_LIMITED = "rate_limited"
    MALFORMED_OUTPUT = "malformed_output"
    TIMEOUT = "timeout"
    CIRCUIT_OPEN = "circuit_open"
    TOOL_FAILURE = "tool_failure"
    TOOL_NOT_ALLOWED = "tool_not_allowed"
    APPROVAL_DENIED = "approval_denied"
    APPROVAL_INVALID = "approval_invalid"
    VERIFICATION_FAILED = "verification_failed"
    DUPLICATE_EXECUTION = "duplicate_execution"
    RECOVERY_REQUIRED = "recovery_required"
    UNKNOWN = "unknown"


class ProviderHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class ToolRisk(str, Enum):
    READ_ONLY = "read_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class Task:
    objective: str
    required_artifacts: tuple[str, ...] = ()
    preferred_provider: str | None = None
    allowed_tools: tuple[str, ...] = ()
    approval_required: bool = False
    dry_run: bool = False
    timeout_s: float = 2.0
    max_retries: int = 1
    idempotency_key: str | None = None
    parent_task_id: str | None = None
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    tool_name: str
    arguments: dict[str, Any]
    summary: str


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: dict[str, Any]
    artifact_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceItem:
    artifact_path: str
    sha256: str
    size_bytes: int
    modified_at: datetime


@dataclass(frozen=True)
class EvidenceReceipt:
    task_id: str
    provider: str
    tool_name: str
    started_at: datetime
    finished_at: datetime
    evidence: tuple[EvidenceItem, ...]
    receipt_sha256: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApprovalDecision:
    approval_id: str
    task_id: str
    action_sha256: str
    actor: str
    decision: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    timestamp_utc: str
    event_type: str
    payload: dict[str, Any]
    previous_hash: str
    event_hash: str


@dataclass
class ExecutionRecord:
    task: Task
    status: TaskStatus = TaskStatus.PENDING
    provider_used: str | None = None
    attempts: int = 0
    fallback_count: int = 0
    retry_count: int = 0
    approval_requested: bool = False
    approval_granted: bool | None = None
    approval_id: str | None = None
    failure_kind: FailureKind | None = None
    message: str = ""
    receipt: EvidenceReceipt | None = None
    latency_ms: float = 0.0
