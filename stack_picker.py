"""
StackPickerDialog — ventana modal para elegir stack agrupado por categoría.

Uso:
    dlg = StackPickerDialog(parent, initial="nextjs-tailwind")
    if dlg.exec() == QDialog.DialogCode.Accepted:
        key = dlg.selected_key  # ej: "sveltekit-tailwind"
"""
from __future__ import annotations

from collections import defaultdict

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from stacks import STACKS


# Orden manual de categorías para que las más comunes salgan arriba
CATEGORY_ORDER = [
    "Sin definir",
    "Web · Frontend",
    "Web · Full-stack",
    "Web · Static",
    "Backend · API",
    "CMS · WordPress",
    "CMS · Shopify",
    "Headless CMS",
    # Justo encima de E-commerce y no al final: es el grupo de la casa, y quien
    # abre el selector para hacer un tema nuestro no debería tener que buscarlo
    # entre ochenta y siete stacks.
    "Temas · pcreative Commerce",
    "E-commerce",
    "Docs · Static",
    "Móvil · Cross-platform",
    "Móvil · Nativo",
    "Desktop",
    "Component Lib",
    "Browser Extension",
    "Email",
]


class StackCard(QPushButton):
    """Tarjeta clicable que representa un stack."""
    def __init__(self, key: str, stack: dict, on_click):
        super().__init__()
        self.key = key
        self.stack = stack
        name = stack.get("name", key)
        lang = stack.get("language", "")
        notes = stack.get("notes", "")
        # Truncar notas a ~120 chars
        if len(notes) > 130:
            notes = notes[:127] + "…"

        self.setText(f"{name}\n  {lang}\n\n  {notes}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(110)
        self.setMaximumHeight(140)
        self.setMinimumWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            "QPushButton {"
            "  text-align: left; padding: 10px 12px; border-radius: 8px;"
            "  border: 1px solid #3a3a44; background: #1e1e25;"
            "  font-size: 13px; color: #e6e6e6;"
            "}"
            "QPushButton:hover {"
            "  border-color: #62b4ff; background: #232331;"
            "}"
            "QPushButton[selected=\"true\"] {"
            "  border-color: #ed1c57; background: #2a1d24;"
            "}"
        )
        self.clicked.connect(lambda: on_click(self.key))

    def set_selected(self, sel: bool):
        self.setProperty("selected", "true" if sel else "false")
        self.style().unpolish(self); self.style().polish(self)


class StackPickerDialog(QDialog):
    def __init__(self, parent=None, initial: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar stack")
        self.setMinimumSize(900, 640)
        self.selected_key: str | None = initial
        self._cards: list[StackCard] = []
        self._build_ui()
        self._highlight_selected()

    def _build_ui(self):
        title = QLabel("Elige un stack")
        f = QFont(); f.setPointSize(16); f.setBold(True)
        title.setFont(f)

        subtitle = QLabel("Haz click en una tarjeta — la ventana se cerrará con tu elección.")
        subtitle.setStyleSheet("color:#888;")

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Filtrar por nombre, lenguaje, notas…")
        self.search.textChanged.connect(self._apply_filter)

        # Cancelar
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)

        header = QHBoxLayout()
        header.addWidget(self.search, 1)
        header.addWidget(self.btn_cancel)

        # Contenido scroll
        container = QWidget()
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setSpacing(14)

        # Agrupar por categoría
        by_cat = defaultdict(list)
        for key, s in STACKS.items():
            by_cat[s.get("category", "Otros")].append((key, s))

        # Orden: primero categorías del CATEGORY_ORDER, luego el resto alfabético
        ordered_cats = [c for c in CATEGORY_ORDER if c in by_cat]
        ordered_cats += sorted([c for c in by_cat if c not in CATEGORY_ORDER])

        self._cat_widgets: list[tuple[QGroupBox, list[StackCard]]] = []
        for cat in ordered_cats:
            box = QGroupBox(f"{cat}  ·  {len(by_cat[cat])}")
            box.setStyleSheet(
                "QGroupBox { font-weight: bold; padding-top: 14px; margin-top: 6px; "
                "border: 1px solid #2a2a30; border-radius: 8px; }"
                "QGroupBox::title { color: #62b4ff; padding: 0 6px; }"
            )
            grid = QGridLayout(box)
            grid.setSpacing(10)
            row, col = 0, 0
            cards_in_cat: list[StackCard] = []
            for key, s in by_cat[cat]:
                card = StackCard(key, s, self._on_card)
                grid.addWidget(card, row, col)
                self._cards.append(card)
                cards_in_cat.append(card)
                col += 1
                if col >= 3:
                    col = 0; row += 1
            self.container_layout.addWidget(box)
            self._cat_widgets.append((box, cards_in_cat))

        self.container_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        root = QVBoxLayout(self)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(header)
        root.addWidget(scroll, 1)

    def _on_card(self, key: str):
        self.selected_key = key
        self._highlight_selected()
        # Pequeño feedback visual antes de cerrar
        self.accept()

    def _highlight_selected(self):
        for c in self._cards:
            c.set_selected(c.key == self.selected_key)

    def _apply_filter(self, text: str):
        text = text.strip().lower()
        for box, cards in self._cat_widgets:
            visible_count = 0
            for c in cards:
                hay = text in c.stack.get("name", "").lower() \
                      or text in c.stack.get("language", "").lower() \
                      or text in c.stack.get("notes", "").lower() \
                      or text in c.key.lower()
                show = (not text) or hay
                c.setVisible(show)
                if show:
                    visible_count += 1
            box.setVisible(visible_count > 0)
