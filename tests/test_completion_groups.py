from governed_agent.completion import CompletionGroup
from governed_agent.models import ExecutionRecord, Task, TaskStatus


def test_child_self_report_without_receipt_does_not_close_parent():
    child = Task(objective="child")
    record = ExecutionRecord(task=child, status=TaskStatus.COMPLETE, message="done")
    group = CompletionGroup(parent_task_id="parent", required_child_ids=frozenset({child.task_id}))
    assert group.accept_child(record) is False
    assert group.ready is False


def test_verified_child_can_satisfy_completion_group(engine_factory, write_response):
    from governed_agent.providers import StaticProvider

    engine, _, tmp_path = engine_factory([StaticProvider("a", response=write_response)])
    child = Task(
        objective="child",
        required_artifacts=(str(tmp_path / "result.txt"),),
        allowed_tools=("artifact.write",),
        parent_task_id="parent",
        max_retries=0,
    )
    record = engine.execute(child)
    group = CompletionGroup(parent_task_id="parent", required_child_ids=frozenset({child.task_id}))
    assert group.accept_child(record)
    assert group.ready
