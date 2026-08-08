"""
cost_tracker.py — agregador de uso/coste por proveedor de IA.

Escanea las sesiones que cada CLI persiste y calcula el coste
multiplicando tokens × tarifas conocidas. La estructura es por
proveedor para que añadir uno nuevo sea trivial (registrar un
scanner + tarifas).

Hoy soporta:

  · Claude Code  — `~/.claude/projects/<encoded>/*.jsonl`. Cada evento
    `type=assistant` trae `message.model` y `message.usage` con tokens
    detallados (input, output, cache_read, cache_creation). Tarifas
    según el catálogo público de Anthropic.

  · Codex (OpenAI) — `~/.codex/logs_2.sqlite` tabla `logs`. Best-effort:
    el `feedback_log_body` contiene tracebacks con `model=<id>` y
    fragmentos JSON con `"usage"`. Extraemos con regex. Puede faltar
    alguna sesión si el log no llegó a flushear todavía.

  · Gemini, OpenCode — placeholder. Si el dir del CLI existe pero no
    sabemos su formato, devolvemos un Provider con `supported=False`
    para que la UI lo muestre como "no soportado".

Los precios son aproximados y conviven todos en `PRICING`. Para
modelos no listados, usamos `_DEFAULT_PRICING` (conservador, tarifas
de Opus/GPT-5) y marcamos el resultado como `pricing_unknown` para
que la UI lo señale.
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# ── Tarifas (USD por 1M tokens) ──────────────────────────────────────
# Fuente: pricing público de Anthropic / OpenAI a mayo 2026.
# Tipo: (input, output, cache_creation, cache_read).
# Para los modelos con tarifas distintas según contexto largo (e.g.
# claude-opus-4-7[1m] = ventana de 1M tokens), usamos la tarifa del
# tier "estándar"; el extra se documenta en el UI como aviso.

import models as _models

#: Se conserva por compatibilidad (algún módulo la importa), pero la fuente de
#: verdad es `models.py`. Se construye desde el catálogo para que no puedan
#: volver a divergir.
PRICING: dict[str, tuple[float, float, float, float]] = {
    m.id: (m.entrada, m.salida, m.cache_escritura, m.cache_lectura)
    for m in _models.CATALOGO
}
_DEFAULT_PRICING = _models.RESERVA


def cost_for(model: str, input_tokens: int, output_tokens: int,
             cache_creation_tokens: int = 0,
             cache_read_tokens: int = 0) -> tuple[float, bool]:
    """Devuelve (coste_usd, pricing_known).

    Delega en `models.coste`, que NORMALIZA el identificador antes de buscar.
    Ese detalle es todo el asunto: aquí se comparaba por igualdad exacta, así
    que `claude-haiku-4-5-20251001` no casaba con `claude-haiku-4-5` y se le
    aplicaba la tarifa de reserva — 15/75 en vez de 1/5.

    Medido sobre las sesiones reales antes de arreglarlo: el panel inflaba
    **5.390 $ sobre 16.000 $, un 34 %**, casi todo por `claude-opus-5`, que
    directamente no figuraba en ninguna tabla.
    """
    return _models.coste(model, input_tokens, output_tokens,
                         cache_creation_tokens, cache_read_tokens)


# ── Modelo de datos ──────────────────────────────────────────────────


@dataclass
class Event:
    """Un único evento (request → respuesta) ya con coste calculado."""
    provider: str
    ts: float                # unix seconds
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    pricing_known: bool = True
    project: str = ""        # opcional: encoded path o slug


@dataclass
class ProviderResult:
    provider: str            # "claude", "codex", "gemini", "opencode"
    supported: bool          # ¿podemos leer sus sesiones?
    available: bool          # ¿existe el dir del CLI?
    events: list[Event] = field(default_factory=list)
    notes: str = ""          # mensaje al user (e.g. "instala el CLI o…")


# ── Scanners por proveedor ───────────────────────────────────────────


def scan_claude(home: Path = Path.home() / ".claude") -> ProviderResult:
    if not home.is_dir():
        return ProviderResult("claude", supported=True, available=False,
                              notes=f"No existe {home} — instala/usa `claude` para empezar.")
    projects_dir = home / "projects"
    if not projects_dir.is_dir():
        return ProviderResult("claude", supported=True, available=False,
                              notes=f"No existe {projects_dir} — sin sesiones todavía.")

    events: list[Event] = []
    for proj_dir in projects_dir.iterdir():
        if not proj_dir.is_dir():
            continue
        project_label = proj_dir.name
        for jsonl in proj_dir.glob("*.jsonl"):
            try:
                # Guard contra archivos enormes (≥50MB) — son raros
                if jsonl.stat().st_size > 50 * 1024 * 1024:
                    continue
                with jsonl.open("r", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            e = json.loads(line)
                        except Exception:
                            continue
                        if e.get("type") != "assistant":
                            continue
                        msg = e.get("message")
                        if not isinstance(msg, dict):
                            continue
                        usage = msg.get("usage") or {}
                        if not isinstance(usage, dict):
                            continue
                        model = msg.get("model") or "claude-unknown"
                        # Limpiar variantes [1m] / [3.7] / etc para que matchen PRICING
                        model_key = re.sub(r"\[[^\]]+\]$", "", model).strip()
                        in_t = int(usage.get("input_tokens") or 0)
                        out_t = int(usage.get("output_tokens") or 0)
                        cw_t = int(usage.get("cache_creation_input_tokens") or 0)
                        cr_t = int(usage.get("cache_read_input_tokens") or 0)
                        if in_t == out_t == cw_t == cr_t == 0:
                            continue
                        cost, known = cost_for(model_key, in_t, out_t, cw_t, cr_t)
                        # Timestamp
                        ts_iso = e.get("timestamp") or ""
                        ts = 0.0
                        try:
                            dt = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
                            ts = dt.timestamp()
                        except Exception:
                            try:
                                ts = jsonl.stat().st_mtime
                            except Exception:
                                pass
                        events.append(Event(
                            provider="claude", ts=ts, model=model,
                            input_tokens=in_t, output_tokens=out_t,
                            cache_creation_tokens=cw_t, cache_read_tokens=cr_t,
                            cost_usd=cost, pricing_known=known,
                            project=project_label,
                        ))
            except (OSError, PermissionError):
                continue
    return ProviderResult("claude", supported=True, available=True,
                          events=events,
                          notes=f"{len(events)} eventos en {projects_dir}")


def scan_codex(sqlite_path: Path = Path.home() / ".codex" / "logs_2.sqlite") -> ProviderResult:
    """Best-effort: parsea logs SQLite buscando model + usage embebidos
    en `feedback_log_body`. No es 100% fiable — algunos eventos no
    tienen usage, otros lo tienen en posiciones distintas."""
    if not sqlite_path.is_file():
        return ProviderResult(
            "codex", supported=True, available=False,
            notes=f"No existe {sqlite_path} — usa `codex` para generar logs.",
        )
    events: list[Event] = []
    try:
        conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
        cur = conn.execute(
            "SELECT ts, feedback_log_body FROM logs "
            "WHERE feedback_log_body LIKE '%input_tokens%'"
        )
        for ts, body in cur:
            if not body:
                continue
            # Buscar el JSON anidado tipo {"type":"response.completed", ...}
            # con "usage" dentro. Tomamos el primero que matchee.
            m = re.search(r'\{"type"\s*:\s*"response[^"]*"\s*,.*?\}\}\s*$', body, re.DOTALL)
            if not m:
                # Fallback: cualquier JSON con "usage" dentro
                m = re.search(r'\{[^{}]*"usage"\s*:\s*\{[^{}]*\}[^{}]*\}', body, re.DOTALL)
                if not m:
                    continue
            try:
                payload = json.loads(m.group(0))
            except Exception:
                # Intentar extraer "model=<id>" del trace + tokens del fragmento
                model_m = re.search(r'model=([\w.\-]+)', body)
                ut_m = re.search(r'"input_tokens"\s*:\s*(\d+)', body)
                ot_m = re.search(r'"output_tokens"\s*:\s*(\d+)', body)
                if not (model_m and ut_m and ot_m):
                    continue
                model = model_m.group(1)
                in_t = int(ut_m.group(1))
                out_t = int(ot_m.group(1))
                cost, known = cost_for(model, in_t, out_t, 0, 0)
                events.append(Event(
                    provider="codex", ts=float(ts), model=model,
                    input_tokens=in_t, output_tokens=out_t,
                    cost_usd=cost, pricing_known=known,
                ))
                continue
            # Si el JSON tiene "response.usage" o "usage" directo
            resp = payload.get("response") if isinstance(payload.get("response"), dict) else None
            usage = (resp or payload).get("usage")
            model = (resp or payload).get("model") or "gpt-unknown"
            if not isinstance(usage, dict):
                continue
            in_t = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
            out_t = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
            cache_r = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
            if in_t == out_t == 0:
                continue
            cost, known = cost_for(model, in_t, out_t, 0, cache_r)
            events.append(Event(
                provider="codex", ts=float(ts), model=model,
                input_tokens=in_t, output_tokens=out_t,
                cache_read_tokens=cache_r,
                cost_usd=cost, pricing_known=known,
            ))
        conn.close()
    except sqlite3.Error as e:
        return ProviderResult(
            "codex", supported=True, available=True,
            notes=f"Error leyendo SQLite: {e}",
        )
    # Dedup: el mismo response puede aparecer varias veces en distintos traces.
    # Lo agrupamos por (ts, model, in, out).
    seen: set[tuple] = set()
    deduped: list[Event] = []
    for ev in events:
        key = (int(ev.ts), ev.model, ev.input_tokens, ev.output_tokens)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ev)
    return ProviderResult(
        "codex", supported=True, available=True,
        events=deduped,
        notes=f"{len(deduped)} eventos (best-effort) en {sqlite_path}",
    )


def scan_gemini(home: Path = Path.home() / ".gemini") -> ProviderResult:
    """Placeholder: gemini-cli no parece persistir tokens en un formato
    documentado. Si el dir existe pero no tenemos parser, decimos
    'no soportado'."""
    return ProviderResult(
        "gemini",
        supported=False,
        available=home.is_dir() or (Path.home() / ".config" / "gemini").is_dir(),
        notes="gemini-cli no expone tokens/coste en un store local conocido. "
              "Consulta https://aistudio.google.com/billing para el desglose oficial.",
    )


def scan_opencode(home: Path = Path.home() / ".opencode") -> ProviderResult:
    return ProviderResult(
        "opencode",
        supported=False,
        available=home.is_dir() or (Path.home() / ".config" / "opencode").is_dir(),
        notes="opencode no expone tokens/coste en un store local conocido. "
              "Consulta https://openrouter.ai/activity para el desglose oficial.",
    )


SCANNERS = {
    "claude":   scan_claude,
    "codex":    scan_codex,
    "gemini":   scan_gemini,
    "opencode": scan_opencode,
}


# ── Agregaciones ─────────────────────────────────────────────────────


@dataclass
class AggregateReport:
    providers: dict[str, ProviderResult]    # raw por proveedor
    total_cost_usd: float = 0.0
    total_input: int = 0
    total_output: int = 0
    by_provider: dict[str, dict] = field(default_factory=dict)
    by_model: dict[str, dict] = field(default_factory=dict)
    by_project: dict[str, dict] = field(default_factory=dict)
    by_day: dict[str, float] = field(default_factory=dict)   # YYYY-MM-DD → coste
    by_day_by_provider: dict[str, dict[str, float]] = field(default_factory=dict)
    last_30_days_usd: float = 0.0
    this_month_usd: float = 0.0


def aggregate(providers: list[str] | None = None) -> AggregateReport:
    """Ejecuta los scanners pedidos y produce un AggregateReport.
    `providers=None` → todos los conocidos."""
    if providers is None:
        providers = list(SCANNERS.keys())
    raw: dict[str, ProviderResult] = {}
    for p in providers:
        scanner = SCANNERS.get(p)
        if scanner:
            try:
                raw[p] = scanner()
            except Exception as e:
                raw[p] = ProviderResult(p, supported=True, available=False,
                                        notes=f"Error: {e}")

    report = AggregateReport(providers=raw)
    by_prov_acc = defaultdict(lambda: {"cost": 0.0, "events": 0, "in": 0, "out": 0})
    by_model_acc = defaultdict(lambda: {"cost": 0.0, "events": 0, "in": 0, "out": 0,
                                         "provider": "", "pricing_known": True})
    by_project_acc = defaultdict(lambda: {"cost": 0.0, "events": 0, "provider": ""})
    by_day_acc = defaultdict(float)
    by_day_prov_acc: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    import time
    now_ts = time.time()
    cutoff_30d = now_ts - 30 * 86400
    # Mes en curso (UTC)
    now_utc = datetime.now(timezone.utc)
    month_start = datetime(now_utc.year, now_utc.month, 1, tzinfo=timezone.utc).timestamp()

    for pr in raw.values():
        for ev in pr.events:
            report.total_cost_usd += ev.cost_usd
            report.total_input += ev.input_tokens
            report.total_output += ev.output_tokens
            by_prov_acc[ev.provider]["cost"] += ev.cost_usd
            by_prov_acc[ev.provider]["events"] += 1
            by_prov_acc[ev.provider]["in"] += ev.input_tokens
            by_prov_acc[ev.provider]["out"] += ev.output_tokens
            mk = by_model_acc[ev.model]
            mk["cost"] += ev.cost_usd
            mk["events"] += 1
            mk["in"] += ev.input_tokens
            mk["out"] += ev.output_tokens
            mk["provider"] = ev.provider
            if not ev.pricing_known:
                mk["pricing_known"] = False
            if ev.project:
                bp = by_project_acc[ev.project]
                bp["cost"] += ev.cost_usd
                bp["events"] += 1
                bp["provider"] = ev.provider
            # Día
            day = datetime.fromtimestamp(ev.ts, tz=timezone.utc).strftime("%Y-%m-%d")
            by_day_acc[day] += ev.cost_usd
            by_day_prov_acc[day][ev.provider] += ev.cost_usd
            if ev.ts >= cutoff_30d:
                report.last_30_days_usd += ev.cost_usd
            if ev.ts >= month_start:
                report.this_month_usd += ev.cost_usd

    report.by_provider = dict(by_prov_acc)
    report.by_model = dict(by_model_acc)
    report.by_project = dict(by_project_acc)
    report.by_day = dict(by_day_acc)
    report.by_day_by_provider = {d: dict(provs) for d, provs in by_day_prov_acc.items()}
    return report
