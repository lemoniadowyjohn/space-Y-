import pytest

from governed_agent.planning import TaskDecomposer, TaskParseError, TaskParser


def test_parser_and_rule_based_decomposition():
    request = TaskParser().parse(
        {
            "objective": "Create verified artifact",
            "required_artifacts": ["result.txt"],
            "allowed_tools": ["artifact.write"],
            "explicit_steps": ["prepare", "write", "verify"],
            "idempotency_key": "case-001",
            "max_retries": 0,
        }
    )
    plan = TaskDecomposer().decompose(request)
    assert plan.task.objective == "Create verified artifact"
    assert plan.task.allowed_tools == ("artifact.write",)
    assert plan.task.idempotency_key == "case-001"
    assert plan.steps == ("prepare", "write", "verify")


def test_parser_rejects_unknown_fields():
    with pytest.raises(TaskParseError):
        TaskParser().parse({"objective": "x", "api_key": "should-not-be-here"})
