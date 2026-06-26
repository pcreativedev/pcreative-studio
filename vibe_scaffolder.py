"""Vibe scaffolder — natural-language → form pre-fill.

The user describes what they want to build in plain Spanish/English
(e.g. "landing premium para clínica dental en Madrid, paleta cálida").
A small structured-output prompt asks the active AI provider to
return a JSON object that maps onto the Pcreative Studio project form:

  {
    "stack_key": "astro-tailwind",
    "template_type": "Landing Page",
    "run_autoskills": true,
    "run_uipro": true,
    "theme_hint": "soft-ui",
    "dev_prompt": "<polished 200-word brief for the dev agent>",
    "reasoning": "<2-3 sentences why>"
  }

The form auto-populates with the proposal. The dev_prompt feeds the
existing `ai_analysis` injection path so it lands inside the
generated CLAUDE.md / AGENTS.md as the agent's initial brief.

Streaming output is shown in a small live-preview dialog while the
AI runs (reuses the `stream_parsers` infrastructure).
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field

from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QVBoxLayout,
)

import ai_providers as aip
import stream_parsers as sp


# ─────────────────── Data model ─────────────────────────────────────
@dataclass
class VibeProposal:
    stack_key: str = "none"
    template_type: str = "Landing Page"
    run_autoskills: bool = True
    run_uipro: bool = True
    theme_hint: str = ""
    dev_prompt: str = ""
    reasoning: str = ""

    def is_valid(self) -> bool:
        return bool(self.stack_key) and bool(self.dev_prompt)


# ─────────────────── Prompt construction ────────────────────────────
def build_vibe_prompt(user_desc: str,
                      stacks: dict,
                      template_types: list[str],
                      builtin_themes: list[str]) -> str:
    """Builds the structured-output prompt sent to the agent.

    `stacks` is the dict mirror of `stacks.STACKS` (key → metadata).
    """
    # Compact stack catalog
    stack_lines = []
    for key, s in stacks.items():
        if key == "none":
            continue
        cat = s.get("category", "")
        name = s.get("name", key)
        stack_lines.append(f"  - {key}: {name} ({cat})")
    stack_list = "\n".join(stack_lines)

    # Template types (drop placeholder)
    type_list = "\n".join(
        f"  - {t}" for t in template_types if not t.startswith("(")
    )

    themes_list = ", ".join(builtin_themes)

    user_desc = user_desc.strip().replace('"""', "'")

    return f"""You are a senior product designer + fullstack engineer helping a
template author scaffold a new project for ThemeForest / CodeCanyon /
Creative Market / Gumroad.

USER DESCRIPTION (in their own words):
\"\"\"
{user_desc}
\"\"\"

AVAILABLE STACKS (must pick exactly one of these keys):
{stack_list}

AVAILABLE TEMPLATE TYPES (must pick exactly one of these):
{type_list}

AVAILABLE BUILTIN THEMES (must pick exactly one of these):
{themes_list}

DECISION RULES (apply in order):

1. If user mentions WordPress / WP → stack must be wordpress-block or
   wordpress-plugin.
2. If user mentions Shopify → stack must be shopify-liquid.
3. If user mentions Laravel / PHP backend → laravel-tailwind.
4. If user mentions mobile / app → flutter or expo-rn-router.
5. If user mentions landing / marketing / one-page → astro-tailwind
   (best perf) or nextjs-tailwind (if dynamic).
6. If user mentions admin / dashboard / SaaS app → nextjs-tailwind.
7. If user mentions portfolio / agency → astro-tailwind or
   nextjs-tailwind.
8. If user mentions e-commerce → shopify-liquid (Shopify) or
   wordpress-block (WooCommerce).
9. If user mentions blog / magazine → astro-tailwind (static fast).
10. Otherwise → nextjs-tailwind (safe default).

THEME RULES (pick by user's mood/niche):

- premium / luxury / wellness / spa / boutique → soft-ui
- tech / SaaS / productivity / developer → linear
- creative / portfolio / agency / artistic → dracula or brutalism
- editorial / magazine / fashion → brutalism (raw aesthetic)
- gaming / cyber / dark / hacker → tokyo-night
- corporate / clean / minimal → themeforge-light
- general / unknown → themeforge-dark

OUTPUT FORMAT — Return ONLY a single JSON object exactly matching this
shape, with no markdown fence, no prose before or after:

{{
  "stack_key": "<one of the available stack keys above>",
  "template_type": "<one of the available template types>",
  "run_autoskills": true,
  "run_uipro": true,
  "theme_hint": "<one of the available builtin themes>",
  "dev_prompt": "<150-300 word brief for the dev agent. Structure: 1) niche/audience, 2) tone & aesthetic, 3) must-have sections / pages, 4) design constraints (responsive 360-1920, WCAG AA, prefers-reduced-motion), 5) tech requirements per the chosen stack. Write in Spanish if the user wrote in Spanish, otherwise in English. End with: 'Hazlo de una sentada, sin pedir confirmación entre secciones.'>",
  "reasoning": "<2-3 sentences in the user's language explaining why you picked this stack and theme>"
}}

CRITICAL: stack_key must be EXACTLY one of the keys listed above
(case-sensitive). theme_hint must be EXACTLY one of the listed
themes. template_type must be a literal string match.
"""


