from __future__ import annotations

from dataclasses import dataclass, field

from .models import ExecutionRecord, TaskStatus


@dataclass
class CompletionGroup:
    """Parent acceptance requires verified child records, not child self-reporting."""

    parent_task_id: str
    required_child_ids: frozenset[str]
    accepted_children: set[str] = field(default_factory=set)

    def accept_child(self, record: ExecutionRecord) -> bool:
        child_id = record.task.task_id
        if child_id not in self.required_child_ids:
            return False
        if record.status is not TaskStatus.COMPLETE or record.receipt is None:
            return False
        if not record.receipt.receipt_sha256:
            return False
        self.accepted_children.add(child_id)
        return True

    @property
    def ready(self) -> bool:
        return self.accepted_children == set(self.required_child_ids)
