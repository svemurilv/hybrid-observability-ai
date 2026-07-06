"""
Observability Connector — base contract (reference implementation).

Implementing this ABC for a platform makes its read capabilities available to the
agent WITHOUT changing agent code ("hands-free" onboarding). Transport-neutral: a
connector may be realized as an MCP server, an HTTP/API adapter, or an OTLP source.

See docs/CONNECTOR_SDK.md for the full specification.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ObservabilityConnector(ABC):
    """Uniform read-only adapter for one observability platform.

    A connector is self-describing: `capabilities()` advertises the operations the
    agent may call; each is executed via `call()`. Results are normalized to a
    vendor-neutral, OpenTelemetry-aligned schema so the agent stays platform-agnostic.
    """

    #: stable id used as record `source` and in the registry (e.g. "platform-a")
    id: str
    #: human-facing label for the UI
    label: str

    @abstractmethod
    async def capabilities(self) -> list[dict[str, Any]]:
        """Return capability descriptors. Called at discovery time and cached; re-queried
        on connector reload. This is what makes onboarding hands-free — the agent adds
        these to its tool vocabulary automatically.

        Each descriptor:
            {
              "name": "search_logs",
              "kind": "logs|metrics|entities|problems|traces|rum|custom",
              "description": "…when to use…",
              "parameters": { "type": "object", "properties": {…}, "required": [...] }
            }
        """

    @abstractmethod
    async def call(self, capability: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute one capability. MUST be read-only. Return one of:
            { "records": [ <normalized record>, … ] }   # logs / entities / problems
            { "series":  [ { "labels": {...}, "points": [[ts, val], …], "unit": "…" } ] }
            { "error": "…", "reason": "…" }              # handled failure (never raise)

        Normalized record (superset; omit unknown fields):
            { "timestamp","severity","service","resource","body","attributes",
              "source","trace_id","span_id","raw" }
        """

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return { id, connected, auth_ok, detail, latency_ms } for the status panel."""

    # ---- optional lifecycle ---------------------------------------------------
    async def aclose(self) -> None:  # pragma: no cover
        """Release pooled clients/sessions."""


# ---------------------------------------------------------------------------
# Minimal in-process registry + capability discovery (reference).
# In production, connectors are declared in connectors.yaml and loaded here.
# ---------------------------------------------------------------------------
class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, ObservabilityConnector] = {}
        self._vocab: dict[str, tuple[str, dict]] = {}   # tool_name -> (connector_id, descriptor)

    def register(self, connector: ObservabilityConnector) -> None:
        self._connectors[connector.id] = connector

    async def discover(self) -> dict[str, tuple[str, dict]]:
        """Assemble the agent's tool vocabulary from all connectors' capabilities.
        Tool names are namespaced by connector id, e.g. 'platform-a.search_logs'."""
        self._vocab.clear()
        for cid, c in self._connectors.items():
            try:
                for cap in await c.capabilities():
                    self._vocab[f"{cid}.{cap['name']}"] = (cid, cap)
            except Exception:
                continue  # a missing/unhealthy connector degrades gracefully
        return dict(self._vocab)

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in self._vocab:
            return {"error": f"unknown capability '{tool_name}'"}
        cid, cap = self._vocab[tool_name]
        return await self._connectors[cid].call(cap["name"], args)

    async def health(self) -> list[dict[str, Any]]:
        out = []
        for c in self._connectors.values():
            try:
                out.append(await c.health())
            except Exception as e:
                out.append({"id": c.id, "connected": False, "detail": str(e)})
        return out
