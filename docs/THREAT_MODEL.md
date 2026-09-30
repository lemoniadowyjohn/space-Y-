# Lightweight Threat Model

This is a portfolio prototype, not a production security design. The threat model exists to make control assumptions explicit.

## Assets protected

- task intent and execution state;
- authorization boundary before side effects;
- artifact/evidence integrity;
- idempotency state used to prevent duplicate work;
- audit history;
- configured tool workspace.

## Trust boundaries

1. **Task input → parser:** user/task data is untrusted until schema validation succeeds.
2. **Provider → engine:** provider output is untrusted structured input, not execution authority.
3. **Engine → tools:** only task-allowlisted tools may execute.
4. **Approval → engine:** approval is bound to task + exact action digest, expires, and is single-use.
5. **Tool output → completion:** tool success is insufficient; required artifacts must independently verify.
6. **Process restart → state store:** a prior incomplete claim is not silently replayed.

## Threats handled in the demo

- malformed provider output;
- provider outage/rate-limit/timeout classes;
- repeated unhealthy-provider selection through circuit state;
- provider choosing a non-authorized tool;
- path traversal outside the configured artifact workspace;
- approval denial, expiration, replay, or action substitution;
- duplicate logical task execution across process restart;
- silent replay after an incomplete/crashed execution claim;
- missing/stale/changed artifacts;
- same-size artifact modification;
- evidence-receipt mutation;
- historical audit-event tampering;
- child self-report being mistaken for verified parent completion.

## Residual risks / non-goals

The repository does **not** implement production authentication/authorization, tenant isolation, encrypted state, secret vaulting, remote-attestation, signed approvals from an identity provider, distributed consensus/locking, production queue leases, network policy, sandboxed arbitrary code execution, real LLM-provider credentials, production telemetry, or incident response automation.

SQLite and JSONL are used here to demonstrate state/audit concepts locally; they are not presented as a distributed production control plane.
