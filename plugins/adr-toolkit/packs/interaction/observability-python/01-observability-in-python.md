---
status: Accepted
date: "{{date}}"
topic: observability-in-python
tags: [interaction, observability, python]
supersedes: []
related: [observability-baseline, python-toolchain, service-conventions]
---
# {{number}}. Observability in Python

## Context

The observability baseline (structured logs, metrics, OpenTelemetry tracing, correlation)
needs concrete Python tooling. Python services run under WSGI or ASGI servers with several
worker processes, which affects how metrics are aggregated and how request context is
carried. Selecting both observability and Python settles the mechanics, whichever framework
the project uses.

## Decision

- **Tracing and metrics** use the **OpenTelemetry Python SDK** with the instrumentation
  package matching the framework in use, plus manual spans around domain operations; export
  over OTLP.
- **Structured logging** emits JSON through the standard `logging` module (with a JSON
  formatter), adding the active **trace and span ids** to every record.
- **Request context** (request id, trace id) is carried in `contextvars`, not thread-locals
  or module globals, so it is correct under both threaded and async execution.
- **Multi-process servers** export telemetry per process through OTLP, or use the metrics
  client's documented multiprocess mode; a metric is never silently per-worker.
- **No PII in logs, spans or metric labels**, per the observability baseline.

## Alternatives considered

- **A vendor APM agent instead of OpenTelemetry** — rejected, as in the baseline, because it
  ties instrumentation to one backend.
- **`print` or unstructured `logging` text** — cannot be queried or correlated by trace id.
- **Thread-local request context** — works for threaded WSGI and silently leaks or loses
  context under asyncio, where many requests share one thread.
- **Per-process Prometheus counters scraped from one worker** — each scrape sees a random
  worker's partial counts; multiprocess mode or OTLP aggregation avoids that.

## Consequences

- Python services produce telemetry that correlates with the other stacks and keeps the
  backend swappable.
- Context handling is correct under sync and async execution.
- Multiprocess metric handling is extra deployment configuration to document and test.
