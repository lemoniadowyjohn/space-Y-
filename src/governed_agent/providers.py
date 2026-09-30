from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
from typing import Any, Callable

from .models import ProviderHealth, ProviderResult, Task, utc_now


class ProviderError(RuntimeError):
    pass


class ProviderUnavailable(ProviderError):
    pass


class RateLimited(ProviderError):
    pass


class ProviderTimeout(ProviderError):
    pass


class MalformedProviderOutput(ProviderError):
    pass


class ProviderCircuitOpen(ProviderError):
    pass


class ProviderAdapter(ABC):
    name: str

    @abstractmethod
    def generate(self, task: Task) -> ProviderResult:
        raise NotImplementedError


@dataclass
class ProviderRuntimeState:
    health: ProviderHealth = ProviderHealth.HEALTHY
    consecutive_failures: int = 0
    circuit_open_until: datetime | None = None


class ProviderHealthRegistry:
    """Tracks provider health and opens a short circuit after repeated failures."""

    def __init__(
        self,
        *,
        failure_threshold: int = 2,
        cooldown_seconds: int = 30,
        now_fn: Callable[[], datetime] = utc_now,
    ) -> None:
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = max(1, cooldown_seconds)
        self.now_fn = now_fn
        self._states: dict[str, ProviderRuntimeState] = {}

    def state(self, provider_name: str) -> ProviderRuntimeState:
        return self._states.setdefault(provider_name, ProviderRuntimeState())

    def eligible(self, provider_name: str) -> bool:
        state = self.state(provider_name)
        if state.circuit_open_until is None:
            return True
        now = self.now_fn()
        if now >= state.circuit_open_until:
            state.health = ProviderHealth.DEGRADED
            state.circuit_open_until = None
            state.consecutive_failures = 0
            return True
        state.health = ProviderHealth.DOWN
        return False

    def record_failure(self, provider_name: str) -> bool:
        state = self.state(provider_name)
        state.consecutive_failures += 1
        state.health = ProviderHealth.DEGRADED
        opened = False
        if state.consecutive_failures >= self.failure_threshold:
            state.health = ProviderHealth.DOWN
            state.circuit_open_until = self.now_fn() + timedelta(seconds=self.cooldown_seconds)
            opened = True
        return opened

    def record_success(self, provider_name: str) -> None:
        state = self.state(provider_name)
        state.health = ProviderHealth.HEALTHY
        state.consecutive_failures = 0
        state.circuit_open_until = None

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "health": state.health.value,
                "consecutive_failures": state.consecutive_failures,
                "circuit_open_until": state.circuit_open_until.isoformat() if state.circuit_open_until else None,
            }
            for name, state in self._states.items()
        }


class StaticProvider(ProviderAdapter):
    """Deterministic provider used for local demos and tests."""

    def __init__(
        self,
        name: str,
        response: dict[str, Any] | None = None,
        failure: str | None = None,
        delay_s: float = 0.0,
    ) -> None:
        self.name = name
        self.response = response or {}
        self.failure = failure
        self.delay_s = delay_s
        self.calls = 0

    def generate(self, task: Task) -> ProviderResult:
        self.calls += 1
        if self.delay_s:
            time.sleep(self.delay_s)
        if self.failure == "unavailable":
            raise ProviderUnavailable(f"{self.name} unavailable")
        if self.failure == "rate_limited":
            raise RateLimited(f"{self.name} rate limited")
        if self.failure == "timeout":
            raise ProviderTimeout(f"{self.name} timed out")
        if self.failure == "malformed":
            raise MalformedProviderOutput(f"{self.name} returned malformed output")

        required = {"tool_name", "arguments", "summary"}
        if not required.issubset(self.response):
            raise MalformedProviderOutput(
                f"{self.name} response missing fields: {sorted(required - self.response.keys())}"
            )
        if not isinstance(self.response["arguments"], dict):
            raise MalformedProviderOutput("arguments must be an object")

        return ProviderResult(
            provider=self.name,
            tool_name=str(self.response["tool_name"]),
            arguments=dict(self.response["arguments"]),
            summary=str(self.response["summary"]),
        )
