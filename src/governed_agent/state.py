from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import sqlite3

from .models import ExecutionRecord, Task, TaskStatus, utc_now


class ClaimStatus(str, Enum):
    CLAIMED = "claimed"
    DUPLICATE_TERMINAL = "duplicate_terminal"
    INCOMPLETE_PREVIOUS_RUN = "incomplete_previous_run"


@dataclass(frozen=True)
class ClaimResult:
    status: ClaimStatus
    existing_status: str | None = None
    existing_task_id: str | None = None


class ExecutionStateStore:
    """SQLite-backed task claim/state store for restart-safe demo idempotency."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS task_state (
                    task_id TEXT PRIMARY KEY,
                    idempotency_key TEXT UNIQUE,
                    status TEXT NOT NULL,
                    record_json TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def claim(self, task: Task) -> ClaimResult:
        with self._connect() as con:
            row = con.execute(
                "SELECT task_id, status FROM task_state WHERE task_id = ? OR (? IS NOT NULL AND idempotency_key = ?)",
                (task.task_id, task.idempotency_key, task.idempotency_key),
            ).fetchone()
            if row:
                terminal = row["status"] in {
                    TaskStatus.COMPLETE.value,
                    TaskStatus.FAILED.value,
                    TaskStatus.DRY_RUN.value,
                }
                return ClaimResult(
                    ClaimStatus.DUPLICATE_TERMINAL if terminal else ClaimStatus.INCOMPLETE_PREVIOUS_RUN,
                    existing_status=row["status"],
                    existing_task_id=row["task_id"],
                )
            con.execute(
                "INSERT INTO task_state(task_id, idempotency_key, status, updated_at) VALUES (?, ?, ?, ?)",
                (task.task_id, task.idempotency_key, TaskStatus.RUNNING.value, utc_now().isoformat()),
            )
        return ClaimResult(ClaimStatus.CLAIMED)

    def save(self, record: ExecutionRecord) -> None:
        payload = {
            "task_id": record.task.task_id,
            "status": record.status.value,
            "provider_used": record.provider_used,
            "failure_kind": record.failure_kind.value if record.failure_kind else None,
            "message": record.message,
            "receipt_sha256": record.receipt.receipt_sha256 if record.receipt else None,
        }
        with self._connect() as con:
            con.execute(
                "UPDATE task_state SET status = ?, record_json = ?, updated_at = ? WHERE task_id = ?",
                (record.status.value, json.dumps(payload, sort_keys=True), utc_now().isoformat(), record.task.task_id),
            )

    def get(self, task_id: str) -> dict | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT task_id, idempotency_key, status, record_json, updated_at FROM task_state WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        return dict(row) if row else None
