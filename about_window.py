#!/usr/bin/env python3
"""About dialog for Razer Lighting."""

import os
import sys
import webbrowser

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QPushButton,
)

VERSION = "1.0.0"
GITHUB_URL = "https://github.com/sl4ppy/RazerLighting"
AVATAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "avatar.gif")


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About Razer Lighting")
        self.setFixedSize(300, 260)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignHCenter)

        # Avatar
        avatar_label = QLabel()
        avatar_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(AVATAR_PATH):
            movie = QMovie(AVATAR_PATH)
            movie.setScaledSize(avatar_label.size() if not movie.isValid() else movie.scaledSize())
            avatar_label.setMovie(movie)
            movie.start()
            self._movie = movie  # prevent GC
        else:
            avatar_label.setText("[avatar]")
        layout.addWidget(avatar_label)

        layout.addSpacing(8)

        # App name + version
        title = QLabel(f"Razer Lighting v{VERSION}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Author
        author = QLabel("by sl4ppy")
        author.setAlignment(Qt.AlignCenter)
        author.setStyleSheet("font-size: 14px;")
        layout.addWidget(author)

        layout.addSpacing(4)

        # Date
        date_label = QLabel("\u00a9 2026")
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(date_label)

        layout.addSpacing(4)

        # GitHub link
        link = QLabel(f'<a href="{GITHUB_URL}">{GITHUB_URL}</a>')
        link.setAlignment(Qt.AlignCenter)
        link.setOpenExternalLinks(True)
        link.setStyleSheet("font-size: 12px;")
        layout.addWidget(link)

        layout.addSpacing(12)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)


def main():
    from config_window import DARK_STYLESHEET
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)
    dialog = AboutDialog()
    dialog.exec_()


if __name__ == "__main__":
    main()
