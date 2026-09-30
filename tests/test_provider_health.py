from governed_agent.models import ProviderHealth, Task, TaskStatus
from governed_agent.providers import ProviderHealthRegistry, StaticProvider
from governed_agent.router import Router


def test_repeated_failures_open_provider_circuit(engine_factory, write_response):
    registry = ProviderHealthRegistry(failure_threshold=1, cooldown_seconds=60)
    bad = StaticProvider("a", response=write_response, failure="unavailable")
    good = StaticProvider("b", response=write_response)
    router = Router([bad, good], health_registry=registry)
    engine, metrics, tmp_path = engine_factory([bad, good], router=router)
    task = Task(
        objective="x",
        required_artifacts=(str(tmp_path / "result.txt"),),
        allowed_tools=("artifact.write",),
        max_retries=0,
    )
    record = engine.execute(task)
    assert record.status is TaskStatus.COMPLETE
    assert registry.state("a").health is ProviderHealth.DOWN
    assert metrics.circuit_open_events == 1


def test_open_circuit_is_skipped_on_next_task(engine_factory, write_response):
    registry = ProviderHealthRegistry(failure_threshold=1, cooldown_seconds=60)
    bad = StaticProvider("a", response=write_response, failure="unavailable")
    good = StaticProvider("b", response=write_response)
    router = Router([bad, good], health_registry=registry)
    engine, _, tmp_path = engine_factory([bad, good], router=router)

    first = Task(
        objective="first",
        required_artifacts=(str(tmp_path / "result.txt"),),
        allowed_tools=("artifact.write",),
        max_retries=0,
    )
    assert engine.execute(first).status is TaskStatus.COMPLETE
    first_bad_calls = bad.calls

    second = Task(
        objective="second",
        required_artifacts=(str(tmp_path / "result.txt"),),
        allowed_tools=("artifact.write",),
        max_retries=0,
    )
    assert engine.execute(second).status is TaskStatus.COMPLETE
    assert bad.calls == first_bad_calls


def test_all_open_circuits_fail_closed(engine_factory, write_response):
    from governed_agent.models import FailureKind

    registry = ProviderHealthRegistry(failure_threshold=1, cooldown_seconds=60)
    provider = StaticProvider("a", response=write_response)
    registry.record_failure("a")
    router = Router([provider], health_registry=registry)
    engine, _, tmp_path = engine_factory([provider], router=router)
    record = engine.execute(
        Task(
            objective="blocked",
            allowed_tools=("artifact.write",),
            required_artifacts=(str(tmp_path / "result.txt"),),
            max_retries=0,
        )
    )
    assert record.failure_kind is FailureKind.CIRCUIT_OPEN
    assert provider.calls == 0
