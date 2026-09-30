from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from .models import EvidenceItem, EvidenceReceipt


def hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def receipt_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(raw).hexdigest()


def build_receipt(
    *,
    task_id: str,
    provider: str,
    tool_name: str,
    started_at: datetime,
    artifact_paths: tuple[str, ...],
    notes: tuple[str, ...] = (),
) -> EvidenceReceipt:
    items: list[EvidenceItem] = []
    for raw in artifact_paths:
        path = Path(raw)
        if not path.exists() or not path.is_file():
            continue
        stat = path.stat()
        items.append(
            EvidenceItem(
                artifact_path=str(path.resolve()),
                sha256=hash_file(path),
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            )
        )
    finished_at = datetime.now(timezone.utc)
    digest_payload = {
        "task_id": task_id,
        "provider": provider,
        "tool_name": tool_name,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "evidence": [
            {
                "artifact_path": item.artifact_path,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
                "modified_at": item.modified_at.isoformat(),
            }
            for item in items
        ],
        "notes": list(notes),
    }
    return EvidenceReceipt(
        task_id=task_id,
        provider=provider,
        tool_name=tool_name,
        started_at=started_at,
        finished_at=finished_at,
        evidence=tuple(items),
        receipt_sha256=receipt_digest(digest_payload),
        notes=notes,
    )
