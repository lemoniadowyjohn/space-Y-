from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from governed_agent.evidence import build_receipt
from governed_agent.models import FailureKind, Task, TaskStatus
from governed_agent.providers import StaticProvider
from governed_agent.verification import VerificationError, verify_completion


def _task(tmp_path: Path, **kwargs):
    defaults = dict(
        objective="test",
        required_artifacts=(str(tmp_path / "result.txt"),),
        allowed_tools=("artifact.write",),
        max_retries=0,
    )
    defaults.update(kwargs)
    return Task(**defaults)


def test_normal_completion(engine_factory, write_response):
    engine, metrics, tmp_path = engine_factory([StaticProvider("a", response=write_response)])
    record = engine.execute(_task(tmp_path))
    assert record.status is TaskStatus.COMPLETE
    assert record.receipt is not None
    assert len(record.receipt.receipt_sha256) == 64
    assert metrics.tasks_complete == 1
    assert engine.audit.verify_integrity()


def test_provider_unavailable(engine_factory, write_response):
    engine, _, tmp_path = engine_factory([StaticProvider("a", response=write_response, failure="unavailable")])
    record = engine.execute(_task(tmp_path))
    assert record.status is TaskStatus.FAILED
    assert record.failure_kind is FailureKind.PROVIDER_UNAVAILABLE


def test_quota_rate_failure(engine_factory, write_response):
    engine, _, tmp_path = engine_factory([StaticProvider("a", response=write_response, failure="rate_limited")])
    record = engine.execute(_task(tmp_path))
    assert record.failure_kind is FailureKind.RATE_LIMITED


def test_tool_failure(engine_factory):
    response = {"tool_name": "tool.fail", "arguments": {"message": "boom"}, "summary": "fail"}
    engine, _, _ = engine_factory([StaticProvider("a", response=response)])
    record = engine.execute(Task(objective="test", allowed_tools=("tool.fail",), max_retries=0))
    assert record.failure_kind is FailureKind.TOOL_FAILURE


def test_tool_not_allowlisted_is_blocked(engine_factory, write_response):
    engine, metrics, tmp_path = engine_factory([StaticProvider("a", response=write_response)])
    record = engine.execute(Task(objective="test", allowed_tools=("artifact.read",), max_retries=0))
    assert record.failure_kind is FailureKind.TOOL_NOT_ALLOWED
    assert metrics.tool_authorization_failures == 1
    assert not (tmp_path / "result.txt").exists()


def test_malformed_structured_output(engine_factory):
    engine, _, tmp_path = engine_factory([StaticProvider("a", response={"tool_name": "artifact.write"})])
    record = engine.execute(_task(tmp_path))
    assert record.failure_kind is FailureKind.MALFORMED_OUTPUT


def test_timeout(engine_factory, write_response):
    engine, _, tmp_path = engine_factory([StaticProvider("a", response=write_response, delay_s=0.05)])
    record = engine.execute(_task(tmp_path, timeout_s=0.001))
    assert record.failure_kind is FailureKind.TIMEOUT


def test_fallback(engine_factory, write_response):
    providers = [
        StaticProvider("a", response=write_response, failure="unavailable"),
        StaticProvider("b", response=write_response),
    ]
    engine, metrics, tmp_path = engine_factory(providers)
    record = engine.execute(_task(tmp_path))
    assert record.status is TaskStatus.COMPLETE
    assert record.provider_used == "b"
    assert record.fallback_count == 1
    assert metrics.fallback_successes == 1


def test_approval_denied(engine_factory, write_response):
    engine, _, tmp_path = engine_factory([StaticProvider("a", response=write_response)], approval=False)
    record = engine.execute(_task(tmp_path, approval_required=True))
    assert record.failure_kind is FailureKind.APPROVAL_DENIED
    assert not (tmp_path / "result.txt").exists()


def test_missing_evidence(engine_factory, write_response):
    bad = dict(write_response)
    bad["arguments"] = {"path": "different.txt", "content": "x"}
    engine, _, tmp_path = engine_factory([StaticProvider("a", response=bad)])
    record = engine.execute(_task(tmp_path))
    assert record.failure_kind is FailureKind.VERIFICATION_FAILED
    assert "missing required evidence" in record.message


