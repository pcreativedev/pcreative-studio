"""Puente **autoskills / uipro-cli → Hermes**.

`autoskills` instala skills (formato agentskills.io) en `<root>/.agents/skills/`
y symlinks en `<root>/.claude/skills/`; `uipro-cli` instala la skill *UI/UX Pro
Max*. **Claude Code** las descubre solo (escanea `.claude/skills/`). **Hermes**,
en cambio, NO escanea `.claude/skills/`: auto-carga `AGENTS.md` / `.hermes.md` /
`CLAUDE.md` del workdir y las skills globales de `~/.hermes/skills/`. Resultado:
Hermes no estaba usando las skills que Pcreative Studio instala con autoskills/uipro.

Este módulo cierra el hueco SIN duplicar las skills: escribe un **bloque
gestionado** en `AGENTS.md` (que Hermes sí auto-carga) que lista cada skill
instalada — nombre, descripción y ruta de su `SKILL.md` — y le ordena a Hermes
leerlas con `read_file` y seguirlas antes de construir. Las skills son formato
agentskills.io, que Hermes soporta nativamente, así que basta con apuntárselas.

Idempotente: reemplaza el bloque entre marcadores. Solo stdlib → se invoca desde
el script de setup (`python3 -m hermes_skills_bridge <root>`) y desde la app
(`bridge_skills_for_hermes(root)`), igual que `skills_wireup`.
"""
from __future__ import annotations

from pathlib import Path

START = "<!-- TF-HERMES-SKILLS:START (gestionado por Pcreative Studio — no editar) -->"
END = "<!-- TF-HERMES-SKILLS:END -->"

# Dónde buscan las skills instaladas (relativo a cada root/sub-app).
SKILL_GLOBS = (".claude/skills/*/SKILL.md", ".agents/skills/*/SKILL.md")


def _frontmatter(text: str) -> dict:
    """Parser mínimo del frontmatter YAML de un SKILL.md (clave: valor de nivel 0)."""
    out: dict = {}
    if not text.startswith("---"):
        return out
    try:
        end = text.index("\n---", 3)
    except ValueError:
        return out
    for raw in text[3:end].splitlines():
        if not raw.strip() or raw.startswith((" ", "\t")) or ":" not in raw:
            continue
        if raw.lstrip().startswith("#"):
            continue
        k, _, v = raw.partition(":")
        v = v.strip().strip("\"'")
        if v:
            out[k.strip()] = v
    return out


def _collect(root: Path) -> list[dict]:
    """Reúne las skills instaladas en root y sub-apps (mono-repo). Dedup por nombre."""
    roots = [root]
    for pat in ("apps", "packages"):
        d = root / pat
        if d.is_dir():
            try:
                roots += [p for p in sorted(d.iterdir()) if p.is_dir()]
            except OSError:
                pass

    seen: set[str] = set()
    skills: list[dict] = []
    for base in roots:
        for glob in SKILL_GLOBS:
            for md in sorted(base.glob(glob)):
                try:
                    text = md.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                fm = _frontmatter(text)
                name = fm.get("name") or md.parent.name
                if name in seen:
                    continue
                seen.add(name)
                try:
                    rel = md.relative_to(root)
                except ValueError:
                    rel = md
                skills.append({
                    "name": name,
                    "description": fm.get("description", "").strip(),
                    "path": str(rel),
                })
    return skills


def _block(skills: list[dict]) -> str:
    lines = [
        START,
        "## 🧩 Skills instaladas (autoskills + UI/UX Pro Max)",
        "",
        "Pcreative Studio ha instalado estas skills (formato agentskills.io) para este "
        "proyecto. **Antes de construir, LEE cada `SKILL.md` con `read_file` y "
        "SIGUE sus convenciones** (stack, accesibilidad, SEO, diseño UI/UX). No "
        "son opcionales: son la capa de calidad de Pcreative Studio.",
        "",
    ]
    if skills:
        for s in skills:
            desc = f" — {s['description']}" if s["description"] else ""
            lines.append(f"- **{s['name']}**{desc}  \n  `{s['path']}`")
    else:
        lines.append("- _(todavía no hay skills instaladas; ejecuta el setup / "
                     "`npx --yes autoskills -a claude` tras el primer scaffold)_")
    lines += ["", END]
    return "\n".join(lines)


def bridge_skills_for_hermes(root) -> list[str]:
    """Escribe/actualiza el bloque de skills en `AGENTS.md` del proyecto para que
    Hermes (que auto-carga AGENTS.md) descubra y use las skills de autoskills/uipro.

    Si no existe `AGENTS.md` pero sí `CLAUDE.md`, crea un `AGENTS.md` que apunta al
    contexto completo en `CLAUDE.md` (Hermes lee AGENTS.md; Claude lee CLAUDE.md).
    Devuelve la lista de nombres de skills enlazadas (para logging)."""
    root = Path(root)
    skills = _collect(root)

    agents = root / "AGENTS.md"
    if not agents.exists():
        header = "# AGENTS.md\n\n"
        if (root / "CLAUDE.md").is_file():
            header += ("> Contexto completo del proyecto en **`CLAUDE.md`** "
                       "(léelo entero antes de empezar).\n\n")
        try:
            agents.write_text(header, encoding="utf-8")
        except OSError:
            return []

    try:
        text = agents.read_text(encoding="utf-8")
    except OSError:
        return []

    block = _block(skills)
    if START in text and END in text:
        pre = text[: text.index(START)]
        post = text[text.index(END) + len(END):]
        new = pre.rstrip() + "\n\n" + block + post
    else:
        new = text.rstrip() + "\n\n" + block + "\n"

    if new != text:
        try:
            agents.write_text(new, encoding="utf-8")
        except OSError:
            pass
    return [s["name"] for s in skills]


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    done = bridge_skills_for_hermes(target)
    if done:
        print("  ✓ skills expuestas a Hermes en AGENTS.md: " + ", ".join(done))
    else:
        print("  (sin skills que exponer a Hermes todavía)")
