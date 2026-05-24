"""Demo deploy module — deploys a built project to a static host
(Netlify / Vercel / Cloudflare Pages / Surge.sh) so the author can
share a public preview URL with potential buyers, clients or
reviewers.

This module is pure logic — detection, CLI checks, URL extraction.
The actual deployment is driven from `project_window._deploy_demo`
which uses QProcess for live streaming to the logs panel.

Supported targets:
- **Netlify** — `netlify deploy --prod --dir <dist>`
- **Vercel** — `vercel --prod --yes` (vercel CLI inspects the repo)
- **Cloudflare Pages** — `npx wrangler pages deploy <dist>`
- **Surge.sh** — `surge <dist>` (no project setup needed, anon-ish)
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


PROVIDERS = ("netlify", "vercel", "cloudflare", "surge")


@dataclass
class BuildConfig:
    has_package_json: bool
    build_cmd: str
    dist_dir: str
    stack_hint: str
    notes: str = ""


def detect_build_config(project_path: Path) -> BuildConfig:
    """Best-effort detection of build command + dist dir from
    package.json + presence of common files. Returns sensible
    defaults for unknown stacks so the user can override in the UI."""
    pkg_path = project_path / "package.json"
    if not pkg_path.is_file():
        if (project_path / "index.html").is_file():
            return BuildConfig(False, "", ".", "static",
                               "Plain HTML site — no build step needed.")
        if (project_path / "hugo.toml").is_file() or (project_path / "config.toml").is_file():
            return BuildConfig(False, "hugo --minify", "public", "hugo")
        if (project_path / "_config.yml").is_file():
            return BuildConfig(False, "bundle exec jekyll build", "_site", "jekyll")
        return BuildConfig(False, "", ".", "unknown",
                           "No package.json found — assuming the project root is "
                           "the deploy directory.")
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except Exception as e:
        return BuildConfig(True, "npm run build", "dist", "unknown",
                           f"Failed to parse package.json: {e}")

    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    scripts = pkg.get("scripts", {})

    # next.js — needs `output: 'export'` for static hosts
    if "next" in deps:
        # Heuristic: check next.config.* for export
        config_paths = [
            project_path / f"next.config.{ext}"
            for ext in ("js", "mjs", "ts", "cjs")
        ]
        next_cfg = next((p for p in config_paths if p.is_file()), None)
        has_export = False
        if next_cfg:
            try:
                cfg_text = next_cfg.read_text(encoding="utf-8")
                if re.search(r"output\s*:\s*['\"]export['\"]", cfg_text):
                    has_export = True
            except Exception:
                pass
        return BuildConfig(
            True,
            "npm run build" if "build" in scripts else "next build",
            "out" if has_export else ".next",
            "nextjs",
            notes=("" if has_export else
                   "Next.js without `output: 'export'`: only Vercel will deploy "
                   "without an explicit static export. For Netlify/CF Pages add "
                   "`output: 'export'` to next.config and re-run."),
        )

    if "astro" in deps:
        return BuildConfig(True, "npm run build", "dist", "astro")
    if "vite" in deps:
        return BuildConfig(True, "npm run build", "dist", "vite")
    if "@sveltejs/kit" in deps:
        has_static = "@sveltejs/adapter-static" in deps
        return BuildConfig(
            True,
            "npm run build",
            "build" if has_static else ".svelte-kit",
            "sveltekit",
            notes=("" if has_static else
                   "SvelteKit without adapter-static — needs Node runtime, "
                   "static hosts won't work. Install @sveltejs/adapter-static "
                   "and re-build."),
        )
    if "gatsby" in deps:
        return BuildConfig(True, "npm run build", "public", "gatsby")
    if "react-scripts" in deps:
        return BuildConfig(True, "npm run build", "build", "cra")
    if "@angular/core" in deps:
        return BuildConfig(True, "npm run build", "dist", "angular",
                           "Angular: dist dir often `dist/<project-name>`. "
                           "Verify in angular.json.")
    if "nuxt" in deps:
        return BuildConfig(True, "npm run generate", ".output/public", "nuxt",
                           "Nuxt: use `nuxt generate` for static; for SSR you "
                           "need a Node host (not supported by this deploy).")

    build = "npm run build" if "build" in scripts else ""
    return BuildConfig(True, build, "dist", "unknown",
                       "Unknown stack — verify the build command and dist dir.")


@dataclass
class ProviderInfo:
    key: str
    name: str
    cli: str
    install_cmd: str
    auth_check_cmd: list[str]
    deploy_cmd: list[str]
    url_regex: re.Pattern
    supports_no_build_dir: bool = False  # vercel inspects repo, ignores dist


def provider_info(key: str) -> ProviderInfo:
    if key == "netlify":
        return ProviderInfo(
            key=key,
            name="Netlify",
            cli="netlify",
            install_cmd="npm i -g netlify-cli",
            auth_check_cmd=["netlify", "status"],
            deploy_cmd=["netlify", "deploy", "--prod", "--dir", "{dist}"],
            url_regex=re.compile(
                r"(?:Website URL|Live URL|Website Draft URL):\s+(https://[^\s]+)"
            ),
        )
    if key == "vercel":
        return ProviderInfo(
            key=key,
            name="Vercel",
            cli="vercel",
            install_cmd="npm i -g vercel",
            auth_check_cmd=["vercel", "whoami"],
            deploy_cmd=["vercel", "--prod", "--yes"],
            url_regex=re.compile(r"(https://[a-z0-9\-]+\.vercel\.app)"),
            supports_no_build_dir=True,
        )
    if key == "cloudflare":
        return ProviderInfo(
            key=key,
            name="Cloudflare Pages",
            cli="npx",
            install_cmd="(none — uses npx wrangler)",
            auth_check_cmd=["npx", "-y", "wrangler", "whoami"],
            deploy_cmd=["npx", "-y", "wrangler", "pages", "deploy", "{dist}"],
            url_regex=re.compile(r"(https://[a-z0-9\-]+\.pages\.dev)"),
        )
    if key == "surge":
        return ProviderInfo(
            key=key,
            name="Surge.sh",
            cli="surge",
            install_cmd="npm i -g surge",
            auth_check_cmd=["surge", "whoami"],
            deploy_cmd=["surge", "{dist}"],
            url_regex=re.compile(r"(https://[a-z0-9\-]+\.surge\.sh)"),
        )
    raise ValueError(f"Unknown provider: {key}")


def check_cli_available(provider_key: str) -> tuple[bool, str]:
    """Returns (available, version_or_error). For cloudflare always
    True (npx auto-fetches)."""
    info = provider_info(provider_key)
    cli = info.cli
    if not shutil.which(cli):
        return False, f"`{cli}` not found on PATH"
    if cli == "npx":
        return True, "npx (wrangler fetched on demand)"
    try:
        r = subprocess.run(
            [cli, "--version"], capture_output=True, text=True, timeout=10
        )
        ver = r.stdout.strip() or r.stderr.strip() or "(no version output)"
        return True, ver
    except Exception as e:
        return False, str(e)


def build_deploy_command(provider_key: str, dist_dir: str) -> list[str]:
    """Returns the argv for the deploy CLI invocation, with `{dist}`
    substituted."""
    info = provider_info(provider_key)
    return [a.replace("{dist}", dist_dir) for a in info.deploy_cmd]


def extract_url(provider_key: str, output: str) -> str | None:
    info = provider_info(provider_key)
    matches = info.url_regex.findall(output)
    if not matches:
        return None
    return matches[-1]
