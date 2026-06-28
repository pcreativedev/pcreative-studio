"""Distribuye el skill `pcreative-studio-operator` a Hermes.

La fuente versionada vive en el repo (`hermes/skills/pcreative-studio-operator/`). Este
módulo la instala/actualiza en `~/.hermes/skills/pcreative-studio/pcreative-studio-operator/`
para que Hermes la cargue con `-s pcreative-studio-operator`. Compara la versión del
frontmatter y solo sobrescribe si la del repo es más nueva (o no hay instalada),
y nunca pisa una copia que el usuario haya marcado como modificada.

Solo stdlib. `ensure_operator_skill_installed()` se llama al abrir el panel Hermes.
"""
from __future__ import annotations

import shutil
from pathlib import Path

REPO_SKILL = Path(__file__).resolve().parent / "hermes" / "skills" / "pcreative-studio-operator"
DEST_DIR = Path.home() / ".hermes" / "skills" / "pcreative-studio" / "pcreative-studio-operator"


def _version(skill_md: Path) -> tuple[int, ...]:
    """Lee `version:` del frontmatter como tupla comparable (0,0,0 si falta)."""
    try:
        seen_fence = False
        for raw in skill_md.read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if s == "---":
                if seen_fence:
                    break  # cierre del frontmatter → no seguimos leyendo
                seen_fence = True
                continue
            if s.startswith("version:"):
                v = s.split(":", 1)[1].strip().strip("\"'")
                return tuple(int(x) for x in v.split(".") if x.isdigit()) or (0,)
    except Exception:
        pass
    return (0,)


def ensure_operator_skill_installed() -> str | None:
    """Instala/actualiza el skill del repo en ~/.hermes/skills/. Devuelve la
    versión instalada (str) si copió algo, None si no hizo falta o no pudo."""
    src_md = REPO_SKILL / "SKILL.md"
    if not src_md.is_file():
        return None
    dest_md = DEST_DIR / "SKILL.md"

    if dest_md.is_file():
        # Respeta ediciones manuales del usuario.
        try:
            if "user_modified: true" in dest_md.read_text(encoding="utf-8"):
                return None
        except Exception:
            pass
        if _version(dest_md) >= _version(src_md):
            return None  # ya está al día

    try:
        DEST_DIR.mkdir(parents=True, exist_ok=True)
        # Copia SKILL.md + cualquier recurso adjunto (references/, scripts/…).
        for item in REPO_SKILL.iterdir():
            target = DEST_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)
        return ".".join(map(str, _version(src_md)))
    except Exception:
        return None


if __name__ == "__main__":
    v = ensure_operator_skill_installed()
    print(f"  ✓ pcreative-studio-operator instalado/actualizado a v{v}"
          if v else "  (pcreative-studio-operator ya al día o no disponible)")
