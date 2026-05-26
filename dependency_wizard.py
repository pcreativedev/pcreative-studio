"""dependency_wizard.py — Diálogo de setup de dependencias.

Muestra qué herramientas están instaladas y cuáles faltan, deja al usuario
elegir cuáles instalar, y ejecuta el plan con QProcess mostrando el log en
vivo. Cross-platform: usa winget (Win) / brew (Mac) / paru·pacman·apt·dnf
(Linux) para tools nativas y `npm install -g` para los CLIs de IA.

Se abre automáticamente en el primer arranque si faltan tools requeridas
(ver `maybe_run_first_run_setup`), y manualmente desde Settings.
"""
from __future__ import annotations

import shlex

from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment
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
            "operator": "🚀 Operator (opcional — Hermes para misiones autónomas)",
        }
        for cat in ("core", "ai", "stack", "operator"):
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
                # Marcar lo que falta, SALVO runtimes de stack y el Operator
                # (Hermes) — esos son opcionales / a demanda.
                cb.setChecked(not installed and cat not in ("stack", "operator"))
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

        self._btn_install.setEnabled(False)
        self._btn_refresh.setEnabled(False)
        self._btn_close.setEnabled(False)

        # Windows: si algún paso requiere admin (winget, instaladores .exe/.msi)
        # lo hacemos TODO en UNA ventana elevada (un solo UAC) lanzada con
        # ShellExecuteW("runas") — la vía Win32 estándar y fiable, DESACOPLADA
        # de Qt (no es un QProcess hijo que Qt mate al cambiar de ventana).
        # Meter winget + npm + instaladores en el mismo .ps1 (con un refresh de
        # PATH entre medias) resuelve además el orden Node→npm.
        if pc.IS_WINDOWS and any(s.elevated for s in steps):
            self._log_line(f"▶ Plan: {len(steps)} paso(s) — todo en una "
                           "ventana elevada (un solo UAC).\n")
            self._launch_windows_elevated_all(steps)
            return

        # Linux/Mac (o Windows solo-npm): QProcess directo + terminal sudo.
        self._term_steps = [s for s in steps if s.needs_terminal]
        self._steps = [s for s in steps if not s.needs_terminal]
        self._step_idx = 0
        self._log_line(f"▶ Plan: {len(steps)} paso(s) "
                       f"({len(self._steps)} directos, {len(self._term_steps)} "
                       f"en terminal). Empezando…\n")
        self._run_next_step()

    def _launch_windows_elevated_all(self, steps):
        """Windows: instala TODO en una única ventana elevada (un solo UAC).

        Construye un .ps1 con 1) los `winget install`, 2) un refresh de PATH
        (para ver Node/PHP recién instalados), 3) los `npm -g` y 4) los
        instaladores .exe (Composer). Lo lanza con `ShellExecuteW(.., "runas")`
        → UAC fiable y proceso DESACOPLADO de la app Qt (no es un QProcess hijo
        que muera). El usuario ve el progreso y, al cerrar, pulsa Re-detectar.
        """
        import ctypes
        winget = [s for s in steps if s.elevated]
        rest = [s for s in steps if not s.elevated]
        lines = [
            "$ErrorActionPreference = 'Continue'",
            # winget vive en WindowsApps (PATH de usuario): asegurarlo en la
            # sesión elevada por si el token admin no lo hereda.
            '$env:PATH = "$env:LOCALAPPDATA\\Microsoft\\WindowsApps;" + $env:PATH',
            "",
        ]
        if winget:
            lines.append("Write-Host '== winget ==' -ForegroundColor Cyan")
            lines += [" ".join(s.argv) for s in winget]
            lines += [
                "",
                "# Refrescar PATH para ver Node/PHP recién instalados",
                '$env:PATH = [Environment]::GetEnvironmentVariable("Path","Machine")'
                ' + ";" + [Environment]::GetEnvironmentVariable("Path","User")'
                ' + ";" + $env:PATH',
                "",
            ]
        for s in rest:
            # win_url / win_ps_install llegan como ['powershell',..,'-Command',INNER]
            # → escribimos el INNER tal cual (ya es PowerShell). npm llega como
            # ['cmd','/c','npm',...] → lo unimos literal.
            if s.argv and s.argv[0].lower().startswith("powershell"):
                lines.append(s.argv[-1])
            else:
                lines.append(" ".join(s.argv))
        lines += [
            "",
            "Write-Host ''",
            "Write-Host '=== Instalacion terminada. Pulsa Enter para cerrar. ===' "
            "-ForegroundColor Green",
            "Read-Host | Out-Null",
        ]
        try:
            batch = pc.app_config_dir() / "winget_batch.ps1"
            batch.parent.mkdir(parents=True, exist_ok=True)
            batch.write_text("\r\n".join(lines), encoding="utf-8")
        except Exception as e:
            self._log_line(f"✗ no pude escribir el batch elevado: {e}\n")
            self._finish_install()
            return
        self._log_line("── Instalando winget + npm + instaladores en una "
                       "ventana elevada…")
        self._log_line("   Aprueba el UAC. Cuando la ventana diga 'terminada', "
                       "ciérrala y pulsa 🔄 Re-detectar.\n")
        params = f'-NoProfile -ExecutionPolicy Bypass -File "{batch}"'
        try:
            r = int(ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "powershell.exe", params, None, 1))
        except Exception as e:
            r = 0
            self._log_line(f"✗ ShellExecuteW falló: {e}\n")
        if r <= 32:
            self._log_line(f"⚠ No se pudo abrir la ventana elevada (código {r}). "
                           "¿Rechazaste el UAC? Pulsa Instalar para reintentar.\n")
        else:
            QMessageBox.information(
                self, "Setup",
                "Se abrió una ventana elevada que instala todo "
                "(winget + npm + Composer).\n\nAprueba el UAC. Cuando la "
                "ventana diga 'terminada', ciérrala y pulsa 🔄 Re-detectar.")
        self._finish_install()

    def _run_next_step(self):
        if self._step_idx >= len(self._steps):
            self._launch_terminal_steps()
            return

        step = self._steps[self._step_idx]
        self._log_line(f"── {step.label}")
        self._log_line(f"   $ {' '.join(step.argv)}")

        self._proc = QProcess(self)
        self._proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        # Env extra (p.ej. NPM_CONFIG_PREFIX=~/.local para npm sin sudo).
        if step.env:
            qenv = QProcessEnvironment.systemEnvironment()
            for k, v in step.env.items():
                qenv.insert(k, str(v))
            self._proc.setProcessEnvironment(qenv)
        self._proc.readyReadStandardOutput.connect(self._on_proc_output)
        self._proc.finished.connect(self._on_step_finished)
        self._proc.errorOccurred.connect(self._on_proc_error)

        program = step.argv[0]
        args = step.argv[1:]
        self._proc.start(program, args)

    def _launch_terminal_steps(self):
        """Lanza los pasos que requieren sudo en UNA terminal (la contraseña
        se teclea ahí). Combina todos los comandos con && para pedirla 1 vez."""
        if not self._term_steps:
            self._finish_install()
            return
        cmds = " && ".join(" ".join(shlex.quote(a) for a in s.argv)
                           for s in self._term_steps)
        # Banner final SIEMPRE (con `;`, aunque algún paso falle): Konsole
        # usa --hold y deja la sesión muerta sin prompt, así que sin este
        # aviso el usuario cree que se quedó colgada. Le decimos que terminó.
        banner = (
            "echo '' ; "
            "echo '════════════════════════════════════════════════' ; "
            "echo '  ✅ Runtimes instalados.' ; "
            "echo '  Cierra esta ventana y pulsa 🔄 Re-detectar en ThemeForge.' ; "
            "echo '════════════════════════════════════════════════'"
        )
        cmds_with_banner = f"{cmds} ; {banner}"
        self._log_line("\n── Pasos con permisos de administrador (sudo):")
        self._log_line(f"   {cmds}")
        try:
            pc.open_in_terminal(str(pc.app_config_dir()),
                                command=cmds_with_banner, hold=True)
            self._log_line("   → Abrí una terminal: teclea tu contraseña ahí.\n")
            QMessageBox.information(
                self, "Setup",
                "Los runtimes que necesitan permisos de administrador "
                "(Rust, Go, Deno, Ruby, Hugo…) se están instalando en una "
                "terminal aparte.\n\nTeclea tu contraseña sudo ahí. Cuando "
                "termine, pulsa 🔄 Re-detectar.",
            )
        except Exception as e:
            self._log_line(f"   ✗ no se pudo abrir terminal: {e}\n")
            self._log_line(f"   Ejecuta a mano:\n   {cmds}\n")
        self._finish_install()

    def _finish_install(self):
        self._log_line("\n✅ Instalación lanzada. Pulsa 🔄 Re-detectar para verificar.")
        self._btn_refresh.setEnabled(True)
        self._btn_close.setEnabled(True)
        self._btn_install.setEnabled(True)

    def _on_proc_output(self):
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardOutput()).decode(errors="replace")
        for line in data.splitlines():
            if line.strip():
                self._log_line(f"   {line}")

    def _on_step_finished(self, code: int, _status):
        step = self._steps[self._step_idx]
        name = step.label.replace('Instalando ', '').rstrip('…')
        # Refrescar el PATH (Windows) ANTES de re-comprobar, para que el
        # binario recién instalado se vea sin reiniciar la app.
        self._refresh_windows_path()
        # winget devuelve exit≠0 cuando el paquete YA estaba instalado /
        # actualizado; brew a veces también. No nos fiamos solo del código:
        # si el binario está ahora en PATH, lo damos por bueno.
        tool = next((t for t in ds.TOOLS if t.key == step.tool_key), None)
        if code == 0 or (tool is not None and ds.is_installed(tool)):
            self._log_line(f"   ✓ {name} OK\n")
        else:
            self._log_line(f"   ✗ falló (exit {code}) — continúo con el resto\n")
        self._step_idx += 1
        self._run_next_step()

    def _refresh_windows_path(self):
        """Refresca el PATH del proceso para que los binarios recién
        instalados se vean sin reiniciar la app.

        - macOS: añade los bin estándar de Homebrew (las apps GUI no los
          heredan del shell de login).
        - Windows: relee PATH de HKLM + HKCU del registro.
        """
        if pc.IS_MACOS:
            import os
            cur = os.environ.get("PATH", "")
            for d in ("/opt/homebrew/bin", "/opt/homebrew/sbin",
                      "/usr/local/bin", "/usr/local/sbin"):
                if os.path.isdir(d) and d not in cur.split(os.pathsep):
                    cur = d + os.pathsep + cur
            os.environ["PATH"] = cur
            return
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
