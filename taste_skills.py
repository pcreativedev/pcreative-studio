"""taste_skills.py — la capa de **criterio de diseño** (Taste-Skill).

Instala el pack de https://github.com/Leonxlnx/taste-skill (MIT) con el CLI
`npx skills`, que deja cada skill en `.claude/skills/<nombre>/SKILL.md` — que es
justo donde el agente busca. A diferencia de `autoskills`, no hace falta cablear
symlinks después: llega colocada.

── POR QUÉ NO SE PONE EN TODOS LOS PROYECTOS ──────────────────────────────────

La skill principal lo dice de sí misma en su primera línea: *«Landing pages,
portfolios, and redesigns. Not dashboards, not data tables, not multi-step
product UI»*. Son 1.200 líneas de criterio pensado para páginas que tienen que
IMPRESIONAR a quien llega de fuera.

Un panel de administración no tiene ese trabajo. El suyo es que una persona que
lleva ocho horas ahí encuentre el botón. Meterle reglas de tipografía editorial,
motion perpetuo y asimetría deliberada no lo mejora: lo estropea, y además
gasta contexto del agente en algo que no le sirve.

Por eso `aplica()` decide, y por eso devuelve también el MOTIVO: cuando el
programa se salta una capa que el usuario ha pedido, tiene que poder leer por
qué en vez de pensar que algo ha fallado.

── LAS ESTÉTICAS SE PISAN ENTRE SÍ ────────────────────────────────────────────

`minimalist-ui` («monocromo, sin adornos»), `industrial-brutalist-ui` («crudo,
contraste extremo») y `high-end-visual-design` («caro, sombras, profundidad»)
son tres respuestas INCOMPATIBLES a la misma pregunta. Instaladas a la vez, el
agente recibe tres órdenes que se contradicen y elige por su cuenta — que es
exactamente el problema que este pack venía a resolver.

Instalarlas todas es una decisión deliberada del usuario (quiere el pack
completo, para poder pedir cualquiera). Lo que hace este módulo es dejarlo
ESCRITO en el contexto del proyecto: una manda, y es la que el usuario nombre.
"""
from __future__ import annotations

from pathlib import Path

REPO = "https://github.com/Leonxlnx/taste-skill"

# ── el catálogo ──────────────────────────────────────────────────────────────
# (nombre de instalación, etiqueta, grupo, necesita servicio de imágenes)
#
# Los nombres son los que acepta `skills add -s`, verificados contra el repo
# con `npx --yes skills add <repo> -l`. NO coinciden con los de las carpetas
# (la carpeta es `taste-skill`, el nombre de instalación `design-taste-frontend`).
SKILLS: list[tuple[str, str, str, bool]] = [
    # Criterio general — la que manda si no se pide otra cosa.
    ("design-taste-frontend", "Criterio de diseño (anti-slop)", "criterio", False),
    ("design-taste-frontend-v1", "Criterio de diseño v1 (compatibilidad)", "criterio", False),
    ("gpt-taste", "Awwwards + GSAP", "criterio", False),
    ("high-end-visual-design", "Acabado de agencia", "estetica", False),
    ("stitch-design-taste", "Sistema de diseño (DESIGN.md)", "criterio", False),
    # Estéticas — excluyentes entre sí, se piden por su nombre.
    ("minimalist-ui", "Minimalista (Notion / Linear)", "estetica", False),
    ("industrial-brutalist-ui", "Brutalista industrial", "estetica", False),
    # Herramientas de trabajo.
    ("redesign-existing-projects", "Rediseñar lo que ya existe", "herramienta", False),
    ("image-to-code", "De una referencia visual a código", "herramienta", False),
    ("full-output-enforcement", "Prohibido el código a medias", "herramienta", False),
    # Generan IMÁGENES, no código. Necesitan un servicio de generación aparte.
    ("imagegen-frontend-web", "Bocetos de web", "imagen", True),
    ("imagegen-frontend-mobile", "Bocetos de móvil", "imagen", True),
    ("brandkit", "Kit de marca", "imagen", True),
]

