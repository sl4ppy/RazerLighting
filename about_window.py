#!/usr/bin/env python3
"""About dialog for Razer Lighting."""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QPixmap, QMovie, QPainter, QColor, QFont, QLinearGradient,
    QRadialGradient, QBrush, QPen, QFontDatabase,
)
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget,
)

VERSION = "1.1.0"
GITHUB_URL = "https://github.com/sl4ppy/RazerLighting"
AVATAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "avatar.gif")


class AboutBackground(QWidget):
    """Paints an atmospheric branded background."""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Dark base gradient
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0.0, QColor(14, 14, 18))
        bg.setColorAt(0.4, QColor(10, 10, 12))
        bg.setColorAt(1.0, QColor(16, 16, 20))
        p.fillRect(self.rect(), bg)

        # Centered teal glow orb
        glow = QRadialGradient(w * 0.5, h * 0.35, w * 0.5)
        glow.setColorAt(0.0, QColor(68, 214, 44, 30))
        glow.setColorAt(0.3, QColor(50, 170, 30, 15))
        glow.setColorAt(0.7, QColor(30, 100, 20, 5))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(0, 0, w, int(h * 0.7))

        # Subtle horizontal line accent
        p.setPen(QPen(QColor(68, 214, 44, 40), 1))
        y_line = int(h * 0.68)
        p.drawLine(int(w * 0.15), y_line, int(w * 0.85), y_line)

        p.end()


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About Razer Lighting")
        self.setFixedSize(380, 340)

        # Background
        self._bg = AboutBackground(self)
        self._bg.setGeometry(0, 0, 380, 340)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignHCenter)
        layout.setContentsMargins(30, 24, 30, 20)

        # Avatar
        avatar_label = QLabel()
        avatar_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(AVATAR_PATH):
            movie = QMovie(AVATAR_PATH)
            movie.setScaledSize(avatar_label.size() if not movie.isValid() else movie.scaledSize())
            avatar_label.setMovie(movie)
            movie.start()
            self._movie = movie
        else:
            avatar_label.setText("")
        layout.addWidget(avatar_label)

        layout.addSpacing(12)

        # App name
        title = QLabel("Razer Lighting")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #e8e8ee;"
            " letter-spacing: 1px; background: transparent;")
        layout.addWidget(title)

        # Version tag
        version = QLabel(f"v{VERSION}")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #44D62C;"
            " letter-spacing: 3px; background: transparent;")
        layout.addWidget(version)

        layout.addSpacing(8)

        # Tagline
        tagline = QLabel("Procedural keyboard lighting for Linux")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(
            "font-size: 11px; color: #505060; font-style: italic; background: transparent;")
        layout.addWidget(tagline)

        layout.addSpacing(6)

        # Author
        author = QLabel("by sl4ppy")
        author.setAlignment(Qt.AlignCenter)
        author.setStyleSheet("font-size: 12px; color: #808090; background: transparent;")
        layout.addWidget(author)

        # Copyright
        date_label = QLabel("\u00a9 2026")
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet("font-size: 10px; color: #404048; background: transparent;")
        layout.addWidget(date_label)

        layout.addSpacing(8)

        # GitHub link
        link = QLabel(
            f'<a href="{GITHUB_URL}" style="color: #44D62C; text-decoration: none;">'
            f'{GITHUB_URL}</a>')
        link.setAlignment(Qt.AlignCenter)
        link.setOpenExternalLinks(True)
        link.setStyleSheet("font-size: 10px; background: transparent;")
        layout.addWidget(link)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #18181c;
                border: 1px solid #252528;
                border-radius: 5px;
                padding: 7px 18px;
                color: #c0c0cc;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #44D62C;
                color: #e8e8ee;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._bg.setGeometry(0, 0, self.width(), self.height())


def main():
    from config_window import DARK_STYLESHEET
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)
    dialog = AboutDialog()
    dialog.exec_()


if __name__ == "__main__":
    main()
