"""
النافذة الرئيسية لتطبيق iPump - مع إضافة أزرار إدارة المضخات والحساسات
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QStatusBar, QMessageBox, QToolBar, 
                           QPushButton, QLabel, QSplitter, QFrame, QMenu,
                           QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QGridLayout,
                           QComboBox, QDateEdit, QTextEdit, QListWidget, QListWidgetItem, QGroupBox)
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from PyQt6.QtCore import QSize

from ui.dashboard import DashboardTab
from ui.analytics import AnalyticsTab
from ui.maintenance import MaintenanceTab
from ui.reporting import ReportingTab
from ui.settings import SettingsTab
from config import APP_CONFIG, UI_CONFIG
from database import db_manager
from ai_models import failure_predictor
from utils.logger import get_logger

class MainWindow(QMainWindow):
    update_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.current_pump_id = 1
        self.setup_ui()
        self.setup_timer()
        self.load_initial_data()
        
    def setup_ui(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle(APP_CONFIG['name'])
        self.setGeometry(100, 100, 1400, 900)
        
        # إنشاء الشريط الرئيسي
        self.create_toolbar()
        
        # إنشاء القائمة الرئيسية
        self.create_menubar()
        
        # إنشاء الويدجت المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # شريط الحالة العلوي
        self.create_status_bar()
        main_layout.addWidget(self.top_status_bar)
        
        # منطقة المحتوى الرئيسية
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # اللوحة الجانبية
        self.side_panel = self.create_side_panel()
        content_splitter.addWidget(self.side_panel)
        
        # منطقة التبويبات الرئيسية
        self.tab_widget = QTabWidget()
        self.setup_tabs()
        content_splitter.addWidget(self.tab_widget)
        
        # تعيين نسب التقسيم
        content_splitter.setSizes([300, 1100])
        main_layout.addWidget(content_splitter)
        
        # شريط الحالة السفلي
        self.create_bottom_status_bar()
        main_layout.addWidget(self.bottom_status_bar)
        
    def create_menubar(self):
        """إنشاء شريط القوائم"""
        menubar = self.menuBar()
        
        # قائمة الملف
        file_menu = menubar.addMenu("الملف")
        
        new_pump_action = QAction("إضافة مضخة جديدة", self)
        new_pump_action.setShortcut("Ctrl+P")
        new_pump_action.triggered.connect(self.add_new_pump)
        file_menu.addAction(new_pump_action)
        
        link_sensors_action = QAction("ربط الحساسات", self)
        link_sensors_action.setShortcut("Ctrl+S")
        link_sensors_action.triggered.connect(self.link_sensors)
        file_menu.addAction(link_sensors_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("استيراد بيانات", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        export_action = QAction("تصدير البيانات", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("خروج", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # قائمة العرض
        view_menu = menubar.addMenu("العرض")
        
        refresh_action = QAction("تحديث", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        view_menu.addAction(refresh_action)
        
        fullscreen_action = QAction("ملء الشاشة", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # قائمة الأدوات
        tools_menu = menubar.addMenu("الأدوات")
        
        pump_manager_action = QAction("مدير المضخات", self)
        pump_manager_action.setShortcut("Ctrl+M")
        pump_manager_action.triggered.connect(self.open_pump_manager)
        tools_menu.addAction(pump_manager_action)
        
        sensor_manager_action = QAction("مدير الحساسات", self)
        sensor_manager_action.setShortcut("Ctrl+L")
        sensor_manager_action.triggered.connect(self.open_sensor_manager)
        tools_menu.addAction(sensor_manager_action)
        
        # قائمة المساعدة
        help_menu = menubar.addMenu("المساعدة")
        
        about_action = QAction("عن البرنامج", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("الوثائق", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
    def create_toolbar(self):
        """إنشاء شريط الأدوات مع أزرار إدارة المضخات"""
        toolbar = QToolBar("الشريط الرئيسي")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # إجراءات الملف
        new_action = QAction("مشروع جديد", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)
        
        save_action = QAction("حفظ", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_data)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # أزرار إدارة المضخات
        add_pump_action = QAction("إضافة مضخة", self)
        add_pump_action.triggered.connect(self.add_new_pump)
        toolbar.addAction(add_pump_action)
        
        link_sensors_action = QAction("ربط حساسات", self)
        link_sensors_action.triggered.connect(self.link_sensors)
        toolbar.addAction(link_sensors_action)
        
        toolbar.addSeparator()
        
        # إجراءات العرض
        refresh_action = QAction("تحديث", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        # زر الإعدادات
        settings_action = QAction("الإعدادات", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
    def create_status_bar(self):
        """إنشاء شريط الحالة العلوي"""
        self.top_status_bar = QFrame()
        self.top_status_bar.setMaximumHeight(60)
        self.top_status_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e3a5f, stop: 1 #0d1b2a);
                border-bottom: 2px solid #1e88e5;
            }
        """)
        
        top_layout = QHBoxLayout(self.top_status_bar)
        top_layout.setContentsMargins(15, 5, 15, 5)
        
        # عنوان التطبيق
        title_label = QLabel(APP_CONFIG['name'])
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1e88e5;")
        
        # معلومات النظام
        system_info = QLabel(f"الإصدار: {APP_CONFIG['version']} | {APP_CONFIG['company']}")
        system_info.setStyleSheet("color: #90a4ae;")
        
        # حالة الاتصال
        self.connection_status = QLabel("🟢 متصل")
        self.connection_status.setStyleSheet("color: #51cf66; font-weight: bold;")
        
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        top_layout.addWidget(system_info)
        top_layout.addSpacing(20)
        top_layout.addWidget(self.connection_status)
        
    def create_side_panel(self):
        """إنشاء اللوحة الجانبية مع أزرار سريعة"""
        side_panel = QFrame()
        side_panel.setFrameShape(QFrame.Shape.StyledPanel)
        side_panel.setMinimumWidth(280)
        side_panel.setMaximumWidth(350)
        side_panel.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-right: 1px solid #1e293b;
            }
        """)
        
        layout = QVBoxLayout(side_panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # عنوان اللوحة الجانبية
        side_title = QLabel("نظرة عامة على النظام")
        side_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1e88e5;
                padding: 10px;
                border-bottom: 2px solid #1e88e5;
                background-color: #1e293b;
                border-radius: 5px;
            }
        """)
        side_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(side_title)
        
        # أزرار سريعة
        quick_actions_group = QGroupBox("إجراءات سريعة")
        quick_actions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #e2e8f0;
                border: 2px solid #334155;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #94a3b8;
            }
        """)
        quick_actions_layout = QVBoxLayout(quick_actions_group)
        
        # زر إضافة مضخة جديدة
        self.quick_add_pump_btn = QPushButton("➕ إضافة مضخة جديدة")
        self.quick_add_pump_btn.clicked.connect(self.add_new_pump)
        self.quick_add_pump_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e88e5;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                text-align: center;
                border: none;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        quick_actions_layout.addWidget(self.quick_add_pump_btn)
        
        # زر ربط الحساسات
        self.quick_link_sensors_btn = QPushButton("🔗 ربط الحساسات بالمضخات")
        self.quick_link_sensors_btn.clicked.connect(self.link_sensors)
        self.quick_link_sensors_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                text-align: center;
                border: none;
            }
            QPushButton:hover {
                background-color: #40a94c;
            }
            QPushButton:pressed {
                background-color: #2f855a;
            }
        """)
        quick_actions_layout.addWidget(self.quick_link_sensors_btn)
        
        # زر إدارة المضخات
        self.quick_manage_pumps_btn = QPushButton("⚙️ إدارة المضخات")
        self.quick_manage_pumps_btn.clicked.connect(self.open_pump_manager)
        self.quick_manage_pumps_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59f00;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                text-align: center;
                border: none;
            }
            QPushButton:hover {
                background-color: #e67700;
            }
            QPushButton:pressed {
                background-color: #b35900;
            }
        """)
        quick_actions_layout.addWidget(self.quick_manage_pumps_btn)
        
        layout.addWidget(quick_actions_group)
        
        # إحصائيات سريعة
        self.setup_quick_stats(layout)
        
        # المضخات النشطة
        self.setup_active_pumps(layout)
        
        # الإنذارات النشطة
        self.setup_active_alerts(layout)
        
        layout.addStretch()
        
        return side_panel
    
    def setup_quick_stats(self, layout):
        """إعداد الإحصائيات السريعة"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #334155;
            }
        """)
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_title = QLabel("📊 الإحصائيات السريعة")
        stats_title.setStyleSheet("font-weight: bold; color: #e3f2fd; font-size: 14px;")
        stats_layout.addWidget(stats_title)
        
        # إحصائيات حية
        stats_grid = QGridLayout()
        
        self.total_pumps_label = QLabel("0")
        self.total_pumps_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e88e5;")
        stats_grid.addWidget(QLabel("إجمالي المضخات:"), 0, 0)
        stats_grid.addWidget(self.total_pumps_label, 0, 1)
        
        self.operational_label = QLabel("0")
        self.operational_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #51cf66;")
        stats_grid.addWidget(QLabel("المضخات العاملة:"), 1, 0)
        stats_grid.addWidget(self.operational_label, 1, 1)
        
        self.sensors_label = QLabel("0")
        self.sensors_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f59f00;")
        stats_grid.addWidget(QLabel("الحساسات النشطة:"), 2, 0)
        stats_grid.addWidget(self.sensors_label, 2, 1)
        
        self.alerts_label = QLabel("0")
        self.alerts_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff6b6b;")
        stats_grid.addWidget(QLabel("الإنذارات النشطة:"), 3, 0)
        stats_grid.addWidget(self.alerts_label, 3, 1)
        
        stats_layout.addLayout(stats_grid)
        layout.addWidget(stats_frame)
    
    def setup_active_pumps(self, layout):
        """إعداد قائمة المضخات النشطة"""
        pumps_frame = QFrame()
        pumps_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #334155;
            }
        """)
        pumps_layout = QVBoxLayout(pumps_frame)
        
        pumps_title = QLabel("🔧 المضخات النشطة")
        pumps_title.setStyleSheet("font-weight: bold; color: #e3f2fd; font-size: 14px;")
        pumps_layout.addWidget(pumps_title)
        
        self.pumps_list = QListWidget()
        self.pumps_list.setStyleSheet("""
            QListWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 5px;
                color: #e2e8f0;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #334155;
            }
            QListWidget::item:selected {
                background-color: #1e88e5;
            }
        """)
        self.pumps_list.itemClicked.connect(self.on_pump_selected)
        pumps_layout.addWidget(self.pumps_list)
        
        layout.addWidget(pumps_frame)
    
    def setup_active_alerts(self, layout):
        """إعداد عرض الإنذارات النشطة"""
        alerts_frame = QFrame()
        alerts_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #334155;
            }
        """)
        alerts_layout = QVBoxLayout(alerts_frame)
        
        alerts_title = QLabel("🚨 الإنذارات النشطة")
        alerts_title.setStyleSheet("font-weight: bold; color: #ff6b6b; font-size: 14px;")
        alerts_layout.addWidget(alerts_title)
        
        self.alerts_list = QLabel("لا توجد إنذارات نشطة")
        self.alerts_list.setStyleSheet("""
            QLabel {
                color: #b0bec5; 
                padding: 10px;
                background-color: #0f172a;
                border-radius: 5px;
                border: 1px solid #334155;
            }
        """)
        self.alerts_list.setWordWrap(True)
        self.alerts_list.setMinimumHeight(80)
        alerts_layout.addWidget(self.alerts_list)
        
        # زر عرض جميع الإنذارات
        view_all_alerts_btn = QPushButton("عرض جميع الإنذارات")
        view_all_alerts_btn.clicked.connect(self.view_all_alerts)
        view_all_alerts_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        alerts_layout.addWidget(view_all_alerts_btn)
        
        layout.addWidget(alerts_frame)
    
    def setup_tabs(self):
        """إعداد التبويبات الرئيسية"""
        self.dashboard_tab = DashboardTab()
        self.analytics_tab = AnalyticsTab()
        self.maintenance_tab = MaintenanceTab()
        self.reporting_tab = ReportingTab()
        self.settings_tab = SettingsTab()
        
        self.tab_widget.addTab(self.dashboard_tab, "🏠 لوحة التحكم")
        self.tab_widget.addTab(self.analytics_tab, "📈 التحليلات")
        self.tab_widget.addTab(self.maintenance_tab, "🔧 إدارة الصيانة")
        self.tab_widget.addTab(self.reporting_tab, "📊 التقارير")
        self.tab_widget.addTab(self.settings_tab, "⚙️ الإعدادات")
        
        # تخصيص مظهر التبويبات
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #334155;
                background-color: #0f172a;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #1e88e5;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #334155;
            }
        """)
        
        # ربط إشارة التحديث
        self.update_signal.connect(self.update_all_tabs)
    
    def setup_timer(self):
        """إعداد المؤقت للتحديث التلقائي"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.auto_update)
        self.update_timer.start(UI_CONFIG['refresh_interval'])
        
        # مؤقت للتحديث البطيء (كل دقيقة)
        self.slow_update_timer = QTimer()
        self.slow_update_timer.timeout.connect(self.slow_update)
        self.slow_update_timer.start(60000)  # كل دقيقة
    
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        self.update_quick_stats()
        self.update_active_pumps()
        self.update_active_alerts()
        self.update_connection_status()
    
    def update_quick_stats(self):
        """تحديث الإحصائيات السريعة"""
        try:
            stats = db_manager.get_system_stats()
            
            self.total_pumps_label.setText(str(stats.get('total_pumps', 0)))
            self.operational_label.setText(str(stats.get('operational_pumps', 0)))
            self.sensors_label.setText(str(stats.get('active_sensors', 0)))
            self.alerts_label.setText(str(stats.get('active_alerts', 0)))
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث الإحصائيات: {e}")
    
    def update_active_pumps(self):
        """تحديث قائمة المضخات النشطة"""
        try:
            self.pumps_list.clear()
            pumps = db_manager.get_pumps_with_stats()
            
            for _, pump in pumps.iterrows():
                status_icon = "🟢" if pump['status'] == 'operational' else "🟡" if pump['status'] == 'maintenance' else "🔴"
                item_text = f"{status_icon} {pump['name']}\n📍 {pump['location']} | ⚡ {pump['sensor_count']} حساس"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, pump['id'])
                
                # تلوين العنصر حسب الحالة
                if pump['status'] == 'operational':
                    item.setBackground(QColor(81, 207, 102, 50))
                elif pump['status'] == 'maintenance':
                    item.setBackground(QColor(255, 179, 0, 50))
                else:
                    item.setBackground(QColor(255, 107, 107, 50))
                
                self.pumps_list.addItem(item)
                
        except Exception as e:
            self.logger.error(f"خطأ في تحديث قائمة المضخات: {e}")
    
    def update_active_alerts(self):
        """تحديث قائمة الإنذارات النشطة"""
        try:
            alerts = db_manager.get_active_alerts()
            
            if alerts.empty:
                self.alerts_list.setText("✅ لا توجد إنذارات نشطة")
                return
            
            alerts_text = ""
            alert_count = 0
            for _, alert in alerts.head(3).iterrows():  # عرض أول 3 إنذارات فقط
                severity_icon = "🔴" if alert['severity'] == 'high' else "🟡" if alert['severity'] == 'medium' else "🔵"
                alerts_text += f"{severity_icon} {alert['pump_name']}: {alert['message']}\n"
                alert_count += 1
            
            if len(alerts) > 3:
                alerts_text += f"... ⚠️ و{len(alerts) - 3} إنذار آخر"
            
            self.alerts_list.setText(alerts_text)
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث الإنذارات: {e}")
    
    def update_connection_status(self):
        """تحديث حالة الاتصال"""
        try:
            # محاكاة فحص حالة الاتصال
            stats = db_manager.get_system_stats()
            last_update = stats.get('last_data_update')
            
            if last_update:
                last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                time_diff = datetime.now().replace(tzinfo=None) - last_update_time.replace(tzinfo=None)
                
                if time_diff.total_seconds() < 300:  # أقل من 5 دقائق
                    self.connection_status.setText("🟢 متصل")
                    self.connection_status.setStyleSheet("color: #51cf66; font-weight: bold;")
                else:
                    self.connection_status.setText("🟡 اتصال ضعيف")
                    self.connection_status.setStyleSheet("color: #f59f00; font-weight: bold;")
            else:
                self.connection_status.setText("🔴 غير متصل")
                self.connection_status.setStyleSheet("color: #ff6b6b; font-weight: bold;")
                
        except Exception as e:
            self.logger.error(f"خطأ في تحديث حالة الاتصال: {e}")
    
    def auto_update(self):
        """التحديث التلقائي للبيانات"""
        self.update_quick_stats()
        self.update_active_alerts()
        self.update_signal.emit()
    
    def slow_update(self):
        """التحديث البطيء للبيانات"""
        self.update_active_pumps()
        self.update_connection_status()
    
    def update_all_tabs(self):
        """تحديث جميع التبويبات"""
        self.dashboard_tab.refresh_data()
        self.analytics_tab.refresh_data()
        self.maintenance_tab.refresh_data()
    
    def create_bottom_status_bar(self):
        """إنشاء شريط الحالة السفلي"""
        self.bottom_status_bar = QStatusBar()
        self.bottom_status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #0f172a;
                color: #94a3b8;
                border-top: 1px solid #334155;
            }
        """)
        self.setStatusBar(self.bottom_status_bar)
        
        # إضافة معلومات الحالة
        self.status_label = QLabel("✅ جاهز")
        self.bottom_status_bar.addWidget(self.status_label)
        
        # إضافة معلومات الذاكرة
        self.memory_label = QLabel()
        self.update_memory_usage()
        self.bottom_status_bar.addPermanentWidget(self.memory_label)
        
        # إضافة الوقت
        self.time_label = QLabel()
        self.update_time()
        self.bottom_status_bar.addPermanentWidget(self.time_label)
        
        # مؤقتات التحديث
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(5000)  # كل 5 ثواني
    
    def update_time(self):
        """تحديث عرض الوقت"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"🕒 {current_time}")
    
    def update_memory_usage(self):
        """تحديث استخدام الذاكرة"""
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            self.memory_label.setText(f"💾 {memory_usage:.1f} MB")
        except:
            self.memory_label.setText("💾 -- MB")
    
    def on_pump_selected(self, item):
        """عند اختيار مضخة من القائمة"""
        try:
            pump_id = item.data(Qt.ItemDataRole.UserRole)
            self.current_pump_id = pump_id
            
            # تحديث التبويبات بالمضخة المحددة
            if hasattr(self.dashboard_tab, 'select_pump'):
                self.dashboard_tab.select_pump(pump_id)
            if hasattr(self.analytics_tab, 'select_pump'):
                self.analytics_tab.select_pump(pump_id)
            
            self.status_label.setText(f"✅ تم اختيار المضخة: {item.text().split(' ')[1]}")
            
        except Exception as e:
            self.logger.error(f"خطأ في اختيار المضخة: {e}")
    
    def add_new_pump(self):
        """إضافة مضخة جديدة"""
        try:
            dialog = AddPumpDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                pump_data = dialog.get_pump_data()
                pump_id = db_manager.add_pump(pump_data)
                
                if pump_id > 0:
                    self.status_label.setText(f"✅ تم إضافة المضخة: {pump_data['name']}")
                    self.load_initial_data()
                    self.update_all_tabs()
                    
                    # الانتقال إلى تبويب إدارة المضخات
                    self.tab_widget.setCurrentWidget(self.maintenance_tab)
                    
                    QMessageBox.information(self, "تم بنجاح", f"تم إضافة المضخة '{pump_data['name']}' بنجاح")
                else:
                    QMessageBox.warning(self, "خطأ", "فشل في إضافة المضخة. قد يكون الاسم مكرراً.")
            
        except Exception as e:
            self.logger.error(f"خطأ في إضافة المضخة: {e}")
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء إضافة المضخة: {str(e)}")
    
    def link_sensors(self):
        """ربط الحساسات بالمضخات"""
        try:
            dialog = LinkSensorsDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.status_label.setText("✅ تم ربط الحساسات بنجاح")
                self.load_initial_data()
                QMessageBox.information(self, "تم بنجاح", "تم ربط الحساسات بالمضخات بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في ربط الحساسات: {e}")
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء ربط الحساسات: {str(e)}")
    
    def open_pump_manager(self):
        """فتح مدير المضخات"""
        try:
            self.tab_widget.setCurrentWidget(self.maintenance_tab)
            self.status_label.setText("📋 فتح مدير المضخات")
        except Exception as e:
            self.logger.error(f"خطأ في فتح مدير المضخات: {e}")
    
    def open_sensor_manager(self):
        """فتح مدير الحساسات"""
        try:
            self.tab_widget.setCurrentWidget(self.maintenance_tab)
            # هنا يمكن إضافة منطق للانتقال إلى قسم الحساسات مباشرة
            self.status_label.setText("📡 فتح مدير الحساسات")
        except Exception as e:
            self.logger.error(f"خطأ في فتح مدير الحساسات: {e}")
    
    def open_settings(self):
        """فتح الإعدادات"""
        try:
            self.tab_widget.setCurrentWidget(self.settings_tab)
            self.status_label.setText("⚙️ فتح الإعدادات")
        except Exception as e:
            self.logger.error(f"خطأ في فتح الإعدادات: {e}")
    
    def view_all_alerts(self):
        """عرض جميع الإنذارات"""
        try:
            # الانتقال إلى تبويب التحليلات أو إنشاء نافذة جديدة للإنذارات
            self.tab_widget.setCurrentWidget(self.analytics_tab)
            self.status_label.setText("🚨 عرض جميع الإنذارات")
        except Exception as e:
            self.logger.error(f"خطأ في عرض الإنذارات: {e}")
    
    def import_data(self):
        """استيراد بيانات"""
        try:
            QMessageBox.information(self, "استيراد بيانات", "سيتم تطوير ميزة الاستيراد في النسخة القادمة")
        except Exception as e:
            self.logger.error(f"خطأ في استيراد البيانات: {e}")
    
    def export_data(self):
        """تصدير البيانات"""
        try:
            QMessageBox.information(self, "تصدير البيانات", "سيتم تطوير ميزة التصدير في النسخة القادمة")
        except Exception as e:
            self.logger.error(f"خطأ في تصدير البيانات: {e}")
    
    def toggle_fullscreen(self):
        """تبديل وضع ملء الشاشة"""
        if self.isFullScreen():
            self.showNormal()
            self.status_label.setText("🖥️ الخروج من وضع ملء الشاشة")
        else:
            self.showFullScreen()
            self.status_label.setText("🖥️ دخول إلى وضع ملء الشاشة")
    
    def show_about(self):
        """عرض معلومات عن البرنامج"""
        about_text = f"""
        <h2>{APP_CONFIG['name']}</h2>
        <p><b>الإصدار:</b> {APP_CONFIG['version']}</p>
        <p><b>الشركة:</b> {APP_CONFIG['company']}</p>
        <p><b>الوصف:</b> {APP_CONFIG['description']}</p>
        <p><b>حقوق النشر:</b> {APP_CONFIG['copyright']}</p>
        <hr>
        <p>نظام متكامل للتنبؤ بفشل المضخات النفطية باستخدام الذكاء الاصطناعي.</p>
        <p>تم تطويره بلغة Python مع واجهة Qt الحديثة.</p>
        """
        
        QMessageBox.about(self, "عن البرنامج", about_text)
    
    def show_documentation(self):
        """عرض الوثائق"""
        QMessageBox.information(self, "الوثائق", "سيتم توفير الوثائق في النسخة القادمة")
    
    def new_project(self):
        """إنشاء مشروع جديد"""
        reply = QMessageBox.question(self, "مشروع جديد", 
                                   "هل تريد إنشاء مشروع جديد؟\nسيتم فقدان أي بيانات غير محفوظة.",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.status_label.setText("🆕 تم إنشاء مشروع جديد")
            # هنا يمكن إضافة منطق لمسح البيانات الحالية
            QTimer.singleShot(2000, lambda: self.status_label.setText("✅ جاهز"))
    
    def save_data(self):
        """حفظ البيانات"""
        self.status_label.setText("💾 جاري حفظ البيانات...")
        # محاكاة عملية الحفظ
        QTimer.singleShot(1500, lambda: self.status_label.setText("✅ تم حفظ البيانات"))
    
    def refresh_data(self):
        """تحديث البيانات يدوياً"""
        self.status_label.setText("🔄 جاري تحديث البيانات...")
        self.auto_update()
        self.slow_update()
        QTimer.singleShot(1000, lambda: self.status_label.setText("✅ تم تحديث البيانات"))
    
    def closeEvent(self, event):
        """معالجة حدث إغلاق التطبيق"""
        reply = QMessageBox.question(self, "تأكيد الخروج",
                                   "هل أنت متأكد من أنك تريد إغلاق التطبيق؟",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("تم إغلاق تطبيق iPump")
            # حفظ الإعدادات وإغلاق الموارد
            self.update_timer.stop()
            self.slow_update_timer.stop()
            self.time_timer.stop()
            self.memory_timer.stop()
            event.accept()
        else:
            event.ignore()

class AddPumpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة مضخة جديدة")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        """تهيئة واجهة إضافة مضخة"""
        layout = QVBoxLayout(self)
        
        # نموذج إدخال البيانات
        form_layout = QFormLayout()
        
        # حقل اسم المضخة
        self.pump_name = QLineEdit()
        self.pump_name.setPlaceholderText("أدخل اسم المضخة (مطلوب)")
        self.pump_name.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("اسم المضخة:*", self.pump_name)
        
        # حقل الموقع
        self.pump_location = QLineEdit()
        self.pump_location.setPlaceholderText("أدخل موقع المضخة (مطلوب)")
        self.pump_location.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("الموقع:*", self.pump_location)
        
        # حقل النوع
        self.pump_type = QComboBox()
        self.pump_type.addItems(["طرد مركزي", "مكبسية", "تغذية", "خدمة مساعدة", "نقل", "مصفاة"])
        self.pump_type.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("نوع المضخة:*", self.pump_type)
        
        # حقل تاريخ التركيب
        self.installation_date = QDateEdit()
        self.installation_date.setDate(QDate.currentDate())
        self.installation_date.setCalendarPopup(True)
        self.installation_date.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("تاريخ التركيب:*", self.installation_date)
        
        # حقل الحالة
        self.pump_status = QComboBox()
        self.pump_status.addItems(["تعمل", "صيانة", "متوقفة"])
        self.pump_status.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("الحالة:*", self.pump_status)
        
        # حقل معلومات إضافية
        self.pump_notes = QTextEdit()
        self.pump_notes.setMaximumHeight(100)
        self.pump_notes.setPlaceholderText("ملاحظات إضافية عن المضخة...")
        self.pump_notes.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("ملاحظات:", self.pump_notes)
        
        layout.addLayout(form_layout)
        
        # معلومات إضافية
        info_label = QLabel("💡 الحقول marked with * are required")
        info_label.setStyleSheet("color: #94a3b8; font-size: 12px; padding: 10px;")
        layout.addWidget(info_label)
        
        # أزرار الحفظ والإلغاء
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_pump_data(self):
        """الحصول على بيانات المضخة المدخلة"""
        status_map = {
            "تعمل": "operational",
            "صيانة": "maintenance", 
            "متوقفة": "stopped"
        }
        
        return {
            'name': self.pump_name.text().strip(),
            'location': self.pump_location.text().strip(),
            'type': self.pump_type.currentText(),
            'installation_date': self.installation_date.date().toString("yyyy-MM-dd"),
            'status': status_map[self.pump_status.currentText()],
            'notes': self.pump_notes.toPlainText().strip()
        }
    
    def accept(self):
        """عند النقر على موافق"""
        if not self.pump_name.text().strip():
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم المضخة")
            return
        
        if not self.pump_location.text().strip():
            QMessageBox.warning(self, "تحذير", "يرجى إدخال موقع المضخة")
            return
        
        super().accept()

class LinkSensorsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ربط الحساسات بالمضخات")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setup_ui()
        
    def setup_ui(self):
        """تهيئة واجهة ربط الحساسات"""
        layout = QVBoxLayout(self)
        
        # قسم اختيار المضخة
        pump_group = QGroupBox("اختيار المضخة")
        pump_layout = QFormLayout(pump_group)
        
        self.pump_selector = QComboBox()
        # تحميل المضخات من قاعدة البيانات
        pumps = db_manager.get_pumps()
        for _, pump in pumps.iterrows():
            self.pump_selector.addItem(f"{pump['name']} - {pump['location']}", pump['id'])
        
        pump_layout.addRow("المضخة:", self.pump_selector)
        layout.addWidget(pump_group)
        
        # قسم الحساسات المتاحة
        sensors_group = QGroupBox("الحساسات المتاحة للربط")
        sensors_layout = QVBoxLayout(sensors_group)
        
        # قائمة الحساسات
        self.sensors_list = QListWidget()
        
        # إضافة أنواع الحساسات المتاحة
        available_sensors = [
            "حساس الاهتزاز X - قياس الاهتزاز في المحور X",
            "حساس الاهتزاز Y - قياس الاهتزاز في المحور Y", 
            "حساس الاهتزاز Z - قياس الاهتزاز في المحور Z",
            "حساس درجة الحرارة - قياس درجة حرارة المضخة",
            "حساس الضغط - قياس ضغط التشغيل",
            "حساس التدفق - قياس معدل التدفق",
            "حساس مستوى الزيت - قياس مستوى زيت التشحيم",
            "حساس جودة الزيت - قياس جودة زيت التشحيم",
            "حساس استهلاك الطاقة - قياس استهلاك الطاقة",
            "حساس حرارة المحامل - قياس درجة حرارة المحامل"
        ]
        
        for sensor in available_sensors:
            item = QListWidgetItem(sensor)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.sensors_list.addItem(item)
        
        sensors_layout.addWidget(self.sensors_list)
        layout.addWidget(sensors_group)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("تحديد الكل")
        self.select_all_btn.clicked.connect(self.select_all_sensors)
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("إلغاء التحديد")
        self.deselect_all_btn.clicked.connect(self.deselect_all_sensors)
        button_layout.addWidget(self.deselect_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # معلومات
        info_label = QLabel("🔍 حدد الحساسات التي تريد ربطها بالمضخة المحددة")
        info_label.setStyleSheet("color: #94a3b8; padding: 10px;")
        layout.addWidget(info_label)
        
        # أزرار الحفظ والإلغاء
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def select_all_sensors(self):
        """تحديد جميع الحساسات"""
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def deselect_all_sensors(self):
        """إلغاء تحديد جميع الحساسات"""
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
    
    def get_selected_sensors(self):
        """الحصول على الحساسات المحددة"""
        selected_sensors = []
        sensor_type_map = {
            "حساس الاهتزاز X": "vibration_x",
            "حساس الاهتزاز Y": "vibration_y",
            "حساس الاهتزاز Z": "vibration_z",
            "حساس درجة الحرارة": "temperature",
            "حساس الضغط": "pressure",
            "حساس التدفق": "flow_rate",
            "حساس مستوى الزيت": "oil_level",
            "حساس جودة الزيت": "oil_quality",
            "حساس استهلاك الطاقة": "power_consumption",
            "حساس حرارة المحامل": "bearing_temperature"
        }
        
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                sensor_name = item.text().split(' - ')[0]
                sensor_type = sensor_type_map.get(sensor_name, sensor_name)
                selected_sensors.append({
                    'sensor_type': sensor_type,
                    'sensor_id': f"{sensor_type.upper()}_{self.pump_selector.currentData()}_{i+1}",
                    'model': 'Generic Sensor'
                })
        
        return selected_sensors
    
    def accept(self):
        """عند النقر على موافق"""
        selected_sensors = self.get_selected_sensors()
        if not selected_sensors:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد حساس واحد على الأقل")
            return
        
        pump_id = self.pump_selector.currentData()
        pump_name = self.pump_selector.currentText().split(' - ')[0]
        
        # عرض ملخص الربط
        summary = f"""
        ملخص عملية الربط:
        
        المضخة: {pump_name}
        عدد الحساسات المحددة: {len(selected_sensors)}
        
        الحساسات المحددة:
        {chr(10).join(['• ' + sensor['sensor_type'] for sensor in selected_sensors])}
        """
        
        reply = QMessageBox.question(
            self, 
            "تأكيد الربط", 
            summary + "\nهل تريد متابعة عملية الربط؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # تنفيذ عملية الربط الفعلية
            success = db_manager.link_sensors_to_pump(pump_id, selected_sensors)
            if success:
                super().accept()
            else:
                QMessageBox.warning(self, "خطأ", "فشل في ربط الحساسات. قد تكون بعض الحساسات مربوطة مسبقاً.")