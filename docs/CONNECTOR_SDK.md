# Observability Connector SDK — Specification (v0.1)

This document specifies the **Observability Connector** contract that makes Hybrid
Observability AI platform-agnostic. Implementing this contract for a new platform is
sufficient to make its read capabilities available to the agent **without changing
agent code** ("hands-free" onboarding). The spec is transport-neutral: a connector may
be realized as an **MCP server**, an **HTTP/API adapter**, or an **OTLP source**.

---

## 1. Design goals

- **Self-describing.** A connector advertises its capabilities (tool schemas) at runtime;
  the agent assembles its usable vocabulary from all registered connectors.
- **Read-only.** Connectors expose read operations only; no write path to any platform.
- **Normalized.** Every returned record is mapped to a vendor-neutral, OpenTelemetry-aligned
  schema so results correlate across platforms.
- **Governed.** Capabilities are the *only* surface the agent can invoke; credentials live in
  the connector, never in agent code or prompts.
- **Optional.** A missing/unhealthy connector degrades gracefully; the framework never hard-fails.

---

## 2. Core types

### 2.1 Normalized record (the cross-connector schema)

All connectors normalize their native records to this shape (superset; unknown fields omitted):

```jsonc
{
  "timestamp":   "2026-07-03T15:24:10.104Z", // RFC3339, UTC
  "severity":    "ERROR",                      // DEBUG|INFO|WARN|ERROR|unknown
  "service":     "order-service",              // logical service/workload
  "resource":    { "k8s.cluster": "...", "k8s.namespace": "...", "host": "..." },
  "body":        "…free-form message / content…",
  "attributes":  { "http.method": "PUT", "http.status": 201, "…": "…" },
  "source":      "connector-id",               // which connector produced it
  "trace_id":    "…", "span_id": "…",          // when available
  "raw":         { "…": "…" }                    // optional: original record (truncated)
}
```

For **metric** results, connectors return series:

```jsonc
{ "series": [ { "labels": {"…":"…"}, "points": [[ts, value], …], "unit": "…" } ],
  "source": "connector-id" }
```

### 2.2 Capability descriptor (self-description)

Each capability is a named, JSON-Schema-typed operation the agent may call:

```jsonc
{
  "name": "search_logs",
  "description": "Search logs on <platform>; use for … Returns normalized records.",
  "kind": "logs|metrics|entities|problems|traces|rum|custom",
  "parameters": { "type": "object", "properties": { /* JSON Schema */ }, "required": ["query"] }
}
```

### 2.3 Health

```jsonc
{ "id": "connector-id", "connected": true, "auth_ok": true, "detail": "…", "latency_ms": 42 }
```

---

## 3. Connector interface (Python reference ABC)

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class ObservabilityConnector(ABC):
    """Uniform read-only adapter for one observability platform.

    A connector is self-describing: capabilities() advertises the operations the
    agent may call; each is executed via call(). Results are normalized so the
    agent stays platform-agnostic.
    """

    #: stable id used as record `source` and in the registry
    id: str
    #: human label for the UI
    label: str

    @abstractmethod
    async def capabilities(self) -> list[dict[str, Any]]:
        """Return the capability descriptors (§2.2). Called at discovery time and
        cached; re-queried on connector reload. This is what makes onboarding
        hands-free — the agent adds these to its tool vocabulary automatically."""

    @abstractmethod
    async def call(self, capability: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute one capability. MUST be read-only. Return either:
           { "records": [ <normalized record §2.1>, … ] }  (logs/entities/problems)
           or { "series": [ … ] }                            (metrics)
           or { "error": "…", "reason": "…" }                (handled failure).
        Implementations normalize native records and truncate `raw` to a bound."""

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return the health descriptor (§2.3) for the system status panel."""

    # ---- optional lifecycle ------------------------------------------------
    async def aclose(self) -> None:  # pragma: no cover
        """Release pooled clients/sessions."""
```

### 3.1 Transport realizations

| Transport | `capabilities()` source | `call()` mechanism | Effort |
|---|---|---|---|
| **MCP connector** | `tools/list` over MCP (automatic) | `tools/call` | lowest — zero platform code |
| **API adapter** | declared in the connector | platform REST/query API | low — thin wrapper + schema |
| **OTLP source** | fixed capability set (query normalized store) | query the ingested OTel store | medium — needs an ingest sink |

An **MCP connector** can wrap a vendor's published MCP server directly; capabilities are
discovered from the protocol, so a new platform needs no adapter code at all.

---

## 4. Registry & discovery

Connectors are declared in configuration (not code):

```yaml
# connectors.yaml
connectors:
  - id: platform-a
    label: "APM / traces+logs"
    transport: mcp
    url: "http://mcp-platform-a:PORT/mcp"
    headers: { Host: localhost }          # transport hardening if needed
  - id: platform-b
    label: "Logs + Metrics + Cloud infra"
    transport: mcp
    url: "http://mcp-platform-b:PORT/sse"
  - id: platform-c
    label: "In-house metrics"
    transport: api
    module: "connectors.inhouse:InHouseConnector"
```

At startup (and on reload) the framework:
1. Instantiates each connector.
2. Calls `capabilities()` and merges the descriptors into the agent's tool vocabulary,
   namespaced by connector id (`platform-a.search_logs`).
3. Polls `health()` for the status panel.

**No agent redeploy is required to gain a connector's capabilities** — only a registry
entry and a reachable endpoint.

---

## 5. Example: a minimal API-adapter connector

```python
class InHouseConnector(ObservabilityConnector):
    id = "inhouse"; label = "In-house metrics"

    def __init__(self, base_url: str, token: str):
        self._base, self._tok = base_url, token

    async def capabilities(self):
        return [{
            "name": "query_metric",
            "kind": "metrics",
            "description": "Query an in-house metric by name/labels over a time range.",
            "parameters": {"type": "object",
                "properties": {"metric": {"type": "string"},
                               "labels": {"type": "object"},
                               "hours": {"type": "integer", "default": 1}},
                "required": ["metric"]},
        }]

    async def call(self, capability, args):
        if capability != "query_metric":
            return {"error": f"unknown capability {capability}"}
        # ... issue read-only request, then normalize to §2.1 series ...
        return {"series": [{"labels": args.get("labels", {}),
                            "points": [[1782164100000, 42.0]], "unit": "count"}],
                "source": self.id}

    async def health(self):
        return {"id": self.id, "connected": True, "auth_ok": True, "detail": "ok"}
```

---

## 6. Portable skill packs (domain knowledge, no code)

A connector may ship an optional **skill pack** — open-format `SKILL.md` documents with
query recipes and platform-specific tips. These are loaded on demand (progressive
disclosure) and require no code. Example frontmatter:

```markdown
---
name: platform-a-queries
description: Query recipes for <platform-a> — filtering by entity id, error triage,
             time-bucketing. Use when building a platform-a query.
---
# Recipes …
```

---

## 7. Conformance checklist

A connector is conformant if it:
- [ ] returns valid capability descriptors from `capabilities()` (JSON-Schema params);
- [ ] performs **only read** operations in `call()`;
- [ ] normalizes records to §2.1 (or series) and bounds `raw`;
- [ ] returns `{error, reason}` (never raises) on handled failures;
- [ ] reports `health()`; and
- [ ] keeps all credentials inside the connector (never surfaced to the agent/prompt).

---

## 8. Certified reference connectors (planned)

Reference connectors for common platform classes (APM/traces, log-analytics, metrics,
cloud-provider monitoring) ship as examples of the contract. Named platforms are
**illustrations of the SDK, not the framework's identity**.
