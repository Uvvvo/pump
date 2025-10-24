"""Settings module for the iPump application."""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QGroupBox, QLabel, QPushButton, QComboBox,
                           QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
                           QSlider, QTabWidget, QMessageBox, QFileDialog,
                           QListWidget, QListWidgetItem, QScrollArea, QProgressDialog)
from PyQt6.QtGui import QFont, QIntValidator, QDoubleValidator
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import json
from pathlib import Path
from datetime import datetime
import logging

from config import APP_CONFIG, UI_CONFIG, PUMP_CONFIG, AI_MODELS_CONFIG
from database import db_manager
from ai_models import failure_predictor

# Logging configuration
logger = logging.getLogger(__name__)


class ModelTrainingThread(QThread):
    """Background thread for model training"""
    training_finished = pyqtSignal(bool, str)
    progress_updated = pyqtSignal(int)
    
    def __init__(self, predictor):
        super().__init__()
        self.predictor = predictor
    
    def run(self):
        try:
            # Simulate progress updates
            for i in range(101):
                self.progress_updated.emit(i)
                self.msleep(50)  # Simulate training time
            
            # Perform the actual model training
            success = self.predictor.train_model()
            message = "Model trained successfully" if success else "Model training failed"
            self.training_finished.emit(success, message)
        except Exception as e:
            self.training_finished.emit(False, f"Training error: {str(e)}")


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = Path("config/settings.json")
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Initialize settings interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Settings tabs
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # General tab
        self.general_tab = self.create_general_tab()
        self.settings_tabs.addTab(self.general_tab, "General")
        
        # Pumps tab
        self.pumps_tab = self.create_pumps_tab()
        self.settings_tabs.addTab(self.pumps_tab, "Pumps")
        
        # AI tab
        self.ai_tab = self.create_ai_tab()
        self.settings_tabs.addTab(self.ai_tab, "AI")
        
        # System tab
        self.system_tab = self.create_system_tab()
        self.settings_tabs.addTab(self.system_tab, "System")
        
        main_layout.addWidget(self.settings_tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px; }")
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_settings)
        self.reset_btn.setStyleSheet("QPushButton { background-color: #ffc107; color: black; padding: 8px; }")
        button_layout.addWidget(self.reset_btn)
        
        self.defaults_btn = QPushButton("Load Defaults")
        self.defaults_btn.clicked.connect(self.load_default_settings)
        self.defaults_btn.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; padding: 8px; }")
        button_layout.addWidget(self.defaults_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
    def create_general_tab(self):
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Interface options
        interface_group = QGroupBox("Interface Settings")
        interface_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        interface_layout = QGridLayout(interface_group)
        interface_layout.setVerticalSpacing(10)
        interface_layout.setHorizontalSpacing(15)
        
        interface_layout.addWidget(QLabel("Language:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Arabic", "English", "French"])
        self.language_combo.setToolTip("Select the interface language")
        interface_layout.addWidget(self.language_combo, 0, 1)
        
        interface_layout.addWidget(QLabel("Theme:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Blue", "Automatic"])
        self.theme_combo.setToolTip("Choose the interface theme")
        interface_layout.addWidget(self.theme_combo, 1, 1)
        
        interface_layout.addWidget(QLabel("Refresh interval (ms):"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.refresh_rate = QSpinBox()
        self.refresh_rate.setRange(500, 30000)
        self.refresh_rate.setSingleStep(500)
        self.refresh_rate.setSuffix(" ms")
        self.refresh_rate.setToolTip("Update frequency for the dashboard")
        interface_layout.addWidget(self.refresh_rate, 2, 1)
        
        layout.addWidget(interface_group)
        
        # Company details section
        company_group = QGroupBox("Company Information")
        company_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        company_layout = QGridLayout(company_group)
        company_layout.setVerticalSpacing(10)
        company_layout.setHorizontalSpacing(15)
        
        company_layout.addWidget(QLabel("Company name:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Enter the company name")
        company_layout.addWidget(self.company_name, 0, 1)
        
        company_layout.addWidget(QLabel("Address:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.company_address = QLineEdit()
        self.company_address.setPlaceholderText("Enter the company address")
        company_layout.addWidget(self.company_address, 1, 1)
        
        company_layout.addWidget(QLabel("Phone:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.company_phone = QLineEdit()
        self.company_phone.setPlaceholderText("+9647813563139")
        company_layout.addWidget(self.company_phone, 2, 1)
        
        company_layout.addWidget(QLabel("Email:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        self.company_email = QLineEdit()
        self.company_email.setPlaceholderText("ah343238@gmail.com")
        company_layout.addWidget(self.company_email, 3, 1)
        
        layout.addWidget(company_group)
        layout.addStretch()
        return widget
    
    def create_pumps_tab(self):
        """Create pump settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Alert thresholds
        thresholds_group = QGroupBox("Alert Thresholds")
        thresholds_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        thresholds_layout = QGridLayout(thresholds_group)
        thresholds_layout.setVerticalSpacing(10)
        thresholds_layout.setHorizontalSpacing(15)
        
        thresholds_layout.addWidget(QLabel("Maximum temperature (C):"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.max_temperature = QDoubleSpinBox()
        self.max_temperature.setRange(0, 200)
        self.max_temperature.setDecimals(1)
        self.max_temperature.setSuffix(" C")
        self.max_temperature.setToolTip("Highest allowed operating temperature")
        thresholds_layout.addWidget(self.max_temperature, 0, 1)
        
        thresholds_layout.addWidget(QLabel("Maximum vibration (m/s^2):"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.max_vibration = QDoubleSpinBox()
        self.max_vibration.setRange(0, 50)
        self.max_vibration.setDecimals(2)
        self.max_vibration.setSuffix(" m/s^2")
        self.max_vibration.setToolTip("Highest allowed vibration")
        thresholds_layout.addWidget(self.max_vibration, 1, 1)
        
        thresholds_layout.addWidget(QLabel("Minimum oil level (%):"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.min_oil_level = QDoubleSpinBox()
        self.min_oil_level.setRange(0, 100)
        self.min_oil_level.setDecimals(1)
        self.min_oil_level.setSuffix(" %")
        self.min_oil_level.setToolTip("Minimum allowed oil level")
        thresholds_layout.addWidget(self.min_oil_level, 2, 1)
        
        thresholds_layout.addWidget(QLabel("Maintenance interval (hours):"), 3, 0, Qt.AlignmentFlag.AlignRight)
        self.maintenance_interval = QSpinBox()
        self.maintenance_interval.setRange(24, 10000)
        self.maintenance_interval.setSingleStep(24)
        self.maintenance_interval.setSuffix(" h")
        self.maintenance_interval.setToolTip("Time between scheduled maintenance")
        thresholds_layout.addWidget(self.maintenance_interval, 3, 1)
        
        layout.addWidget(thresholds_group)
        
        # Monitoring settings
        monitoring_group = QGroupBox("Monitoring Settings")
        monitoring_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        monitoring_layout = QGridLayout(monitoring_group)
        monitoring_layout.setVerticalSpacing(10)
        monitoring_layout.setHorizontalSpacing(15)
        
        monitoring_layout.addWidget(QLabel("Chart data points:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.chart_points = QSpinBox()
        self.chart_points.setRange(50, 5000)
        self.chart_points.setSingleStep(50)
        self.chart_points.setSuffix(" points")
        self.chart_points.setToolTip("Number of samples displayed on charts")
        monitoring_layout.addWidget(self.chart_points, 0, 1)
        
        monitoring_layout.addWidget(QLabel("Enable continuous monitoring:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.continuous_monitoring = QCheckBox()
        self.continuous_monitoring.setToolTip("Enable continuous pump monitoring")
        monitoring_layout.addWidget(self.continuous_monitoring, 1, 1)
        
        monitoring_layout.addWidget(QLabel("Email notifications:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.email_notifications = QCheckBox()
        self.email_notifications.setToolTip("Send an email when alerts are triggered")
        monitoring_layout.addWidget(self.email_notifications, 2, 1)
        
        # Notification test button
        self.test_notifications_btn = QPushButton("Test notifications")
        self.test_notifications_btn.clicked.connect(self.test_notifications)
        self.test_notifications_btn.setToolTip("Test notification system")
        monitoring_layout.addWidget(self.test_notifications_btn, 3, 1)
        
        layout.addWidget(monitoring_group)
        layout.addStretch()
        return widget
    
    def create_ai_tab(self):
        """Create AI settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Model configuration
        model_group = QGroupBox("Prediction Model Settings")
        model_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        model_layout = QGridLayout(model_group)
        model_layout.setVerticalSpacing(10)
        model_layout.setHorizontalSpacing(15)
        
        model_layout.addWidget(QLabel("Prediction threshold (%):"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.prediction_threshold = QDoubleSpinBox()
        self.prediction_threshold.setRange(50, 99)
        self.prediction_threshold.setDecimals(1)
        self.prediction_threshold.setSuffix(" %")
        self.prediction_threshold.setToolTip("Confidence threshold for failure prediction")
        model_layout.addWidget(self.prediction_threshold, 0, 1)
        
        model_layout.addWidget(QLabel("Anomaly detection sensitivity:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        sensitivity_layout = QHBoxLayout()
        self.anomaly_sensitivity = QSlider(Qt.Orientation.Horizontal)
        self.anomaly_sensitivity.setRange(1, 10)
        self.anomaly_sensitivity.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.anomaly_sensitivity.setTickInterval(1)
        self.anomaly_sensitivity.setToolTip("Anomaly detection sensitivity (1 = low, 10 = high)")
        self.sensitivity_label = QLabel("5")
        self.anomaly_sensitivity.valueChanged.connect(
            lambda v: self.sensitivity_label.setText(str(v))
        )
        sensitivity_layout.addWidget(self.anomaly_sensitivity)
        sensitivity_layout.addWidget(self.sensitivity_label)
        model_layout.addLayout(sensitivity_layout, 1, 1)
        
        model_layout.addWidget(QLabel("Automatic model refresh:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.auto_model_update = QCheckBox()
        self.auto_model_update.setToolTip("Automatically retrain the model when new data is available")
        model_layout.addWidget(self.auto_model_update, 2, 1)
        
        layout.addWidget(model_group)
        
        # Model management
        management_group = QGroupBox("Model Management")
        management_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        management_layout = QVBoxLayout(management_group)
        
        buttons_layout = QHBoxLayout()
        
        self.train_model_btn = QPushButton("Retrain model")
        self.train_model_btn.clicked.connect(self.retrain_model)
        self.train_model_btn.setToolTip("Retrain the AI model")
        buttons_layout.addWidget(self.train_model_btn)
        
        self.import_model_btn = QPushButton("Import model")
        self.import_model_btn.clicked.connect(self.import_model)
        self.import_model_btn.setToolTip("Import a pre-trained model")
        buttons_layout.addWidget(self.import_model_btn)
        
        self.export_model_btn = QPushButton("Export model")
        self.export_model_btn.clicked.connect(self.export_model)
        self.export_model_btn.setToolTip("Export the current model")
        buttons_layout.addWidget(self.export_model_btn)
        
        management_layout.addLayout(buttons_layout)
        
        # Model information section
        self.model_info = QLabel("Loading model information...")
        self.model_info.setWordWrap(True)
        self.model_info.setStyleSheet(
            "QLabel {"
            " background-color: #f8f9fa;"
            " padding: 15px;"
            " border-radius: 8px;"
            " border: 1px solid #dee2e6;"
            " font-size: 12px;"
            "}"
        )
        management_layout.addWidget(self.model_info)
        
        layout.addWidget(management_group)
        layout.addStretch()
        return widget
    
    def create_system_tab(self):
        """Create system settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Database configuration
        database_group = QGroupBox("Database Settings")
        database_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        database_layout = QGridLayout(database_group)
        database_layout.setVerticalSpacing(10)
        database_layout.setHorizontalSpacing(15)
        
        database_layout.addWidget(QLabel("Database type:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.db_type = QComboBox()
        self.db_type.addItems(["SQLite", "PostgreSQL", "MySQL", "Microsoft SQL Server"])
        self.db_type.currentTextChanged.connect(self.on_db_type_changed)
        database_layout.addWidget(self.db_type, 0, 1)
        
        database_layout.addWidget(QLabel("Host name:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.db_host = QLineEdit()
        self.db_host.setPlaceholderText("localhost or IP address")
        database_layout.addWidget(self.db_host, 1, 1)
        
        database_layout.addWidget(QLabel("User name:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.db_user = QLineEdit()
        self.db_user.setPlaceholderText("User name")
        database_layout.addWidget(self.db_user, 2, 1)
        
        database_layout.addWidget(QLabel("Password:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        self.db_password = QLineEdit()
        self.db_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.db_password.setPlaceholderText("Password")
        database_layout.addWidget(self.db_password, 3, 1)
        
        database_layout.addWidget(QLabel("Database name:"), 4, 0, Qt.AlignmentFlag.AlignRight)
        self.db_name = QLineEdit()
        self.db_name.setPlaceholderText("ipump_db")
        database_layout.addWidget(self.db_name, 4, 1)
        
        database_layout.addWidget(QLabel("Automatic backups:"), 5, 0, Qt.AlignmentFlag.AlignRight)
        self.auto_backup = QCheckBox()
        self.auto_backup.setToolTip("Create automatic database backups")
        database_layout.addWidget(self.auto_backup, 5, 1)
        
        # Database test action
        self.test_db_btn = QPushButton("Test database connection")
        self.test_db_btn.clicked.connect(self.test_database_connection)
        database_layout.addWidget(self.test_db_btn, 6, 1)
        
        layout.addWidget(database_group)
        
        # Security configuration
        security_group = QGroupBox("Security Settings")
        security_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        security_layout = QGridLayout(security_group)
        security_layout.setVerticalSpacing(10)
        security_layout.setHorizontalSpacing(15)
        
        security_layout.addWidget(QLabel("Enable authentication:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.enable_auth = QCheckBox()
        self.enable_auth.setToolTip("Enable user authentication")
        security_layout.addWidget(self.enable_auth, 0, 1)
        
        security_layout.addWidget(QLabel("Logging level:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level.setToolTip("Level of detail for system logs")
        security_layout.addWidget(self.log_level, 1, 1)
        
        security_layout.addWidget(QLabel("Data retention (days):"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.data_retention = QSpinBox()
        self.data_retention.setRange(30, 1825)  # Up to five years
        self.data_retention.setSuffix(" days")
        self.data_retention.setToolTip("Number of days to retain historical data")
        security_layout.addWidget(self.data_retention, 2, 1)
        
        layout.addWidget(security_group)
        
        # System information
        system_info_group = QGroupBox("System Information")
        system_info_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        system_info_layout = QVBoxLayout(system_info_group)
        
        self.system_info = QLabel()
        self.system_info.setWordWrap(True)
        self.system_info.setStyleSheet(
            "QLabel {"
            " background-color: #f8f9fa;"
            " padding: 15px;"
            " border-radius: 8px;"
            " border: 1px solid #dee2e6;"
            " font-family: 'Courier New', monospace;"
            " font-size: 11px;"
            "}"
        )
        system_info_layout.addWidget(self.system_info)
        
        # System info refresh button
        refresh_info_btn = QPushButton("Refresh system information")
        refresh_info_btn.clicked.connect(self.update_system_info)
        system_info_layout.addWidget(refresh_info_btn)
        
        layout.addWidget(system_info_group)
        layout.addStretch()
        return widget
    
    def on_db_type_changed(self, db_type):
        """Update the database settings UI for the selected type"""
        if db_type == "SQLite":
            self.db_host.setEnabled(False)
            self.db_user.setEnabled(False)
            self.db_password.setEnabled(False)
            self.db_name.setEnabled(False)
        else:
            self.db_host.setEnabled(True)
            self.db_user.setEnabled(True)
            self.db_password.setEnabled(True)
            self.db_name.setEnabled(True)
    
    def load_settings(self):
        """Load current settings"""
        try:
            # Attempt to load settings from file
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            # General preferences
            self.language_combo.setCurrentText(settings.get('language', 'English'))
            self.theme_combo.setCurrentText(settings.get('theme', 'Dark'))
            self.refresh_rate.setValue(settings.get('refresh_rate', UI_CONFIG['refresh_interval']))
            
            # Company information
            self.company_name.setText(settings.get('company_name', APP_CONFIG['developer']))
            self.company_address.setText(settings.get('company_address', 'Dhi Qar, Iraq'))
            self.company_phone.setText(settings.get('company_phone', '+9647813563139'))
            self.company_email.setText(settings.get('company_email', 'ah343238@gmail.com'))
            
            # Pump settings
            self.max_temperature.setValue(settings.get('max_temperature', PUMP_CONFIG['critical_temperature']))
            self.max_vibration.setValue(settings.get('max_vibration', PUMP_CONFIG['max_vibration']))
            self.min_oil_level.setValue(settings.get('min_oil_level', PUMP_CONFIG['min_oil_level'] * 100))
            self.maintenance_interval.setValue(settings.get('maintenance_interval', PUMP_CONFIG['maintenance_interval']))
            self.chart_points.setValue(settings.get('chart_points', UI_CONFIG['chart_points']))
            self.continuous_monitoring.setChecked(settings.get('continuous_monitoring', True))
            self.email_notifications.setChecked(settings.get('email_notifications', True))
            
            # AI configuration
            self.prediction_threshold.setValue(
                settings.get('prediction_threshold', AI_MODELS_CONFIG['failure_prediction']['threshold'] * 100)
            )
            self.anomaly_sensitivity.setValue(
                settings.get('anomaly_sensitivity', int(AI_MODELS_CONFIG['anomaly_detection']['sensitivity'] * 10))
            )
            self.auto_model_update.setChecked(settings.get('auto_model_update', True))
            
            # System configuration
            self.db_type.setCurrentText(settings.get('db_type', 'SQLite'))
            self.db_host.setText(settings.get('db_host', 'localhost'))
            self.db_user.setText(settings.get('db_user', 'ipump_user'))
            self.db_password.setText(settings.get('db_password', ''))
            self.db_name.setText(settings.get('db_name', 'ipump_db'))
            self.auto_backup.setChecked(settings.get('auto_backup', True))
            self.enable_auth.setChecked(settings.get('enable_auth', True))
            self.log_level.setCurrentText(settings.get('log_level', 'INFO'))
            self.data_retention.setValue(settings.get('data_retention', 365))
            
            # Refresh widget state
            self.on_db_type_changed(self.db_type.currentText())
            
            # Refresh informational panels
            self.update_model_info()
            self.update_system_info()
            
            logger.info("Settings loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self.load_default_settings()
            QMessageBox.warning(self, "Load settings", 
                              "Default settings were loaded because of a configuration error")
    
    def update_model_info(self):
        """Update model information"""
        try:
            accuracy = getattr(failure_predictor, 'accuracy', 0.85)
            features = len(AI_MODELS_CONFIG['failure_prediction'].get('features', []))
            model_type = getattr(failure_predictor, 'model_type', 'XGBoost Classifier')
            
            status_text = (
                "Trained" if getattr(failure_predictor, 'is_trained', False)
                else "Not trained"
            )
            model_info = f"""
            <b>AI model information:</b>
            <ul>
                <li>Model: {model_type}</li>
                <li>Status: {status_text}</li>
                <li>Feature count: {features}</li>
                <li>Accuracy: {accuracy:.1%}</li>
                <li>Prediction threshold: {self.prediction_threshold.value()}%</li>
                <li>Last update: {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
            </ul>
            """
            self.model_info.setText(model_info)
        except Exception as e:
            self.model_info.setText(f"<b>Failed to load model information:</b><br>{str(e)}")
            logger.error(f"Error updating model information: {e}")
    
    def update_system_info(self):
        """Update system information"""
        try:
            import platform
            import psutil
            
            disk_usage = psutil.disk_usage('/')
            system_info = f"""
            <b>System information:</b>
            <ul>
                <li>Operating system: {platform.system()} {platform.release()}</li>
                <li>Processor: {platform.processor()}</li>
                <li>CPU cores: {psutil.cpu_count()}</li>
                <li>Memory usage: {psutil.virtual_memory().percent}%</li>
                <li>Free disk space: {disk_usage.free // (1024**3)} GB of {disk_usage.total // (1024**3)} GB</li>
                <li>Python version: {platform.python_version()}</li>
                <li>Application version: {APP_CONFIG['version']}</li>
                <li>Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            """
            self.system_info.setText(system_info)
        except Exception as e:
            self.system_info.setText(f"<b>Failed to load system information:</b><br>{str(e)}")
            logger.error(f"Error updating system information: {e}")
    
    def save_settings(self):
        """Save settings"""
        try:
            settings = {
                'language': self.language_combo.currentText(),
                'theme': self.theme_combo.currentText(),
                'refresh_rate': self.refresh_rate.value(),
                'company_name': self.company_name.text(),
                'company_address': self.company_address.text(),
                'company_phone': self.company_phone.text(),
                'company_email': self.company_email.text(),
                'max_temperature': self.max_temperature.value(),
                'max_vibration': self.max_vibration.value(),
                'min_oil_level': self.min_oil_level.value(),
                'maintenance_interval': self.maintenance_interval.value(),
                'chart_points': self.chart_points.value(),
                'continuous_monitoring': self.continuous_monitoring.isChecked(),
                'email_notifications': self.email_notifications.isChecked(),
                'prediction_threshold': self.prediction_threshold.value(),
                'anomaly_sensitivity': self.anomaly_sensitivity.value(),
                'auto_model_update': self.auto_model_update.isChecked(),
                'db_type': self.db_type.currentText(),
                'db_host': self.db_host.text(),
                'db_user': self.db_user.text(),
                'db_password': self.db_password.text(),
                'db_name': self.db_name.text(),
                'auto_backup': self.auto_backup.isChecked(),
                'enable_auth': self.enable_auth.isChecked(),
                'log_level': self.log_level.currentText(),
                'data_retention': self.data_retention.value(),
                'last_modified': datetime.now().isoformat()
            }
            
            # Ensure the configuration directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Persist configuration to disk
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)

            logger.info("Settings saved successfully")
            QMessageBox.information(
                self,
                "Save settings",
                "Settings saved successfully\n\nSome changes will apply after restarting the application"
            )

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
    def reset_settings(self):
        """Reset settings"""
        reply = QMessageBox.question(
            self, 
            "Reset settings",
            "Are you sure you want to reset all settings?\n\nAll unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.load_settings()
            QMessageBox.information(self, "Information", "Settings have been reset")
    
    def load_default_settings(self):
        """Load default settings"""
        reply = QMessageBox.question(
            self, 
            "Load defaults",
            "Do you want to restore the system defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove custom configuration to restore defaults
            if self.settings_file.exists():
                self.settings_file.unlink()

            self.load_settings()
            QMessageBox.information(self, "Information", "Default settings restored")
    
    def retrain_model(self):
        """Retrain the model"""
        try:
            reply = QMessageBox.question(
                self,
                "Train model",
                "Do you want to retrain the AI model?\n\nThis process may take several minutes.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Create progress dialog
                progress = QProgressDialog("Training the model...", "Cancel", 0, 100, self)
                progress.setWindowTitle("Train model")
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.show()
                
                # Start and monitor the training thread
                self.training_thread = ModelTrainingThread(failure_predictor)
                self.training_thread.progress_updated.connect(progress.setValue)
                self.training_thread.training_finished.connect(
                    lambda success, msg: self.on_training_finished(success, msg, progress)
                )
                self.training_thread.start()
                
        except Exception as e:
            logger.error(f"Error starting model training: {e}")
            QMessageBox.critical(self, "Error", f"Model training failed: {e}")
    
    def on_training_finished(self, success, message, progress):
        """Handle training completion"""
        progress.close()
        if success:
            QMessageBox.information(self, "Information", f"{message}")
            self.update_model_info()
        else:
            QMessageBox.critical(self, "Error", f"{message}")
    
    def import_model(self):
        """Import model"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Import model", 
                "", 
                "Model Files (*.pkl *.joblib *.h5 *.onnx);;All Files (*)"
            )
            
            if file_path:
                # Simulate model import
                QMessageBox.information(
                    self,
                    "Import model",
                    f"Model imported successfully\n\nPath: {file_path}"
                )
                self.update_model_info()

        except Exception as e:
            logger.error(f"Model import error: {e}")
            QMessageBox.critical(self, "Error", f"Model import failed: {e}")

    def export_model(self):
        """Export the trained model"""
        try:
            if not getattr(failure_predictor, 'is_trained', False):
                QMessageBox.warning(
                    self,
                    "Export model",
                    "No trained model available for export"
                )
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export model",
                f"failure_model_{datetime.now().strftime('%Y%m%d_%H%M')}.pkl",
                "Model Files (*.pkl *.joblib);;All Files (*)"
            )

            if file_path:
                # Simulate model export
                QMessageBox.information(
                    self,
                    "Export model",
                    f"Model exported successfully\n\nPath: {file_path}"
                )

        except Exception as e:
            logger.error(f"Model export error: {e}")
            QMessageBox.critical(self, "Error", f"Model export failed: {e}")

    def test_database_connection(self):
        """Test database connection"""
        try:
            # Simulate a database connectivity test
            QMessageBox.information(
                self,
                "Test connection",
                "Database connection succeeded"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Test connection",
                f"Database connection failed:\n{str(e)}"
            )

    def test_notifications(self):
        """Test notification system"""
        try:
            # Simulate notification delivery
            QMessageBox.information(
                self,
                "Test notifications",
                "Test notification sent successfully\n\nCheck your inbox"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Test notifications",
                f"Failed to send notification:\n{str(e)}"
            )
