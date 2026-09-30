from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .approvals import StaticApprovalPolicy
from .audit import AuditTrail
from .engine import WorkflowEngine
from .metrics import Metrics
from .planning import TaskDecomposer, TaskParser
from .providers import StaticProvider
from .router import Router
from .state import ExecutionStateStore
from .tools import build_default_tools


def _portable_path(raw: str) -> str:
    path = Path(raw)
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.name


def _serialize(record, plan_steps):
    data = asdict(record)
    data["status"] = record.status.value
    if record.failure_kind is not None:
        data["failure_kind"] = record.failure_kind.value
    data["task"]["created_at"] = record.task.created_at.isoformat()
    data["task"]["required_artifacts"] = [
        _portable_path(path) for path in data["task"]["required_artifacts"]
    ]
    if record.receipt:
        data["receipt"]["started_at"] = record.receipt.started_at.isoformat()
        data["receipt"]["finished_at"] = record.receipt.finished_at.isoformat()
        for item in data["receipt"]["evidence"]:
            item["artifact_path"] = _portable_path(item["artifact_path"])
            item["modified_at"] = item["modified_at"].isoformat()
    data["plan_steps"] = list(plan_steps)
    return data


def build_scenario(name: str, workspace: Path):
    target = workspace / f"{name}.txt"
    response = {
        "tool_name": "artifact.write",
        "arguments": {"path": target.name, "content": f"scenario={name}\nstatus=created\n"},
        "summary": "Create the requested demo artifact.",
    }

    payload = {
        "objective": "Create a verified demo artifact",
        "required_artifacts": [str(target)],
        "allowed_tools": ["artifact.write"],
        "idempotency_key": f"demo-{name}",
        "max_retries": 0,
    }
    providers = [StaticProvider("provider-a", response=response)]
    approval = StaticApprovalPolicy(True)

    if name == "fallback":
        payload["objective"] = "Create an artifact after provider fallback"
        providers = [
            StaticProvider("provider-a", response=response, failure="rate_limited"),
            StaticProvider("provider-b", response=response),
        ]
    elif name == "approval":
        payload["objective"] = "Create an artifact only after approval"
        payload["approval_required"] = True
    elif name != "success":
        raise ValueError(f"unknown scenario: {name}")

    request = TaskParser().parse(payload)
    plan = TaskDecomposer().decompose(request)
    return providers, approval, plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["success", "fallback", "approval"], default="success")
    parser.add_argument("--workspace", default="artifacts")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    providers, approval, plan = build_scenario(args.scenario, workspace)
    metrics = Metrics()
    runtime = workspace / ".runtime"
    engine = WorkflowEngine(
        router=Router(providers),
        tools=build_default_tools(workspace),
        approval_policy=approval,
        metrics=metrics,
        audit=AuditTrail(runtime / f"{args.scenario}-{plan.task.task_id}-audit.jsonl"),
        state_store=ExecutionStateStore(runtime / f"{args.scenario}-{plan.task.task_id}-state.sqlite3"),
    )
    record = engine.execute(plan.task)
    print(
        json.dumps(
            {
                "record": _serialize(record, plan.steps),
                "metrics": metrics.snapshot(),
                "provider_health": engine.router.health_registry.snapshot(),
                "audit_integrity": engine.audit.verify_integrity(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
