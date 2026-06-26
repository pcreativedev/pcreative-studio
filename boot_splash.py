"""boot_splash.py — Neo-Tokyo boot sequence splash for Pcreative Studio.

A PyQt6 port of the prototype's `BootSequence` (handoff design pack): a
terminal-style cold-boot animation over a cyberpunk grid/glow atmosphere —
neon wordmark, Japanese subtitle, and self-typing boot log, then a fade-out.

It is **pure QPainter** (no multimedia / no OpenGL), so unlike the video
splash it runs fine even in software-GL / headless-GPU environments and
never leaves a black window behind.

Drop-in compatible with the previous splash:

    from boot_splash import BootSplash
    splash = BootSplash()
    splash.finished.connect(_enter_app)   # fired once, always
    splash.start()

The user can skip at any time with a click or any key. A safety timer
guarantees `finished` fires even if something stalls.
"""
from __future__ import annotations

import random
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal, QPropertyAnimation
from PyQt6.QtGui import (
    QFont, QFontDatabase, QPainter, QColor, QPen, QRadialGradient, QGuiApplication,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect,
)

# ── Neo-Tokyo tokens (copiados EXACTO del design pack) ──────────────────
BG_VOID = "#04060c"
ACCENT = "#00f0ff"      # cyan — acento primario
ACCENT_2 = "#ff2e88"    # magenta — acento secundario
CODEX = "#86efac"       # verde de las líneas de boot
TX_FAINT = "#5c6e9c"    # subtítulo JP
GRID_RGBA = (120, 160, 255, 12)   # rgba(120,160,255,0.045) ≈ alpha 12/255

# Líneas del boot log — idénticas al prototipo (atmosphere.jsx · BootSequence).
BOOT_LINES = [
    "> themeforge.core // 鍛造エンジン",
    "> mounting neon kernel ............ OK",
    "> loading agents [claude·codex·gemini·opencode] .. OK",
    "> calibrating glow matrix ......... OK",
    "> establishing uplink 東京/NEO ..... OK",
    "> ready.",
]

SAFETY_MS = 8_000   # tope absoluto: pase lo que pase, entrar a la app.


def _load_bundled_fonts() -> None:
    """Carga cualquier .ttf/.otf de assets/fonts (Zen Dots, Chakra Petch,
    JetBrains Mono, Noto Sans JP) si el usuario los empaqueta. Degrada con
    gracia: si no hay fuentes, se usan los fallbacks del sistema."""
    fonts_dir = Path(__file__).resolve().parent / "assets" / "fonts"
    if not fonts_dir.is_dir():
        return
    for f in fonts_dir.iterdir():
        if f.suffix.lower() in (".ttf", ".otf"):
            try:
                QFontDatabase.addApplicationFont(str(f))
            except Exception:
                pass


def _font(families: list[str], size: int, *, bold=False, spacing_pct=100) -> QFont:
    f = QFont()
    f.setFamilies(families)          # Qt hace fallback per-glyph (CJK incluido)
    f.setPixelSize(size)
    if bold:
        f.setWeight(QFont.Weight.Bold)
    if spacing_pct != 100:
        f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, spacing_pct)
    return f


# Familias con fallback (incluye Noto CJK al final para que el kanji/katakana
# nunca salga en cuadritos aunque la fuente principal no tenga CJK).
_MEGA = ["Zen Dots", "Chakra Petch", "Orbitron", "DejaVu Sans", "Noto Sans CJK JP"]
_MONO = ["JetBrains Mono", "DejaVu Sans Mono", "monospace", "Noto Sans CJK JP"]
_JP = ["Noto Sans CJK JP", "Noto Sans JP", "Noto Sans CJK", "sans-serif"]


