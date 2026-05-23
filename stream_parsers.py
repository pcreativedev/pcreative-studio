"""Stream-JSON parsers for the 4 supported AI CLI agents.

Each AI CLI emits a different event format when invoked with its
structured-output flag:

  - claude `--output-format=stream-json --include-partial-messages --verbose`
  - codex  `exec --json`
  - gemini `-o stream-json`
  - opencode `run --format json`

This module normalises all of them to a canonical event dict that
`_ReferenceAnalysisDialog._handle_event` consumes uniformly. Parsers
are intentionally defensive: any unrecognised event returns an empty
dict (the dialog ignores it). Malformed JSON is silently dropped —
the calling code uses a stdout buffer so partial lines are reassembled
before parsing.

Canonical event keys (all optional):

    text_delta             str   — text chunk to append to output pane
    model                  str   — model id (for PRICING lookup)
    ttft_ms                int   — milliseconds since process start
    input_tokens           int
    output_tokens          int
    cache_creation_tokens  int
    cache_read_tokens      int
    cost_usd               float — pre-computed total (claude only)
    status                 str   — human-readable status for the dialog
    tool_use               str   — name of tool the agent invoked
    done                   bool  — terminal event (we can compute cost ourselves)
"""
from __future__ import annotations

import json
from typing import Callable, Optional


def _empty() -> dict:
    return {}


# ─────────────────────── Claude ──────────────────────────────────────
def parse_claude(line: str) -> dict:
    try:
        evt = json.loads(line)
    except Exception:
        return _empty()

    out: dict = {}
    t = evt.get("type")

    if t == "system":
        sub = evt.get("subtype")
        if sub == "init":
            out["model"] = evt.get("model")
            out["status"] = "🔌 Conectado · esperando primer token…"
        elif sub == "status":
            out["status"] = f"⏳ {evt.get('status', '')}…"
    elif t == "rate_limit_event":
        info = evt.get("rate_limit_info", {})
        if info.get("status") and info["status"] != "allowed":
            out["status"] = f"⚠️ Rate limit: {info.get('status')}"
    elif t == "stream_event":
        ev = evt.get("event") or {}
        ev_t = ev.get("type")
        if ev_t == "message_start":
            ttft = evt.get("ttft_ms")
            if ttft is not None:
                out["ttft_ms"] = ttft
            usage = (ev.get("message") or {}).get("usage") or {}
            if "input_tokens" in usage:
                out["input_tokens"] = usage["input_tokens"]
            out["status"] = "✏️ Generando respuesta…"
        elif ev_t == "content_block_start":
            block = ev.get("content_block") or {}
            if block.get("type") == "tool_use":
                name = block.get("name", "tool")
                out["tool_use"] = name
                if name == "WebSearch":
                    out["status"] = "🔎 Buscando en internet…"
                elif name == "WebFetch":
                    out["status"] = "🌐 Descargando página…"
                else:
                    out["status"] = f"🔧 Usando {name}…"
        elif ev_t == "content_block_delta":
            delta_obj = ev.get("delta") or {}
            if delta_obj.get("type") != "input_json_delta":
                text = delta_obj.get("text")
                if text:
                    out["text_delta"] = text
        elif ev_t == "content_block_stop":
            out["status"] = "✏️ Generando respuesta…"
        elif ev_t == "message_delta":
            usage = ev.get("usage") or {}
            if "output_tokens" in usage:
                out["output_tokens"] = usage["output_tokens"]
    elif t == "user":
        out["status"] = "📥 Resultado de tool · procesando…"
    elif t == "result":
        cost = evt.get("total_cost_usd")
        if cost is not None:
            out["cost_usd"] = cost
        out["done"] = True

    return out


# ─────────────────────── Codex ───────────────────────────────────────
def parse_codex(line: str) -> dict:
    """Codex `exec --json` emits JSONL events with a `msg` wrapper.

    Common event types observed in openai/codex source:
      - session_started   → model
      - agent_message_delta → text streaming
      - agent_message     → final assembled message (we ignore — already
                            built from deltas)
      - agent_reasoning_delta → optional CoT (skip in pane to keep noise low)
      - token_count       → usage stats
      - task_complete / task_completed → done
      - error             → status
    """
    try:
        evt = json.loads(line)
    except Exception:
        return _empty()

    out: dict = {}
    msg = evt.get("msg") if isinstance(evt.get("msg"), dict) else evt
    t = msg.get("type") if isinstance(msg, dict) else None

    if t == "session_started":
        out["model"] = msg.get("model")
        out["status"] = "🔌 Sesión Codex iniciada · esperando token…"
    elif t in ("agent_message_delta", "agent_text_delta"):
        delta = msg.get("delta") or msg.get("text") or msg.get("content")
        if isinstance(delta, str) and delta:
            out["text_delta"] = delta
    elif t in ("agent_reasoning_delta", "reasoning_delta"):
        # Skip CoT in the output pane (only the final answer is useful)
        out["status"] = "🧠 Razonando…"
    elif t == "tool_use" or t == "exec_command":
        name = msg.get("name") or msg.get("tool") or msg.get("command")
        if name:
            out["tool_use"] = str(name)
            out["status"] = f"🔧 Usando {name}…"
    elif t in ("token_count", "tokens"):
        # Codex fields: input_tokens / output_tokens / cached_input_tokens
        if "input_tokens" in msg:
            out["input_tokens"] = msg["input_tokens"]
        if "output_tokens" in msg:
            out["output_tokens"] = msg["output_tokens"]
        cache = msg.get("cached_input_tokens") or msg.get("cache_read_input_tokens")
        if cache:
            out["cache_read_tokens"] = cache
    elif t in ("task_complete", "task_completed", "session_ended"):
        out["done"] = True
    elif t == "error":
        out["status"] = f"⚠️ {msg.get('message', 'error')}"

    return out


