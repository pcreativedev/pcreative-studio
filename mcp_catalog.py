"""Curated catalog of community MCP servers that ThemeForge can
auto-configure for scaffolded projects.

These are NOT distributed with ThemeForge. We only generate a
`.mcp.json` in the project root pointing at the right packages /
binaries. The user's AI client (Claude Code, Cursor, Windsurf)
launches each MCP on demand via `npx`, `uvx`, or `go run`, the same
way it would for any other MCP.

License: every entry below has its upstream license documented and
verified at curation time (see NOTICE.md). All entries are MIT or
Apache-2.0, both fully compatible with ThemeForge's GPL v3 since we
never bundle their source — we only generate a config file that the
client uses to spawn them at runtime.

Adding a new MCP to the catalog:

  1. Verify its license (must be permissive: MIT / Apache-2.0 / BSD /
     ISC / similar).
  2. Add a `MCPEntry` below with the canonical install command (npx
     for Node, uvx for Python, go install for Go, etc.).
  3. Tag `relevance` carefully — over-broad tagging spams projects
     with MCPs they don't need.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ─────────────────── Data shape ─────────────────────────────────────
@dataclass
class MCPEntry:
    key: str                     # short id used as the mcpServers key
    name: str                    # display label
    license: str                 # SPDX id: MIT / Apache-2.0 / etc
    repo: str                    # canonical URL (link in NOTICE)
    description: str             # 1-line what does it
    relevance: list[str]         # tags: any|web-frontend|wordpress|shopify|backend|design|database|mobile
    install: dict                # the mcp.json server spec (command + args + env)
    env_hint: str = ""           # one-line note about env vars / setup required
    requires_auth: bool = False  # true if user needs to provide a token


# ─────────────────── The catalog ────────────────────────────────────
CATALOG: list[MCPEntry] = [

    # ── Universal ──────────────────────────────────────────────────
    MCPEntry(
        key="filesystem",
        name="Filesystem (modelcontextprotocol)",
        license="MIT",
        repo="https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
        description="Sandboxed filesystem access scoped to the project directory.",
        relevance=["any"],
        install={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "__PROJECT_PATH__"],
        },
    ),
    MCPEntry(
        key="fetch",
        name="Fetch (modelcontextprotocol)",
        license="MIT",
        repo="https://github.com/modelcontextprotocol/servers-archived/tree/main/src/fetch",
        description="Web content fetching with HTML→markdown conversion.",
        relevance=["any"],
        install={
            "command": "uvx",
            "args": ["mcp-server-fetch"],
        },
    ),
    MCPEntry(
        key="memory",
        name="Memory (modelcontextprotocol)",
        license="MIT",
        repo="https://github.com/modelcontextprotocol/servers-archived/tree/main/src/memory",
        description="Knowledge-graph persistent memory across agent sessions.",
        relevance=["any"],
        install={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
        },
    ),
    MCPEntry(
        key="github",
        name="GitHub (official)",
        license="MIT",
        repo="https://github.com/github/github-mcp-server",
        description="Repo / issues / PRs / Actions / search across your GitHub account.",
        relevance=["any"],
        install={
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                "ghcr.io/github/github-mcp-server",
            ],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GH_TOKEN}"},
        },
        env_hint=(
            "Requires GH_TOKEN env var with a fine-grained PAT scoped "
            "to the relevant repos. See `gh auth token` for the token "
            "of your active CLI session."
        ),
        requires_auth=True,
    ),

    # ── Web frontend (browser testing + debug) ──────────────────────
    MCPEntry(
        key="playwright",
        name="Playwright (Microsoft, official)",
        license="Apache-2.0",
        repo="https://github.com/microsoft/playwright-mcp",
        description=(
            "Drives a Chromium browser via Playwright. Test rendered "
            "themes, capture screenshots, run a11y audits, scrape "
            "competitor sites for layout reference."
        ),
        relevance=["web-frontend", "wordpress", "shopify"],
        install={
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"],
        },
    ),
    MCPEntry(
        key="chrome-devtools",
        name="Chrome DevTools (Google, official)",
        license="Apache-2.0",
        repo="https://github.com/ChromeDevTools/chrome-devtools-mcp",
        description=(
            "Connect the AI agent to a live Chrome instance for "
            "in-browser debugging: console, network, performance, "
            "accessibility tree, computed styles."
        ),
        relevance=["web-frontend", "wordpress", "shopify"],
        install={
            "command": "npx",
            "args": ["-y", "chrome-devtools-mcp@latest"],
        },
    ),

    # ── Design / Figma ──────────────────────────────────────────────
    MCPEntry(
        key="figma-context",
        name="Figma Context (GLips)",
        license="MIT",
        repo="https://github.com/GLips/Figma-Context-MCP",
        description=(
            "Read access to Figma files: extract layout, tokens, "
            "components. Lets the agent see the source design before "
            "writing CSS / Tailwind."
        ),
        relevance=["web-frontend", "design"],
        install={
            "command": "npx",
            # `--stdio` = habla MCP por stdio (sin él arranca un server HTTP y el
            # cliente no conecta). La key va SOLO por env (pasarla como arg CLI la
            # filtra en la lista de procesos / el historial del shell).
            "args": ["-y", "figma-developer-mcp", "--stdio"],
            "env": {"FIGMA_API_KEY": "${FIGMA_API_KEY}"},
        },
        env_hint=(
            "Requires FIGMA_API_KEY env var with a Figma personal access "
            "token. Get one at figma.com → Settings → Security → Personal "
            "access tokens (scope: read file content). Then paste a Figma "
            "frame/layer link (right-click → Copy link to selection) and "
            "ask the agent to implement it."
        ),
        requires_auth=True,
    ),

    # ── E-commerce ──────────────────────────────────────────────────
    MCPEntry(
        key="shopify-dev",
        name="Shopify Dev (official)",
        license="MIT (per Shopify open-source standard)",
        repo="https://github.com/Shopify/dev-mcp",
        description=(
            "Shopify's official Dev MCP — admin/storefront/checkout "
            "API docs, code completion for Liquid templates, theme "
            "validation."
        ),
        relevance=["shopify"],
        install={
            "command": "npx",
            "args": ["-y", "@shopify/dev-mcp"],
        },
    ),

    # ── Databases ───────────────────────────────────────────────────
    MCPEntry(
        key="postgres",
        name="Postgres (crystaldba)",
        license="MIT",
        repo="https://github.com/crystaldba/postgres-mcp",
        description=(
            "Full-featured Postgres MCP: schema inspection, query, "
            "EXPLAIN analysis, health checks, index suggestions. "
            "Useful for themes that ship demo data."
        ),
        relevance=["database", "backend"],
        install={
            "command": "uvx",
            "args": ["postgres-mcp", "--access-mode", "restricted"],
            "env": {"DATABASE_URI": "${DATABASE_URL}"},
        },
        env_hint=(
            "Requires DATABASE_URL env var. ThemeForge's Postgres "
            "toggle (Extras tab) injects this automatically."
        ),
        requires_auth=False,
    ),

    # ── Optional / advanced ─────────────────────────────────────────
    MCPEntry(
        key="browsermcp",
        name="Browser MCP (browsermcp.io)",
        license="Apache-2.0",
        repo="https://github.com/browsermcp/mcp",
        description=(
            "Automate the user's local Chrome via a browser extension "
            "bridge. Alternative to Playwright when you want the "
            "user's logged-in session."
        ),
        relevance=["web-frontend"],
        install={
            "command": "npx",
            "args": ["-y", "@browsermcp/mcp@latest"],
        },
    ),
    MCPEntry(
        key="themeforge",
        name="ThemeForge (this repo)",
        license="GPL-3.0",
        repo="https://github.com/pcreativedev/themeforge",
        description=(
            "ThemeForge's own MCP server: list_stacks, list_themes, "
            "estimate_cost, run_preflight, build_zip, suggest_stack, "
            "list_recent_projects, list_supported_providers."
        ),
        relevance=["any"],
        install={
            "command": "python3",
            "args": ["__THEMEFORGE_HOME__/mcp_server.py"],
        },
    ),
]


# ─────────────────── Recommendation engine ──────────────────────────
def recommend_for_stack(stack_key: str, stack_meta: dict | None = None) -> list[MCPEntry]:
    """Picks the curated MCPs whose `relevance` tags match this stack.

    Scoring:
    - "any" is always included.
    - Stack category determines other tags:
        Web · Frontend / Static / Full-stack  → web-frontend
        CMS · WordPress                       → wordpress + web-frontend
        CMS · Shopify                         → shopify + web-frontend
        Backend · API                          → backend
        Móvil · *                              → mobile
        E-commerce                             → web-frontend (+ shopify if hints in name)
    Themes / portfolio / agency get web-frontend only.
    """
    category = (stack_meta or {}).get("category", "").lower()
    tags: set[str] = {"any"}

    if "web" in category or "static" in category or "frontend" in category or "full-stack" in category:
        tags.add("web-frontend")
        tags.add("design")
    if "wordpress" in category:
        tags.update({"wordpress", "web-frontend", "design"})
    if "shopify" in category:
        tags.update({"shopify", "web-frontend", "design"})
    if "ecommerce" in category or "e-commerce" in category:
        tags.add("web-frontend")
    if "backend" in category or "api" in category:
        tags.add("backend")
    if "móvil" in category or "movil" in category or "mobile" in category:
        tags.add("mobile")
    if "game" in category or "videojuego" in category:
        tags.add("web-frontend")  # most game stacks are web-based

    return [e for e in CATALOG if any(t in tags for t in e.relevance)]


def list_all() -> list[MCPEntry]:
    """Returns the full catalog."""
    return list(CATALOG)


def by_key(key: str) -> MCPEntry | None:
    return next((e for e in CATALOG if e.key == key), None)


# ─────────────────── .mcp.json generation ───────────────────────────
def generate_mcp_json(
    entries: list[MCPEntry],
    project_path: Path,
    themeforge_home: Path | None = None,
) -> dict:
    """Builds the `.mcp.json` file content for a scaffolded project.

    The `__PROJECT_PATH__` placeholder in any entry's install args is
    replaced with the absolute project path. `__THEMEFORGE_HOME__` is
    replaced with the location of THIS repo (so the ThemeForge MCP
    server entry points at the right `mcp_server.py`).
    """
    project_str = str(Path(project_path).resolve())
    tf_home_str = str(Path(themeforge_home or Path(__file__).parent).resolve())

    def _substitute(value):
        if isinstance(value, str):
            return value.replace("__PROJECT_PATH__", project_str).replace(
                "__THEMEFORGE_HOME__", tf_home_str
            )
        if isinstance(value, list):
            return [_substitute(v) for v in value]
        if isinstance(value, dict):
            return {k: _substitute(v) for k, v in value.items()}
        return value

    servers = {}
    for e in entries:
        servers[e.key] = _substitute(e.install)
    return {"mcpServers": servers}


def write_mcp_json(
    project_path: Path,
    entries: list[MCPEntry],
    themeforge_home: Path | None = None,
) -> Path:
    """Writes `.mcp.json` to project_path. Returns the file path."""
    project_path = Path(project_path).resolve()
    project_path.mkdir(parents=True, exist_ok=True)
    target = project_path / ".mcp.json"
    payload = generate_mcp_json(entries, project_path, themeforge_home)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def entries_summary(entries: list[MCPEntry]) -> str:
    """Human-readable one-liner per entry — useful for previews and CLI."""
    return "\n".join(
        f"  · {e.key:18s} ({e.license:12s}) — {e.description[:60]}"
        for e in entries
    )
