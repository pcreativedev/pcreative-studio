"""credentials_panel.py — Widget reutilizable de gestión de credenciales IA.

Muestra los providers con su estado (detect_status de ai_providers) y
acciones contextuales: instalar el CLI, login OAuth, añadir/cambiar/quitar
API key. Toda la lógica vive en ai_providers.py; esto es solo la UI.

Se usa en dos sitios:
  - Paso "Credenciales" del onboarding wizard (onboarding_wizard.py).
  - Sección "🔑 AI credentials" del panel de Settings.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QInputDialog, QLineEdit, QMessageBox,
)

import ai_providers as aip
import platform_compat as pc

# Icono por estado de detect_status.
_STATE_ICON = {
    "ok": "🟢",
    "need_login": "🟡",
    "need_key": "⚪",
    "missing_cli": "🔴",
}


class CredentialsWidget(QWidget):
    """Tabla de providers IA con estado + acciones de credenciales."""

    changed = pyqtSignal()  # emitido cuando algo cambia (login/key)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._rows: dict[str, dict] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        hint = QLabel(
            "Estado de cada proveedor de IA. <b>OAuth</b> abre el login en una "
            "terminal (sigue las instrucciones en pantalla); <b>API key</b> se "
            "guarda cifrada en <code>keys.json</code> (chmod 0600)."
        )
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setWordWrap(True)
        root.addWidget(hint)

        for key in aip.PROVIDERS:
            row = self._build_row(key)
            root.addWidget(row)

        # Integraciones (no-IA): token de Figma para el MCP figma-context.
        root.addWidget(self._build_figma_row())

        btns = QHBoxLayout()
        btns.addStretch()
        self._btn_refresh = QPushButton("🔄 Re-detectar")
        self._btn_refresh.clicked.connect(self.refresh)
        btns.addWidget(self._btn_refresh)
        root.addLayout(btns)

        self.refresh()

    def _build_row(self, key: str) -> QFrame:
        p = aip.PROVIDERS[key]
        frame = QFrame()
        frame.setStyleSheet("QFrame { border-bottom: 1px solid #2a2a33; }")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(4, 4, 4, 4)

        status = QLabel("…")
        status.setTextFormat(Qt.TextFormat.RichText)
        status.setWordWrap(True)
        lay.addWidget(status, 1)

        # Botones de acción (se muestran/ocultan según estado en refresh()).
        btn_install = QPushButton("⬇️ Instalar CLI")
        btn_login = QPushButton("🔓 Login")
        btn_addkey = QPushButton("🔑 Añadir key")
        btn_editkey = QPushButton("✏️ Cambiar key")
        btn_logout = QPushButton("🚪 Quitar key")
        btn_install.clicked.connect(lambda _=False, k=key: self._install_cli(k))
        btn_login.clicked.connect(lambda _=False, k=key: self._login(k))
        btn_addkey.clicked.connect(lambda _=False, k=key: self._add_key(k))
        btn_editkey.clicked.connect(lambda _=False, k=key: self._add_key(k))
        btn_logout.clicked.connect(lambda _=False, k=key: self._remove_key(k))
        for b in (btn_install, btn_login, btn_addkey, btn_editkey, btn_logout):
            lay.addWidget(b)

        self._rows[key] = {
            "status": status, "install": btn_install, "login": btn_login,
            "addkey": btn_addkey, "editkey": btn_editkey, "logout": btn_logout,
        }
        return frame

    # ── Estado ──────────────────────────────────────────────────────────
    def refresh(self):
        for key, w in self._rows.items():
            p = aip.PROVIDERS[key]
            try:
                state, info = aip.detect_status(key)
            except Exception as e:
                state, info = "missing_cli", f"error: {e}"
            icon = _STATE_ICON.get(state, "⚪")
            w["status"].setText(
                f"{icon} <b>{p['name']}</b><br>"
                f"<small style='color:#9aa'>{info}</small>"
            )
            is_api = p.get("auth_kind") in ("api", "oauth_or_api") and p.get("key_id")
            # Visibilidad de botones según estado.
            w["install"].setVisible(state == "missing_cli")
            w["login"].setVisible(state in ("need_login",) or
                                   (state == "ok" and p.get("auth_kind") in ("oauth", "oauth_or_api")
                                    and p.get("login_argv") is not None))
            w["login"].setText("🔓 Login" if state != "ok" else "🔁 Re-login")
            w["addkey"].setVisible(state == "need_key" and bool(is_api))
            w["editkey"].setVisible(state == "ok" and bool(is_api))
            w["logout"].setVisible(state == "ok" and bool(is_api))

        # Estado del token de Figma (integración MCP, no provider de IA).
        if hasattr(self, "_figma_status"):
            try:
                has_figma = bool(aip.load_keys().get("figma"))
            except Exception:
                has_figma = False
            self._figma_status.setText(
                ("🟢" if has_figma else "⚪")
                + " <b>Figma</b> <small>(token para el MCP figma-context)</small><br>"
                + "<small style='color:#9aa'>"
                + ("token guardado — el agente puede leer/importar tus diseños de Figma"
                   if has_figma else
                   "sin token — añádelo para importar/leer diseños de Figma")
                + "</small>"
            )
            self._figma_set.setText("✏️ Cambiar token" if has_figma else "🔑 Añadir token")
            self._figma_clear.setVisible(has_figma)

    # ── Acciones ────────────────────────────────────────────────────────
    def _install_cli(self, key: str):
        """Abre el wizard de dependencias para instalar el CLI faltante."""
        try:
            from dependency_wizard import DependencyWizard
            DependencyWizard(self).exec()
            self.refresh()
            self.changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Instalar CLI", f"Error: {e}")

    def _login(self, key: str):
        """Lanza el login OAuth del provider en una terminal (interactivo)."""
        argv = aip.login_argv(key)
        if not argv:
            QMessageBox.information(self, "Login", "Este provider no usa login OAuth.")
            return
        cmd = " ".join(argv)
        try:
            pc.open_in_terminal(str(pc.app_config_dir()), command=cmd, hold=True)
            QMessageBox.information(
                self, "Login",
                f"Se abrió una terminal ejecutando:\n  {cmd}\n\n"
                "Completa el login ahí (puede abrir el navegador) y luego pulsa "
                "🔄 Re-detectar.",
            )
        except Exception as e:
            QMessageBox.warning(self, "Login", f"No se pudo abrir la terminal: {e}\n\n"
                                               f"Ejecuta manualmente: {cmd}")

    def _add_key(self, key: str):
        """Pide la API key y la guarda cifrada."""
        p = aip.PROVIDERS[key]
        key_id = p.get("key_id")
        if not key_id:
            return
        text, ok = QInputDialog.getText(
            self, f"API key — {p['name']}",
            f"Pega tu {p.get('env_var', 'API key')}:",
            echo=QLineEdit.EchoMode.Password,
        )
        if ok and text.strip():
            try:
                aip.save_key(key_id, text.strip())
                # Algunos CLIs (Codex) necesitan un paso extra tras guardar la key.
                post = p.get("post_key_argv")
                if post and pc.IS_LINUX:  # solo informamos; el login real lo hace el user
                    pass
                self.refresh()
                self.changed.emit()
                QMessageBox.information(self, "API key", "Key guardada (chmod 0600).")
            except Exception as e:
                QMessageBox.warning(self, "API key", f"Error guardando: {e}")

    def _remove_key(self, key: str):
        p = aip.PROVIDERS[key]
        key_id = p.get("key_id")
        if not key_id:
            return
        r = QMessageBox.question(self, "Quitar key",
                                 f"¿Quitar la API key de {p['name']}?")
        if r == QMessageBox.StandardButton.Yes:
            try:
                aip.delete_key(key_id)
                self.refresh()
                self.changed.emit()
            except Exception as e:
                QMessageBox.warning(self, "Quitar key", f"Error: {e}")

    # ── Integración Figma (token MCP) ────────────────────────────────────
    def _build_figma_row(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { border-top: 1px solid #2a2a33; }")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(4, 8, 4, 4)
        self._figma_status = QLabel("…")
        self._figma_status.setTextFormat(Qt.TextFormat.RichText)
        self._figma_status.setWordWrap(True)
        lay.addWidget(self._figma_status, 1)
        self._figma_set = QPushButton("🔑 Añadir token")
        self._figma_set.clicked.connect(self._set_figma_key)
        self._figma_clear = QPushButton("🚪 Quitar")
        self._figma_clear.clicked.connect(self._remove_figma_key)
        lay.addWidget(self._figma_set)
        lay.addWidget(self._figma_clear)
        return frame

    def _set_figma_key(self):
        import os
        text, ok = QInputDialog.getText(
            self, "Token de Figma",
            "Pega tu Figma Personal Access Token\n"
            "(figma.com → Settings → Security → Personal access tokens, scope lectura):",
            echo=QLineEdit.EchoMode.Password,
        )
        if ok and text.strip():
            try:
                aip.save_key("figma", text.strip())
                os.environ["FIGMA_API_KEY"] = text.strip()  # disponible ya en esta sesión
                self.refresh()
                self.changed.emit()
                QMessageBox.information(
                    self, "Figma",
                    "Token guardado (chmod 0600). El MCP de Figma ya puede leer "
                    "tus diseños. Copia el link de un frame en Figma (clic derecho "
                    "→ Copy link to selection) y pídeselo al agente.")
            except Exception as e:
                QMessageBox.warning(self, "Figma", f"Error guardando: {e}")

    def _remove_figma_key(self):
        import os
        r = QMessageBox.question(self, "Quitar token", "¿Quitar el token de Figma?")
        if r == QMessageBox.StandardButton.Yes:
            try:
                aip.delete_key("figma")
                os.environ.pop("FIGMA_API_KEY", None)
                self.refresh()
                self.changed.emit()
            except Exception as e:
                QMessageBox.warning(self, "Figma", f"Error: {e}")
