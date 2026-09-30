# Security and sanitization

This repository is intentionally self-contained and requires no real provider credentials.

## Implemented safeguards in the demo

- strict task-field validation;
- explicit per-task tool allowlists;
- artifact workspace path containment;
- action-bound, expiring, one-time approvals;
- persistent local idempotency through SQLite;
- fail-closed handling of incomplete prior execution;
- artifact and receipt hashing;
- tamper-evident audit chaining;
- common secret-pattern scan in `scripts/acceptance_check.py`.

## Publishing rules

Do not commit `.env` files, provider tokens, account identifiers, customer data, proprietary prompts, private endpoints, machine-specific infrastructure paths, or recovered operational logs.

`.env.example` contains placeholders only. Demo providers are deterministic local fakes and make no external model API calls.

Before publishing, inspect the **full Git history** as well as the current tree. Removing a secret from the latest commit is insufficient if it remains in earlier Git objects.

See `docs/THREAT_MODEL.md` for residual risks and explicit non-goals.
