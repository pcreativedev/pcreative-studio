"""
api_gateway.py — Fase 0 de "Pcreative Studio móvil": expone el motor como API remota.

Reconvierte el puente nativo (window.tfBridge / QWebChannel) en una API:
  - HTTP JSON-RPC (POST /rpc)     → métodos síncronos (listar, CRUD, stats…)
  - WebSocket (/ws)               → métodos con streaming + eventos en vivo
  - POST /upload                  → subir foto (cámara móvil) para OCR
  - GET /health                   → sonda

El motor headless es la única fuente de verdad; escritorio y móvil hablan esta
API. Los métodos opcionales se cargan por plugins (ver `_load_plugins`).

Auth: bearer token (env PCREATIVE STUDIO_API_TOKEN, o ~/.config/themeforge/api_token.txt).
Pensado para vivir DETRÁS de Tailscale/WireGuard (no exponer crudo a internet).

Arrancar:  uvicorn api_gateway:app --host 0.0.0.0 --port 8765
           (o: python api_gateway.py)
"""
from __future__ import annotations

import asyncio
import json
import secrets
import tempfile
from pathlib import Path

from fastapi import (Depends, FastAPI, Header, HTTPException, UploadFile,
                     WebSocket, WebSocketDisconnect)
from fastapi.responses import JSONResponse

try:
    import platform_compat as pc
    _CFG = pc.app_config_dir()
except Exception:
    _CFG = Path.home() / ".config" / "themeforge"

app = FastAPI(title="Pcreative Studio Gateway", version="0.1")

# CORS abierto (la API está protegida por token + Tailscale, no por origen).
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])


# ---------------------------------------------------------------------------
# Auth (bearer token; combínalo con Tailscale para acceso de red privado)
# ---------------------------------------------------------------------------
def _token() -> str:
    import os
    t = os.environ.get("PCREATIVE STUDIO_API_TOKEN")
    if t:
        return t.strip()
    p = _CFG / "api_token.txt"
    if p.is_file():
        return p.read_text(encoding="utf-8").strip()
    _CFG.mkdir(parents=True, exist_ok=True)
    t = secrets.token_urlsafe(24)
    p.write_text(t, encoding="utf-8")
    try:
        pc.secure_file_chmod(p)
    except Exception:
        pass
    print(f"[gateway] token generado → {p}\n[gateway] PCREATIVE STUDIO_API_TOKEN={t}")
    return t


API_TOKEN = _token()


def _check(token: str | None) -> bool:
    return bool(token) and secrets.compare_digest(token, API_TOKEN)


def require_http(authorization: str | None = Header(default=None)) -> bool:
    tok = None
    if authorization and authorization.lower().startswith("bearer "):
        tok = authorization[7:].strip()
    if not _check(tok):
        raise HTTPException(status_code=401, detail="token inválido")
    return True


# ---------------------------------------------------------------------------
# Registro de métodos
#   SYNC   — síncronos (lectura/CRUD/stats), van por HTTP /rpc (o WS)
#   STREAM — red/larga duración, van por WS y emiten eventos `progress`/`result`
# Las entradas base son las de creación de proyectos (abajo). Plugins opcionales
# pueden añadir más métodos vía `_load_plugins`.
# ---------------------------------------------------------------------------
SYNC: dict = {}
STREAM: dict = {}


# ===================== Crear proyecto (Vibe / Recreate / Stack) =====================
def _list_stacks(p):
    """Datos para los pickers del móvil: stacks, tipos, nichos, agentes."""
    from stacks import STACKS, TEMPLATE_TYPES, TEMPLATE_NICHES, AGENTS
    stacks = [{"key": k, "name": v.get("name", k),
               "category": v.get("category", "") or ("Sin definir" if k == "none" else ""),
               "language": v.get("language", "")} for k, v in STACKS.items()]
    return {"ok": True, "stacks": stacks, "template_types": list(TEMPLATE_TYPES),
            "niches": list(TEMPLATE_NICHES), "providers": list(AGENTS.keys())}


