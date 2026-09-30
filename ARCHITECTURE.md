# Architecture

The demo separates policy, routing and execution so each decision boundary can be tested independently.

```text
Task
 |
policy evaluation
 |---- approval required ----> awaiting_approval
 |
eligibility filter
(capability + health + quota)
 |
free-first deterministic ordering
 |
provider attempt
 |---- failure ----> mark unavailable -> next provider
 |
success
 |
ExecutionResult
(status + provider + attempt history + reasons)
```

Provider implementations are injected as callables. CI can therefore simulate outages and fallback deterministically without external services.
