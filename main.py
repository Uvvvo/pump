#!/usr/bin/env python3
"""
iPump - نظام التنبؤ بفشل المضخات النفطية باستخدام الذكاء الاصطناعي
المطور: فريق الهندسة والذكاء الاصطناعي
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
        """تهيئة إعدادات التطبيق"""
        # تعيين الخط العام
        font = QFont("Segoe UI", 10)
        self.app.setFont(font)
        
        # تطبيق الثيم الداكن
        self.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        
        # تعيين أيقونة التطبيق
        if os.path.exists("assets/icon.png"):
            self.app.setWindowIcon(QIcon("assets/icon.png"))
        
        # إعداد نظام التسجيل
        self.logger = setup_logger()
        self.logger.info("تم تشغيل تطبيق iPump")
        
    def run(self):
        """تشغيل التطبيق"""
        self.main_window.show()
        return self.app.exec()

def main():
    """الدالة الرئيسية"""
    try:
        ipump_app = iPumpApp()
        sys.exit(ipump_app.run())
    except Exception as e:
        print(f"خطأ في تشغيل التطبيق: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()