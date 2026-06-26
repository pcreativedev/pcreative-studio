"""
push_service.py — Notificaciones push (FCM HTTP v1) para Pcreative Studio móvil.

Avisa al teléfono ("build terminado", "lead caliente"…) vía Firebase Cloud
Messaging. El cliente Capacitor registra su token con POST /push/register; el
servidor envía push a todos los tokens guardados.

Sin dependencias pesadas: el access-token OAuth2 del service account se firma a
mano con PyJWT (RS256) y se intercambia en oauth2.googleapis.com. Inerte hasta
que configures el service account de Firebase:
  - GOOGLE_APPLICATION_CREDENTIALS=/ruta/fcm-service-account.json   (o)
  - ~/.config/themeforge/fcm-service-account.json
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

try:
    import platform_compat as pc
    _CFG = pc.app_config_dir()
except Exception:
    _CFG = Path.home() / ".config" / "themeforge"

TOKENS_PATH = _CFG / "push_tokens.json"
_SA_DEFAULT = _CFG / "fcm-service-account.json"
_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"

_access = {"token": "", "exp": 0}


# ---------------------------------------------------------------------------
# Registro de tokens de dispositivo
# ---------------------------------------------------------------------------
def _load_tokens() -> dict:
    if TOKENS_PATH.is_file():
        try:
            return json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tokens": {}}


def add_token(token: str, platform: str = "android") -> dict:
    token = (token or "").strip()
    if not token:
        return {"ok": False, "error": "token vacío"}
    data = _load_tokens()
    data.setdefault("tokens", {})[token] = {"platform": platform, "ts": int(time.time())}
    _CFG.mkdir(parents=True, exist_ok=True)
    TOKENS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(data["tokens"])}


def remove_token(token: str) -> None:
    data = _load_tokens()
    if token in data.get("tokens", {}):
        del data["tokens"][token]
        TOKENS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_tokens() -> list[str]:
    return list(_load_tokens().get("tokens", {}).keys())


# ---------------------------------------------------------------------------
# Service account / OAuth2
# ---------------------------------------------------------------------------
def _sa_path() -> Path | None:
    env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env and Path(env).is_file():
        return Path(env)
    if _SA_DEFAULT.is_file():
        return _SA_DEFAULT
    return None


def configured() -> bool:
    return _sa_path() is not None


def _access_token() -> str:
    if _access["token"] and _access["exp"] > time.time() + 60:
        return _access["token"]
    sa_path = _sa_path()
    if not sa_path:
        raise RuntimeError("FCM no configurado: falta el service account de Firebase.")
    import jwt  # PyJWT
    import requests
    sa = json.loads(sa_path.read_text(encoding="utf-8"))
    now = int(time.time())
    claims = {
        "iss": sa["client_email"], "scope": _SCOPE,
        "aud": sa.get("token_uri", "https://oauth2.googleapis.com/token"),
        "iat": now, "exp": now + 3600,
    }
    assertion = jwt.encode(claims, sa["private_key"], algorithm="RS256")
    resp = requests.post(sa.get("token_uri", "https://oauth2.googleapis.com/token"), data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }, timeout=20)
    resp.raise_for_status()
    tok = resp.json()
    _access["token"] = tok["access_token"]
    _access["exp"] = now + int(tok.get("expires_in", 3600))
    return _access["token"]


def _project_id() -> str:
    sa_path = _sa_path()
    return json.loads(sa_path.read_text(encoding="utf-8"))["project_id"] if sa_path else ""


# ---------------------------------------------------------------------------
# Envío
# ---------------------------------------------------------------------------
def send(title: str, body: str, data: dict | None = None,
         tokens: list[str] | None = None) -> dict:
    """Envía una push a todos los dispositivos registrados (o a `tokens`)."""
    if not configured():
        return {"ok": False, "error": "FCM no configurado (sin service account)."}
    targets = tokens if tokens is not None else list_tokens()
    if not targets:
        return {"ok": True, "sent": 0, "note": "sin dispositivos registrados"}
    import requests
    try:
        access = _access_token()
        pid = _project_id()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    url = f"https://fcm.googleapis.com/v1/projects/{pid}/messages:send"
    headers = {"Authorization": f"Bearer {access}", "Content-Type": "application/json"}
    sent, errors = 0, []
    for tk in targets:
        msg = {"message": {"token": tk, "notification": {"title": title, "body": body}}}
        if data:
            msg["message"]["data"] = {k: str(v) for k, v in data.items()}
        try:
            r = requests.post(url, headers=headers, json=msg, timeout=20)
            if r.status_code == 200:
                sent += 1
            else:
                errors.append(f"{r.status_code}: {r.text[:120]}")
                # token muerto → límpialo
                if r.status_code in (404, 400) and "UNREGISTERED" in r.text:
                    remove_token(tk)
        except Exception as e:
            errors.append(str(e))
    return {"ok": True, "sent": sent, "errors": errors}
