from __future__ import annotations

from pathlib import Path
from datetime import timedelta

from .evidence import hash_file, receipt_digest
from .models import EvidenceReceipt, Task


class VerificationError(RuntimeError):
    pass


FRESHNESS_CLOCK_TOLERANCE = timedelta(seconds=1)


def _receipt_payload(receipt: EvidenceReceipt) -> dict:
    return {
        "task_id": receipt.task_id,
        "provider": receipt.provider,
        "tool_name": receipt.tool_name,
        "started_at": receipt.started_at.isoformat(),
        "finished_at": receipt.finished_at.isoformat(),
        "evidence": [
            {
                "artifact_path": item.artifact_path,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
                "modified_at": item.modified_at.isoformat(),
            }
            for item in receipt.evidence
        ],
        "notes": list(receipt.notes),
    }


def verify_completion(task: Task, receipt: EvidenceReceipt) -> None:
    if receipt.task_id != task.task_id:
        raise VerificationError("receipt belongs to a different task")
    if receipt.receipt_sha256 != receipt_digest(_receipt_payload(receipt)):
        raise VerificationError("evidence receipt integrity check failed")

    evidence_by_name = {Path(item.artifact_path).name: item for item in receipt.evidence}
    evidence_by_path = {item.artifact_path: item for item in receipt.evidence}

    for required in task.required_artifacts:
        required_path = str(Path(required).resolve())
        item = evidence_by_path.get(required_path) or evidence_by_name.get(Path(required).name)
        if item is None:
            raise VerificationError(f"missing required evidence: {required}")
        if item.modified_at + FRESHNESS_CLOCK_TOLERANCE < task.created_at:
            raise VerificationError(f"stale evidence: {required}")
        current = Path(item.artifact_path)
        if not current.exists():
            raise VerificationError(f"artifact disappeared after execution: {required}")
        if current.stat().st_size != item.size_bytes:
            raise VerificationError(f"artifact changed after receipt: {required}")
        if hash_file(current) != item.sha256:
            raise VerificationError(f"artifact hash changed after receipt: {required}")