TODAS = [s[0] for s in SKILLS]
SIN_IMAGEN = [s[0] for s in SKILLS if not s[3]]

# Clave de agente de Pcreative Studio → nombre que entiende el CLI `skills`.
# Cubre los siete proveedores: una capa de calidad que solo funcionara con
# Claude sería una capa que la mayoría de proyectos no recibe.
AGENTES = {
    "claude": "claude-code",
    "claude-api": "claude-code",
    "codex": "codex",
    "codex-api": "codex",
    "gemini": "gemini-cli",
    "opencode": "opencode",
    "openrouter": "opencode",
    "hermes": "hermes-agent",
}

# ── cuándo NO ────────────────────────────────────────────────────────────────

#: Tipos de plantilla que no son un escaparate.
_TIPOS_FUERA = {"Admin / Dashboard"}

#: Categorías de stack sin una interfaz que a alguien le entre por los ojos.
_CATEGORIAS_FUERA = {"Backend · API", "Headless CMS", "Email"}

#: Palabras que, en el nombre de un proyecto o de una carpeta, delatan
#: trastienda. Las mismas que ya usa el ranking de sub-apps del mono-repo.
_PALABRAS_FUERA = (
    "admin", "dashboard", "panel", "backoffice", "back-office", "backend",
    "api", "cms", "worker", "cron", "erp", "crm-panel",
)


def _tiene_palabra_de_trastienda(texto: str) -> str | None:
    bajo = (texto or "").lower()
    for p in _PALABRAS_FUERA:
        # Con separador delante o detrás, para que «apixaban» no cuente como «api»
        # ni «administrador de fincas» quede fuera por decir «admin».
        for sep in ("-", "_", " ", "/", "."):
            if f"{sep}{p}" in bajo or f"{p}{sep}" in bajo:
                return p
        if bajo == p:
            return p
    return None


def aplica(
    template_type: str | None = None,
    stack_category: str | None = None,
    project_name: str | None = None,
) -> tuple[bool, str]:
    """¿Tiene sentido el criterio de diseño en este proyecto?

    Devuelve `(sí, motivo)`. El motivo se enseña siempre — cuando una capa
    pedida no se ejecuta, el silencio se lee como avería.
    """
    if template_type and template_type.strip() in _TIPOS_FUERA:
        return False, f"el tipo es «{template_type.strip()}», y no es un escaparate"

    if template_type and template_type.startswith("Videojuego"):
        return False, "en un videojuego el diseño es el juego, no una página"

    if stack_category and stack_category.strip() in _CATEGORIAS_FUERA:
        return False, f"«{stack_category.strip()}» no tiene interfaz que mirar"

    palabra = _tiene_palabra_de_trastienda(project_name or "")
    if palabra:
        return False, f"el nombre del proyecto dice «{palabra}»: suena a trastienda"

    return True, "es un proyecto con cara visible"


def detectar_en_disco(root: Path) -> tuple[bool, str]:
    """Lo mismo, para un proyecto que ya existe y se abre desde la galería.

    Ahí no hay tipo de plantilla que consultar: hay que mirar lo que hay. Se
    mira la forma del repo, no su nombre, porque una carpeta llamada `mi-tienda`
    puede ser el panel de una tienda.
    """
    try:
        nombres = [p.name.lower() for p in root.iterdir() if p.is_dir()]
    except OSError:
        return True, "no he podido mirar dentro: se aplica por defecto"

    # Un mono-repo con `apps/` decide por sus sub-apps.
    if "apps" in nombres or "packages" in nombres:
        try:
            subs = [p.name.lower() for p in (root / "apps").iterdir() if p.is_dir()]
        except OSError:
            subs = []
        if subs and all(_tiene_palabra_de_trastienda(s) for s in subs):
            return False, "todas sus sub-apps son de trastienda"
        return True, "tiene al menos una sub-app de cara al público"

    palabra = _tiene_palabra_de_trastienda(root.name)
    if palabra:
        return False, f"la carpeta dice «{palabra}»"

    return True, "es un proyecto con cara visible"


