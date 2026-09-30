from dataclasses import replace
from datetime import timedelta

import pytest

from governed_agent.approvals import ApprovalError, StaticApprovalPolicy
from governed_agent.models import Task, utc_now


def test_approval_is_bound_to_exact_action():
    policy = StaticApprovalPolicy(True)
    task = Task(objective="x")
    decision = policy.request(task, "artifact.write", {"path": "a.txt"})
    with pytest.raises(ApprovalError, match="action hash mismatch"):
        policy.validate_and_consume(decision, task, "artifact.write", {"path": "b.txt"})


def test_approval_is_one_time_use():
    policy = StaticApprovalPolicy(True)
    task = Task(objective="x")
    args = {"path": "a.txt"}
    decision = policy.request(task, "artifact.write", args)
    policy.validate_and_consume(decision, task, "artifact.write", args)
    with pytest.raises(ApprovalError, match="replay"):
        policy.validate_and_consume(decision, task, "artifact.write", args)


def test_expired_approval_is_rejected():
    policy = StaticApprovalPolicy(True)
    task = Task(objective="x")
    args = {"path": "a.txt"}
    decision = policy.request(task, "artifact.write", args)
    expired = replace(decision, expires_at=utc_now() - timedelta(seconds=1))
    with pytest.raises(ApprovalError, match="expired"):
        policy.validate_and_consume(expired, task, "artifact.write", args)