def _suggest(description: str, provider: str) -> dict:
    """Vibe: descripción natural → stack + dev_prompt (reusa vibe_scaffolder)."""
    import os
    import shlex
    import subprocess
    import ai_providers as aip
    import platform_compat as _pc
    from stacks import STACKS, TEMPLATE_TYPES
    import themes as _t
    from vibe_scaffolder import build_vibe_prompt, parse_vibe_response

    builtin = [t.name for t in _t.list_themes() if not t.is_user]
    prompt = build_vibe_prompt(description, STACKS, TEMPLATE_TYPES, builtin)
    state, info = aip.detect_status(provider)
    if state != "ok":
        return {"error": f"agente '{provider}' no listo: {info}", "stack_key": None}
    argv = aip.oneshot_argv(provider, allow_web=False)
    cmd_str = " ".join(shlex.quote(a) for a in argv)
    env = {**os.environ, **dict(aip.get_env(provider))}
    try:
        proc = subprocess.run(_pc.shell_argv(cmd_str), input=prompt, capture_output=True,
                              text=True, timeout=120, env=env)
    except Exception as e:
        return {"error": f"inferencia falló: {e}", "stack_key": None}
    proposal, perr = parse_vibe_response(proc.stdout)
    if not proposal:
        return {"error": f"no se pudo parsear: {perr}", "stack_key": None}
    return {"stack_key": proposal.stack_key, "template_type": proposal.template_type,
            "dev_prompt": proposal.dev_prompt, "reasoning": proposal.reasoning}


