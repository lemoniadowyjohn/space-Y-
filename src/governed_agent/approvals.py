from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from hashlib import sha256
import json
import uuid

from .models import ApprovalDecision, Task, utc_now


class ApprovalError(RuntimeError):
    pass


def action_digest(task: Task, tool_name: str, arguments: dict) -> str:
    payload = {
        "task_id": task.task_id,
        "tool_name": tool_name,
        "arguments": arguments,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(raw).hexdigest()


class ApprovalPolicy(ABC):
    @abstractmethod
    def request(self, task: Task, tool_name: str, arguments: dict) -> ApprovalDecision:
        raise NotImplementedError

    @abstractmethod
    def validate_and_consume(
        self, decision: ApprovalDecision, task: Task, tool_name: str, arguments: dict
    ) -> None:
        raise NotImplementedError


class StaticApprovalPolicy(ApprovalPolicy):
    """Deterministic local approval adapter with expiry/action binding/one-time use."""

    def __init__(self, decision: bool, *, actor: str = "demo-reviewer", ttl_seconds: int = 300) -> None:
        self.decision = decision
        self.actor = actor
        self.ttl_seconds = ttl_seconds
        self._used: set[str] = set()

    def request(self, task: Task, tool_name: str, arguments: dict) -> ApprovalDecision:
        created = utc_now()
        return ApprovalDecision(
            approval_id=f"APR-{uuid.uuid4().hex[:16]}",
            task_id=task.task_id,
            action_sha256=action_digest(task, tool_name, arguments),
            actor=self.actor,
            decision="approve" if self.decision else "deny",
            created_at=created,
            expires_at=created + timedelta(seconds=self.ttl_seconds),
        )

    def validate_and_consume(
        self, decision: ApprovalDecision, task: Task, tool_name: str, arguments: dict
    ) -> None:
        if decision.approval_id in self._used:
            raise ApprovalError("approval replay detected")
        if decision.task_id != task.task_id:
            raise ApprovalError("approval task mismatch")
        if decision.action_sha256 != action_digest(task, tool_name, arguments):
            raise ApprovalError("approval action hash mismatch")
        if decision.expires_at < utc_now():
            raise ApprovalError("approval expired")
        if decision.decision != "approve":
            raise ApprovalError("approval denied")
        self._used.add(decision.approval_id)
