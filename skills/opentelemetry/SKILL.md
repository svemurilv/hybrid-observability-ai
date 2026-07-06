---
name: opentelemetry
description: OpenTelemetry concepts for normalization/correlation — signals (traces/metrics/logs), semantic conventions (service.name, trace_id, http.*, k8s.*), OTLP ingest. Use when normalizing signals across platforms or building an OTLP connector. Trigger — "otel", "opentelemetry", "otlp", "semantic conventions", "trace_id".
---
# OpenTelemetry for cross-platform correlation
OTel is the vendor-neutral schema this framework normalizes to (see docs/CONNECTOR_SDK.md §2.1).

## Signals
- **traces** — spans with `trace_id`/`span_id`; **metrics** — counter/gauge/histogram; **logs** — body + attributes.

## Key semantic-convention attributes (normalize to these)
- `service.name`, `service.namespace`
- `trace_id`, `span_id`
- `http.request.method`, `http.response.status_code`, `url.path`
- `k8s.cluster.name`, `k8s.namespace.name`, `k8s.pod.name`, `host.name`
- `error.type`, `exception.message`

## Correlation key
Use `trace_id` to stitch a request across platforms; fall back to a business correlation id found in the log body/attributes.

## OTLP connector
Ingest OTLP (gRPC :4317 / HTTP :4318); map resource + attributes to the normalized record
(`timestamp, severity, service, resource, body, attributes, trace_id`).
Pitfalls: platforms name fields differently — normalize on ingest to semantic-convention keys so correlation works everywhere.
