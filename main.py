#!/usr/bin/env python3
"""iPump - Intelligent pump failure prediction system.

Application developer: Hussein Abdullah
Phone: 07813563139
Location: Dhi Qar, Iraq
Email: ah343238@gmail.com
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QTimer, Qt, QSize
import qdarkstyle

from ui.main_window import MainWindow
from utils.logger import setup_logger
from config import APP_CONFIG

class iPumpApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_application()
        self.main_window = MainWindow()
        
    def setup_application(self):
        """Configure global application settings."""
        # Configure default font
        font = QFont("Segoe UI", 10)
        self.app.setFont(font)

        # Apply the dark theme
        self.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))

        # Set application icon when available
        if os.path.exists("assets/icon.png"):
            self.app.setWindowIcon(QIcon("assets/icon.png"))

        # Initialize logging
        self.logger = setup_logger()
        self.logger.info("iPump application started")

    def run(self):
        """Start the Qt event loop."""
        self.main_window.show()
        return self.app.exec()

def main():
    """Entry point of the application."""
    try:
        ipump_app = iPumpApp()
        sys.exit(ipump_app.run())
    except Exception as e:
        print(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()