from governed_agent.models import Task, TaskStatus
from governed_agent.providers import StaticProvider


def test_dry_run_does_not_execute_tool(engine_factory, write_response):
    engine, metrics, tmp_path = engine_factory([StaticProvider("a", response=write_response)])
    task = Task(
        objective="preview",
        dry_run=True,
        allowed_tools=("artifact.write",),
        required_artifacts=(str(tmp_path / "result.txt"),),
    )
    record = engine.execute(task)
    assert record.status is TaskStatus.DRY_RUN
    assert not (tmp_path / "result.txt").exists()
    assert metrics.tool_calls == 0


def test_metrics_snapshot(engine_factory, write_response):
    engine, metrics, tmp_path = engine_factory([StaticProvider("a", response=write_response)])
    engine.execute(
        Task(
            objective="x",
            allowed_tools=("artifact.write",),
            required_artifacts=(str(tmp_path / "result.txt"),),
            max_retries=0,
        )
    )
    snapshot = metrics.snapshot()
    assert snapshot["task_success_rate"] == 1.0
    assert snapshot["tool_call_success_rate"] == 1.0
    assert snapshot["average_latency_ms"] >= 0.0
    assert snapshot["audit_events"] >= 4
