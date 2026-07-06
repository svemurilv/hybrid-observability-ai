"""
skills.py — Agent Skills loader for Ask AI (progressive disclosure).

Loads open-format "Agent Skills" — markdown files with YAML frontmatter
(name / description) + a body of detailed guidance — from a skills/ directory.
Same SKILL.md format as grafana/skills and Dynatrace/dynatrace-for-ai, so those
packs can be dropped in directly.

Design (mirrors Claude Code, and deliberately avoids the prompt-bloat that broke
qwen3): only the lightweight INDEX (name + one-line description) is injected into
the system prompt. The FULL body is pulled on demand via the load_skill tool, so
heavy guidance enters context only for a matching question.

Layout supported:
  skills/<name>/SKILL.md     (open Agent-Skills convention)
  skills/<name>.md           (flat fallback)
"""
from __future__ import annotations

import os
import re
import pathlib
import logging

log = logging.getLogger("skills")

SKILLS_DIR = os.getenv("SKILLS_DIR", "skills")
SKILLS_ENABLED = os.getenv("SKILLS_ENABLED", "1") == "1"
_MAX_BODY_CHARS = int(os.getenv("SKILL_MAX_BODY_CHARS", "20000"))  # cap one skill body


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split `---\\nkey: value\\n---\\nbody` into ({frontmatter}, body).

    Handles inline values AND YAML block scalars (`>`, `>-`, `|`, `|-`) — the
    real grafana/skills + dynatrace-for-ai packs use folded multi-line
    descriptions, which a naive line-splitter mangles (and would mis-read an
    indented `Trigger:` line as a top-level key).
    """
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    fm: dict[str, str] = {}
    lines = fm_raw.split("\n")
    i = 0
    while i < len(lines):
        mk = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", lines[i])  # top-level key only
        if not mk:
            i += 1
            continue
        key, val = mk.group(1), mk.group(2).strip()
        if val in (">", ">-", ">+", "|", "|-", "|+"):
            folded = val[0] == ">"
            i += 1
            buf: list[str] = []
            while i < len(lines):
                cont = lines[i]
                if cont.strip() == "":
                    buf.append("")
                    i += 1
                elif re.match(r"^\s+", cont):          # indented → part of block
                    buf.append(cont.strip())
                    i += 1
                else:                                   # dedented → next key
                    break
            joined = " ".join(buf) if folded else "\n".join(buf)
            fm[key] = re.sub(r"\s+", " ", joined).strip()
        else:
            fm[key] = val.strip().strip("\"'")
            i += 1
    return fm, body


def _discover() -> dict[str, dict]:
    base = pathlib.Path(SKILLS_DIR)
    out: dict[str, dict] = {}
    if not base.exists():
        return out
    paths = sorted(base.glob("*/SKILL.md")) + sorted(base.glob("*.md"))
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:
            log.warning(f"[skills] could not read {p}: {e}")
            continue
        fm, body = _parse_frontmatter(text)
        name = (fm.get("name")
                or (p.parent.name if p.name.lower() == "skill.md" else p.stem)).strip()
        if not name:
            continue
        out[name] = {
            "name": name,
            "description": (fm.get("description") or "").strip(),
            "body": body.strip()[:_MAX_BODY_CHARS],
            "path": str(p),
        }
    return out


_cache: dict[str, dict] | None = None


def all_skills(force: bool = False) -> dict[str, dict]:
    global _cache
    if not SKILLS_ENABLED:
        return {}
    if _cache is None or force:
        _cache = _discover()
        if _cache:
            log.info(f"[skills] loaded {len(_cache)} skill(s): {', '.join(_cache)}")
    return _cache


def index_text() -> str:
    """One line per skill — cheap to inject into the system prompt."""
    sk = all_skills()
    if not sk:
        return ""
    return "\n".join(f"- {s['name']}: {s['description']}" for s in sk.values())


def get_body(name: str) -> str | None:
    """Full guidance body for one skill (loaded on demand by the load_skill tool)."""
    s = all_skills().get((name or "").strip())
    return s["body"] if s else None
