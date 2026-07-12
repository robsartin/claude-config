---
status: Accepted
date: "{{date}}"
topic: observability-in-js-ts
tags: [interaction, observability, js-ts]
supersedes: []
related: [observability-baseline, js-ts-toolchain]
---
# {{number}}. Observability in JS/TS

## Context

The observability baseline needs concrete JS/TS tooling for Node services and, where
relevant, the browser. Selecting both observability and js-ts settles the mechanics.

## Decision

- **Tracing and metrics** via the **OpenTelemetry JS SDK** — auto-instrumentation for
  HTTP/framework spans plus manual spans around domain operations; export over OTLP.
- **Structured logging** with **pino** (JSON), including the active **trace/span id** on
  each line so logs correlate with traces.
- **Context propagation** uses OpenTelemetry context (W3C `traceparent`) across service
  calls; a request id is generated at the edge if absent.
- **Browser** (where applicable) uses OpenTelemetry web for real-user monitoring, sampled
  to control volume, and never logs PII.

## Alternatives considered

- **A vendor SDK (Datadog RUM, Sentry tracing) instead of the OpenTelemetry JS SDK** —
  rejected because it locks tracing to one backend instead of keeping export OTLP-based and
  swappable.
- **`console.log`/`morgan` text logs instead of structured `pino` JSON** — rejected because
  unstructured logs can't reliably carry or be correlated by trace/span ids.
- **A custom request-id header instead of W3C `traceparent` propagation** — rejected because
  it wouldn't interoperate with upstream/downstream services using standard OpenTelemetry
  context propagation.

## Consequences

- Node (and optionally browser) telemetry is OpenTelemetry-native, so backends stay
  swappable and correlate with other stacks.
- pino keeps logging fast and structured with trace correlation built in.
- Auto-instrumentation plus sampling configuration is ongoing setup and tuning work.
