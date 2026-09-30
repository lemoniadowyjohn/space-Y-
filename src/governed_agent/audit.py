from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .models import AuditEvent, utc_now


def _stable_hash(value: dict[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(raw).hexdigest()


class AuditTrail:
    """Small tamper-evident event chain for the local portfolio demo."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self.events: list[AuditEvent] = []
        if self.path and self.path.exists():
            self._load()

    def _load(self) -> None:
        assert self.path is not None
        self.events = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            self.events.append(AuditEvent(**payload))

    def append(self, event_type: str, payload: dict[str, Any]) -> AuditEvent:
        previous_hash = self.events[-1].event_hash if self.events else "GENESIS"
        sequence = len(self.events) + 1
        base = {
            "sequence": sequence,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
        }
        event = AuditEvent(
            sequence=sequence,
            timestamp_utc=utc_now().isoformat(),
            event_type=event_type,
            payload=payload,
            previous_hash=previous_hash,
            event_hash=_stable_hash(base),
        )
        self.events.append(event)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        return event

    def verify_integrity(self) -> bool:
        previous_hash = "GENESIS"
        for event in self.events:
            base = {
                "sequence": event.sequence,
                "event_type": event.event_type,
                "payload": event.payload,
                "previous_hash": previous_hash,
            }
            if event.previous_hash != previous_hash or event.event_hash != _stable_hash(base):
                return False
            previous_hash = event.event_hash
        return True
