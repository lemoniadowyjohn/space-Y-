# Small-Commit Implementation Roadmap

The repository can be reconstructed or reviewed as a sequence of bounded commits. Every stage has a behavioral completion gate rather than a documentation-only definition of done.

| Stage | Commit intent | Primary files | Completion gate |
|---|---|---|---|
| A01 | Repository skeleton | `pyproject.toml`, `.gitignore`, `src/`, `tests/` | editable install works without credentials |
| A02 | Task schema and parser | `models.py`, `planning.py` | unknown fields fail closed |
| A03 | Provider abstraction | `providers.py` | typed provider failures can be reproduced |
| A04 | Deterministic routing | `router.py` | stable route and preferred-provider behavior |
| A05 | Tool registry | `tools.py` | workspace containment and explicit registry |
| A06 | Basic approval gate | `approvals.py`, `engine.py` | denied action produces no side effect |
| A07 | Artifact evidence receipt | `evidence.py` | successful output produces hash/size/time evidence |
| A08 | Completion verification | `verification.py`, `repository.py` | missing/stale/changed artifact blocks completion |
| A09 | Retry/fallback taxonomy | `engine.py` | provider failures may fall back; tool failure does not blindly replay |
| A10 | Behavioral tests | `tests/` | required failure matrix passes |
| A11 | Metrics | `metrics.py` | success/failure/retry/approval/latency metrics inspectable |
| A12 | Docker artifact | `Dockerfile` | package can be installed/run in a clean Python image |
| A13 | Reproducible scenarios | `demo.py`, `examples/` | success/fallback/approval scenarios return structured records |
| A14 | Architecture documentation | `docs/ARCHITECTURE.md` | diagram matches code path |
| A15 | Recruiter-facing README | `README.md` | problem/solution/demo visible in first screen |
| A16 | Sanitized outputs | `demo_outputs/` | no host paths, secrets or customer data |
| A17 | Least-privilege tool allowlist | `models.py`, `tools.py`, `engine.py` | non-allowlisted provider action is blocked |
| A18 | Action-bound approvals | `approvals.py` | mismatch/expiry/replay tests pass |
| A19 | Provider health/circuit | `providers.py`, `router.py` | unhealthy provider opens circuit and is skipped |
| A20 | Restart-safe idempotency | `state.py`, `engine.py` | duplicate logical task blocked across engine restart |
| A21 | Crash-state recovery boundary | `state.py`, `engine.py` | incomplete prior claim returns `RECOVERY_REQUIRED` |
| A22 | Tamper-evident audit | `audit.py`, `engine.py` | mutation breaks chain verification |
| A23 | Parent/child evidence gate | `completion.py` | child self-report without receipt cannot close group |
| A24 | Portfolio acceptance automation | `scripts/acceptance_check.py`, CI | tests+demos+secret scan+docs all pass |
| A25 | Claim/evidence matrix | `docs/CAPABILITY_MATRIX.md` | important claims trace to code/test or explicit non-claim |
| A26 | Threat model/interview evidence | `docs/THREAT_MODEL.md`, `INTERVIEW_EVIDENCE.md` | trust boundaries and limitations are explicit |
