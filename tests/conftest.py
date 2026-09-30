from pathlib import Path
import pytest

from governed_agent.approvals import StaticApprovalPolicy
from governed_agent.audit import AuditTrail
from governed_agent.engine import WorkflowEngine
from governed_agent.metrics import Metrics
from governed_agent.router import Router
from governed_agent.tools import build_default_tools


@pytest.fixture
def engine_factory(tmp_path: Path):
    def make(providers, approval=True, *, router=None, state_store=None, audit=None):
        metrics = Metrics()
        engine = WorkflowEngine(
            router=router or Router(providers),
            tools=build_default_tools(tmp_path),
            approval_policy=StaticApprovalPolicy(approval),
            metrics=metrics,
            audit=audit or AuditTrail(),
            state_store=state_store,
        )
        return engine, metrics, tmp_path

    return make


@pytest.fixture
def write_response():
    return {
        "tool_name": "artifact.write",
        "arguments": {"path": "result.txt", "content": "verified output"},
        "summary": "write result",
    }
