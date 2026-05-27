"""Hace descubribles por Claude Code las skills instaladas por autoskills.

autoskills instala las skills en `<dir>/.agents/skills/<name>/` pero NO
siempre crea los symlinks en `<dir>/.claude/skills/`, que es lo único que
Claude Code escanea. uipro-cli, en cambio, escribe directo en `.claude/skills/`.
Resultado: el agente solo "veía" la skill de UI/UX Pro y no las de autoskills.

Este módulo enlaza (symlink relativo) cada skill de `.agents/skills/` dentro de
`.claude/skills/`. Es idempotente y no toca directorios reales ya existentes
(p. ej. la carpeta de ui-ux-pro-max). Solo stdlib → se puede invocar desde el
script de setup (`python3 -m skills_wireup <root>`) y desde la app.
"""
from __future__ import annotations

import os
from pathlib import Path

# Skills agnósticas de stack: en mono-repos también se enlazan en la raíz
# para que estén disponibles desde cualquier cwd.
CROSS_CUTTING = {
    "accessibility", "seo", "frontend-design", "tailwind-css-patterns",
    "bash-defensive-patterns", "typescript-advanced-types",
}


def _link_into(agents_skills: Path, claude_skills: Path,
               names: set[str] | None = None) -> list[str]:
    """Symlink (relativo) cada skill de `agents_skills` en `claude_skills`.
    Si `names` se da, solo esas. No pisa directorios reales (no-symlink).
    Devuelve los nombres enlazados."""
    if not agents_skills.is_dir():
        return []
    claude_skills.mkdir(parents=True, exist_ok=True)
    linked: list[str] = []
    for skill in sorted(agents_skills.iterdir()):
        if not skill.is_dir():
            continue
        if names is not None and skill.name not in names:
            continue
        link = claude_skills / skill.name
        # Si ya hay un dir real (no symlink), respetarlo (p. ej. uipro).
        if link.exists() and not link.is_symlink():
            continue
        target = os.path.relpath(skill, claude_skills)
        try:
            if link.is_symlink():
                link.unlink()
            link.symlink_to(target)
            linked.append(skill.name)
        except OSError:
            # Windows sin permisos de symlink, etc. → se ignora esa skill.
            pass
    return linked


def ensure_skills_discoverable(root: Path) -> list[str]:
    """Enlaza las skills de autoskills a `.claude/skills/` para que el agente
    las descubra. Idempotente.

    - Single-app: enlaza TODO `root/.agents/skills/*` → `root/.claude/skills/`.
    - Mono-repo: enlaza cada `apps|packages/*/.agents/skills/*` en su propio
      `.claude/skills/`, y las cross-cutting también en la raíz.

    Devuelve la lista de skills enlazadas (para logging)."""
    root = Path(root)
    linked: list[str] = []

    subs: list[Path] = []
    for pat in ("apps", "packages"):
        d = root / pat
        if d.is_dir():
            try:
                subs += [p for p in sorted(d.iterdir()) if p.is_dir()]
            except OSError:
                pass

    if subs:
        # Mono-repo: per-app + cross-cutting a la raíz.
        cross: set[str] = set()
        for sub in subs:
            linked += _link_into(sub / ".agents" / "skills",
                                 sub / ".claude" / "skills")
            sk = sub / ".agents" / "skills"
            if sk.is_dir():
                for s in sk.iterdir():
                    if s.is_dir() and s.name in CROSS_CUTTING:
                        cross.add(s.name)
        for sub in subs:
            if not cross:
                break
            got = _link_into(sub / ".agents" / "skills",
                             root / ".claude" / "skills", names=cross)
            linked += got
            cross -= set(got)

    # Raíz single-app (o root con su propio .agents/skills/).
    linked += _link_into(root / ".agents" / "skills", root / ".claude" / "skills")

    # settings.json vacío señaliza a Claude Code que hay config de proyecto.
    if linked:
        sp = root / ".claude" / "settings.json"
        if not sp.exists():
            try:
                sp.parent.mkdir(parents=True, exist_ok=True)
                sp.write_text("{}\n", encoding="utf-8")
            except OSError:
                pass

    # Quitar duplicados conservando orden.
    seen: set[str] = set()
    out = []
    for n in linked:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    done = ensure_skills_discoverable(target)
    if done:
        print("  ✓ skills de autoskills enlazadas en .claude/skills/: "
              + ", ".join(done))
    else:
        print("  (sin skills de autoskills que enlazar)")