def _stream_proc(argv, emit, cwd=None, env=None, input_text=None) -> int:
    """Ejecuta un proceso y emite cada línea de salida como evento `log`."""
    import subprocess
    proc = subprocess.Popen(
        argv, cwd=cwd, env=env,
        stdin=(subprocess.PIPE if input_text is not None else None),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    if input_text is not None:
        try:
            proc.stdin.write(input_text); proc.stdin.close()
        except Exception:
            pass
    for line in proc.stdout:
        emit("log", {"line": line.rstrip("\n")})
    proc.wait()
    return proc.returncode or 0


def _stream_suggest(p, emit):
    emit("log", {"line": "→ Vibe: consultando a la IA el stack ideal…"})
    return _suggest(p.get("description", ""), p.get("provider") or "claude")


def _stream_create_build(p, emit):
    """Crea el proyecto (Vibe/Recreate/Stack), ejecuta el setup streameando logs
    y luego corre el agente autónomo en el portátil. Todo en vivo al móvil."""
    import os
    import shlex
    import ai_providers as aip
    import platform_compat as _pc
    from stacks import STACKS
    from themeforge import (write_setup_script, PROJECTS_DIR, slugify,
                            load_projects_meta, save_projects_meta)

    mode = p.get("mode", "scratch")
    name = (p.get("name") or "Proyecto Móvil").strip()
    provider = p.get("provider") or "claude"
    do_build = p.get("build", True)
    stack = p.get("stack") or "none"
    ttype = p.get("template_type") or "(Sin tipo específico)"
    niche = p.get("niche") or ""
    ref = (p.get("reference") or "").strip()
    ref_kind = p.get("reference_kind") or "url"
    ai_analysis = None
    ai_kind = "reference"

    if mode == "vibe":
        sug = _suggest(p.get("description", ""), provider)
        if sug.get("stack_key"):
            stack = sug["stack_key"]
            ttype = sug.get("template_type") or ttype
            ai_analysis = sug.get("dev_prompt") or p.get("description", "")
            ai_kind = "vibe"
            emit("stack_suggested", {"stack": stack, "template_type": ttype,
                                     "reasoning": sug.get("reasoning", "")})
        else:
            stack = "none"
            ai_analysis = p.get("description", "")
            ai_kind = "vibe"
            emit("log", {"line": "  (no se pudo inferir stack; el agente lo decidirá)"})
        build_prompt = ai_analysis + "\n\nConstruye el proyecto COMPLETO de una sentada, con datos demo realistas, sin pedir confirmación."
        mode_eff = "scratch"
    elif mode == "recreate":
        mode_eff = "recreate"
        build_prompt = "Lee CLAUDE.md y la carpeta reference/. Recrea (mejorándolo x10) ese sitio de una sentada, código propio, sin copiar assets, sin pedir confirmación."
    else:
        mode_eff = "scratch"
        build_prompt = "Lee CLAUDE.md y construye el template COMPLETO de una sentada, multipágina, con datos demo realistas y diseño premium, sin pedir confirmación."

    if stack not in STACKS:
        return {"ok": False, "error": f"stack desconocido: {stack}"}
    if provider not in aip.PROVIDERS:
        provider = "claude" if "claude" in aip.PROVIDERS else next(iter(aip.PROVIDERS))

    slug = slugify(name)
    project_dir = PROJECTS_DIR / slug
    n = 2
    while project_dir.exists() and any(project_dir.iterdir()):
        slug = f"{slugify(name)}-{n}"; project_dir = PROJECTS_DIR / slug; n += 1

    try:
        script = write_setup_script(
            project_dir=project_dir, stack_key=stack, template_type=ttype,
            project_name=name, agent_key=provider, run_autoskills=True, mode=mode_eff,
            reference_kind=(ref_kind if mode_eff == "recreate" else None),
            reference_value=(ref if mode_eff == "recreate" else None),
            existing_repo=None, create_github_repo=False, github_user=None,
            embedded=True, run_uipro=True, niche=(niche or None),
            launch_agent=False, ai_analysis=ai_analysis, ai_analysis_kind=ai_kind)
    except Exception as e:
        return {"ok": False, "error": f"write_setup_script: {e}"}

    try:
        meta = load_projects_meta()
        meta[slug] = {"name": name, "stack": stack, "provider": provider,
                      "mode": mode_eff, "type": ttype}
        save_projects_meta(meta)
    except Exception:
        pass

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    emit("phase", {"phase": "setup", "slug": slug, "stack": stack})
    rc = _stream_proc(["bash", str(script)], emit, cwd=str(PROJECTS_DIR), env={**os.environ})
    if rc != 0:
        return {"ok": False, "error": f"setup salió con código {rc}", "slug": slug,
                "path": str(project_dir)}
    if not do_build:
        return {"ok": True, "slug": slug, "path": str(project_dir), "built": False}

    state, info = aip.detect_status(provider)
    if state != "ok":
        return {"ok": True, "slug": slug, "path": str(project_dir), "built": False,
                "note": f"setup OK; agente '{provider}' no listo: {info}"}
    emit("phase", {"phase": "agent", "provider": provider})
    argv = aip.oneshot_argv(provider, allow_web=True)
    cmd_str = " ".join(shlex.quote(a) for a in argv)
    env = {**os.environ, **dict(aip.get_env(provider))}
    rc2 = _stream_proc(_pc.shell_argv(cmd_str), emit, cwd=str(project_dir), env=env,
                       input_text=build_prompt)
    try:
        import push_service
        if push_service.configured():
            push_service.send("Pcreative Studio", f"Build terminado: {name} ✅", {"slug": slug})
    except Exception:
        pass
    return {"ok": True, "slug": slug, "path": str(project_dir), "built": True, "agent_exit": rc2}


SYNC["list_stacks"] = _list_stacks
STREAM["suggest_stack"] = _stream_suggest
STREAM["create_build"] = _stream_create_build


def _load_plugins() -> None:
    """Carga métodos opcionales si su módulo está presente en este despliegue.
    Si el módulo no existe, simplemente se omite (gateway base sin extras)."""
    for mod in ("api_gateway_private",):
        try:
            __import__(mod).register(SYNC, STREAM)
        except Exception:
            pass


_load_plugins()


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True, "service": "themeforge-gateway", "version": "0.1",
            "methods": {"sync": sorted(SYNC), "stream": sorted(STREAM)}}


