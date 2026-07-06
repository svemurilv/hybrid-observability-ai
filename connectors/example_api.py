"""
Example API-adapter connector — a minimal, runnable illustration of the contract.

Replace the body of `call()` with a real read-only request to your platform's query
API, and normalize the response to the schema in base.py. This file is intentionally
generic and has no dependency on any specific vendor.
"""
from __future__ import annotations

from typing import Any

from .base import ObservabilityConnector


class ExampleMetricsConnector(ObservabilityConnector):
    id = "example-metrics"
    label = "Example metrics platform"

    def __init__(self, base_url: str, token: str):
        self._base, self._tok = base_url, token

    async def capabilities(self) -> list[dict[str, Any]]:
        return [{
            "name": "query_metric",
            "kind": "metrics",
            "description": ("Query a metric by name/labels over a time range on the "
                           "example metrics platform. Returns a normalized series."),
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string"},
                    "labels": {"type": "object"},
                    "hours":  {"type": "integer", "default": 1},
                },
                "required": ["metric"],
            },
        }]

    async def call(self, capability: str, args: dict[str, Any]) -> dict[str, Any]:
        if capability != "query_metric":
            return {"error": f"unknown capability {capability}"}
        # --- replace with a real read-only request to your platform ---------------
        #   resp = await http_get(self._base + "/query", params=…, auth=self._tok)
        #   points = normalize(resp)
        # Returned here is a stub so the file runs as an example.
        return {
            "series": [{
                "labels": args.get("labels", {}) | {"metric": args["metric"]},
                "points": [[1782164100000, 0.0]],   # [epoch_ms, value]
                "unit": "count",
            }],
            "source": self.id,
        }

    async def health(self) -> dict[str, Any]:
        return {"id": self.id, "connected": True, "auth_ok": bool(self._tok), "detail": "ok"}