class BootSplash(QWidget):
    """Splash de arranque Neo-Tokyo (boot sequence) que se autocierra."""

    finished = pyqtSignal()

    def __init__(self, glow: float = 1.0, parent: QWidget | None = None):
        super().__init__(parent)
        self._done = False
        self._fading = False
        self._shown = 0
        self._cursor_on = True
        self._glow = max(0.0, min(1.4, glow))
        self._blink = None
        self._flick = None

        _load_bundled_fonts()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.resize(760, 480)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addStretch()

        # Wordmark neón.
        self.wordmark = QLabel("PCREATIVE STUDIO")
        self.wordmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wordmark.setFont(_font(_MEGA, 46, bold=True, spacing_pct=104))
        self.wordmark.setStyleSheet(f"color: {ACCENT}; background: transparent;")
        glow_fx = QGraphicsDropShadowEffect(self.wordmark)
        glow_fx.setBlurRadius(18 * self._glow + 6)
        glow_fx.setColor(QColor(ACCENT))
        glow_fx.setOffset(0, 0)
        self.wordmark.setGraphicsEffect(glow_fx)
        root.addWidget(self.wordmark)

        # Subtítulo japonés.
        self.jp = QLabel("ネオ東京 ・ 鍛造システム")
        self.jp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.jp.setFont(_font(_JP, 13, spacing_pct=180))
        self.jp.setStyleSheet(f"color: {TX_FAINT}; background: transparent;")
        root.addWidget(self.jp)
        root.addSpacing(26)

        # Log de boot (monospace, verde codex), tecleado línea a línea.
        self.term = QLabel("")
        self.term.setTextFormat(Qt.TextFormat.RichText)
        self.term.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.term.setFont(_font(_MONO, 13))
        self.term.setStyleSheet(f"color: {CODEX}; background: transparent;")
        self.term.setMinimumHeight(160)
        self.term.setMinimumWidth(560)
        wrap = QVBoxLayout()
        wrap.addWidget(self.term, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addLayout(wrap)
        root.addStretch()

    # ── ciclo de vida ──────────────────────────────────────────────────
    def start(self):
        self._center_on_screen()
        self.show()
        self.raise_()
        self.activateWindow()
        # Cursor parpadeante (1 Hz).
        self._blink = QTimer(self)
        self._blink.timeout.connect(self._toggle_cursor)
        self._blink.start(530)
        # Flicker del wordmark (dips breves, como el keyframe `flicker`).
        self._flick = QTimer(self)
        self._flick.timeout.connect(self._do_flicker)
        self._flick.start(2500)
        # Primera línea.
        QTimer.singleShot(220, self._next_line)
        # Red de seguridad.
        QTimer.singleShot(SAFETY_MS, self._finish)

    def _center_on_screen(self):
        scr = QGuiApplication.primaryScreen()
        if scr:
            geo = scr.availableGeometry()
            self.move(geo.center().x() - self.width() // 2,
                      geo.center().y() - self.height() // 2)

    def _next_line(self):
        if self._done or self._fading:
            return
        if self._shown >= len(BOOT_LINES):
            return
        self._shown += 1
        self._render_term()
        if self._shown < len(BOOT_LINES):
            delay = 150 + int(random.random() * 120)
            QTimer.singleShot(delay, self._next_line)
        else:
            # Todas las líneas mostradas → pausa breve y fade-out.
            QTimer.singleShot(420, self._begin_fade)

    def _render_term(self):
        rows = []
        for i in range(min(self._shown, len(BOOT_LINES))):
            line = BOOT_LINES[i]
            # Cursor ▊ en la última línea mientras aún se teclea.
            if i == self._shown - 1 and self._shown < len(BOOT_LINES) and self._cursor_on:
                line = line + "▊"
            rows.append(self._escape(line))
        self.term.setText("<br>".join(rows))

    @staticmethod
    def _escape(s: str) -> str:
        return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def _toggle_cursor(self):
        self._cursor_on = not self._cursor_on
        if not self._done:
            self._render_term()

    def _do_flicker(self):
        """Dip breve de opacidad del wordmark (≈ keyframe flicker)."""
        if self._done:
            return
        self.wordmark.setStyleSheet(
            f"color: rgba(0,240,255,0.45); background: transparent;")
        QTimer.singleShot(60, lambda: self.wordmark.setStyleSheet(
            f"color: {ACCENT}; background: transparent;") if not self._done else None)

    def _begin_fade(self):
        if self._done or self._fading:
            return
        self._fading = True
        self._stop_timers()
        self._anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim.setDuration(450)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._finish)
        self._anim.start()

    def _stop_timers(self):
        """Para los timers periódicos para que NADA dispare sobre el widget
        después de cerrarse (con WA_DeleteOnClose el objeto C++ se borra y un
        timer pendiente lo tocaría → crash)."""
        for t in (self._blink, self._flick):
            try:
                if t is not None:
                    t.stop()
            except Exception:
                pass

    def _finish(self):
        if self._done:
            return
        self._done = True
        self._stop_timers()
        try:
            self.finished.emit()
        finally:
            self.close()

    # ── skip manual ─────────────────────────────────────────────────────
    def mousePressEvent(self, _ev):  # noqa: N802
        self._skip()

    def keyPressEvent(self, _ev):  # noqa: N802
        self._skip()

    def _skip(self):
        if self._done:
            return
        # Salta directo al fade (sin esperar a teclear el resto).
        self._shown = len(BOOT_LINES)
        self._render_term()
        self._begin_fade()

    # ── atmósfera (grid + glows radiales) ───────────────────────────────
    def paintEvent(self, _ev):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Fondo.
        p.fillRect(self.rect(), QColor(BG_VOID))

        # Glow radial cian (arriba-izquierda).
        ga = QRadialGradient(QPointF(w * 0.12, h * 0.04), w * 0.6)
        ca = QColor(ACCENT); ca.setAlphaF(0.22 * self._glow)
        ga.setColorAt(0.0, ca)
        ga.setColorAt(0.65, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), ga)

        # Glow radial magenta (abajo-derecha).
        gb = QRadialGradient(QPointF(w * 0.9, h * 1.0), w * 0.6)
        cb = QColor(ACCENT_2); cb.setAlphaF(0.18 * self._glow)
        gb.setColorAt(0.0, cb)
        gb.setColorAt(0.65, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), gb)

        # Grid 46px, con alpha pesando hacia arriba (mask radial del proto).
        step = 46
        base = QColor(*GRID_RGBA)
        pen = QPen(base)
        pen.setWidthF(1.0)
        for y in range(0, h, step):
            a = max(0.0, 1.0 - (y / max(1, h)) * 0.85)
            c = QColor(*GRID_RGBA[:3]); c.setAlphaF(GRID_RGBA[3] / 255 * a)
            pen.setColor(c); p.setPen(pen)
            p.drawLine(0, y, w, y)
        for x in range(0, w, step):
            a = 0.55  # columnas con alpha media constante
            c = QColor(*GRID_RGBA[:3]); c.setAlphaF(GRID_RGBA[3] / 255 * a)
            pen.setColor(c); p.setPen(pen)
            p.drawLine(x, 0, x, h)
        p.end()
