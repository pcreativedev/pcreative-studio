"""video_splash.py — Splash de bienvenida en video al arrancar Pcreative Studio.

Reproduce un MP4 en una ventana frameless centrada, con audio. El usuario
puede saltarlo en cualquier momento con un clic o cualquier tecla. Cuando
el video acaba (o se salta, o falla el backend) emite `finished` para que
`main()` muestre la ventana principal.

Defensa anti-cuelgue: si el backend multimedia no arranca el video en
`SAFETY_MS`, se fuerza `finished` igualmente — la app nunca se queda
bloqueada detrás de un splash que no reproduce.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

# Si el video no ha terminado por sí solo en este margen (video de 10s +
# colchón), forzamos el cierre. Cubre el caso de backend multimedia roto.
SAFETY_MS = 12_000

# Si a los CHECK_MS la reproducción no ha avanzado (position==0 y no está
# en PlayingState), asumimos que el backend no puede reproducir el video
# (códec ausente, entorno sin aceleración) y cerramos para no dejar una
# ventana negra colgada. El clic/tecla siempre sirven como escape manual.
CHECK_MS = 3_500


class VideoSplash(QWidget):
    """Ventana de splash que reproduce un video y se autocierra."""

    finished = pyqtSignal()

    def __init__(self, video_path: Path, width: int = 1280, height: int = 720,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._done = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setStyleSheet("background: #000;")
        # El splash debe poder recibir foco de teclado para el skip con tecla.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._video = QVideoWidget(self)
        # CLAVE: sin esto, el QVideoWidget hijo se traga los clics y el
        # mousePressEvent del splash nunca se dispara → no se puede saltar.
        self._video.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._video)
        self.resize(width, height)

        # Reproductor + salida de audio.
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self._video)
        self._audio.setVolume(1.0)
        self._player.setSource(QUrl.fromLocalFile(str(video_path)))

        self._player.mediaStatusChanged.connect(self._on_status)
        self._player.errorOccurred.connect(lambda *_: self._finish())

        # Hint de "clic para saltar" superpuesto abajo-izquierda.
        self._hint = QLabel("clic o tecla para saltar", self._video)
        self._hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._hint.setStyleSheet(
            "color: rgba(255,255,255,170); background: rgba(0,0,0,90);"
            "padding: 4px 12px; border-radius: 8px; font-size: 11px;"
        )
        self._hint.adjustSize()
        self._hint.move(18, height - self._hint.height() - 18)

    def start(self) -> None:
        """Centra, muestra y arranca la reproducción."""
        scr = self.screen().availableGeometry()
        self.move(scr.center().x() - self.width() // 2,
                  scr.center().y() - self.height() // 2)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()  # para que keyPressEvent reciba las teclas
        self._player.play()
        # Early-exit: si el video no arranca de verdad (negro en VM sin
        # aceleración, códec ausente), cerramos en vez de dejar negro.
        QTimer.singleShot(CHECK_MS, self._check_playing)
        # Red de seguridad final: si nada termina el video, lo forzamos.
        QTimer.singleShot(SAFETY_MS, self._finish)

    def _check_playing(self) -> None:
        """A los CHECK_MS: si la reproducción no avanzó, asumimos que el
        backend no puede pintar el video y entramos a la app."""
        if self._done:
            return
        playing = (self._player.playbackState()
                   == QMediaPlayer.PlaybackState.PlayingState)
        if not playing or self._player.position() <= 0:
            self._finish()

    def _on_status(self, status) -> None:
        if status in (
            QMediaPlayer.MediaStatus.EndOfMedia,
            QMediaPlayer.MediaStatus.InvalidMedia,
        ):
            self._finish()

    def _finish(self) -> None:
        if self._done:
            return
        self._done = True
        try:
            self._player.stop()
        except Exception:
            pass
        self.finished.emit()
        self.close()

    # ── Skip con clic o tecla ───────────────────────────────────────────
    def mousePressEvent(self, _event) -> None:
        self._finish()

    def keyPressEvent(self, _event) -> None:
        self._finish()
