"""
Reference helpers for reliable open-weight, multi-LLM agents.

These encode two production-hardening patterns from the whitepaper (§4.5, §5) that
are easy to get wrong with open-weight models. They are model- and framework-agnostic.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# 1) Context-window auto-cap  (whitepaper §4.4 / §5.1)
# ---------------------------------------------------------------------------
# Open-weight models silently truncate prompts that exceed their context window,
# dropping the OLDEST tokens — which include the system prompt. The agent then loops
# calling tools without ever synthesizing an answer ("ran out of tool-use rounds",
# huge input tokens, tiny output). Tie the input budget to the window so config drift
# can never reintroduce this.

_CHARS_PER_TOKEN = 3.2          # conservative for mixed English + JSON tool output
_SAFETY_TOKENS   = 512


def max_input_chars(num_ctx: int, output_tokens: int,
                    chars_per_token: float = _CHARS_PER_TOKEN) -> int:
    """Maximum input characters that fit the model window with room for output."""
    usable_tokens = max(1000, num_ctx - output_tokens - _SAFETY_TOKENS)
    return int(usable_tokens * chars_per_token)


def cap_context_budget(configured_budget_chars: int, num_ctx: int,
                       output_tokens: int) -> int:
    """Clamp a configured character budget so the prompt cannot overflow the window."""
    ceiling = max_input_chars(num_ctx, output_tokens)
    return min(configured_budget_chars, ceiling)


# ---------------------------------------------------------------------------
# 2) Hidden-reasoning-channel handling  (whitepaper §5.2)
# ---------------------------------------------------------------------------
# Some hybrid reasoning models route their output into a separate "thinking" channel
# and leave the visible content empty. Disable thinking for those model families so
# the answer lands in `content` (also faster). Fall back to the thinking text only if
# content is still empty.

def should_disable_thinking(model: str) -> bool:
    """True for model families that hide answers in a thinking channel by default."""
    m = (model or "").lower()
    # Add families as needed; scope narrowly to avoid rejecting models that don't
    # support the flag (e.g. do NOT match coder variants that never "think").
    return m.startswith("qwen3:")           # dense qwen3, not qwen3-coder


def resolve_content(message: dict) -> str:
    """Return message content, falling back to the thinking channel if content is empty."""
    content = (message.get("content") or "").strip()
    if content:
        return content
    thinking = (message.get("thinking") or message.get("reasoning") or "").strip()
    return thinking   # last-resort surface so the user never sees a blank answer
