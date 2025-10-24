"""
Main window for iPump application
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QStatusBar, QMessageBox, QToolBar,
                             QPushButton, QLabel, QSplitter, QFrame, QMenu,
                             QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QGridLayout,
                             QComboBox, QDateEdit, QTextEdit, QListWidget, QListWidgetItem, QGroupBox,
                             QSpinBox)
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate, QThread, QSize
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
import pandas as pd

from ui.dashboard import DashboardTab
from ui.analytics import AnalyticsTab
from ui.maintenance import MaintenanceTab
from ui.reporting import ReportingTab
from ui.settings import SettingsTab

from config import APP_CONFIG, UI_CONFIG
from database import db_manager
from ai_models import failure_predictor
from utils.logger import get_logger

from ui.workers import BackgroundWorker

class MainWindow(QMainWindow):
    update_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.current_pump_id = 1
        self.cache = {}  # Add caching system
        self.cache_timeout = 30000  # 30 seconds
        self.last_update_time = {}
        self._bg_thread = None
        self._bg_worker = None
        self.setup_ui()
        self.setup_timer()
        self.load_initial_data()

    def setup_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(APP_CONFIG['name'])
        self.setGeometry(100, 100, 1400, 900)
        
        # Create main toolbar
        self.create_toolbar()
        
        # Create main menu
        self.create_menubar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Top status bar
        self.create_status_bar()
        main_layout.addWidget(self.top_status_bar)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Side panel
        self.side_panel = self.create_side_panel()
        content_splitter.addWidget(self.side_panel)
        
        # Main tabs area
        self.tab_widget = QTabWidget()
        self.setup_tabs()
        content_splitter.addWidget(self.tab_widget)
        
        # Set split ratios
        content_splitter.setSizes([300, 1100])
        main_layout.addWidget(content_splitter)
        
        # Bottom status bar
        self.create_bottom_status_bar()
        main_layout.addWidget(self.bottom_status_bar)

    @staticmethod
    def configure_push_button(button: QPushButton, *, accent: bool = False) -> None:
        """Apply a consistent style to QPushButton instances."""
        button.setMinimumHeight(44)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(
            """
            QPushButton {
                background-color: %s;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 16px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: %s;
            }
            QPushButton:pressed {
                background-color: %s;
            }
            """
            % (
                "#2563eb" if accent else "#1e293b",
                "#1d4ed8" if accent else "#243447",
                "#1e40af" if accent else "#1b2533",
            )
        )
        
    def create_menubar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_pump_action = QAction("Add New Pump", self)
        new_pump_action.setShortcut("Ctrl+P")
        new_pump_action.triggered.connect(self.add_new_pump)
        file_menu.addAction(new_pump_action)
        
        link_sensors_action = QAction("Link Sensors", self)
        link_sensors_action.setShortcut("Ctrl+S")
        link_sensors_action.triggered.connect(self.link_sensors)
        file_menu.addAction(link_sensors_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("Import Data", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        export_action = QAction("Export Data", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        view_menu.addAction(refresh_action)
        
        # Window size submenu
        window_menu = view_menu.addMenu("Window Size")
        
        small_action = QAction("Small (800x600)", self)
        small_action.triggered.connect(lambda: self.set_window_size_preset('small'))
        window_menu.addAction(small_action)
        
        medium_action = QAction("Medium (1024x768)", self)
        medium_action.triggered.connect(lambda: self.set_window_size_preset('medium'))
        window_menu.addAction(medium_action)
        
        large_action = QAction("Large (1366x900)", self)
        large_action.triggered.connect(lambda: self.set_window_size_preset('large'))
        window_menu.addAction(large_action)
        
        window_menu.addSeparator()
        
        custom_action = QAction("Custom...", self)
        custom_action.triggered.connect(self.show_custom_size_dialog)
        window_menu.addAction(custom_action)
        
        default_action = QAction("Default", self)
        default_action.triggered.connect(lambda: self.set_window_size_preset('default'))
        window_menu.addAction(default_action)
        
        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        pump_manager_action = QAction("Pump Manager", self)
        pump_manager_action.setShortcut("Ctrl+M")
        pump_manager_action.triggered.connect(self.open_pump_manager)
        tools_menu.addAction(pump_manager_action)
        
        sensor_manager_action = QAction("Sensor Manager", self)
        sensor_manager_action.setShortcut("Ctrl+L")
        sensor_manager_action.triggered.connect(self.open_sensor_manager)
        tools_menu.addAction(sensor_manager_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
    def create_toolbar(self):
        """Create toolbar with pump management buttons"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setStyleSheet(
            """
            QToolBar {
                padding: 4px 10px;
                spacing: 10px;
            }
            QToolButton {
                padding: 6px 14px;
                margin: 0 4px;
                font-size: 13px;
                font-weight: 500;
                color: #e2e8f0;
            }
            QToolButton:hover {
                background-color: #1e293b;
                border-radius: 4px;
            }
            """
        )
        self.addToolBar(toolbar)

        # File actions
        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_data)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Pump management buttons
        add_pump_action = QAction("Add Pump", self)
        add_pump_action.triggered.connect(self.add_new_pump)
        toolbar.addAction(add_pump_action)
        
        link_sensors_action = QAction("Link Sensors", self)
        link_sensors_action.triggered.connect(self.link_sensors)
        toolbar.addAction(link_sensors_action)
        
        toolbar.addSeparator()
        
        # View actions
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        # Settings button
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
    def create_status_bar(self):
        """Create top status bar"""
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
        
        # Application title
        title_label = QLabel(APP_CONFIG['name'])
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1e88e5;")
        
        # System info
        system_info = QLabel(
            f"Version: {APP_CONFIG['version']} | {APP_CONFIG['developer']}"
        )
        system_info.setStyleSheet("color: #90a4ae;")

        # Connection status
        self.connection_status = QLabel("Connected")
        self.connection_status.setStyleSheet("color: #51cf66; font-weight: bold;")
        
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        top_layout.addWidget(system_info)
        top_layout.addSpacing(20)
        top_layout.addWidget(self.connection_status)
        
    def create_side_panel(self):
        """Create side panel with quick buttons"""
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
        
        # Side panel title
        side_title = QLabel("System Overview")
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
        
        # Quick actions
        quick_actions_group = QGroupBox("Quick Actions")
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
        
        # Add new pump button
        self.quick_add_pump_btn = QPushButton("Add New Pump")
        self.configure_push_button(self.quick_add_pump_btn, accent=True)
        self.quick_add_pump_btn.clicked.connect(self.add_new_pump)
        quick_actions_layout.addWidget(self.quick_add_pump_btn)

        # Link sensors button
        self.quick_link_sensors_btn = QPushButton("Link Sensors to Pumps")
        self.configure_push_button(self.quick_link_sensors_btn)
        self.quick_link_sensors_btn.clicked.connect(self.link_sensors)
        quick_actions_layout.addWidget(self.quick_link_sensors_btn)

        # Pump manager button
        self.quick_manage_pumps_btn = QPushButton("Manage Pumps")
        self.configure_push_button(self.quick_manage_pumps_btn)
        self.quick_manage_pumps_btn.clicked.connect(self.open_pump_manager)
        quick_actions_layout.addWidget(self.quick_manage_pumps_btn)
        
        layout.addWidget(quick_actions_group)
        
        # Quick stats
        self.setup_quick_stats(layout)
        
        # Active pumps
        self.setup_active_pumps(layout)
        
        # Active alerts
        self.setup_active_alerts(layout)
        
        layout.addStretch()
        
        return side_panel
    
    def setup_quick_stats(self, layout):
        """Setup quick statistics"""
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
        
        stats_title = QLabel("Quick Statistics")
        stats_title.setStyleSheet("font-weight: bold; color: #e3f2fd; font-size: 14px;")
        stats_layout.addWidget(stats_title)
        
        # Live statistics
        stats_grid = QGridLayout()
        
        self.total_pumps_label = QLabel("0")
        self.total_pumps_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e88e5;")
        stats_grid.addWidget(QLabel("Total Pumps:"), 0, 0)
        stats_grid.addWidget(self.total_pumps_label, 0, 1)
        
        self.operational_label = QLabel("0")
        self.operational_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #51cf66;")
        stats_grid.addWidget(QLabel("Operational Pumps:"), 1, 0)
        stats_grid.addWidget(self.operational_label, 1, 1)
        
        self.sensors_label = QLabel("0")
        self.sensors_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f59f00;")
        stats_grid.addWidget(QLabel("Active Sensors:"), 2, 0)
        stats_grid.addWidget(self.sensors_label, 2, 1)
        
        self.alerts_label = QLabel("0")
        self.alerts_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff6b6b;")
        stats_grid.addWidget(QLabel("Active Alerts:"), 3, 0)
        stats_grid.addWidget(self.alerts_label, 3, 1)
        
        stats_layout.addLayout(stats_grid)
        layout.addWidget(stats_frame)
    
    def setup_active_pumps(self, layout):
        """Setup active pumps list"""
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
        
        pumps_title = QLabel("Active Pumps")
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
        """Setup active alerts display"""
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
        
        alerts_title = QLabel("Active Alerts")
        alerts_title.setStyleSheet("font-weight: bold; color: #ff6b6b; font-size: 14px;")
        alerts_layout.addWidget(alerts_title)
        
        self.alerts_list = QLabel("No active alerts")
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
        
        # View all alerts button
        view_all_alerts_btn = QPushButton("View All Alerts")
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
        """Setup main tabs"""
        self.dashboard_tab = DashboardTab()
        self.analytics_tab = AnalyticsTab()
        self.maintenance_tab = MaintenanceTab()
        self.reporting_tab = ReportingTab()
        self.settings_tab = SettingsTab()
        
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.analytics_tab, "Analytics")
        self.tab_widget.addTab(self.maintenance_tab, "Maintenance")
        self.tab_widget.addTab(self.reporting_tab, "Reports")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Customize tab appearance
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
        
        # Connect update signal
        self.update_signal.connect(self.update_all_tabs)
    
    def setup_timer(self):
        """Setup timer for automatic updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.start_background_update)
        
        # Set minimum refresh interval
        refresh_interval = UI_CONFIG.get('refresh_interval', 30000)
        if refresh_interval < 1000:
            refresh_interval = 1000
        self.update_timer.start(refresh_interval)

        self.slow_update_timer = QTimer()
        self.slow_update_timer.timeout.connect(self.slow_update)
        self.slow_update_timer.start(300000)  # 5 minutes

    def start_background_update(self):
        """Start background update in separate thread for sensor data collection"""
        try:
            if self._bg_thread is not None and self._bg_thread.isRunning():
                return

            if not hasattr(self.dashboard_tab, 'generate_sensor_data'):
                self.auto_update()
                return

            thread = QThread()
            worker = BackgroundWorker(self.dashboard_tab.generate_sensor_data)

            worker.moveToThread(thread)
            thread.started.connect(worker.run)

            worker.signals.result.connect(self.on_sensor_data_ready)
            worker.signals.error.connect(self.on_worker_error)
            worker.signals.finished.connect(thread.quit)
            worker.signals.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)

            self._bg_thread = thread
            self._bg_worker = worker

            thread.start()
        except Exception as e:
            self.logger.error(f"Error starting background update: {e}")

    def on_sensor_data_ready(self, sensor_data):
        """Apply background processing results to UI"""
        try:
            if hasattr(self.dashboard_tab, 'update_kpi_values'):
                try:
                    self.dashboard_tab.update_kpi_values(sensor_data)
                except Exception:
                    self.logger.debug("Error in update_kpi_values (ignored).")

            if hasattr(self.dashboard_tab, 'update_live_charts'):
                try:
                    self.dashboard_tab.update_live_charts(sensor_data)
                except Exception:
                    self.logger.debug("Error updating live charts (ignored).")

            if hasattr(self.dashboard_tab, 'update_predictions'):
                try:
                    self.dashboard_tab.update_predictions(sensor_data)
                except Exception:
                    self.logger.debug("Error updating predictions (ignored).")

            if hasattr(self.dashboard_tab, 'update_pump_status'):
                try:
                    self.dashboard_tab.update_pump_status(sensor_data)
                except Exception:
                    self.logger.debug("Error updating pump status (ignored).")
        except Exception as e:
            self.logger.error(f"Error applying sensor data to UI: {e}")

    def on_worker_error(self, err_text):
        self.logger.error(f"Worker error: {err_text}")

    def get_cached_data(self, key, fetch_function, force_refresh=False):
        """Get data with caching"""
        now = datetime.now().timestamp() * 1000
        
        if not force_refresh and key in self.cache:
            data, timestamp = self.cache[key]
            if now - timestamp < self.cache_timeout:
                return data
        
        # Fetch new data
        data = fetch_function()
        self.cache[key] = (data, now)
        return data
    
    def clear_cache(self, key=None):
        """Clear cache"""
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()
    
    def load_initial_data(self):
        """Load initial data"""
        self.update_quick_stats()
        self.update_active_pumps()
        self.update_active_alerts()
        self.update_connection_status()
    
    def update_quick_stats(self):
        """Update quick statistics"""
        try:
            stats = self.get_cached_data('system_stats', db_manager.get_system_stats)
            
            self.total_pumps_label.setText(str(stats.get('total_pumps', 0)))
            self.operational_label.setText(str(stats.get('operational_pumps', 0)))
            self.sensors_label.setText(str(stats.get('active_sensors', 0)))
            self.alerts_label.setText(str(stats.get('active_alerts', 0)))
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def update_active_pumps(self):
        """Update active pumps list"""
        try:
            pumps = self.get_cached_data('pumps', db_manager.get_pumps_with_stats)

            current_items = {}
            for i in range(self.pumps_list.count()):
                item = self.pumps_list.item(i)
                pump_id = item.data(Qt.ItemDataRole.UserRole)
                current_items[pump_id] = (i, item)

            for _, pump in pumps.iterrows():
                pump_id = pump['id']
                item_text = self.format_pump_item_text(pump)

                if pump_id in current_items:
                    index, item = current_items[pump_id]
                    if item.text() != item_text:
                        item.setText(item_text)
                        self.update_pump_item_style(item, pump)
                    item.setData(Qt.ItemDataRole.UserRole + 1, pump['name'])
                    current_items.pop(pump_id)
                else:
                    self.add_pump_item(pump)

            indices_to_remove = [idx for (idx, _) in current_items.values()]
            for idx in sorted(indices_to_remove, reverse=True):
                self.pumps_list.takeItem(idx)

        except Exception as e:
            self.logger.error(f"Error updating pumps list: {e}")
    
    @staticmethod
    def format_pump_item_text(pump) -> str:
        """Return a normalized pump entry representation."""
        status_label = {
            'operational': 'Operational',
            'maintenance': 'Maintenance',
        }.get(pump['status'], 'Offline')
        return (
            f"{pump['name']}\n"
            f"Status: {status_label} | Location: {pump['location']} | "
            f"Sensors: {pump['sensor_count']}"
        )

    def add_pump_item(self, pump):
        """Add new pump item"""
        item_text = self.format_pump_item_text(pump)

        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, pump['id'])
        item.setData(Qt.ItemDataRole.UserRole + 1, pump['name'])
        self.update_pump_item_style(item, pump)
        self.pumps_list.addItem(item)
    
    def update_pump_item_style(self, item, pump):
        """Update pump item style"""
        if pump['status'] == 'operational':
            item.setBackground(QColor(81, 207, 102, 50))
        elif pump['status'] == 'maintenance':
            item.setBackground(QColor(255, 179, 0, 50))
        else:
            item.setBackground(QColor(255, 107, 107, 50))
    
    def update_active_alerts(self):
        """Update active alerts list"""
        try:
            alerts = self.get_cached_data('alerts', db_manager.get_active_alerts)
            
            if alerts.empty:
                if self.alerts_list.text() != "No active alerts":
                    self.alerts_list.setText("No active alerts")
                return
            
            alerts_text = self.format_alerts_text(alerts)
            if self.alerts_list.text() != alerts_text:
                self.alerts_list.setText(alerts_text)
                
        except Exception as e:
            self.logger.error(f"Error updating alerts: {e}")
    
    def format_alerts_text(self, alerts):
        """Format alerts text"""
        alerts_text = ""
        for _, alert in alerts.head(3).iterrows():  # Show only first 3 alerts
            severity_label = {
                'high': 'High severity',
                'medium': 'Medium severity',
                'low': 'Low severity',
            }.get(alert['severity'], 'Info')
            alerts_text += (
                f"{severity_label}: {alert['pump_name']} - {alert['message']}\n"
            )

        if len(alerts) > 3:
            alerts_text += f"... and {len(alerts) - 3} more alerts"
        
        return alerts_text
    
    def update_connection_status(self):
        """Update connection status"""
        try:
            stats = self.get_cached_data('system_stats', db_manager.get_system_stats)
            last_update = stats.get('last_data_update')
            
            if last_update:
                last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                time_diff = datetime.now().replace(tzinfo=None) - last_update_time.replace(tzinfo=None)
                
                if time_diff.total_seconds() < 300:  # Less than 5 minutes
                    self.connection_status.setText("Connected")
                    self.connection_status.setStyleSheet("color: #51cf66; font-weight: bold;")
                else:
                    self.connection_status.setText("Weak connection")
                    self.connection_status.setStyleSheet("color: #f59f00; font-weight: bold;")
            else:
                self.connection_status.setText("Disconnected")
                self.connection_status.setStyleSheet("color: #ff6b6b; font-weight: bold;")
                
        except Exception as e:
            self.logger.error(f"Error updating connection status: {e}")
    
    def auto_update(self):
        """Automatic data update"""
        try:
            self.update_quick_stats()
            self.update_active_alerts()
            self.update_signal.emit()
        except Exception as e:
            self.logger.error(f"Error in auto update: {e}")
            self.clear_cache()
    
    def slow_update(self):
        """Slow data update"""
        try:
            self.update_active_pumps()
            self.update_connection_status()
        except Exception as e:
            self.logger.error(f"Error in slow update: {e}")
    
    def update_all_tabs(self):
        """Update all tabs"""
        self.dashboard_tab.refresh_data()
        self.analytics_tab.refresh_data()
        self.maintenance_tab.refresh_data()
    
    def create_bottom_status_bar(self):
        """Create bottom status bar"""
        self.bottom_status_bar = QStatusBar()
        self.bottom_status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #0f172a;
                color: #94a3b8;
                border-top: 1px solid #334155;
            }
        """)
        self.setStatusBar(self.bottom_status_bar)
        
        # Add status information
        self.status_label = QLabel("Ready")
        self.bottom_status_bar.addWidget(self.status_label)
        
        # Add memory information
        self.memory_label = QLabel()
        self.update_memory_usage()
        self.bottom_status_bar.addPermanentWidget(self.memory_label)
        
        # Add time
        self.time_label = QLabel()
        self.update_time()
        self.bottom_status_bar.addPermanentWidget(self.time_label)
        
        # Update timers - reduced frequency
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(5000)  # Every 5 seconds instead of every second
        
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(30000)  # Every 30 seconds instead of every 5 seconds
    
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.time_label.setText(f"Time: {current_time}")

    def update_memory_usage(self):
        """Update memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            self.memory_label.setText(f"Memory: {memory_usage:.1f} MB")
        except Exception:
            self.memory_label.setText("Memory: -- MB")
    
    def on_pump_selected(self, item):
        """When pump is selected from list"""
        try:
            pump_id = item.data(Qt.ItemDataRole.UserRole)
            self.current_pump_id = pump_id

            pump_name = item.data(Qt.ItemDataRole.UserRole + 1)
            if not pump_name and item.text():
                pump_name = item.text().splitlines()[0]

            # Update tabs with selected pump
            if hasattr(self.dashboard_tab, 'select_pump'):
                self.dashboard_tab.select_pump(pump_id)
            if hasattr(self.analytics_tab, 'select_pump'):
                self.analytics_tab.select_pump(pump_id)

            if pump_name:
                self.status_label.setText(f"Selected pump: {pump_name}")
            else:
                self.status_label.setText("Selected pump")

        except Exception as e:
            self.logger.error(f"Error selecting pump: {e}")
    
    def add_new_pump(self):
        """Add new pump"""
        try:
            dialog = AddPumpDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                pump_data = dialog.get_pump_data()
                pump_id = db_manager.add_pump(pump_data)
                
                if pump_id > 0:
                    self.status_label.setText(f"Pump added: {pump_data['name']}")
                    # Clear relevant cache
                    self.clear_cache('pumps')
                    self.clear_cache('system_stats')
                    self.load_initial_data()
                    self.update_all_tabs()
                    
                    # Switch to maintenance tab
                    self.tab_widget.setCurrentWidget(self.maintenance_tab)
                    
                    QMessageBox.information(self, "Success", f"Pump '{pump_data['name']}' added successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to add pump. Name may be duplicate.")
            
        except Exception as e:
            self.logger.error(f"Error adding pump: {e}")
            QMessageBox.warning(self, "Error", f"Error adding pump: {str(e)}")
    
    def link_sensors(self):
        """Link sensors to pumps"""
        try:
            dialog = LinkSensorsDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.status_label.setText("Sensors linked successfully")
                # Clear relevant cache
                self.clear_cache('pumps')
                self.clear_cache('system_stats')
                self.clear_cache('alerts')
                self.load_initial_data()
                QMessageBox.information(self, "Success", "Sensors linked to pumps successfully")
            
        except Exception as e:
            self.logger.error(f"Error linking sensors: {e}")
            QMessageBox.warning(self, "Error", f"Error linking sensors: {str(e)}")
    
    def open_pump_manager(self):
        """Open pump manager"""
        try:
            self.tab_widget.setCurrentWidget(self.maintenance_tab)
            self.status_label.setText("Opening pump manager")
        except Exception as e:
            self.logger.error(f"Error opening pump manager: {e}")
    
    def open_sensor_manager(self):
        """Open sensor manager"""
        try:
            self.tab_widget.setCurrentWidget(self.maintenance_tab)
            self.status_label.setText("Opening sensor manager")
        except Exception as e:
            self.logger.error(f"Error opening sensor manager: {e}")
    
    def open_settings(self):
        """Open settings"""
        try:
            self.tab_widget.setCurrentWidget(self.settings_tab)
            self.status_label.setText("Opening settings")
        except Exception as e:
            self.logger.error(f"Error opening settings: {e}")
    
    def view_all_alerts(self):
        """View all alerts"""
        try:
            self.tab_widget.setCurrentWidget(self.analytics_tab)
            self.status_label.setText("Viewing all alerts")
        except Exception as e:
            self.logger.error(f"Error viewing alerts: {e}")
    
    def import_data(self):
        """Import data"""
        try:
            QMessageBox.information(self, "Import Data", "Import feature will be developed in the next version")
        except Exception as e:
            self.logger.error(f"Error importing data: {e}")
    
    def export_data(self):
        """Export data"""
        try:
            QMessageBox.information(self, "Export Data", "Export feature will be developed in the next version")
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
            self.status_label.setText("Exited fullscreen mode")
        else:
            self.showFullScreen()
            self.status_label.setText("Entered fullscreen mode")
    
    def show_about(self):
        """Show about information"""
        about_text = f"""
        <h2>{APP_CONFIG['name']}</h2>
        <p><b>Version:</b> {APP_CONFIG['version']}</p>
        <p><b>Developer:</b> {APP_CONFIG['developer']}</p>
        <p><b>Location:</b> {APP_CONFIG['location']}</p>
        <p><b>Phone:</b> {APP_CONFIG['phone']}</p>
        <p><b>Email:</b> {APP_CONFIG['email']}</p>
        <p><b>Description:</b> {APP_CONFIG['description']}</p>
        <p><b>Copyright:</b> {APP_CONFIG['copyright']}</p>
        <hr>
        <p>Integrated system for predicting pump failure using AI.</p>
        <p>Developed in Python with modern Qt interface.</p>
        """
        
        QMessageBox.about(self, "About", about_text)
    
    def show_documentation(self):
        """Show documentation"""
        QMessageBox.information(self, "Documentation", "Documentation will be provided in the next version")
    
    def new_project(self):
        """Create new project"""
        reply = QMessageBox.question(self, "New Project", 
                                   "Create new project?\nAny unsaved data will be lost.",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.status_label.setText("New project created")
            # Clear all cache
            self.clear_cache()
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    def save_data(self):
        """Save data"""
        self.status_label.setText("Saving data...")
        # Simulate save process
        QTimer.singleShot(1500, lambda: self.status_label.setText("Data saved"))

    def refresh_data(self):
        """Manual data refresh"""
        self.status_label.setText("Refreshing data...")
        self.clear_cache()
        # Request background update
        self.start_background_update()
        # Light updates
        self.slow_update()
        QTimer.singleShot(1000, lambda: self.status_label.setText("Data refreshed"))
    
    def apply_window_size(self, width: int, height: int):
        """Apply window size ensuring limits from config"""
        try:
            win_conf = UI_CONFIG.get('window', {})
            min_w, min_h = win_conf.get('min_size', (640, 480))
            max_w, max_h = win_conf.get('max_size', (3840, 2160))
            w = max(min_w, min(width, max_w))
            h = max(min_h, min(height, max_h))
            self.resize(w, h)
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"Window size: {w}x{h}")
        except Exception as e:
            self.logger.error(f"Error applying window size: {e}")
    
    def set_window_size_preset(self, preset_name: str):
        """Set window size based on preset name"""
        try:
            presets = UI_CONFIG.get('window', {}).get('presets', {})
            if preset_name in presets:
                w, h = presets[preset_name]
                self.apply_window_size(int(w), int(h))
            else:
                self.logger.warning(f"Unknown window size preset: {preset_name}")
        except Exception as e:
            self.logger.error(f"Error applying window size preset: {e}")
    
    def show_custom_size_dialog(self):
        """Show custom size dialog"""
        dlg = CustomSizeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            w, h = dlg.get_size()
            self.apply_window_size(w, h)
    
    def closeEvent(self, event):
        """Handle application close event"""
        reply = QMessageBox.question(self, "Confirm Exit",
                                   "Are you sure you want to close the application?",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("iPump application closed")
            # Save settings and close resources
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
        self.setWindowTitle("Add New Pump")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize add pump interface"""
        layout = QVBoxLayout(self)
        
        # Data entry form
        form_layout = QFormLayout()
        
        # Pump name field
        self.pump_name = QLineEdit()
        self.pump_name.setPlaceholderText("Enter pump name (required)")
        self.pump_name.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("Pump Name:*", self.pump_name)
        
        # Location field
        self.pump_location = QLineEdit()
        self.pump_location.setPlaceholderText("Enter pump location (required)")
        self.pump_location.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("Location:*", self.pump_location)
        
        # Type field
        self.pump_type = QComboBox()
        self.pump_type.addItems(["Centrifugal", "Piston", "Feed", "Auxiliary", "Transfer", "Filter"])
        self.pump_type.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("Pump Type:*", self.pump_type)
        
        # Installation date field
        self.installation_date = QDateEdit()
        self.installation_date.setDate(QDate.currentDate())
        self.installation_date.setCalendarPopup(True)
        self.installation_date.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("Installation Date:*", self.installation_date)
        
        # Status field
        self.pump_status = QComboBox()
        self.pump_status.addItems(["Operational", "Maintenance", "Stopped"])
        self.pump_status.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("Status:*", self.pump_status)
        
        # Additional info field
        self.pump_notes = QTextEdit()
        self.pump_notes.setMaximumHeight(100)
        self.pump_notes.setPlaceholderText("Additional notes about the pump...")
        self.pump_notes.setStyleSheet("padding: 8px; border-radius: 4px;")
        form_layout.addRow("Notes:", self.pump_notes)
        
        layout.addLayout(form_layout)
        
        # Additional information
        info_label = QLabel("Fields marked with * are required")
        info_label.setStyleSheet("color: #94a3b8; font-size: 12px; padding: 10px;")
        layout.addWidget(info_label)
        
        # Save and cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_pump_data(self):
        """Get entered pump data"""
        status_map = {
            "Operational": "operational",
            "Maintenance": "maintenance", 
            "Stopped": "stopped"
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
        """When OK is clicked"""
        if not self.pump_name.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter pump name")
            return
        
        if not self.pump_location.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter pump location")
            return
        
        super().accept()

class LinkSensorsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Link Sensors to Pumps")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize link sensors interface"""
        layout = QVBoxLayout(self)
        
        # Pump selection section
        pump_group = QGroupBox("Select Pump")
        pump_layout = QFormLayout(pump_group)
        
        self.pump_selector = QComboBox()
        # Load pumps from database
        pumps = db_manager.get_pumps()
        for _, pump in pumps.iterrows():
            self.pump_selector.addItem(f"{pump['name']} - {pump['location']}", pump['id'])
        
        pump_layout.addRow("Pump:", self.pump_selector)
        layout.addWidget(pump_group)
        
        # Available sensors section
        sensors_group = QGroupBox("Available Sensors for Linking")
        sensors_layout = QVBoxLayout(sensors_group)
        
        # Sensors list
        self.sensors_list = QListWidget()
        
        # Add available sensor types
        available_sensors = [
            "Vibration Sensor X - Measure vibration on X axis",
            "Vibration Sensor Y - Measure vibration on Y axis", 
            "Vibration Sensor Z - Measure vibration on Z axis",
            "Temperature Sensor - Measure pump temperature",
            "Pressure Sensor - Measure operating pressure",
            "Flow Sensor - Measure flow rate",
            "Oil Level Sensor - Measure lubrication oil level",
            "Oil Quality Sensor - Measure oil quality",
            "Power Consumption Sensor - Measure power consumption",
            "Bearing Temperature Sensor - Measure bearing temperature"
        ]
        
        for sensor in available_sensors:
            item = QListWidgetItem(sensor)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.sensors_list.addItem(item)
        
        sensors_layout.addWidget(self.sensors_list)
        layout.addWidget(sensors_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_sensors)
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all_sensors)
        button_layout.addWidget(self.deselect_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Information
        info_label = QLabel("Select the sensors you want to link to the selected pump")
        info_label.setStyleSheet("color: #94a3b8; padding: 10px;")
        layout.addWidget(info_label)
        
        # Save and cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def select_all_sensors(self):
        """Select all sensors"""
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def deselect_all_sensors(self):
        """Deselect all sensors"""
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
    
    def get_selected_sensors(self):
        """Get selected sensors"""
        selected_sensors = []
        sensor_type_map = {
            "Vibration Sensor X": "vibration_x",
            "Vibration Sensor Y": "vibration_y",
            "Vibration Sensor Z": "vibration_z",
            "Temperature Sensor": "temperature",
            "Pressure Sensor": "pressure",
            "Flow Sensor": "flow_rate",
            "Oil Level Sensor": "oil_level",
            "Oil Quality Sensor": "oil_quality",
            "Power Consumption Sensor": "power_consumption",
            "Bearing Temperature Sensor": "bearing_temperature"
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
        """When OK is clicked"""
        selected_sensors = self.get_selected_sensors()
        if not selected_sensors:
            QMessageBox.warning(self, "Warning", "Please select at least one sensor")
            return
        
        pump_id = self.pump_selector.currentData()
        pump_name = self.pump_selector.currentText().split(' - ')[0]
        
        # Show linking summary
        summary_lines = [
            "Linking Summary:",
            "",
            f"Pump: {pump_name}",
            f"Selected Sensors: {len(selected_sensors)}",
            "",
            "Selected Sensors:",
        ]
        summary_lines.extend([f"- {sensor['sensor_type']}" for sensor in selected_sensors])
        summary = "\n".join(summary_lines)
        
        reply = QMessageBox.question(
            self, 
            "Confirm Linking", 
            summary + "\nDo you want to proceed with linking?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Execute actual linking process
            success = db_manager.link_sensors_to_pump(pump_id, selected_sensors)
            if success:
                super().accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to link sensors. Some sensors may already be linked.")

class CustomSizeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Window Size")
        self.setModal(True)
        layout = QFormLayout(self)
    
        self.width_spin = QSpinBox()
        self.width_spin.setRange(320, 7680)
        self.width_spin.setValue(UI_CONFIG.get('window', {}).get('default_size', (1200,800))[0])
    
        self.height_spin = QSpinBox()
        self.height_spin.setRange(240, 4320)
        self.height_spin.setValue(UI_CONFIG.get('window', {}).get('default_size', (1200,800))[1])
    
        layout.addRow("Width (px):", self.width_spin)
        layout.addRow("Height (px):", self.height_spin)
    
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def get_size(self):
        return int(self.width_spin.value()), int(self.height_spin.value())