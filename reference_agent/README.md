# Reference agent patterns

This directory contains the **generalizable, model-agnostic patterns** from the paper —
not a full agent runtime. They are the parts most people re-implement incorrectly when
running open-weight, multi-LLM agents in production.

## Files
- **`skills.py`** — the progressive-disclosure **Agent Skills** loader (§4.4). Parses
  open-format `SKILL.md` packs; injects only a compact *index* into the system prompt and
  loads full guidance on demand via a `load_skill` tool. This avoids the prompt-bloat that
  degrades smaller open-weight models.
- **`context.py`** — two hardening helpers:
  - `cap_context_budget()` — ties the input budget to the model window so a prompt can't
    silently overflow and drop the system prompt (§4.4 / §5.1).
  - `should_disable_thinking()` / `resolve_content()` — handle hybrid reasoning models
    that hide the answer in a "thinking" channel and return empty content (§5.2).

## Wiring them into an agent (sketch)
```python
from reference_agent import skills
from reference_agent.context import cap_context_budget, should_disable_thinking, resolve_content

# 1) lean system prompt + on-demand skills
system = BASE_PROMPT
idx = skills.index_text()
if idx:
    system += "\n\nAVAILABLE SKILLS — call load_skill(name) when a question matches:\n" + idx

# 2) never overflow the window
budget = cap_context_budget(configured_budget_chars=48000, num_ctx=32768, output_tokens=3000)

# 3) per-call, for reasoning models that hide output
body = {"model": model, "messages": messages, "stream": False}
if should_disable_thinking(model):
    body["think"] = False
# … after the call …
answer = resolve_content(response["message"])
```

## Not included (intentionally)
The full agent loop, tool registry, caching ladder, and UI are part of a specific
deployment and are omitted here. Build your loop around the **Connector SDK**
(`docs/CONNECTOR_SDK.md`) and these patterns.