# ─────────────────────── Gemini ──────────────────────────────────────
def parse_gemini(line: str) -> dict:
    """Gemini CLI `-o stream-json` emits events similar to Claude's
    stream-json but with simpler schema. Defensive parser: tries
    several documented field paths to maximise compatibility across
    gemini-cli versions.
    """
    try:
        evt = json.loads(line)
    except Exception:
        return _empty()

    out: dict = {}
    t = evt.get("type") or evt.get("event")

    # Model announcement
    model = evt.get("model") or evt.get("model_name")
    if model:
        out["model"] = model

    # Text delta — try multiple field paths
    delta = (
        evt.get("delta")
        or evt.get("content")
        or evt.get("text")
        or (evt.get("response") or {}).get("text")
        or (evt.get("candidates") or [{}])[0].get("text")
    )
    if isinstance(delta, str) and delta:
        out["text_delta"] = delta

    # Usage metadata — gemini reports under "usageMetadata" (camelCase
    # following Google's API) or "usage" depending on version
    usage = evt.get("usageMetadata") or evt.get("usage") or {}
    if isinstance(usage, dict):
        if "promptTokenCount" in usage:
            out["input_tokens"] = usage["promptTokenCount"]
        elif "input_tokens" in usage:
            out["input_tokens"] = usage["input_tokens"]
        if "candidatesTokenCount" in usage:
            out["output_tokens"] = usage["candidatesTokenCount"]
        elif "output_tokens" in usage:
            out["output_tokens"] = usage["output_tokens"]
        if "cachedContentTokenCount" in usage:
            out["cache_read_tokens"] = usage["cachedContentTokenCount"]

    # Status / done
    if t == "init" or t == "session_start":
        out["status"] = "🔌 Conectado a Gemini · esperando token…"
    elif t == "tool_use" or t == "function_call":
        name = evt.get("name") or evt.get("function_name") or "tool"
        out["tool_use"] = str(name)
        out["status"] = f"🔧 Usando {name}…"
    elif t in ("done", "complete", "finish", "result", "stop"):
        out["done"] = True

    # Heuristic: if there's no type but there IS a text delta, that's
    # gemini's default "content" stream — keep it.
    return out


# ─────────────────────── OpenCode ────────────────────────────────────
def parse_opencode(line: str) -> dict:
    """OpenCode `run --format json` emits raw JSON events. Schema
    varies across opencode-ai versions; defensive parser tries several
    paths."""
    try:
        evt = json.loads(line)
    except Exception:
        return _empty()

    out: dict = {}
    t = evt.get("type")

    # Model
    model = (
        evt.get("model")
        or evt.get("modelID")
        or (evt.get("session") or {}).get("model")
        or (evt.get("metadata") or {}).get("model")
    )
    if model:
        out["model"] = model

    # Text delta
    delta = (
        evt.get("delta")
        or evt.get("text")
        or evt.get("content")
        or (evt.get("part") or {}).get("text")
        or (evt.get("message") or {}).get("content")
    )
    if isinstance(delta, str) and delta:
        out["text_delta"] = delta

    # Usage — opencode reports either flat or nested
    usage = evt.get("usage") or evt.get("tokens") or {}
    if isinstance(usage, dict):
        # camelCase + snake_case + opencode-specific names
        in_t = usage.get("input") or usage.get("input_tokens") or usage.get("prompt_tokens")
        out_t = usage.get("output") or usage.get("output_tokens") or usage.get("completion_tokens")
        cache_r = usage.get("cache_read") or usage.get("cache_read_tokens")
        cache_w = usage.get("cache_write") or usage.get("cache_creation_tokens")
        if in_t is not None:
            out["input_tokens"] = in_t
        if out_t is not None:
            out["output_tokens"] = out_t
        if cache_r is not None:
            out["cache_read_tokens"] = cache_r
        if cache_w is not None:
            out["cache_creation_tokens"] = cache_w

    # Status / lifecycle
    if t in ("session.start", "message.start", "session_start"):
        out["status"] = "🔌 Conectado a OpenCode · esperando token…"
    elif t in ("tool.use", "tool_call", "tool.start"):
        name = evt.get("tool") or evt.get("name") or "tool"
        out["tool_use"] = str(name)
        out["status"] = f"🔧 Usando {name}…"
    elif t in ("message.complete", "message.end", "session.end", "done"):
        out["done"] = True
    elif t == "error":
        out["status"] = f"⚠️ {evt.get('message') or evt.get('error') or 'error'}"

    return out


# ─────────────────────── Dispatcher ──────────────────────────────────
PARSERS: dict[str, Callable[[str], dict]] = {
    "claude": parse_claude,
    "codex": parse_codex,
    "gemini": parse_gemini,
    "opencode": parse_opencode,
}


def parser_for(cli: str) -> Optional[Callable[[str], dict]]:
    """Returns the parse function for the given CLI binary name
    (`claude`/`codex`/`gemini`/`opencode`), or None for unknown."""
    return PARSERS.get(cli)
