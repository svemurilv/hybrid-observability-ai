---
name: grafana-observability
description: Grafana query recipes — LogQL (Loki logs), PromQL (Prometheus metrics), dashboard/datasource discovery. Use when querying Grafana Loki/Prometheus or exploring dashboards. Trigger — "grafana", "loki", "logql", "promql", "prometheus".
---
# Grafana: LogQL + PromQL
## LogQL — errors for a service (Loki)
```
{service="service-a"} |= "error" | json | line_format "{{.message}}"
```
## LogQL — error rate over time
```
sum(rate({service="service-a"} |= "error" [5m]))
```
## PromQL — 5xx rate
```
sum(rate(http_server_requests_seconds_count{app="service-a",status=~"5.."}[5m]))
```
## PromQL — p99 latency
```
histogram_quantile(0.99, sum(rate(http_server_requests_seconds_bucket{app="service-a"}[5m])) by (le))
```
## Discover sources / dashboards (Grafana API or MCP)
`list_datasources` · `search_dashboards(query="...")` · `get_dashboard_panel_queries(uid=...)`
Pitfalls: LogQL order is `{labels}` → line filters `|=`/`|~` → parsers (`json`/`logfmt`); PromQL `rate()` needs a range vector `[5m]`; match label sets exactly.
