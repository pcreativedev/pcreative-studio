"""onboarding_wizard.py — Asistente de configuración inicial (primer arranque).

Wizard de bienvenida en varios pasos:
  1. Bienvenida
  2. Dependencias (Node/git/CLIs) — botón al instalador
  3. Credenciales IA (embed CredentialsWidget)
  4. Defaults del formulario (stack/provider/tipo)
  5. Listo

Se muestra automáticamente la 1ª vez (ver `maybe_run_onboarding`). Persiste
el flag + los defaults en app_prefs. También se puede reabrir desde Settings.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QPushButton, QComboBox,
    QFormLayout, QHBoxLayout,
)

import app_prefs
import ai_providers as aip
from stacks import STACKS, TEMPLATE_TYPES
from credentials_panel import CredentialsWidget


class OnboardingWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ThemeForge — Configuración inicial")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(720, 560)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)

        # Widgets que leeremos al terminar.
        self._stack_combo: QComboBox | None = None
        self._provider_combo: QComboBox | None = None
        self._type_combo: QComboBox | None = None

        self.addPage(self._welcome_page())
        self.addPage(self._deps_page())
        self.addPage(self._creds_page())
        self.addPage(self._defaults_page())
        self.addPage(self._finish_page())

        self.finished.connect(self._on_finished)

    # ── Página 1: bienvenida ────────────────────────────────────────────
    def _welcome_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Bienvenido a ThemeForge")
        page.setSubTitle("Vamos a dejar todo listo en unos pasos.")
        lay = QVBoxLayout(page)
        lbl = QLabel(
            "ThemeForge forja plantillas web premium con agentes de IA.\n\n"
            "Este asistente te ayudará a:\n"
            "  1.  Instalar las dependencias que falten (Node, git, CLIs).\n"
            "  2.  Configurar las credenciales de tu proveedor de IA.\n"
            "  3.  Elegir tus valores por defecto al crear proyectos.\n\n"
            "Puedes saltarte cualquier paso y configurarlo luego desde "
            "Settings. Pulsa «Siguiente» para empezar."
        )
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        lay.addStretch()
        return page

    # ── Página 2: dependencias ──────────────────────────────────────────
    def _deps_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Dependencias")
        page.setSubTitle("Herramientas externas que ThemeForge necesita.")
        lay = QVBoxLayout(page)

        self._deps_status = QLabel("…")
        self._deps_status.setWordWrap(True)
        self._deps_status.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(self._deps_status)

        btn = QPushButton("🔧 Abrir instalador de dependencias")
        btn.clicked.connect(self._open_dep_wizard)
        lay.addWidget(btn)
        lay.addStretch()

        # Refrescar el estado cada vez que se entra a la página.
        page.initializePage = self._refresh_deps_status  # type: ignore
        return page

    def _refresh_deps_status(self):
        try:
            import dependency_setup as ds
            missing = ds.detect_missing()
            present = ds.detect_present()
            if not missing:
                self._deps_status.setText(
                    "✅ Todas las dependencias detectadas. Puedes continuar."
                )
            else:
                names = ", ".join(t.name for t in missing)
                req = [t.name for t in missing if t.required]
                msg = f"⬇️ Faltan: <b>{names}</b>.<br>"
                if req:
                    msg += (f"<span style='color:#e06c75'>Requeridas: "
                            f"{', '.join(req)}</span> — necesarias para que la "
                            "app funcione.<br>")
                msg += (f"<small style='color:#9aa'>Instaladas: "
                        f"{', '.join(t.name for t in present) or '—'}</small>")
                self._deps_status.setText(msg)
        except Exception as e:
            self._deps_status.setText(f"No se pudo comprobar: {e}")

    def _open_dep_wizard(self):
        try:
            from dependency_wizard import DependencyWizard
            DependencyWizard(self).exec()
            self._refresh_deps_status()
        except Exception as e:
            self._deps_status.setText(f"Error abriendo el instalador: {e}")

    # ── Página 3: credenciales ──────────────────────────────────────────
    def _creds_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Credenciales de IA")
        page.setSubTitle("Conecta al menos un proveedor para que el agente trabaje.")
        lay = QVBoxLayout(page)
        self._creds = CredentialsWidget()
        lay.addWidget(self._creds)
        from PyQt6.QtWidgets import QLabel as _QLabel
        market_hint = _QLabel(
            "<div style='padding:10px 12px; background:#1e3a4f; "
            "border:1px solid #3b82f6; border-radius:6px; color:#bfdbfe;'>"
            "💡 <b>Pestaña «Market»</b> — análisis de mercado con IA (Gemini 2.5 Pro por defecto).<br>"
            "Requiere <b>OPENROUTER_API_KEY</b> (gratis crearla en "
            "<a href='https://openrouter.ai/keys' style='color:#93c5fd;'>openrouter.ai/keys</a>). "
            "Sin esa key la pestaña queda inactiva — el resto de ThemeForge funciona igual.</div>"
        )
        market_hint.setOpenExternalLinks(True)
        market_hint.setWordWrap(True)
        lay.addWidget(market_hint)
        return page

    # ── Página 4: defaults ──────────────────────────────────────────────
    def _defaults_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Valores por defecto")
        page.setSubTitle("Se pre-seleccionarán al crear un proyecto nuevo.")
        form = QFormLayout(page)

        self._stack_combo = QComboBox()
        for key, s in STACKS.items():
            if key == "none":
                continue
            self._stack_combo.addItem(f"{s['name']}  —  {s['category']}", key)
        self._select_data(self._stack_combo, app_prefs.default_stack())

        self._provider_combo = QComboBox()
        for key, p in aip.PROVIDERS.items():
            self._provider_combo.addItem(p["name"], key)
        self._select_data(self._provider_combo, app_prefs.default_provider())

        self._type_combo = QComboBox()
        for t in TEMPLATE_TYPES:
            self._type_combo.addItem(t)
        dt = app_prefs.default_type()
        if dt:
            idx = self._type_combo.findText(dt)
            if idx >= 0:
                self._type_combo.setCurrentIndex(idx)

        form.addRow("Stack por defecto:", self._stack_combo)
        form.addRow("Proveedor de IA:", self._provider_combo)
        form.addRow("Tipo de plantilla:", self._type_combo)
        return page

    @staticmethod
    def _select_data(combo: QComboBox, data: str):
        idx = combo.findData(data)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    # ── Página 5: listo ─────────────────────────────────────────────────
    def _finish_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("¡Listo!")
        page.setSubTitle("Ya puedes empezar a forjar plantillas.")
        lay = QVBoxLayout(page)
        lbl = QLabel(
            "Configuración guardada.\n\n"
            "Puedes volver a abrir este asistente o ajustar credenciales y "
            "dependencias en cualquier momento desde la pestaña <b>Settings</b>.\n\n"
            "Pulsa «Finalizar» para entrar en ThemeForge."
        )
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        lay.addStretch()
        return page

    # ── Al terminar ─────────────────────────────────────────────────────
    def _on_finished(self, result):
        # Guardar defaults (aunque cancele, no pasa nada; solo si completó).
        try:
            if self._stack_combo and self._provider_combo and self._type_combo:
                app_prefs.set_defaults(
                    stack=self._stack_combo.currentData(),
                    provider=self._provider_combo.currentData(),
                    type_=self._type_combo.currentText(),
                )
        except Exception:
            pass
        # Marcar onboarding hecho en cualquier caso (no re-mostrar cada arranque).
        app_prefs.mark_onboarding_done()


def maybe_run_onboarding(parent=None) -> bool:
    """Muestra el wizard si el onboarding no se ha completado nunca.
    Devuelve True si lo mostró. Llamado desde main() al primer arranque."""
    if app_prefs.onboarding_done():
        return False
    OnboardingWizard(parent).exec()
    return True
