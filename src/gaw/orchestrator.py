from __future__ import annotations

from .models import Attempt, ExecutionResult, ProviderFn, ProviderState, Task
from .policy import evaluate
from .router import eligible_providers


class Orchestrator:
    def __init__(
        self,
        providers: list[ProviderState],
        implementations: dict[str, ProviderFn],
    ) -> None:
        self.providers = providers
        self.implementations = implementations

    def run(self, task: Task, *, approved: bool = False) -> ExecutionResult:
        policy = evaluate(task, approved=approved)
        if not policy.allowed:
            return ExecutionResult(
                status="awaiting_approval" if policy.requires_approval else "blocked",
                reasons=(policy.reason,),
            )

        candidates = eligible_providers(task, self.providers)
        if not candidates:
            return ExecutionResult(
                status="blocked",
                reasons=("no eligible provider",),
            )

        attempts: list[Attempt] = []
        for provider in candidates:
            implementation = self.implementations.get(provider.name)
            if implementation is None:
                attempts.append(
                    Attempt(provider.name, "skipped", "implementation missing")
                )
                continue
            try:
                output = implementation(task)
                provider.quota_remaining -= 1
                attempts.append(Attempt(provider.name, "success", "completed"))
                return ExecutionResult(
                    status="completed",
                    output=output,
                    provider=provider.name,
                    attempts=tuple(attempts),
                )
            except Exception as exc:
                provider.healthy = False
                attempts.append(
                    Attempt(provider.name, "failed", type(exc).__name__)
                )

        return ExecutionResult(
            status="blocked",
            attempts=tuple(attempts),
            reasons=("all eligible providers failed",),
        )
