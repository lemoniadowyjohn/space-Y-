from __future__ import annotations

from dataclasses import dataclass

from .models import Task


HIGH_RISK_TOOLS = {
    "execute_trade",
    "send_external_email",
    "delete_file",
    "deploy_production",
}


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str


def evaluate(task: Task, approved: bool = False) -> PolicyDecision:
    high_risk = task.risk.lower() == "high" or task.action in HIGH_RISK_TOOLS
    if high_risk and not approved:
        return PolicyDecision(False, True, "human approval required")
    return PolicyDecision(True, False, "policy passed")
