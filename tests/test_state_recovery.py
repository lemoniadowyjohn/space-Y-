from governed_agent.approvals import StaticApprovalPolicy
from governed_agent.engine import WorkflowEngine
from governed_agent.models import FailureKind, Task, TaskStatus
from governed_agent.providers import StaticProvider
from governed_agent.router import Router
from governed_agent.state import ExecutionStateStore
from governed_agent.tools import build_default_tools


def _response():
    return {
        "tool_name": "artifact.write",
        "arguments": {"path": "result.txt", "content": "ok"},
        "summary": "write",
    }


def test_idempotency_survives_engine_restart(tmp_path):
    store = ExecutionStateStore(tmp_path / "state.sqlite3")
    task = Task(
        objective="x",
        required_artifacts=(str(tmp_path / "result.txt"),),
        allowed_tools=("artifact.write",),
        idempotency_key="stable-key-1",
        max_retries=0,
    )
    first_engine = WorkflowEngine(
        router=Router([StaticProvider("a", response=_response())]),
        tools=build_default_tools(tmp_path),
        approval_policy=StaticApprovalPolicy(True),
        state_store=store,
    )
    assert first_engine.execute(task).status is TaskStatus.COMPLETE

    second_task = Task(
        objective="same logical work",
        required_artifacts=(str(tmp_path / "result2.txt"),),
        allowed_tools=("artifact.write",),
        idempotency_key="stable-key-1",
        max_retries=0,
    )
    second_engine = WorkflowEngine(
        router=Router([StaticProvider("a", response=_response())]),
        tools=build_default_tools(tmp_path),
        approval_policy=StaticApprovalPolicy(True),
        state_store=ExecutionStateStore(tmp_path / "state.sqlite3"),
    )
    record = second_engine.execute(second_task)
    assert record.failure_kind is FailureKind.DUPLICATE_EXECUTION


def test_incomplete_previous_run_requires_explicit_recovery(tmp_path):
    store = ExecutionStateStore(tmp_path / "state.sqlite3")
    task = Task(
        objective="x",
        allowed_tools=("artifact.write",),
        idempotency_key="crash-key",
    )
    claim = store.claim(task)
    assert claim.status.value == "claimed"

    engine = WorkflowEngine(
        router=Router([StaticProvider("a", response=_response())]),
        tools=build_default_tools(tmp_path),
        approval_policy=StaticApprovalPolicy(True),
        state_store=ExecutionStateStore(tmp_path / "state.sqlite3"),
    )
    record = engine.execute(task)
    assert record.failure_kind is FailureKind.RECOVERY_REQUIRED
    assert "explicit recovery required" in record.message
