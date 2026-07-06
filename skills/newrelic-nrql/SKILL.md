---
name: newrelic-nrql
description: New Relic Query Language (NRQL) recipes — SELECT ... FROM event/metric, WHERE, FACET, TIMESERIES, SINCE. Use when querying New Relic APM/logs/metrics/traces. Trigger — "new relic", "nrql", "FACET", "TIMESERIES".
---
# New Relic NRQL recipes
## Error count by service (last hour)
```
SELECT count(*) FROM TransactionError SINCE 1 hour ago FACET appName
```
## 5xx by endpoint
```
SELECT count(*) FROM Transaction WHERE httpResponseCode >= '500' FACET name SINCE 6 hours ago
```
## p95 latency timeseries
```
SELECT percentile(duration, 95) FROM Transaction WHERE appName='service-a' TIMESERIES SINCE 1 hour ago
```
## Logs search
```
SELECT message FROM Log WHERE service_name='service-a' AND level='ERROR' SINCE 1 hour ago LIMIT 50
```
## Correlate a trace
```
SELECT * FROM Span WHERE trace.id = '<TRACE_ID>' SINCE 1 day ago
```
Pitfalls: `FACET` = group by; `TIMESERIES` = trend; `SINCE`/`UNTIL` for time; quote string values.
