from __future__ import annotations

from .models import Task
from .providers import ProviderAdapter, ProviderHealthRegistry


class Router:
    """Deterministic provider ordering plus health/circuit eligibility."""

    def __init__(
        self,
        providers: list[ProviderAdapter],
        health_registry: ProviderHealthRegistry | None = None,
    ) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        self.providers = providers
        self.health_registry = health_registry or ProviderHealthRegistry()

    def route(self, task: Task) -> list[ProviderAdapter]:
        if task.preferred_provider is None:
            ordered = list(self.providers)
        else:
            preferred = [p for p in self.providers if p.name == task.preferred_provider]
            others = [p for p in self.providers if p.name != task.preferred_provider]
            ordered = preferred + others
        return [p for p in ordered if self.health_registry.eligible(p.name)]

    def record_failure(self, provider_name: str) -> bool:
        return self.health_registry.record_failure(provider_name)

    def record_success(self, provider_name: str) -> None:
        self.health_registry.record_success(provider_name)
