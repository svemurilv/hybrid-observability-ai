---
name: splunk-spl
description: Splunk Search Processing Language (SPL) recipes — search then pipe transforms; filter by index/sourcetype/host, stats aggregation, timechart trends, rex field extraction, transaction correlation. Use when querying Splunk. Trigger — "splunk", "SPL", "index=", "sourcetype".
---
# Splunk SPL recipes
A base search, then `|` transforms. Put the most selective terms first; use `earliest`/`latest` for time.

## Errors by source (last hour)
```
index=<index> sourcetype=<type> (error OR ERROR) earliest=-1h
| stats count by source, host | sort -count
```
## Count over time (trend)
```
index=<index> status>=500 earliest=-24h | timechart span=5m count
```
## One service, recent errors
```
index=<index> service="service-a" level=ERROR | table _time, message, host | head 50
```
## Extract a field, then group
```
index=<index> | rex "trace_id=(?<trace_id>\w+)" | stats count by trace_id
```
## Correlate a transaction across sources
```
index=<index> "<TRANSACTION_ID>" earliest=-24h | sort _time
```
Pitfalls: `stats` for counts, `timechart` for trends; field names are case-sensitive; scope time explicitly.