# ─────────────────── Response parser ────────────────────────────────
def parse_vibe_response(raw: str) -> tuple[VibeProposal | None, str]:
    """Robustly parses the AI response. Returns (proposal, error_msg)."""
    if not raw or not raw.strip():
        return None, "respuesta vacía"

    text = raw.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Find first {...} block (greedy to last })
    m = re.search(r"\{[\s\S]+\}", text)
    if not m:
        return None, "no se encontró bloque JSON"

    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        # Attempt: trim everything after the LAST balanced }
        try:
            # Manual balance scan
            depth = 0
            end = 0
            start = m.start()
            for i, ch in enumerate(text[start:], start=start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > start:
                data = json.loads(text[start:end])
            else:
                return None, f"JSON malformado: {e}"
        except Exception as e2:
            return None, f"JSON malformado: {e2}"

    if not isinstance(data, dict):
        return None, "el JSON no es un objeto"

    p = VibeProposal(
        stack_key=str(data.get("stack_key", "")).strip(),
        template_type=str(data.get("template_type", "Landing Page")).strip(),
        run_autoskills=bool(data.get("run_autoskills", True)),
        run_uipro=bool(data.get("run_uipro", True)),
        theme_hint=str(data.get("theme_hint", "")).strip(),
        dev_prompt=str(data.get("dev_prompt", "")).strip(),
        reasoning=str(data.get("reasoning", "")).strip(),
    )
    if not p.stack_key:
        return None, "stack_key vacío en la respuesta"
    if not p.dev_prompt:
        return None, "dev_prompt vacío en la respuesta"
    return p, ""


# ─────────────────── Dialog ─────────────────────────────────────────
class VibeDialog(QDialog):
    """Modal that runs the agent with the structured prompt and shows
    streaming output. On completion, parses the JSON, displays a
    preview, and lets the user Apply or Discard.

    Result: `self.proposal` is set to the VibeProposal on Accepted.
    """

    def __init__(self, parent, user_desc: str, agent_key: str,
                 stacks: dict, template_types: list[str],
                 builtin_themes: list[str]):
        super().__init__(parent)
        self.setWindowTitle("✨ Vibe scaffolder — generando propuesta")
        self.resize(820, 640)

        self.proposal: VibeProposal | None = None
        self.create_now = False  # True si el user pulsa "🚀 Crear proyecto ya"
        self._buf = ""
        self._stdout_buffer = ""
        self._parser = sp.parser_for(aip.PROVIDERS[agent_key]["command"])
        self._agent_key = agent_key
        self._t0 = 0.0

        # ── Header ──────────────────────────────────────────────────
        title = QLabel(f"<b>Pidiendo a {aip.PROVIDERS[agent_key]['short']}</b> "
                       f"una propuesta de stack + theme + dev prompt.")
        title.setWordWrap(True)

        # Show what we asked
        user_summary = QLabel(f"<i>{user_desc}</i>")
        user_summary.setWordWrap(True)
        user_summary.setStyleSheet("color: #aaa; padding: 4px 0;")

        # ── Streaming output ────────────────────────────────────────
        self.out = QPlainTextEdit()
        self.out.setReadOnly(True)
        self.out.setFont(QFont("monospace", 10))
        self.out.setPlaceholderText("La respuesta llegará aquí en streaming…")
        self.out.setMinimumHeight(280)

        self.status_lbl = QLabel("⏳ Lanzando agente…")
        self.tokens_lbl = QLabel("")
        self.tokens_lbl.setStyleSheet("color: #888; font-family: monospace;")
        status_row = QHBoxLayout()
        status_row.addWidget(self.status_lbl)
        status_row.addStretch()
        status_row.addWidget(self.tokens_lbl)

        # ── Preview pane (filled after parse) ───────────────────────
        self.preview_lbl = QLabel("")
        self.preview_lbl.setWordWrap(True)
        self.preview_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.preview_lbl.setStyleSheet(
            "background: #1e2a40; padding: 10px; border-radius: 6px; "
            "color: #e6e6e6;"
        )
        self.preview_lbl.hide()

        # ── Buttons ─────────────────────────────────────────────────
        self.bb = QDialogButtonBox()
        self.btn_apply = self.bb.addButton("✨ Aplicar al form",
                                           QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_apply.setEnabled(False)
        self.btn_create = self.bb.addButton("🚀 Crear proyecto ya",
                                            QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_create.setEnabled(False)
        self.btn_create.setToolTip(
            "Aplica la propuesta y crea el proyecto directamente en modo "
            "'from scratch', sin volver al formulario."
        )
        self.btn_cancel = self.bb.addButton("Cancelar",
                                             QDialogButtonBox.ButtonRole.RejectRole)
        self.btn_apply.clicked.connect(self.accept)
        self.btn_create.clicked.connect(self._accept_create)
        self.btn_cancel.clicked.connect(self._cancel)

        # ── Layout ──────────────────────────────────────────────────
        root = QVBoxLayout(self)
        root.addWidget(title)
        root.addWidget(user_summary)
        root.addWidget(self.out, 1)
        root.addLayout(status_row)
        root.addWidget(self.preview_lbl)
        root.addWidget(self.bb)

        # ── Run agent ───────────────────────────────────────────────
        prompt = build_vibe_prompt(user_desc, stacks, template_types, builtin_themes)
        self._launch(prompt)

    # ── Process management ──────────────────────────────────────────
    def _launch(self, prompt: str):
        import shlex
        argv = aip.oneshot_argv(self._agent_key, allow_web=False)
        cmd_str = " ".join(shlex.quote(a) for a in argv)
        extra_env = aip.get_env(self._agent_key)

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        if extra_env:
            from PyQt6.QtCore import QProcessEnvironment
            env = QProcessEnvironment.systemEnvironment()
            for k, v in extra_env.items():
                env.insert(k, v)
            self.proc.setProcessEnvironment(env)

        self.proc.readyReadStandardOutput.connect(self._on_output)
        self.proc.finished.connect(self._on_finished)
        self.proc.errorOccurred.connect(
            lambda e: self.status_lbl.setText(f"⚠️ proc error: {e}")
        )
        self.proc.started.connect(lambda: self._on_started(prompt))

        # Run via bash so login PATH applies
        import platform_compat as pc
        sh, args = pc.shell_program_and_args(cmd_str)
        self.proc.start(sh, args)
        self._t0 = time.time()

    def _on_started(self, prompt: str):
        self.proc.write((prompt + "\n").encode("utf-8"))
        self.proc.waitForBytesWritten(3000)
        self.proc.closeWriteChannel()
        self.status_lbl.setText("⏳ Esperando respuesta…")

    def _on_output(self):
        chunk = self.proc.readAllStandardOutput().data().decode(errors="replace")
        if not chunk:
            return
        self._buf += chunk

        # If we have a stream parser, extract text deltas for nicer display
        if self._parser:
            self._stdout_buffer += chunk
            while "\n" in self._stdout_buffer:
                line, self._stdout_buffer = self._stdout_buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                evt = self._parser(line)
                if evt:
                    delta = evt.get("text_delta")
                    if delta:
                        self.out.moveCursor(self.out.textCursor().MoveOperation.End)
                        self.out.insertPlainText(delta)
                        self.out.moveCursor(self.out.textCursor().MoveOperation.End)
        else:
            self.out.moveCursor(self.out.textCursor().MoveOperation.End)
            self.out.insertPlainText(chunk)
            self.out.moveCursor(self.out.textCursor().MoveOperation.End)

    def _extract_error(self) -> str:
        """Saca el motivo real del fallo del buffer stream-json del CLI.
        Los errores de Claude Code (p.ej. modelo no disponible) llegan en el
        JSON de stdout, no en stderr — por eso antes solo se veía 'exit N'."""
        import json as _json
        msg = ""
        for line in (self._buf or "").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                obj = _json.loads(line)
            except Exception:
                continue
            # El objeto `result` final trae el texto del error si is_error.
            if obj.get("type") == "result" and obj.get("result"):
                msg = str(obj["result"])
            # O el contenido de texto del assistant.
            elif obj.get("type") == "assistant":
                for part in (obj.get("message", {}) or {}).get("content", []) or []:
                    if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                        msg = part["text"]
        # stderr como último recurso.
        if not msg and self.proc is not None:
            try:
                err = self.proc.readAllStandardError().data().decode(errors="replace").strip()
                if err:
                    msg = err
            except Exception:
                pass
        return (msg or "").strip()

    def _on_finished(self, code, _status):
        elapsed = time.time() - self._t0
        if code != 0:
            reason = self._extract_error()
            short = (reason[:160] + "…") if len(reason) > 160 else reason
            self.status_lbl.setText(
                f"❌ exit {code} ({elapsed:.1f}s)" + (f" — {short}" if short else "")
            )
            if reason:
                # Vuelca el motivo completo en el panel de salida para que se lea.
                self.out.moveCursor(self.out.textCursor().MoveOperation.End)
                self.out.insertPlainText(f"\n\n⚠️ {reason}\n")
            self.btn_cancel.setText("Cerrar")
            return

        # Parse final JSON from the full buffered output. If we used
        # stream-json we want the assistant's text content (already
        # captured into self.out via deltas). Fall back to raw buffer.
        full_text = self.out.toPlainText() or self._buf
        proposal, err = parse_vibe_response(full_text)
        if not proposal:
            self.status_lbl.setText(f"⚠️ no se pudo parsear: {err}")
            self.btn_cancel.setText("Cerrar")
            return

        self.proposal = proposal
        self.status_lbl.setText(f"✅ Propuesta lista ({elapsed:.1f}s)")
        # Build preview
        try:
            from stacks import STACKS as _S
            stack_name = _S.get(proposal.stack_key, {}).get("name", proposal.stack_key)
        except Exception:
            stack_name = proposal.stack_key
        preview_html = (
            f"<b>Propuesta:</b><br>"
            f"&nbsp;&nbsp;• <b>Stack:</b> {stack_name} "
            f"(<code>{proposal.stack_key}</code>)<br>"
            f"&nbsp;&nbsp;• <b>Tipo:</b> {proposal.template_type}<br>"
            f"&nbsp;&nbsp;• <b>Theme:</b> {proposal.theme_hint or '(sin sugerencia)'}<br>"
            f"&nbsp;&nbsp;• <b>autoskills:</b> {'✓' if proposal.run_autoskills else '✗'}  "
            f"<b>uipro:</b> {'✓' if proposal.run_uipro else '✗'}<br>"
            f"<br>"
            f"<b>Razonamiento:</b> <i>{proposal.reasoning}</i>"
        )
        self.preview_lbl.setText(preview_html)
        self.preview_lbl.show()
        self.btn_apply.setEnabled(True)
        self.btn_create.setEnabled(True)

    def _accept_create(self):
        """El user quiere crear el proyecto directamente tras el vibe."""
        self.create_now = True
        self.accept()

    def _cancel(self):
        try:
            if self.proc and self.proc.state() != QProcess.ProcessState.NotRunning:
                self.proc.kill()
        except Exception:
            pass
        self.reject()
