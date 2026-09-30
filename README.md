# Governed Agent Workflow Demo

[![CI](https://github.com/lemoniadowyjohn/space-Y-/actions/workflows/ci.yml/badge.svg)](https://github.com/lemoniadowyjohn/space-Y-/actions/workflows/ci.yml)

> **Repository slug note:** `space-Y-` is historical. The project presented on the default branch is the **Governed Agent Workflow Demo**. The prior coursework landing page is preserved on the `legacy-space-y-coursework` branch.

A compact Python portfolio project demonstrating policy-aware task routing, provider health/quota checks, deterministic fallback, inspectable execution attempts and explicit human approval for high-risk side effects.

## Verified baseline

- GitHub Actions: **PASS**
- automated tests: **6 passing**
- policy regression coverage includes explicit high-risk action approval
- synthetic/demo inputs only; no credentials or private agent configuration

## Problem

Agent workflows can appear successful while silently routing to unavailable providers, crossing approval boundaries or hiding fallback failures. This project makes those decisions explicit and testable.

## Demonstrated controls

- capability-based routing;
- provider health and quota gates;
- free-provider preference;
- deterministic fallback after provider failure;
- high-risk approval boundary;
- blocked state when no provider is eligible;
- inspectable attempt history;
- pytest regression tests and GitHub Actions CI.

## Run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
python examples/demo.py
```

## Claim boundary

This is a sanitized portfolio implementation based on agent-orchestration engineering concepts. It is not presented as an enterprise production LLM platform, commercial deployment or senior AI architecture. No private agent configuration, credentials or employer/customer data are included.

See [ARCHITECTURE.md](ARCHITECTURE.md), [LIMITATIONS.md](LIMITATIONS.md) and [SECURITY.md](SECURITY.md).

## Related portfolio

- [Industrial Quality Documentation Assistant](https://github.com/lemoniadowyjohn/hermes) — evidence-grounded industrial RAG portfolio project.
- [CARLA Map Quality Toolkit](https://github.com/lemoniadowyjohn/carla-control-suite/tree/portfolio/carla-map-quality-toolkit-20260930/portfolio/carla-map-quality-toolkit) — automotive/geospatial validation toolkit with CI-backed quality gates.
