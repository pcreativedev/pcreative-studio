"""
SettingsPanel — pestaña del builder con configuración y estado.

Muestra:
  - GitHub (login activo, repos accesibles)
  - Agentes AI (claude, codex en PATH)
  - Stacks instalados / faltantes
  - Skills configuradas por stack (editor)
  - Versiones de Node / npm / Python / PHP / Flutter
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from stacks import STACKS
import platform_compat as pc


def _run(cmd: list[str], timeout: int = 5) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=timeout).decode().strip()
    except Exception:
        return ""


def _which(cmd: str) -> str:
    return shutil.which(cmd) or ""


class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        title = QLabel("Settings & Status")
        f = QFont(); f.setPointSize(18); f.setBold(True)
        title.setFont(f)

        # Status
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(280)
        self.status_text.setStyleSheet("background:#1e1e25;color:#e6e6e6;font-family:monospace;font-size:12px;")

        self.btn_refresh = QPushButton("↻ Refresh status")
        self.btn_refresh.clicked.connect(self.refresh_status)

        self.btn_deps = QPushButton("🔧 Setup dependencies…")
        self.btn_deps.setToolTip(
            "Detecta e instala las herramientas que ThemeForge necesita "
            "(Node, git, GitHub CLI, los CLIs de IA, netlify) vía "
            "winget / brew / paru según tu sistema operativo."
        )
        self.btn_deps.clicked.connect(self._open_dependency_wizard)

        status_box = QGroupBox("System status")
        sb = QVBoxLayout()
        sb.addWidget(self.status_text)
        sb_btns = QHBoxLayout()
        sb_btns.addWidget(self.btn_refresh)
        sb_btns.addWidget(self.btn_deps)
        sb.addLayout(sb_btns)
        status_box.setLayout(sb)

        # ── Theme picker ────────────────────────────────────────────
        try:
            import themes
            self._themes_module = themes
            self.theme_combo = QComboBox()
            self._theme_keys: list[str] = []
            current = themes.current_theme_name()
            for info in themes.list_themes():
                self._theme_keys.append(info.name)
                icon = "🌑" if info.is_dark else "☀️"
                label = f"{icon}  {info.display_name}"
                if info.is_user:
                    label += "   (custom)"
                self.theme_combo.addItem(label)
                if info.name == current:
                    self.theme_combo.setCurrentIndex(self.theme_combo.count() - 1)
            self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

            self.theme_help = QLabel(
                "<small>Aplicación inmediata · sin reinicio. Los themes "
                "custom van en <code>~/.config/themeforge/themes/*.json</code>.</small>"
            )
            self.theme_help.setTextFormat(Qt.TextFormat.RichText)
            self.theme_help.setWordWrap(True)

            self.btn_theme_edit = QPushButton("✏️ Customize current theme…")
            self.btn_theme_edit.setToolTip(
                "Abre el editor visual: color pickers + sliders + dropdowns "
                "de variants. Los cambios se aplican en vivo a toda la app. "
                "Guarda como nuevo tema custom o cancela para revertir."
            )
            self.btn_theme_edit.clicked.connect(self._open_theme_editor)

            self.btn_theme_figma = QPushButton("📥 Import from Figma…")
            self.btn_theme_figma.setToolTip(
                "Importa un theme desde un archivo DTCG JSON (exportado por "
                "el plugin Tokens Studio de Figma, plan gratuito) o "
                "directamente vía Figma REST API (requiere plan Enterprise "
                "+ Personal Access Token)."
            )
            self.btn_theme_figma.clicked.connect(self._open_figma_import)

            # Refresh the dropdown if a new theme is saved while the
            # editor is open (or when applied externally).
            try:
                themes.theme_signals.theme_changed.connect(self._refresh_theme_combo)
            except Exception:
                pass

            theme_box = QGroupBox("🎨 App theme")
            tb = QHBoxLayout()
            tb.addWidget(QLabel("Theme:"))
            tb.addWidget(self.theme_combo, 1)
            tb.addWidget(self.btn_theme_edit)
            tb.addWidget(self.btn_theme_figma)
            theme_outer = QVBoxLayout()
            theme_outer.addLayout(tb)
            theme_outer.addWidget(self.theme_help)
            theme_box.setLayout(theme_outer)
        except Exception as e:
            theme_box = None
            print(f"[settings_panel] theme picker disabled: {e}")

        # Skills por stack
        self.stack_list = QListWidget()
        for key, s in STACKS.items():
            self.stack_list.addItem(f"{s['name']}  ·  {key}")
        self.stack_list.currentRowChanged.connect(self._on_stack_changed)

        self.skills_list = QListWidget()
        self.skill_add_btn = QPushButton("+ Añadir skill")
        self.skill_add_btn.clicked.connect(self._add_skill)
        self.skill_remove_btn = QPushButton("− Quitar")
        self.skill_remove_btn.clicked.connect(self._remove_skill)

        skill_btns = QHBoxLayout()
        skill_btns.addWidget(self.skill_add_btn)
        skill_btns.addWidget(self.skill_remove_btn)

        skills_box = QGroupBox("Predeclared skills per stack")
        sbox = QHBoxLayout()
        sl = QVBoxLayout(); sl.addWidget(QLabel("Stack:")); sl.addWidget(self.stack_list)
        sr = QVBoxLayout(); sr.addWidget(QLabel("Skills (npx skills add):")); sr.addWidget(self.skills_list); sr.addLayout(skill_btns)
        sbox.addLayout(sl, 1); sbox.addLayout(sr, 1)
        skills_box.setLayout(sbox)

        # Office
        self.pixel_status_label = QLabel("(cargando…)")
        self.pixel_status_label.setStyleSheet("color:#aaa;font-family:monospace;font-size:12px;")
        self.btn_pixel_install = QPushButton("📦 Install / Update")
        self.btn_pixel_install.clicked.connect(self._pixel_install)
        self.btn_pixel_launch = QPushButton("▶ Start")
        self.btn_pixel_launch.clicked.connect(self._pixel_launch)
        self.btn_pixel_open = QPushButton("🌐 Open dashboard")
        self.btn_pixel_open.clicked.connect(self._pixel_open)
        self.btn_pixel_stop = QPushButton("✕ Stop")
        self.btn_pixel_stop.clicked.connect(self._pixel_stop)
        self.btn_pixel_refresh = QPushButton("↻")
        self.btn_pixel_refresh.clicked.connect(self._pixel_refresh)

        pixel_box = QGroupBox("🎮 Office (pixel-art visualizer of Claude Code sessions)")
        pbox = QVBoxLayout()
        pbox.addWidget(self.pixel_status_label)
        pbtn = QHBoxLayout()
        pbtn.addWidget(self.btn_pixel_install)
        pbtn.addWidget(self.btn_pixel_launch)
        pbtn.addWidget(self.btn_pixel_open)
        pbtn.addWidget(self.btn_pixel_stop)
        pbtn.addWidget(self.btn_pixel_refresh)
        pbtn.addStretch()
        pbox.addLayout(pbtn)
        pixel_box.setLayout(pbox)

        # Atajos
        self.btn_open_themeforge = QPushButton("📁 Open ~/Proyectos/themeforge")
        self.btn_open_themeforge.clicked.connect(
            lambda: pc.open_in_file_manager(Path.home() / "Proyectos" / "themeforge"))
        self.btn_open_context = QPushButton("📚 Open context/")
        self.btn_open_context.clicked.connect(
            lambda: pc.open_in_file_manager(Path.home() / "Proyectos" / "themeforge" / "context"))
        self.btn_edit_stacks = QPushButton("📝 Edit stacks.py")
        self.btn_edit_stacks.clicked.connect(self._edit_stacks)

        shortcuts_box = QGroupBox("Shortcuts")
        sbtn = QHBoxLayout()
        sbtn.addWidget(self.btn_open_themeforge)
        sbtn.addWidget(self.btn_open_context)
        sbtn.addWidget(self.btn_edit_stacks)
        sbtn.addStretch()
        shortcuts_box.setLayout(sbtn)

        # Root
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.addWidget(title)
        if theme_box is not None:
            il.addWidget(theme_box)
        il.addWidget(status_box)
        il.addWidget(skills_box, 1)
        il.addWidget(pixel_box)
        il.addWidget(shortcuts_box)

        scroll = QScrollArea()
        scroll.setWidget(inner)
        scroll.setWidgetResizable(True)

        root = QVBoxLayout(self)
        root.addWidget(scroll)

        self.refresh_status()
        self._pixel_refresh()
        if self.stack_list.count() > 0:
            self.stack_list.setCurrentRow(0)

    def refresh_status(self):
        lines = []

        # GitHub
        gh = _which("gh")
        if gh:
            who = _run(["gh", "api", "user", "--jq", ".login"]) or "(no logueado)"
            scopes = _run(["gh", "auth", "status"], timeout=5)
            scope_line = next((l for l in scopes.splitlines() if "scopes" in l.lower()), "")
            lines.append(f"GitHub      : @{who}  {scope_line.strip()}")
        else:
            lines.append("GitHub      : gh CLI no instalado")


        # Agentes AI
        lines.append("")
        lines.append("─ Agentes AI ────────────────────────────")
        for tool in ("claude", "codex", "sgpt", "gh"):
            p = _which(tool)
            if p:
                v = _run([tool, "--version"])
                lines.append(f"  {tool:<10}: {p}  {v.split(chr(10))[0][:60]}")
            else:
                lines.append(f"  {tool:<10}: ✗ no en PATH")

        # Runtimes
        lines.append("")
        lines.append("─ Runtimes ──────────────────────────────")
        for tool, cmd_args in [
            ("node", ["node", "--version"]),
            ("npm", ["npm", "--version"]),
            ("bun", ["bun", "--version"]),
            ("python3", ["python3", "--version"]),
            ("php", ["php", "--version"]),
            ("composer", ["composer", "--version"]),
            ("flutter", ["flutter", "--version"]),
            ("go", ["go", "version"]),
            ("cargo", ["cargo", "--version"]),
            ("deno", ["deno", "--version"]),
            ("mix", ["mix", "--version"]),
            ("ruby", ["ruby", "--version"]),
            ("rails", ["rails", "--version"]),
            ("java", ["java", "--version"]),
        ]:
            v = _run(cmd_args).splitlines()
            if v:
                lines.append(f"  {tool:<10}: {v[0][:80]}")

        # Tools
        lines.append("")
        lines.append("─ Tools ─────────────────────────────────")
        for tool in ("docker", "git", "wget", "unzip", "sshpass", "shopify", "wp"):
            p = _which(tool)
            lines.append(f"  {tool:<10}: {p or '✗ no en PATH'}")

        self.status_text.setPlainText("\n".join(lines))

    def _on_stack_changed(self, row: int):
        self.skills_list.clear()
        if row < 0: return
        key = list(STACKS)[row]
        for s in STACKS[key].get("skills") or []:
            self.skills_list.addItem(s)

    def _add_skill(self):
        row = self.stack_list.currentRow()
        if row < 0: return
        key = list(STACKS)[row]
        skill, ok = QInputDialog.getText(self, "Nueva skill", f"owner/repo/skill-name para {key}:")
        if ok and skill.strip():
            STACKS[key].setdefault("skills", []).append(skill.strip())
            self._on_stack_changed(row)
            QMessageBox.information(self, "Skill añadida",
                f"Skill añadida en memoria para {key}.\n\n"
                "NOTA: el cambio NO se persiste en stacks.py. Edita el archivo a mano para que sobreviva al reinicio.")

    def _remove_skill(self):
        row = self.stack_list.currentRow()
        if row < 0: return
        key = list(STACKS)[row]
        skill = self.skills_list.currentItem()
        if not skill: return
        try:
            STACKS[key]["skills"].remove(skill.text())
        except ValueError:
            pass
        self._on_stack_changed(row)

    # ── Office ──────────────────────────────────────────
    def _pixel_refresh(self):
        try:
            import pixel_office
            s = pixel_office.status()
        except Exception as e:
            self.pixel_status_label.setText(f"error: {e}")
            return
        installed = "✓ instalado" if s["installed"] else "✗ no instalado"
        path = s["install_dir"] or "—"
        dash = "✓ arriba" if s["dashboard_up"] else "✗ parado"
        self.pixel_status_label.setText(
            f"{installed}    dashboard: {dash}\n"
            f"path: {path}\n"
            f"url: {s['dashboard_url']}"
        )
        self.btn_pixel_launch.setEnabled(s["installed"] and not s["dashboard_up"])
        self.btn_pixel_open.setEnabled(s["dashboard_up"])
        self.btn_pixel_stop.setEnabled(s["dashboard_up"])

    def _pixel_install(self):
        try:
            import pixel_office
        except Exception as e:
            QMessageBox.critical(self, "Office", f"Could not import pixel_office: {e}")
            return
        if QMessageBox.question(
            self, "Install Office",
            f"I'll clone the repo into {pixel_office.INSTALL_DIR} and run npm install.\n\n"
            "This registers Claude Code hooks globally in ~/.claude/settings.json.\n\n"
            "Continue?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self.btn_pixel_install.setEnabled(False)
        self.btn_pixel_install.setText("Installing…")
        QWidget.repaint(self)
        ok, msg = pixel_office.install()
        self.btn_pixel_install.setEnabled(True)
        self.btn_pixel_install.setText("📦 Install / Update")
        if ok:
            QMessageBox.information(self, "Office", msg)
        else:
            QMessageBox.warning(self, "Office", msg)
        self._pixel_refresh()

    def _pixel_launch(self):
        try:
            import pixel_office
        except Exception as e:
            QMessageBox.critical(self, "Office", f"Could not import pixel_office: {e}")
            return
        proc = pixel_office.launch_background()
        if proc is None and not pixel_office.is_dashboard_up():
            QMessageBox.warning(self, "Office", "Failed to start — is it installed, and is npm on PATH?")
        self._pixel_refresh()

    def _pixel_open(self):
        try:
            import pixel_office
            pc.open_url(pixel_office.DASHBOARD_URL)
        except Exception as e:
            QMessageBox.warning(self, "Office", f"Could not open the browser: {e}")

    def _pixel_stop(self):
        # Mata cualquier `npm start` cuya cwd sea el directorio de pixel-office-openclaw.
        try:
            import pixel_office
            install_dir = pixel_office.find_install_dir()
        except Exception:
            install_dir = None
        if install_dir is None:
            QMessageBox.information(self, "Office", "No está instalado.")
            return
        try:
            pc.kill_processes_under_path(str(install_dir))
        except Exception as e:
            QMessageBox.warning(self, "Office", f"No se pudo parar: {e}")
        self._pixel_refresh()

    def _open_dependency_wizard(self):
        """Abre el wizard de detección + instalación de dependencias."""
        try:
            from dependency_wizard import DependencyWizard
            dlg = DependencyWizard(self)
            dlg.exec()
            # Tras instalar, refresca el panel de estado del sistema.
            self.refresh_status()
        except Exception as e:
            QMessageBox.critical(self, "Setup dependencies", f"Error: {e}")

    def _open_theme_editor(self):
        """Open the visual theme editor dialog. Changes apply live;
        Save persists as a new custom theme."""
        try:
            from theme_editor import ThemeEditorDialog
            dlg = ThemeEditorDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Theme editor", f"Error: {e}")

    def _open_figma_import(self):
        """Open the Figma DTCG / REST API import dialog."""
        try:
            from figma_import_dialog import FigmaImportDialog
            dlg = FigmaImportDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Figma import", f"Error: {e}")

    def _refresh_theme_combo(self, _name: str = ""):
        """Repopulate the dropdown so newly-saved custom themes appear.
        Triggered by the `theme_signals.theme_changed` signal."""
        try:
            current = self._themes_module.current_theme_name()
            self.theme_combo.blockSignals(True)
            self.theme_combo.clear()
            self._theme_keys = []
            for info in self._themes_module.list_themes():
                self._theme_keys.append(info.name)
                icon = "🌑" if info.is_dark else "☀️"
                label = f"{icon}  {info.display_name}"
                if info.is_user:
                    label += "   (custom)"
                self.theme_combo.addItem(label)
                if info.name == current:
                    self.theme_combo.setCurrentIndex(self.theme_combo.count() - 1)
            self.theme_combo.blockSignals(False)
        except Exception as e:
            print(f"[settings_panel] refresh combo failed: {e}")

    def _on_theme_changed(self, idx: int):
        """Aplica el tema seleccionado al QApplication en caliente,
        persiste la elección en `~/.config/themeforge/settings.json`
        y emite la señal `theme_signals.theme_changed` para que el
        resto de widgets que dependen del color (iconos en tabs, etc.)
        se refresquen sin reinicio."""
        if idx < 0 or idx >= len(self._theme_keys):
            return
        name = self._theme_keys[idx]
        try:
            pack = self._themes_module.load_theme(name)
            from PyQt6.QtWidgets import QApplication
            self._themes_module.apply_theme(QApplication.instance(), pack)
            self._themes_module.save_current_theme(name)
            self._themes_module.clear_icon_cache()
            self._themes_module.theme_signals.theme_changed.emit(name)
        except Exception as e:
            print(f"[settings_panel] failed to apply theme {name}: {e}")

    def _edit_stacks(self):
        path = Path.home() / "Proyectos" / "themeforge" / "stacks.py"
        # Prefer VSCode-family (handles macOS .app fallback)
        argv = pc.vscode_argv(path)
        if argv:
            subprocess.Popen(argv)
            return
        # Linux: try kate before the file-manager fallback
        if pc.IS_LINUX and shutil.which("kate"):
            subprocess.Popen(["kate", str(path)])
            return
        # Last resort: open in file manager
        pc.open_in_file_manager(path)
