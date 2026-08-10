"""main.py - Entry point for Temp Cleaner application."""

import os
import sys

from PyQt6.QtWidgets import QApplication
from gui_langas import MainWindow


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