def test_stale_evidence(tmp_path):
    artifact = tmp_path / "result.txt"
    artifact.write_text("old", encoding="utf-8")
    task = Task(objective="test", required_artifacts=(str(artifact),))
    receipt = build_receipt(
        task_id=task.task_id,
        provider="a",
        tool_name="artifact.write",
        started_at=task.created_at,
        artifact_paths=(str(artifact),),
    )
    stale_item = replace(receipt.evidence[0], modified_at=task.created_at - timedelta(seconds=10))
    stale_receipt = replace(receipt, evidence=(stale_item,))
    try:
        verify_completion(task, stale_receipt)
    except VerificationError as exc:
        assert "integrity" in str(exc) or "stale evidence" in str(exc)
    else:
        raise AssertionError("stale evidence should fail")


def test_duplicate_execution(engine_factory, write_response):
    engine, _, tmp_path = engine_factory([StaticProvider("a", response=write_response)])
    task = _task(tmp_path)
    first = engine.execute(task)
    second = engine.execute(task)
    assert first.status is TaskStatus.COMPLETE
    assert second.failure_kind is FailureKind.DUPLICATE_EXECUTION


def test_complete_without_required_artifact_is_blocked(engine_factory, write_response):
    bad = dict(write_response)
    bad["arguments"] = {"path": "result.txt", "content": "created"}
    engine, _, tmp_path = engine_factory([StaticProvider("a", response=bad)])
    task = Task(
        objective="test",
        required_artifacts=(str(tmp_path / "required.txt"),),
        allowed_tools=("artifact.write",),
        max_retries=0,
    )
    record = engine.execute(task)
    assert record.status is TaskStatus.FAILED
    assert record.failure_kind is FailureKind.VERIFICATION_FAILED


def test_same_size_artifact_mutation_is_detected(tmp_path):
    artifact = tmp_path / "result.txt"
    task = Task(objective="test", required_artifacts=(str(artifact),))
    artifact.write_text("AAAA", encoding="utf-8")
    receipt = build_receipt(
        task_id=task.task_id,
        provider="a",
        tool_name="artifact.write",
        started_at=task.created_at,
        artifact_paths=(str(artifact),),
    )
    artifact.write_text("BBBB", encoding="utf-8")
    try:
        verify_completion(task, receipt)
    except VerificationError as exc:
        assert "hash changed" in str(exc)
    else:
        raise AssertionError("same-size mutation should fail hash verification")


def test_receipt_tamper_is_detected(tmp_path):
    artifact = tmp_path / "result.txt"
    artifact.write_text("AAAA", encoding="utf-8")
    task = Task(objective="test", required_artifacts=(str(artifact),))
    receipt = build_receipt(
        task_id=task.task_id,
        provider="a",
        tool_name="artifact.write",
        started_at=task.created_at,
        artifact_paths=(str(artifact),),
    )
    tampered = replace(receipt, notes=("changed after signing",))
    try:
        verify_completion(task, tampered)
    except VerificationError as exc:
        assert "receipt integrity" in str(exc)
    else:
        raise AssertionError("tampered receipt should fail")


def test_retry_can_recover_same_provider(engine_factory, tmp_path):
    from governed_agent.models import ProviderResult
    from governed_agent.providers import ProviderAdapter, RateLimited

    class FlakyProvider(ProviderAdapter):
        name = "flaky"

        def __init__(self):
            self.calls = 0

        def generate(self, task):
            self.calls += 1
            if self.calls == 1:
                raise RateLimited("temporary quota")
            return ProviderResult(
                provider=self.name,
                tool_name="artifact.write",
                arguments={"path": "result.txt", "content": "retry recovered"},
                summary="recovered after retry",
            )

    provider = FlakyProvider()
    engine, metrics, _ = engine_factory([provider])
    task = Task(
        objective="recover after bounded retry",
        required_artifacts=(str(tmp_path / "result.txt"),),
        allowed_tools=("artifact.write",),
        max_retries=1,
    )
    record = engine.execute(task)
    assert record.status is TaskStatus.COMPLETE
    assert record.retry_count == 1
    assert provider.calls == 2
    assert metrics.retries == 1