@app.post("/rpc")
async def rpc(req: dict, _=Depends(require_http)):
    """JSON-RPC mínimo: {id, method, params}. Solo métodos SÍNCRONOS."""
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}
    if method not in SYNC:
        hint = " (usa /ws para streaming)" if method in STREAM else ""
        return JSONResponse(status_code=404,
                            content={"id": rid, "error": f"método desconocido: {method}{hint}"})
    try:
        result = await asyncio.to_thread(SYNC[method], params)
        return {"id": rid, "result": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"id": rid, "error": str(e)})


@app.post("/upload")
async def upload(file: UploadFile, _=Depends(require_http)):
    """Sube una imagen desde la cámara del móvil y devuelve su ruta local
    (para que un método de procesamiento la consuma luego)."""
    suffix = Path(file.filename or "foto.jpg").suffix or ".jpg"
    tmp = Path(tempfile.gettempdir()) / f"tf-upload-{secrets.token_hex(6)}{suffix}"
    tmp.write_bytes(await file.read())
    return {"ok": True, "path": str(tmp)}


# ---- Push (FCM) — el cliente Capacitor registra su token; el servidor avisa ----
@app.post("/push/register")
async def push_register(req: dict, _=Depends(require_http)):
    import push_service
    return push_service.add_token(req.get("token", ""), req.get("platform", "android"))


@app.get("/push/status")
async def push_status(_=Depends(require_http)):
    import push_service
    return {"ok": True, "configured": push_service.configured(),
            "devices": len(push_service.list_tokens())}


@app.post("/push/test")
async def push_test(_=Depends(require_http)):
    import push_service
    return await asyncio.to_thread(push_service.send, "Pcreative Studio",
                                   "Push de prueba ✅", {"kind": "test"})


# ---------------------------------------------------------------------------
# WebSocket — RPC + streaming + eventos (estilo Pterodactyl: envelope uniforme)
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def ws(sock: WebSocket):
    # Auth: header Authorization o ?token=
    tok = sock.query_params.get("token")
    if not tok:
        ah = sock.headers.get("authorization", "")
        if ah.lower().startswith("bearer "):
            tok = ah[7:].strip()
    if not _check(tok):
        await sock.close(code=4401)
        return
    await sock.accept()
    loop = asyncio.get_event_loop()
    try:
        while True:
            raw = await sock.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await sock.send_text(json.dumps({"error": "json inválido"}))
                continue
            rid = msg.get("id")
            method = msg.get("method", "")
            params = msg.get("params") or {}

            async def emit_async(event, data):
                await sock.send_text(json.dumps({"id": rid, "event": event, "data": data},
                                                ensure_ascii=False))

            def emit(event, data):  # llamable desde el hilo worker
                asyncio.run_coroutine_threadsafe(emit_async(event, data), loop)

            if method in STREAM:
                await emit_async("started", {"method": method})
                try:
                    result = await asyncio.to_thread(STREAM[method], params, emit)
                    await sock.send_text(json.dumps({"id": rid, "result": result}, ensure_ascii=False))
                except Exception as e:
                    await sock.send_text(json.dumps({"id": rid, "error": str(e)}))
            elif method in SYNC:
                try:
                    result = await asyncio.to_thread(SYNC[method], params)
                    await sock.send_text(json.dumps({"id": rid, "result": result}, ensure_ascii=False))
                except Exception as e:
                    await sock.send_text(json.dumps({"id": rid, "error": str(e)}))
            else:
                await sock.send_text(json.dumps({"id": rid, "error": f"método desconocido: {method}"}))
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await sock.close()
        except Exception:
            pass


# Sirve la PWA del móvil desde el propio gateway → ábrela en el navegador del
# móvil en http://<host>:8765/app/mobile/  (mismo origen = sin CORS ni mixed-content).
from fastapi.staticfiles import StaticFiles  # noqa: E402
_WEBUI = Path(__file__).resolve().parent / "webui"
if _WEBUI.is_dir():
    app.mount("/app", StaticFiles(directory=str(_WEBUI), html=True), name="webui")


if __name__ == "__main__":
    import uvicorn
    print(f"[gateway] token activo: {API_TOKEN}")
    uvicorn.run("api_gateway:app", host="0.0.0.0", port=8765, reload=False)
