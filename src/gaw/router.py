from __future__ import annotations

from .models import ProviderState, Task


def eligible_providers(
    task: Task,
    providers: list[ProviderState],
) -> list[ProviderState]:
    eligible = [
        provider
        for provider in providers
        if provider.healthy
        and provider.quota_remaining > 0
        and task.capability in provider.capabilities
    ]
    return sorted(
        eligible,
        key=lambda provider: (
            not provider.free,
            provider.priority,
            provider.name,
        ),
    )
