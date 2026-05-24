"""dependency_wizard.py — Diálogo de setup de dependencias.

Muestra qué herramientas están instaladas y cuáles faltan, deja al usuario
elegir cuáles instalar, y ejecuta el plan con QProcess mostrando el log en
vivo. Cross-platform: usa winget (Win) / brew (Mac) / paru·pacman·apt·dnf
(Linux) para tools nativas y `npm install -g` para los CLIs de IA.

Se abre automáticamente en el primer arranque si faltan tools requeridas
(ver `maybe_run_first_run_setup`), y manualmente desde Settings.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QPlainTextEdit, QScrollArea, QWidget, QFrame, QMessageBox,
)

import dependency_setup as ds
import platform_compat as pc


class DependencyWizard(QDialog):
    """Detecta + instala las herramientas externas de ThemeForge."""

    def __init__(self, parent=None, only_missing: bool = True):
        super().__init__(parent)
        self.setWindowTitle("ThemeForge — Setup de dependencias")
        self.setMinimumSize(640, 560)

        self._checks: dict[str, QCheckBox] = {}
        self._steps: list[ds.InstallStep] = []
        self._step_idx = 0
        self._proc: QProcess | None = None

        root = QVBoxLayout(self)

        # Cabecera
        title = QLabel("🔧 Dependencias de ThemeForge")
        f = QFont(); f.setPointSize(15); f.setBold(True)
        title.setFont(f)
        root.addWidget(title)

        pm = ds.native_package_manager()
        pm_label = pm[0] if pm else "ninguno detectado"
        sub = QLabel(
            f"Plataforma: <b>{pc.platform_label()}</b> · "
            f"Gestor de paquetes: <b>{pm_label}</b><br>"
            "Marca lo que quieras instalar y pulsa <b>Instalar seleccionadas</b>. "
            "Node.js y git son necesarios para que la app funcione."
        )
        sub.setTextFormat(Qt.TextFormat.RichText)
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Lista de herramientas con estado + checkbox
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        self._list_lay = QVBoxLayout(inner)
        self._list_lay.setSpacing(4)

        # Agrupar por categoría: Core (imprescindible) · IA (agentes) ·
        # Stacks (runtimes que solo necesitas si usas ese stack). Las stack
        # tools van DESmarcadas por defecto (se instalan a demanda).
        cat_titles = {
            "core":  "🔧 Imprescindibles (Node, git)",
            "ai":    "🤖 Agentes de IA",
            "stack": "📦 Runtimes de stacks (instala solo el que vayas a usar)",
        }
        for cat in ("core", "ai", "stack"):
            tools = [t for t in ds.TOOLS if t.category == cat]
            if not tools:
                continue
            header = QLabel(cat_titles.get(cat, cat))
            header.setStyleSheet("font-weight:bold; color:#7aa2f7; margin-top:8px;")
            self._list_lay.addWidget(header)

            for tool in tools:
                installed = ds.is_installed(tool)
                row = QFrame()
                row_lay = QHBoxLayout(row)
                row_lay.setContentsMargins(16, 2, 6, 2)

                cb = QCheckBox()
                # Marcar lo que falta, SALVO los runtimes de stack (a demanda).
                cb.setChecked(not installed and cat != "stack")
                cb.setEnabled(not installed)
                self._checks[tool.key] = cb
                row_lay.addWidget(cb)

                status = "✅" if installed else "⬇️"
                req = " <span style='color:#e06c75'>(requerido)</span>" if tool.required else ""
                txt = QLabel(
                    f"{status} <b>{tool.name}</b>{req}<br>"
                    f"<small style='color:#888'>{tool.description}</small>"
                )
                txt.setTextFormat(Qt.TextFormat.RichText)
                txt.setWordWrap(True)
                row_lay.addWidget(txt, 1)
                self._list_lay.addWidget(row)

        self._list_lay.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        # Log de instalación
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(160)
        self._log.setStyleSheet(
            "font-family: monospace; font-size: 11px; "
            "background: #1a1a1a; color: #ccc;"
        )
        self._log.setPlaceholderText("El progreso de la instalación aparecerá aquí…")
        root.addWidget(self._log)

        # Botones
        btns = QHBoxLayout()
        self._btn_refresh = QPushButton("🔄 Re-detectar")
        self._btn_refresh.clicked.connect(self._refresh)
        btns.addWidget(self._btn_refresh)
        btns.addStretch()
        self._btn_close = QPushButton("Cerrar")
        self._btn_close.clicked.connect(self.reject)
        btns.addWidget(self._btn_close)
        self._btn_install = QPushButton("⬇️ Instalar seleccionadas")
        self._btn_install.setDefault(True)
        self._btn_install.clicked.connect(self._start_install)
        btns.addWidget(self._btn_install)
        root.addLayout(btns)

        self._update_install_enabled()

    # ── Helpers ─────────────────────────────────────────────────────────
    def _selected_tools(self) -> list[ds.Tool]:
        return [t for t in ds.TOOLS
                if self._checks[t.key].isChecked() and self._checks[t.key].isEnabled()]

    def _update_install_enabled(self):
        self._btn_install.setEnabled(bool(self._selected_tools()))

    def _refresh(self):
        """Re-evalúa qué hay instalado y reconstruye el diálogo."""
        new = DependencyWizard(self.parent())
        new.show()
        self.close()

    def _log_line(self, text: str):
        self._log.appendPlainText(text)
        self._log.verticalScrollBar().setValue(
            self._log.verticalScrollBar().maximum()
        )

    # ── Instalación secuencial ──────────────────────────────────────────
    def _start_install(self):
        tools = self._selected_tools()
        if not tools:
            return
        steps, warnings = ds.install_plan(tools)
        for w in warnings:
            self._log_line(f"⚠  {w}")
        if not steps:
            QMessageBox.information(
                self, "Setup",
                "No hay nada que instalar automáticamente en esta plataforma.\n"
                "Revisa los avisos del log."
            )
            return

        self._steps = steps
        self._step_idx = 0
        self._btn_install.setEnabled(False)
        self._btn_refresh.setEnabled(False)
        self._btn_close.setEnabled(False)
        self._log_line(f"▶ Plan: {len(steps)} paso(s). Empezando…\n")
        self._run_next_step()

    def _run_next_step(self):
        if self._step_idx >= len(self._steps):
            self._log_line("\n✅ Instalación completada. Pulsa 🔄 Re-detectar para verificar.")
            self._btn_refresh.setEnabled(True)
            self._btn_close.setEnabled(True)
            self._btn_install.setEnabled(True)
            QMessageBox.information(
                self, "Setup",
                "Instalación terminada.\n\n"
                "Puede que tengas que reiniciar ThemeForge (o abrir una "
                "terminal nueva) para que el PATH actualizado se vea."
            )
            return

        step = self._steps[self._step_idx]
        self._log_line(f"── {step.label}")
        self._log_line(f"   $ {' '.join(step.argv)}")

        self._proc = QProcess(self)
        self._proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._proc.readyReadStandardOutput.connect(self._on_proc_output)
        self._proc.finished.connect(self._on_step_finished)
        self._proc.errorOccurred.connect(self._on_proc_error)

        program = step.argv[0]
        args = step.argv[1:]
        self._proc.start(program, args)

    def _on_proc_output(self):
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardOutput()).decode(errors="replace")
        for line in data.splitlines():
            if line.strip():
                self._log_line(f"   {line}")

    def _on_step_finished(self, code: int, _status):
        step = self._steps[self._step_idx]
        if code == 0:
            self._log_line(f"   ✓ {step.label.replace('Instalando ', '').rstrip('…')} OK\n")
            # Tras instalar algo (sobre todo Node), refrescar el PATH desde
            # el registro para que los siguientes pasos npm vean los nuevos
            # binarios sin tener que reiniciar la app.
            self._refresh_windows_path()
        else:
            self._log_line(f"   ✗ falló (exit {code}) — continúo con el resto\n")
        self._step_idx += 1
        self._run_next_step()

    def _refresh_windows_path(self):
        """Relee PATH de HKLM + HKCU y lo aplica a os.environ para que los
        QProcess siguientes hereden los binarios recién instalados."""
        if not pc.IS_WINDOWS:
            return
        try:
            import winreg, os
            parts = []
            for hive, sub in (
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                (winreg.HKEY_CURRENT_USER, r"Environment"),
            ):
                try:
                    with winreg.OpenKey(hive, sub) as k:
                        parts.append(str(winreg.QueryValueEx(k, "Path")[0]))
                except OSError:
                    pass
            if parts:
                merged = ";".join(parts)
                cur = os.environ.get("PATH", "")
                os.environ["PATH"] = merged + (";" + cur if cur else "")
        except Exception:
            pass

    def _on_proc_error(self, _err):
        self._log_line("   ✗ no se pudo ejecutar el comando "
                       "(¿gestor de paquetes no instalado?)\n")


def maybe_run_first_run_setup(parent=None) -> bool:
    """Si faltan herramientas REQUERIDAS (Node/git), abre el wizard de
    forma modal antes de entrar a la app. Devuelve True si lo mostró.

    Se llama desde `main()`. No persiste flags: si todo lo requerido está,
    no molesta; si falta, conviene resolverlo siempre.
    """
    missing_required = ds.detect_missing(only_required=True)
    if not missing_required:
        return False
    dlg = DependencyWizard(parent)
    dlg.exec()
    return True
