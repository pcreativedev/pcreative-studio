#!/usr/bin/env python3
"""ThemeForge MCP server (stdio transport).

Exposes ThemeForge's core actions as Model Context Protocol tools so
AI clients (Claude Code, Cursor, Windsurf, OpenCode, etc.) can invoke
them directly from their own conversation — no need to open the
ThemeForge GUI.

Phase 1 tools (read-mostly + safe writes):

  - list_stacks()        — 60+ scaffold targets (Next.js, Astro,
                            Laravel, WordPress, Flutter, …)
  - list_themes()        — 8 builtin app themes
  - list_recent_projects() — read ~/.config/themeforge/projects-meta.json
  - list_supported_providers() — 7 AI providers + their auth status
  - estimate_cost()      — USD cost for (model, in_tokens, out_tokens)
  - suggest_stack()      — natural language → recommended stack
  - run_preflight()      — ThemeForest readiness checks on a path
  - build_zip()          — package a project for marketplace upload

Run it:

    python3 ~/Proyectos/themeforge/mcp_server.py     # stdio mode

Register in Claude Code's mcp.json:

    {
      "mcpServers": {
        "themeforge": {
          "command": "python3",
          "args": ["/home/<you>/Proyectos/themeforge/mcp_server.py"]
        }
      }
    }

The same JSON shape works for Cursor's `~/.cursor/mcp.json`, Windsurf's
config, and most other MCP clients (see docs/MCP-SETUP.md).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Make ThemeForge's modules importable when this script is launched from
# a foreign cwd (e.g. Claude Code's project dir).
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP(
    "themeforge",
    instructions=(
        "ThemeForge is a desktop GUI for scaffolding marketplace-ready "
        "template projects (ThemeForest / CodeCanyon / Gumroad / "
        "Creative Market) driven by AI agents. These tools expose its "
        "core actions: list available stacks/themes/providers, suggest "
        "a stack from a natural-language description, estimate cost, "
        "run pre-flight checks, and package projects for marketplace "
        "upload. For full GUI-only features (preview, live editor, "
        "multi-agent compare) point the user at the desktop app."
    ),
)


# ─────────────────── Read tools ─────────────────────────────────────
@mcp.tool()
def list_stacks() -> list[dict]:
    """List every project stack ThemeForge can scaffold.

    Returns a list of dicts with: key, name, category, language,
    min_version. The `key` is what `scaffold_project()` accepts.
    Filters out the placeholder `none` stack.
    """
    from stacks import STACKS
    return [
        {
            "key": k,
            "name": s.get("name", k),
            "category": s.get("category", ""),
            "language": s.get("language", ""),
            "min_version": s.get("min_version", ""),
            "notes": s.get("notes", "")[:200],
        }
        for k, s in STACKS.items()
        if k != "none"
    ]


@mcp.tool()
def list_themes() -> list[dict]:
    """List app themes that ThemeForge can apply to its own UI.

    Themes are JSON token files. Builtin themes ship with the install;
    user themes live in `~/.config/themeforge/themes/`. Both are
    returned; `is_user=true` marks user-installed entries.
    """
    import themes
    return [
        {
            "name": t.name,
            "display_name": t.display_name,
            "author": t.author,
            "is_dark": t.is_dark,
            "is_user": t.is_user,
            "description": t.description,
        }
        for t in themes.list_themes()
    ]


@mcp.tool()
def list_recent_projects(limit: int = 10, include_archived: bool = False) -> list[dict]:
    """List projects scaffolded with ThemeForge, sorted by last-modified.

    Reads `~/.config/themeforge/projects-meta.json`. Returns at most
    `limit` entries. Set `include_archived=true` to include items moved
    to `~/Proyectos/themes-archive/`.
    """
    from themeforge import list_projects
    rows = list_projects(archived=False)
    if include_archived:
        rows = list_projects(archived=False) + list_projects(archived=True)
    # Sort by mtime desc; `mtime` is a float epoch
    rows.sort(key=lambda r: r.get("mtime", 0), reverse=True)
    out = []
    for r in rows[:limit]:
        out.append({
            "slug": r.get("slug", ""),
            "name": r.get("name", ""),
            "path": str(r.get("path", "")),
            "stack": r.get("stack", ""),
            "last_modified_iso": r.get("mtime_iso", ""),
            "git_status": r.get("git_status", ""),
            "has_claude_md": bool(r.get("has_claude_md", False)),
        })
    return out


@mcp.tool()
def list_supported_providers() -> list[dict]:
    """Inventory of the 7 AI providers ThemeForge supports.

    Returns auth status per provider so the agent knows which are
    actually usable. Status values:
      - "ok"        — CLI installed + authenticated.
      - "no-cli"    — CLI binary not on PATH.
      - "no-auth"   — CLI installed but no OAuth / API key.
      - "error"     — other.
    """
    import ai_providers as aip
    out = []
    for key, p in aip.PROVIDERS.items():
        state, info = aip.detect_status(key)
        out.append({
            "key": key,
            "name": p.get("name", key),
            "short": p.get("short", key),
            "command": p.get("command", ""),
            "context_file": p.get("context_file", ""),
            "auth_kind": p.get("auth_kind", ""),
            "status": state,
            "info": info,
        })
    return out


@mcp.tool()
def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> dict:
    """Estimate the USD cost of an AI call.

    Uses ThemeForge's `cost_tracker.PRICING` table. If the model isn't
    in the table, returns a conservative default (Opus rates) and
    `pricing_known: false`. Use exact model IDs like
    `claude-opus-4-7`, `gpt-5-codex`, `gemini-2.5-flash`.
    """
    from cost_tracker import cost_for, PRICING
    cost, known = cost_for(
        model, input_tokens, output_tokens,
        cache_creation_tokens, cache_read_tokens,
    )
    return {
        "model": model,
        "cost_usd": round(cost, 6),
        "pricing_known": known,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_tokens": cache_creation_tokens,
        "cache_read_tokens": cache_read_tokens,
        "available_models": sorted(PRICING.keys()),
    }


@mcp.tool()
def suggest_stack(description: str, provider_for_inference: str = "claude") -> dict:
    """Recommend a stack + theme + dev prompt from a natural-language
    description. Calls the active AI provider with a structured prompt
    (same engine the GUI's ✨ Vibe scaffolder uses).

    Args:
      description: what the user wants to build (Spanish or English).
      provider_for_inference: which CLI to use for the suggestion.
        Defaults to "claude". Must be one of the keys returned by
        `list_supported_providers()`.

    Returns the parsed JSON proposal: stack_key / template_type /
    theme_hint / dev_prompt / reasoning. The agent can then call
    `scaffold_project()` with the recommended values.
    """
    import ai_providers as aip
    import subprocess
    import shlex
    from stacks import STACKS, TEMPLATE_TYPES
    import themes as _t
    from vibe_scaffolder import build_vibe_prompt, parse_vibe_response

    builtin_theme_names = [t.name for t in _t.list_themes() if not t.is_user]
    prompt = build_vibe_prompt(
        description, STACKS, TEMPLATE_TYPES, builtin_theme_names,
    )

    state, info = aip.detect_status(provider_for_inference)
    if state != "ok":
        return {
            "error": f"Provider '{provider_for_inference}' not ready: {info}",
            "stack_key": None,
        }

    argv = aip.oneshot_argv(provider_for_inference, allow_web=False)
    cmd_str = " ".join(shlex.quote(a) for a in argv)
    env = dict(aip.get_env(provider_for_inference))

    try:
        import platform_compat as _pc
        proc = subprocess.run(
            _pc.shell_argv(cmd_str),
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
            env={**__import__("os").environ, **env},
        )
    except subprocess.TimeoutExpired:
        return {"error": "agent timeout (60s)", "stack_key": None}
    except Exception as e:
        return {"error": f"agent run failed: {e}", "stack_key": None}

    proposal, parse_err = parse_vibe_response(proc.stdout)
    if not proposal:
        return {
            "error": f"could not parse agent response: {parse_err}",
            "raw_output_tail": proc.stdout[-500:],
            "stack_key": None,
        }
    return {
        "stack_key": proposal.stack_key,
        "template_type": proposal.template_type,
        "theme_hint": proposal.theme_hint,
        "run_autoskills": proposal.run_autoskills,
        "run_uipro": proposal.run_uipro,
        "dev_prompt": proposal.dev_prompt,
        "reasoning": proposal.reasoning,
    }


@mcp.tool()
def run_preflight(project_path: str) -> dict:
    """Run ThemeForge's pre-flight checker on a project directory.

    Returns each check with: id, title, level (pass/warn/fail/info),
    message, hint. The agent can use this to fix issues before the
    user submits to ThemeForest / CodeCanyon / etc.
    """
    from preflight import run_all
    p = Path(project_path).expanduser().resolve()
    if not p.is_dir():
        return {"error": f"Not a directory: {p}"}
    checks = run_all(p)
    return {
        "project_path": str(p),
        "summary": {
            "pass": sum(1 for c in checks if c.level == "pass"),
            "warn": sum(1 for c in checks if c.level == "warn"),
            "fail": sum(1 for c in checks if c.level == "fail"),
            "info": sum(1 for c in checks if c.level == "info"),
        },
        "checks": [
            {
                "id": c.id,
                "title": c.title,
                "level": c.level,
                "message": c.message,
                "hint": c.hint or "",
                "details": c.details[:500] if c.details else "",
            }
            for c in checks
        ],
    }


@mcp.tool()
def build_zip(
    project_path: str,
    include_documentation: bool = True,
    include_screenshots: bool = True,
    include_source: bool = False,
) -> dict:
    """Package a project into a marketplace-ready ZIP.

    Excludes 30+ noise patterns (node_modules, .git, .env, .claude/
    memory, AGENTS.md, MEMORY.md, *.log, .DS_Store, vendor, target,
    etc.). Output: `~/Proyectos/themes-builds/<slug>-<ts>.zip`.

    Args:
      project_path: absolute path to the project directory.
      include_documentation: bundle `documentation/` if it exists.
      include_screenshots: bundle `screenshots/` if it exists.
      include_source: bundle `source/` (PSDs, Figma exports).

    Returns the resulting ZIP path + size, or an error.
    """
    from themeforge import build_marketplace_zip
    p = Path(project_path).expanduser().resolve()
    if not p.is_dir():
        return {"error": f"Not a directory: {p}"}
    ok, msg, out_path = build_marketplace_zip(
        p,
        include_documentation=include_documentation,
        include_screenshots=include_screenshots,
        include_source=include_source,
    )
    return {
        "ok": ok,
        "message": msg,
        "zip_path": str(out_path) if out_path else "",
        "zip_size_bytes": out_path.stat().st_size if (ok and out_path) else 0,
    }


# ─────────────────── Entry point ────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
