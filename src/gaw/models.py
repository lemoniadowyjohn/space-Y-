from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Task:
    task_id: str
    capability: str
    prompt: str
    tool: str | None = None
    risk: str = "low"


@dataclass
class ProviderState:
    name: str
    capabilities: set[str]
    healthy: bool = True
    quota_remaining: int = 100
    free: bool = True
    priority: int = 100


@dataclass(frozen=True)
class Attempt:
    provider: str
    outcome: str
    detail: str


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    output: str = ""
    provider: str | None = None
    attempts: tuple[Attempt, ...] = ()
    reasons: tuple[str, ...] = ()


ProviderFn = Callable[[Task], str]
