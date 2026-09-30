from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .models import Task


class TaskParseError(ValueError):
    pass


@dataclass(frozen=True)
class TaskRequest:
    objective: str
    required_artifacts: tuple[str, ...] = ()
    explicit_steps: tuple[str, ...] = ()
    preferred_provider: str | None = None
    allowed_tools: tuple[str, ...] = ()
    approval_required: bool = False
    dry_run: bool = False
    timeout_s: float = 2.0
    max_retries: int = 1
    idempotency_key: str | None = None
    parent_task_id: str | None = None


@dataclass(frozen=True)
class ExecutionPlan:
    task: Task
    steps: tuple[str, ...]


class TaskParser:
    """Strict parser for the public demo's task contract; unknown fields fail closed."""

    _allowed = {
        "objective",
        "required_artifacts",
        "explicit_steps",
        "preferred_provider",
        "allowed_tools",
        "approval_required",
        "dry_run",
        "timeout_s",
        "max_retries",
        "idempotency_key",
        "parent_task_id",
    }

    def parse(self, payload: Mapping[str, Any]) -> TaskRequest:
        unknown = set(payload) - self._allowed
        if unknown:
            raise TaskParseError(f"unknown task fields: {sorted(unknown)}")

        objective = payload.get("objective")
        if not isinstance(objective, str) or not objective.strip():
            raise TaskParseError("objective must be a non-empty string")

        required = payload.get("required_artifacts", ())
        steps = payload.get("explicit_steps", ())
        allowed_tools = payload.get("allowed_tools", ())
        for name, value in {
            "required_artifacts": required,
            "explicit_steps": steps,
            "allowed_tools": allowed_tools,
        }.items():
            if not isinstance(value, (list, tuple)) or not all(
                isinstance(x, str) and x.strip() for x in value
            ):
                raise TaskParseError(f"{name} must be a list/tuple of non-empty strings")

        approval = payload.get("approval_required", False)
        dry_run = payload.get("dry_run", False)
        timeout_s = payload.get("timeout_s", 2.0)
        max_retries = payload.get("max_retries", 1)
        preferred = payload.get("preferred_provider")
        idempotency_key = payload.get("idempotency_key")
        parent_task_id = payload.get("parent_task_id")

        if not isinstance(approval, bool) or not isinstance(dry_run, bool):
            raise TaskParseError("approval_required and dry_run must be boolean")
        if not isinstance(timeout_s, (int, float)) or timeout_s <= 0:
            raise TaskParseError("timeout_s must be > 0")
        if not isinstance(max_retries, int) or max_retries < 0:
            raise TaskParseError("max_retries must be a non-negative integer")
        for name, value in {
            "preferred_provider": preferred,
            "idempotency_key": idempotency_key,
            "parent_task_id": parent_task_id,
        }.items():
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise TaskParseError(f"{name} must be a non-empty string or null")

        return TaskRequest(
            objective=objective.strip(),
            required_artifacts=tuple(x.strip() for x in required),
            explicit_steps=tuple(x.strip() for x in steps),
            preferred_provider=preferred.strip() if preferred else None,
            allowed_tools=tuple(x.strip() for x in allowed_tools),
            approval_required=approval,
            dry_run=dry_run,
            timeout_s=float(timeout_s),
            max_retries=max_retries,
            idempotency_key=idempotency_key.strip() if idempotency_key else None,
            parent_task_id=parent_task_id.strip() if parent_task_id else None,
        )


class TaskDecomposer:
    """Rule-based decomposition; no hidden LLM planning is claimed."""

    DEFAULT_STEPS = (
        "validate task contract and tool allowlist",
        "select an eligible provider",
        "request structured action",
        "apply approval policy if required",
        "execute one authorized tool action",
        "build evidence receipt",
        "verify completion criteria",
    )

    def decompose(self, request: TaskRequest) -> ExecutionPlan:
        task = Task(
            objective=request.objective,
            required_artifacts=request.required_artifacts,
            preferred_provider=request.preferred_provider,
            allowed_tools=request.allowed_tools,
            approval_required=request.approval_required,
            dry_run=request.dry_run,
            timeout_s=request.timeout_s,
            max_retries=request.max_retries,
            idempotency_key=request.idempotency_key,
            parent_task_id=request.parent_task_id,
        )
        steps = request.explicit_steps or self.DEFAULT_STEPS
        return ExecutionPlan(task=task, steps=steps)
