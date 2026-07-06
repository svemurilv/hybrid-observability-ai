---
name: opensearch
description: OpenSearch / Elasticsearch recipes — Query DSL (bool/term/range) and PPL (Piped Processing Language). Use when querying OpenSearch/Elastic indices. Trigger — "opensearch", "elasticsearch", "query dsl", "ppl".
---
# OpenSearch: Query DSL + PPL
## Query DSL — errors for a service (last hour)
```json
{ "query": { "bool": { "filter": [
  { "term":  { "service.keyword": "service-a" } },
  { "term":  { "level.keyword": "ERROR" } },
  { "range": { "@timestamp": { "gte": "now-1h" } } } ] } },
  "size": 50, "sort": [ { "@timestamp": "desc" } ] }
```
## Query DSL — count by service
```json
{ "size": 0, "aggs": { "by_service": { "terms": { "field": "service.keyword" } } } }
```
## PPL — same, piped
```
source=<index> | where level='ERROR' and service='service-a' | sort - @timestamp | head 50
```
## PPL — count by service
```
source=<index> | stats count() by service
```
## Correlate a transaction
```
source=<index> | where like(message, '%<TRANSACTION_ID>%')
```
Pitfalls: use `.keyword` sub-fields for `term`/aggregations on text; `range` on `@timestamp`; PPL is easier for ad-hoc triage.
