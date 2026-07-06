---
name: dql-patterns
description: Dynatrace Query Language (DQL) recipes for log analysis — filtering by order/work-order id, counting errors by workload, time-bucketing, and common pitfalls. Use when building a search_dynatrace_dql query.
---

# DQL recipes for POS log analysis

Run these with **search_dynatrace_dql**. Every query starts with `fetch logs`.

## Find everything for an order or work-order id
IDs appear in free-form `content`, not just xxcustom fields — always use contains():
```
fetch logs
| filter contains(content, "<CORRELATION_ID>") or contains(content, "<ENTITY_ID>")
| sort timestamp desc
| limit 200
```

## Which workloads are erroring most (trend / triage)
```
fetch logs
| filter loglevel == "ERROR"
| summarize cnt = count(), by: { k8s.workload.name }
| sort cnt desc
```

## Errors over time (time-bucketed)
```
fetch logs
| filter loglevel == "ERROR" and contains(content, "<term>")
| makeTimeseries count(), interval: 5m
```

## Drill into one workload's recent errors
```
fetch logs
| filter k8s.workload.name == "<workload-name>" and loglevel == "ERROR"
| fields timestamp, content
| sort timestamp desc
| limit 50
```

## Pitfalls
- DQL pre-flight validation runs automatically — if it fails, read the
  `notifications` array, fix the syntax, and retry yourself (don't ask the user).
- Use `==` for equality (not `=`); string values need double quotes.
- `contains()` is case-sensitive — try both the raw id and known variants.
- Keep `limit` reasonable (≤200) so the result fits the model context.
- For "how many", prefer `summarize count()` over fetching rows and counting.
