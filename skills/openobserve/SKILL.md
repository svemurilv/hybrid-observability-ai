---
name: openobserve
description: OpenObserve recipes — SQL over log/metric streams, filtering, aggregation, histogram, full-text match. Use when querying OpenObserve. Trigger — "openobserve", "stream", "match_all".
---
# OpenObserve recipes (SQL over streams)
## Errors by service (last hour)
```
SELECT service, count(*) AS cnt FROM "<stream>" WHERE level='ERROR' GROUP BY service ORDER BY cnt DESC
```
## Filter to a service
```
SELECT _timestamp, message, host FROM "<stream>" WHERE service='service-a' AND level='ERROR' ORDER BY _timestamp DESC LIMIT 50
```
## Count over time (histogram)
```
SELECT histogram(_timestamp, '5 minute') AS ts, count(*) FROM "<stream>" WHERE code>=500 GROUP BY ts
```
## Correlate a transaction (full-text)
```
SELECT * FROM "<stream>" WHERE match_all('<TRANSACTION_ID>') ORDER BY _timestamp
```
Pitfalls: streams are the tables; timestamp field is `_timestamp`; full-text via `match_all()`; set the time range via API/UI.
