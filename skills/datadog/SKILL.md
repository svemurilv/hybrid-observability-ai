---
name: datadog
description: Datadog recipes — log search facets, metrics query language, APM trace search. Use when querying Datadog logs/metrics/traces. Trigger — "datadog", "dd", "log search", "apm".
---
# Datadog recipes
## Log search — errors for a service (last 1h)
```
service:service-a status:error @http.status_code:[500 TO 599]
```
## Metrics — 5xx rate
```
sum:trace.http.request.errors{service:service-a,http.status_code:5*}.as_rate()
```
## Metrics — p95 latency
```
p95:trace.http.request.duration{service:service-a}
```
## APM trace search
```
service:service-a operation_name:http.request status:error
```
## Correlate a transaction
```
"<TRANSACTION_ID>"    # Logs search, scoped to the incident time window
```
Pitfalls: log search uses `key:value` facets and `@attr` for structured fields; metrics use `{tag filters}` + rollups; always scope the time picker.