# ── generar el trozo de script ───────────────────────────────────────────────

def bloque_shell(agent_key: str, skills: list[str] | None = None) -> list[str]:
    """Las líneas de shell que instalan el pack durante el setup.

    Nunca es fatal: una skill que no baja no puede impedir que el proyecto se
    cree. Lo peor que puede pasar es quedarse sin la capa de criterio, y eso se
    arregla con un comando; un setup abortado a mitad, no.
    """
    agente = AGENTES.get(agent_key)
    if not agente:
        return [f'echo "→ Saltando Taste-Skill: no sé qué agente es «{agent_key}» para el CLI."']

    elegidas = skills or TODAS
    args = " ".join(f"-s {s}" for s in elegidas)
    return [
        "",
        'echo "──── Taste-Skill (criterio de diseño) ────"',
        f'echo "→ Instalando {len(elegidas)} skills para {agente}…"',
        f'npx --yes skills add {REPO} {args} -a {agente} -y '
        f'|| echo "(Taste-Skill falló — el proyecto sigue sin él)"',
    ]


def bloque_contexto(skills: list[str] | None = None) -> str:
    """El trozo que va al CLAUDE.md / AGENTS.md del proyecto.

    Sin esto, las skills se instalan y el agente arranca sin saber que están —
    que es exactamente el fallo que hubo que corregir con autoskills en la
    v1.2.4. Instalar no es lo mismo que usar.
    """
    elegidas = set(skills or TODAS)
    puestas = [(n, etiqueta, grupo) for n, etiqueta, grupo, _ in SKILLS if n in elegidas]
    if not puestas:
        return ""

    criterio = [f"`{n}` — {e}" for n, e, g in puestas if g == "criterio"]
    esteticas = [f"`{n}` — {e}" for n, e, g in puestas if g == "estetica"]
    herramientas = [f"`{n}` — {e}" for n, e, g in puestas if g == "herramienta"]
    imagen = [f"`{n}` — {e}" for n, e, g in puestas if g == "imagen"]

    partes = [
        "## 🎯 Taste-Skill — criterio de diseño (ÚSALO)",
        "",
        "En `.claude/skills/` tienes instalado el criterio de diseño. **Léelo antes",
        "de escribir una sola línea de interfaz.** Está ahí para que lo que salga no",
        "parezca generado: nada de degradado morado, héroe centrado sobre malla",
        "oscura, tres tarjetas iguales y `Inter + slate-900`.",
        "",
    ]
    if criterio:
        partes += ["**El criterio, primero:**", ""] + [f"- {x}" for x in criterio] + [""]
    if esteticas:
        partes += [
            "**Estéticas disponibles — MANDA UNA SOLA:**",
            "",
        ] + [f"- {x}" for x in esteticas] + [
            "",
            "> Son respuestas incompatibles a la misma pregunta: una dice monocromo y",
            "> sin adornos, otra dice sombras y profundidad. Aplica **la que el",
            "> usuario haya pedido por su nombre**, y si no ha pedido ninguna, quédate",
            "> en el criterio general y no mezcles.",
            "",
        ]
    if herramientas:
        partes += ["**Herramientas:**", ""] + [f"- {x}" for x in herramientas] + [""]
    if imagen:
        partes += [
            "**Generan imágenes, no código** (necesitan un servicio de imágenes; sin él, ignóralas):",
            "",
        ] + [f"- {x}" for x in imagen] + [""]

    partes += [
        "Antes de plantear nada, di en una línea cómo lees el encargo: qué clase de",
        "página es, para quién, y qué lenguaje visual le pega. Si de verdad hay dos",
        "lecturas posibles, pregunta **una** cosa; si puedes deducirlo, no preguntes.",
    ]
    return "\n".join(partes)
