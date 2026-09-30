from gaw.models import ProviderState, Task
from gaw.orchestrator import Orchestrator


def task(**kwargs):
    values = {
        "task_id": "T-1",
        "capability": "analysis",
        "prompt": "analyze synthetic input",
    }
    values.update(kwargs)
    return Task(**values)


def test_prefers_free_healthy_provider():
    providers = [
        ProviderState("paid", {"analysis"}, free=False, priority=1),
        ProviderState("free", {"analysis"}, free=True, priority=50),
    ]
    orch = Orchestrator(
        providers,
        {"paid": lambda t: "paid", "free": lambda t: "free"},
    )
    result = orch.run(task())
    assert result.status == "completed"
    assert result.provider == "free"


def test_falls_back_after_provider_failure():
    providers = [
        ProviderState("first", {"analysis"}, free=True, priority=1),
        ProviderState("second", {"analysis"}, free=True, priority=2),
    ]

    def fail(_):
        raise RuntimeError("synthetic outage")

    orch = Orchestrator(
        providers,
        {"first": fail, "second": lambda t: "fallback-ok"},
    )
    result = orch.run(task())
    assert result.provider == "second"
    assert [a.outcome for a in result.attempts] == ["failed", "success"]
    assert providers[0].healthy is False


def test_high_risk_action_requires_approval():
    provider = ProviderState("free", {"analysis"})
    orch = Orchestrator([provider], {"free": lambda t: "executed"})
    pending = orch.run(task(action="external_side_effect", risk="high"))
    assert pending.status == "awaiting_approval"
    approved = orch.run(
        task(action="external_side_effect", risk="high"),
        approved=True,
    )
    assert approved.status == "completed"


def test_zero_quota_blocks_provider():
    provider = ProviderState("free", {"analysis"}, quota_remaining=0)
    orch = Orchestrator([provider], {"free": lambda t: "never"})
    result = orch.run(task())
    assert result.status == "blocked"
    assert "no eligible provider" in result.reasons


def test_capability_mismatch_is_not_routed():
    provider = ProviderState("free", {"vision"})
    orch = Orchestrator([provider], {"free": lambda t: "never"})
    result = orch.run(task(capability="analysis"))
    assert result.status == "blocked"
