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


# ─────────────────── Action tools (Operator) ────────────────────────
@mcp.tool()
def create_project(
    name: str,
    stack: str,
    template_type: str = "(Sin tipo específico)",
    niche: str = "",
    provider: str = "codex",
    run_autoskills: bool = True,
    run_uipro: bool = True,
    run_setup: bool = True,
    timeout: int = 420,
) -> dict:
    """Create a new ThemeForge project and prepare it for an AI agent build.

    Creates `~/Proyectos/themes/<slug>/`, writes the AI context file
    (marketplace / Envato requirements), and — when run_setup=True — runs the
    stack scaffold + autoskills (stack + a11y/SEO/design skills) + UI/UX Pro Max
    design system (67 styles / 161 palettes) HEADLESS. It does NOT run the
    agentic build — call run_agent_build() next.

    Args:
      name: human project name (folder slug is derived).
      stack: a key from list_stacks() (e.g. "nextjs-tailwind").
      template_type: marketplace template type, or leave default.
      niche: optional niche/industry injected into the AI context.
      provider: agent the build will target; maps the autoskills/uipro flags.
        One of list_supported_providers() keys; default "codex".
      run_autoskills / run_uipro: keep True to inherit ThemeForge's quality layer.
      run_setup: run scaffold+autoskills+uipro now (True) or just dir+context (False).
      timeout: seconds for the setup step (scaffold/npm can be slow).

    Returns project_path, slug, setup_script, setup_exit and an output tail.
    """
    import os
    import subprocess
    from stacks import STACKS
    import ai_providers as aip
    from themeforge import (
        write_setup_script, PROJECTS_DIR,
        load_projects_meta, save_projects_meta, slugify,
    )

    if stack not in STACKS:
        return {"error": f"unknown stack '{stack}' — call list_stacks() first."}
    if provider not in aip.PROVIDERS:
        return {"error": f"unknown provider '{provider}' — call list_supported_providers()."}

    slug = slugify(name)
    project_dir = PROJECTS_DIR / slug
    if project_dir.exists() and any(project_dir.iterdir()):
        return {"error": f"project dir already exists and is non-empty: {project_dir}"}

    try:
        script = write_setup_script(
            project_dir=project_dir, stack_key=stack, template_type=template_type,
            project_name=name, agent_key=provider, run_autoskills=run_autoskills,
            mode="scratch", reference_kind=None, reference_value=None,
            existing_repo=None, create_github_repo=False, github_user=None,
            embedded=True, run_uipro=run_uipro, niche=(niche or None),
            launch_agent=False,
        )
    except Exception as e:
        return {"error": f"write_setup_script failed: {e}"}

    out = {
        "project_path": str(project_dir), "slug": slug, "stack": stack,
        "provider": provider, "setup_script": str(script),
        "run_autoskills": run_autoskills, "run_uipro": run_uipro,
        "ran_setup": run_setup,
    }
    if run_setup:
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.run(
                ["bash", str(script)], cwd=str(PROJECTS_DIR),
                capture_output=True, text=True, timeout=timeout,
                env={**os.environ},
            )
            out["setup_exit"] = proc.returncode
            out["setup_output_tail"] = (proc.stdout + "\n" + proc.stderr)[-2000:]
        except subprocess.TimeoutExpired:
            out["setup_exit"] = -1
            out["setup_output_tail"] = (
                f"(setup timed out after {timeout}s; it may still be finishing)"
            )
    try:
        meta = load_projects_meta()
        if slug not in meta:
            meta[slug] = {"name": name, "stack": stack}
            save_projects_meta(meta)
    except Exception:
        pass
    out["next"] = (
        "Call run_agent_build(project_path, prompt, provider) to build it, "
        "then run_preflight() to verify and build_zip() to package."
    )
    return out


@mcp.tool()
def run_agent_build(
    project_path: str,
    prompt: str,
    provider: str = "codex",
    timeout: int = 900,
) -> dict:
    """Run an AI agent autonomously (one-shot, non-interactive) inside an
    existing project to build or modify it per `prompt`.

    Uses the same autonomous CLI invocation as the GUI (`codex exec`,
    `claude --print`, `gemini -p`…). The agent edits files in the project
    directory. Pair with run_preflight() to verify, then call again with the
    issues to iterate. Returns the agent output tail + exit code.

    Args:
      project_path: absolute path (from create_project()).
      prompt: what to build/fix (the dev prompt; be specific).
      provider: which agent CLI to drive; default "codex".
      timeout: seconds (full template builds can take many minutes).
    """
    import os
    import shlex
    import subprocess
    import ai_providers as aip
    import platform_compat as _pc

    p = Path(project_path).expanduser().resolve()
    if not p.is_dir():
        return {"error": f"not a directory: {p}"}
    if provider not in aip.PROVIDERS:
        return {"error": f"unknown provider '{provider}'."}
    state, info = aip.detect_status(provider)
    if state != "ok":
        return {"error": f"provider '{provider}' not ready: {info}"}

    argv = aip.oneshot_argv(provider, allow_web=True)
    cmd_str = " ".join(shlex.quote(a) for a in argv)
    env = {**os.environ, **dict(aip.get_env(provider))}
    try:
        proc = subprocess.run(
            _pc.shell_argv(cmd_str), input=prompt, cwd=str(p),
            capture_output=True, text=True, timeout=timeout, env=env,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"agent build timed out ({timeout}s)",
                "timed_out": True, "project_path": str(p)}
    except Exception as e:
        return {"error": f"agent run failed: {e}"}
    return {
        "project_path": str(p), "provider": provider,
        "exit_code": proc.returncode,
        "output_tail": (proc.stdout or "")[-3000:],
        "stderr_tail": (proc.stderr or "")[-500:],
    }


# ─────────────────── Entry point ────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
