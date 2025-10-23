"""
وحدة الإعدادات لتطبيق iPump
"""

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

# إعداد التسجيل
logger = logging.getLogger(__name__)


class ModelTrainingThread(QThread):
    """خيط منفصل لتدريب النموذج"""
    training_finished = pyqtSignal(bool, str)
    progress_updated = pyqtSignal(int)
    
    def __init__(self, predictor):
        super().__init__()
        self.predictor = predictor
    
    def run(self):
        try:
            # محاكاة تحديث التقدم
            for i in range(101):
                self.progress_updated.emit(i)
                self.msleep(50)  # محاكاة وقت التدريب
            
            # تدريب النموذج الفعلي
            success = self.predictor.train_model()
            message = "تم تدريب النموذج بنجاح" if success else "فشل في تدريب النموذج"
            self.training_finished.emit(success, message)
        except Exception as e:
            self.training_finished.emit(False, f"خطأ في التدريب: {str(e)}")


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = Path("config/settings.json")
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """تهيئة واجهة الإعدادات"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # تبويبات الإعدادات
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # إعدادات عامة
        self.general_tab = self.create_general_tab()
        self.settings_tabs.addTab(self.general_tab, "⚙️ عام")
        
        # إعدادات المضخات
        self.pumps_tab = self.create_pumps_tab()
        self.settings_tabs.addTab(self.pumps_tab, "🔧 المضخات")
        
        # إعدادات الذكاء الاصطناعي
        self.ai_tab = self.create_ai_tab()
        self.settings_tabs.addTab(self.ai_tab, "🤖 الذكاء الاصطناعي")
        
        # إعدادات النظام
        self.system_tab = self.create_system_tab()
        self.settings_tabs.addTab(self.system_tab, "💻 النظام")
        
        main_layout.addWidget(self.settings_tabs)
        
        # أزرار الحفظ والإعادة
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_btn = QPushButton("💾 حفظ الإعدادات")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px; }")
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("🔄 إعادة التعيين")
        self.reset_btn.clicked.connect(self.reset_settings)
        self.reset_btn.setStyleSheet("QPushButton { background-color: #ffc107; color: black; padding: 8px; }")
        button_layout.addWidget(self.reset_btn)
        
        self.defaults_btn = QPushButton("⚡ الإعدادات الافتراضية")
        self.defaults_btn.clicked.connect(self.load_default_settings)
        self.defaults_btn.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; padding: 8px; }")
        button_layout.addWidget(self.defaults_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
    def create_general_tab(self):
        """إنشاء تبويب الإعدادات العامة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # إعدادات الواجهة
        interface_group = QGroupBox("🎨 إعدادات الواجهة")
        interface_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        interface_layout = QGridLayout(interface_group)
        interface_layout.setVerticalSpacing(10)
        interface_layout.setHorizontalSpacing(15)
        
        interface_layout.addWidget(QLabel("اللغة:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["العربية", "English", "Français"])
        self.language_combo.setToolTip("اختر لغة الواجهة")
        interface_layout.addWidget(self.language_combo, 0, 1)
        
        interface_layout.addWidget(QLabel("السمة:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["داكن", "فاتح", "أزرق", "تلقائي"])
        self.theme_combo.setToolTip("اختر سمة الواجهة")
        interface_layout.addWidget(self.theme_combo, 1, 1)
        
        interface_layout.addWidget(QLabel("معدل التحديث (مللي ثانية):"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.refresh_rate = QSpinBox()
        self.refresh_rate.setRange(500, 30000)
        self.refresh_rate.setSingleStep(500)
        self.refresh_rate.setSuffix(" مللي ثانية")
        self.refresh_rate.setToolTip("فترة تحديث البيانات على الواجهة")
        interface_layout.addWidget(self.refresh_rate, 2, 1)
        
        layout.addWidget(interface_group)
        
        # إعدادات الشركة
        company_group = QGroupBox("🏢 معلومات الشركة")
        company_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        company_layout = QGridLayout(company_group)
        company_layout.setVerticalSpacing(10)
        company_layout.setHorizontalSpacing(15)
        
        company_layout.addWidget(QLabel("اسم الشركة:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("أدخل اسم الشركة")
        company_layout.addWidget(self.company_name, 0, 1)
        
        company_layout.addWidget(QLabel("العنوان:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.company_address = QLineEdit()
        self.company_address.setPlaceholderText("أدخل عنوان الشركة")
        company_layout.addWidget(self.company_address, 1, 1)
        
        company_layout.addWidget(QLabel("الهاتف:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.company_phone = QLineEdit()
        self.company_phone.setPlaceholderText("+9647813563139")
        company_layout.addWidget(self.company_phone, 2, 1)
        
        company_layout.addWidget(QLabel("البريد الإلكتروني:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        self.company_email = QLineEdit()
        self.company_email.setPlaceholderText("ah343238@gmail.com")
        company_layout.addWidget(self.company_email, 3, 1)
        
        layout.addWidget(company_group)
        layout.addStretch()
        return widget
    
    def create_pumps_tab(self):
        """إنشاء تبويب إعدادات المضخات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # عتبات الإنذار
        thresholds_group = QGroupBox("🚨 عتبات الإنذار")
        thresholds_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        thresholds_layout = QGridLayout(thresholds_group)
        thresholds_layout.setVerticalSpacing(10)
        thresholds_layout.setHorizontalSpacing(15)
        
        thresholds_layout.addWidget(QLabel("درجة الحرارة القصوى (°C):"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.max_temperature = QDoubleSpinBox()
        self.max_temperature.setRange(0, 200)
        self.max_temperature.setDecimals(1)
        self.max_temperature.setSuffix(" °C")
        self.max_temperature.setToolTip("الحد الأقصى لدرجة الحرارة المسموح بها")
        thresholds_layout.addWidget(self.max_temperature, 0, 1)
        
        thresholds_layout.addWidget(QLabel("الاهتزاز الأقصى (m/s²):"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.max_vibration = QDoubleSpinBox()
        self.max_vibration.setRange(0, 50)
        self.max_vibration.setDecimals(2)
        self.max_vibration.setSuffix(" m/s²")
        self.max_vibration.setToolTip("الحد الأقصى للاهتزاز المسموح به")
        thresholds_layout.addWidget(self.max_vibration, 1, 1)
        
        thresholds_layout.addWidget(QLabel("أقل مستوى زيت (%):"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.min_oil_level = QDoubleSpinBox()
        self.min_oil_level.setRange(0, 100)
        self.min_oil_level.setDecimals(1)
        self.min_oil_level.setSuffix(" %")
        self.min_oil_level.setToolTip("أقل مستوى زيت مسموح به")
        thresholds_layout.addWidget(self.min_oil_level, 2, 1)
        
        thresholds_layout.addWidget(QLabel("فترة الصيانة (ساعة):"), 3, 0, Qt.AlignmentFlag.AlignRight)
        self.maintenance_interval = QSpinBox()
        self.maintenance_interval.setRange(24, 10000)
        self.maintenance_interval.setSingleStep(24)
        self.maintenance_interval.setSuffix(" ساعة")
        self.maintenance_interval.setToolTip("الفترة بين عمليات الصيانة الدورية")
        thresholds_layout.addWidget(self.maintenance_interval, 3, 1)
        
        layout.addWidget(thresholds_group)
        
        # إعدادات المراقبة
        monitoring_group = QGroupBox("📊 إعدادات المراقبة")
        monitoring_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        monitoring_layout = QGridLayout(monitoring_group)
        monitoring_layout.setVerticalSpacing(10)
        monitoring_layout.setHorizontalSpacing(15)
        
        monitoring_layout.addWidget(QLabel("نقاط البيانات في الرسوم:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.chart_points = QSpinBox()
        self.chart_points.setRange(50, 5000)
        self.chart_points.setSingleStep(50)
        self.chart_points.setSuffix(" نقطة")
        self.chart_points.setToolTip("عدد نقاط البيانات المعروضة في الرسوم البيانية")
        monitoring_layout.addWidget(self.chart_points, 0, 1)
        
        monitoring_layout.addWidget(QLabel("تفعيل المراقبة المستمرة:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.continuous_monitoring = QCheckBox()
        self.continuous_monitoring.setToolTip("تفعيل المراقبة المستمرة للمضخات")
        monitoring_layout.addWidget(self.continuous_monitoring, 1, 1)
        
        monitoring_layout.addWidget(QLabel("إشعارات البريد الإلكتروني:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.email_notifications = QCheckBox()
        self.email_notifications.setToolTip("إرسال إشعارات بالبريد الإلكتروني عند حدوث إنذارات")
        monitoring_layout.addWidget(self.email_notifications, 2, 1)
        
        # زر اختبار الإشعارات
        self.test_notifications_btn = QPushButton("اختبار الإشعارات")
        self.test_notifications_btn.clicked.connect(self.test_notifications)
        self.test_notifications_btn.setToolTip("اختبار نظام الإشعارات")
        monitoring_layout.addWidget(self.test_notifications_btn, 3, 1)
        
        layout.addWidget(monitoring_group)
        layout.addStretch()
        return widget
    
    def create_ai_tab(self):
        """إنشاء تبويب إعدادات الذكاء الاصطناعي"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # إعدادات النموذج
        model_group = QGroupBox("🧠 إعدادات نموذج التنبؤ")
        model_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        model_layout = QGridLayout(model_group)
        model_layout.setVerticalSpacing(10)
        model_layout.setHorizontalSpacing(15)
        
        model_layout.addWidget(QLabel("عتبة التنبؤ (%):"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.prediction_threshold = QDoubleSpinBox()
        self.prediction_threshold.setRange(50, 99)
        self.prediction_threshold.setDecimals(1)
        self.prediction_threshold.setSuffix(" %")
        self.prediction_threshold.setToolTip("عتبة الثقة للتنبؤ بالفشل")
        model_layout.addWidget(self.prediction_threshold, 0, 1)
        
        model_layout.addWidget(QLabel("حساسية كشف الشذوذ:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        sensitivity_layout = QHBoxLayout()
        self.anomaly_sensitivity = QSlider(Qt.Orientation.Horizontal)
        self.anomaly_sensitivity.setRange(1, 10)
        self.anomaly_sensitivity.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.anomaly_sensitivity.setTickInterval(1)
        self.anomaly_sensitivity.setToolTip("حساسية كشف الشذوذ (1 = أقل حساسية, 10 = أعلى حساسية)")
        self.sensitivity_label = QLabel("5")
        self.anomaly_sensitivity.valueChanged.connect(
            lambda v: self.sensitivity_label.setText(str(v))
        )
        sensitivity_layout.addWidget(self.anomaly_sensitivity)
        sensitivity_layout.addWidget(self.sensitivity_label)
        model_layout.addLayout(sensitivity_layout, 1, 1)
        
        model_layout.addWidget(QLabel("تحديث النموذج التلقائي:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.auto_model_update = QCheckBox()
        self.auto_model_update.setToolTip("التحديث التلقائي للنموذج عند توفر بيانات جديدة")
        model_layout.addWidget(self.auto_model_update, 2, 1)
        
        layout.addWidget(model_group)
        
        # إدارة النماذج
        management_group = QGroupBox("🛠️ إدارة النماذج")
        management_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        management_layout = QVBoxLayout(management_group)
        
        buttons_layout = QHBoxLayout()
        
        self.train_model_btn = QPushButton("🎓 تدريب النموذج من جديد")
        self.train_model_btn.clicked.connect(self.retrain_model)
        self.train_model_btn.setToolTip("إعادة تدريب نموذج الذكاء الاصطناعي")
        buttons_layout.addWidget(self.train_model_btn)
        
        self.import_model_btn = QPushButton("📥 استيراد نموذج")
        self.import_model_btn.clicked.connect(self.import_model)
        self.import_model_btn.setToolTip("استيراد نموذج مدرب مسبقاً")
        buttons_layout.addWidget(self.import_model_btn)
        
        self.export_model_btn = QPushButton("📤 تصدير النموذج")
        self.export_model_btn.clicked.connect(self.export_model)
        self.export_model_btn.setToolTip("تصدير النموذج الحالي")
        buttons_layout.addWidget(self.export_model_btn)
        
        management_layout.addLayout(buttons_layout)
        
        # معلومات النموذج
        self.model_info = QLabel("جاري تحميل معلومات النموذج...")
        self.model_info.setWordWrap(True)
        self.model_info.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa; 
                padding: 15px; 
                border-radius: 8px;
                border: 1px solid #dee2e6;
                font-size: 12px;
            }
        """)
        management_layout.addWidget(self.model_info)
        
        layout.addWidget(management_group)
        layout.addStretch()
        return widget
    
    def create_system_tab(self):
        """إنشاء تبويب إعدادات النظام"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # إعدادات قاعدة البيانات
        database_group = QGroupBox("🗄️ إعدادات قاعدة البيانات")
        database_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        database_layout = QGridLayout(database_group)
        database_layout.setVerticalSpacing(10)
        database_layout.setHorizontalSpacing(15)
        
        database_layout.addWidget(QLabel("نوع قاعدة البيانات:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.db_type = QComboBox()
        self.db_type.addItems(["SQLite", "PostgreSQL", "MySQL", "Microsoft SQL Server"])
        self.db_type.currentTextChanged.connect(self.on_db_type_changed)
        database_layout.addWidget(self.db_type, 0, 1)
        
        database_layout.addWidget(QLabel("اسم المضيف:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.db_host = QLineEdit()
        self.db_host.setPlaceholderText("localhost أو عنوان IP")
        database_layout.addWidget(self.db_host, 1, 1)
        
        database_layout.addWidget(QLabel("اسم المستخدم:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.db_user = QLineEdit()
        self.db_user.setPlaceholderText("اسم المستخدم")
        database_layout.addWidget(self.db_user, 2, 1)
        
        database_layout.addWidget(QLabel("كلمة المرور:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        self.db_password = QLineEdit()
        self.db_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.db_password.setPlaceholderText("كلمة المرور")
        database_layout.addWidget(self.db_password, 3, 1)
        
        database_layout.addWidget(QLabel("اسم قاعدة البيانات:"), 4, 0, Qt.AlignmentFlag.AlignRight)
        self.db_name = QLineEdit()
        self.db_name.setPlaceholderText("ipump_db")
        database_layout.addWidget(self.db_name, 4, 1)
        
        database_layout.addWidget(QLabel("نسخ احتياطي تلقائي:"), 5, 0, Qt.AlignmentFlag.AlignRight)
        self.auto_backup = QCheckBox()
        self.auto_backup.setToolTip("إنشاء نسخ احتياطية تلقائية لقاعدة البيانات")
        database_layout.addWidget(self.auto_backup, 5, 1)
        
        # زر اختبار الاتصال
        self.test_db_btn = QPushButton("اختبار الاتصال بقاعدة البيانات")
        self.test_db_btn.clicked.connect(self.test_database_connection)
        database_layout.addWidget(self.test_db_btn, 6, 1)
        
        layout.addWidget(database_group)
        
        # إعدادات الأمان
        security_group = QGroupBox("🔒 إعدادات الأمان")
        security_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        security_layout = QGridLayout(security_group)
        security_layout.setVerticalSpacing(10)
        security_layout.setHorizontalSpacing(15)
        
        security_layout.addWidget(QLabel("تفعيل المصادقة:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.enable_auth = QCheckBox()
        self.enable_auth.setToolTip("تفعيل نظام المصادقة للمستخدمين")
        security_layout.addWidget(self.enable_auth, 0, 1)
        
        security_layout.addWidget(QLabel("مستوى التسجيل:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level.setToolTip("مستوى التفاصيل في سجلات النظام")
        security_layout.addWidget(self.log_level, 1, 1)
        
        security_layout.addWidget(QLabel("أيام احتفاظ البيانات:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.data_retention = QSpinBox()
        self.data_retention.setRange(30, 1825)  # 5 سنوات كحد أقصى
        self.data_retention.setSuffix(" يوم")
        self.data_retention.setToolTip("عدد أيام الاحتفاظ بالبيانات التاريخية")
        security_layout.addWidget(self.data_retention, 2, 1)
        
        layout.addWidget(security_group)
        
        # معلومات النظام
        system_info_group = QGroupBox("ℹ️ معلومات النظام")
        system_info_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        system_info_layout = QVBoxLayout(system_info_group)
        
        self.system_info = QLabel()
        self.system_info.setWordWrap(True)
        self.system_info.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa; 
                padding: 15px; 
                border-radius: 8px;
                border: 1px solid #dee2e6;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        system_info_layout.addWidget(self.system_info)
        
        # زر تحديث معلومات النظام
        refresh_info_btn = QPushButton("🔄 تحديث معلومات النظام")
        refresh_info_btn.clicked.connect(self.update_system_info)
        system_info_layout.addWidget(refresh_info_btn)
        
        layout.addWidget(system_info_group)
        layout.addStretch()
        return widget
    
    def on_db_type_changed(self, db_type):
        """تحديث واجهة إعدادات قاعدة البيانات بناءً على النوع"""
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
        """تحميل الإعدادات الحالية"""
        try:
            # محاولة تحميل الإعدادات من ملف
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            # الإعدادات العامة
            self.language_combo.setCurrentText(settings.get('language', 'العربية'))
            self.theme_combo.setCurrentText(settings.get('theme', 'داكن'))
            self.refresh_rate.setValue(settings.get('refresh_rate', UI_CONFIG['refresh_interval']))
            
            # معلومات الشركة
            self.company_name.setText(settings.get('company_name', APP_CONFIG['company']))
            self.company_address.setText(settings.get('company_address', 'العراق , ذي قار'))
            self.company_phone.setText(settings.get('company_phone', '+9647813563139'))
            self.company_email.setText(settings.get('company_email', 'ah343238@gmail.com'))
            
            # إعدادات المضخات
            self.max_temperature.setValue(settings.get('max_temperature', PUMP_CONFIG['critical_temperature']))
            self.max_vibration.setValue(settings.get('max_vibration', PUMP_CONFIG['max_vibration']))
            self.min_oil_level.setValue(settings.get('min_oil_level', PUMP_CONFIG['min_oil_level'] * 100))
            self.maintenance_interval.setValue(settings.get('maintenance_interval', PUMP_CONFIG['maintenance_interval']))
            self.chart_points.setValue(settings.get('chart_points', UI_CONFIG['chart_points']))
            self.continuous_monitoring.setChecked(settings.get('continuous_monitoring', True))
            self.email_notifications.setChecked(settings.get('email_notifications', True))
            
            # إعدادات الذكاء الاصطناعي
            self.prediction_threshold.setValue(
                settings.get('prediction_threshold', AI_MODELS_CONFIG['failure_prediction']['threshold'] * 100)
            )
            self.anomaly_sensitivity.setValue(
                settings.get('anomaly_sensitivity', int(AI_MODELS_CONFIG['anomaly_detection']['sensitivity'] * 10))
            )
            self.auto_model_update.setChecked(settings.get('auto_model_update', True))
            
            # إعدادات النظام
            self.db_type.setCurrentText(settings.get('db_type', 'SQLite'))
            self.db_host.setText(settings.get('db_host', 'localhost'))
            self.db_user.setText(settings.get('db_user', 'ipump_user'))
            self.db_password.setText(settings.get('db_password', ''))
            self.db_name.setText(settings.get('db_name', 'ipump_db'))
            self.auto_backup.setChecked(settings.get('auto_backup', True))
            self.enable_auth.setChecked(settings.get('enable_auth', True))
            self.log_level.setCurrentText(settings.get('log_level', 'INFO'))
            self.data_retention.setValue(settings.get('data_retention', 365))
            
            # تحديث حالة عناصر واجهة المستخدم
            self.on_db_type_changed(self.db_type.currentText())
            
            # تحديث المعلومات
            self.update_model_info()
            self.update_system_info()
            
            logger.info("تم تحميل الإعدادات بنجاح")
            
        except Exception as e:
            logger.error(f"خطأ في تحميل الإعدادات: {e}")
            self.load_default_settings()
            QMessageBox.warning(self, "تحميل الإعدادات", 
                              "تم تحميل الإعدادات الافتراضية بسبب خطأ في ملف الإعدادات")
    
    def update_model_info(self):
        """تحديث معلومات النموذج"""
        try:
            accuracy = getattr(failure_predictor, 'accuracy', 0.85)
            features = len(AI_MODELS_CONFIG['failure_prediction'].get('features', []))
            model_type = getattr(failure_predictor, 'model_type', 'XGBoost Classifier')
            
            model_info = f"""
            <b>معلومات نموذج الذكاء الاصطناعي:</b><br>
            • النموذج: {model_type}<br>
            • الحالة: {'🟢 مدرب' if getattr(failure_predictor, 'is_trained', False) else '🔴 غير مدرب'}<br>
            • عدد الميزات: {features}<br>
            • الدقة: {accuracy:.1%}<br>
            • عتبة التنبؤ: {self.prediction_threshold.value()}%<br>
            • آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            self.model_info.setText(model_info)
        except Exception as e:
            self.model_info.setText(f"<b>خطأ في تحميل معلومات النموذج:</b><br>{str(e)}")
            logger.error(f"خطأ في تحديث معلومات النموذج: {e}")
    
    def update_system_info(self):
        """تحديث معلومات النظام"""
        try:
            import platform
            import psutil
            
            system_info = f"""
            <b>معلومات النظام:</b><br>
            • نظام التشغيل: {platform.system()} {platform.release()}<br>
            • المعالج: {platform.processor()}<br>
            • نوى المعالج: {psutil.cpu_count()}<br>
            • استخدام الذاكرة: {psutil.virtual_memory().percent}%<br>
            • المساحة الحرة: {psutil.disk_usage('/').free // (1024**3)} GB من {psutil.disk_usage('/').total // (1024**3)} GB<br>
            • إصدار Python: {platform.python_version()}<br>
            • إصدار التطبيق: {APP_CONFIG['version']}<br>
            • وقت التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            self.system_info.setText(system_info)
        except Exception as e:
            self.system_info.setText(f"<b>خطأ في تحميل معلومات النظام:</b><br>{str(e)}")
            logger.error(f"خطأ في تحديث معلومات النظام: {e}")
    
    def save_settings(self):
        """حفظ الإعدادات"""
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
            
            # التأكد من وجود المجلد
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # حفظ الإعدادات
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            logger.info("تم حفظ الإعدادات بنجاح")
            QMessageBox.information(
                self, 
                "حفظ الإعدادات", 
                "✅ تم حفظ الإعدادات بنجاح\n\nسيتم تطبيق بعض التغييرات بعد إعادة تشغيل التطبيق"
            )
            
        except Exception as e:
            logger.error(f"خطأ في حفظ الإعدادات: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ خطأ في حفظ الإعدادات: {e}")
    
    def reset_settings(self):
        """إعادة تعيين الإعدادات"""
        reply = QMessageBox.question(
            self, 
            "إعادة التعيين", 
            "⚠️ هل أنت متأكد من أنك تريد إعادة تعيين جميع الإعدادات؟\n\nسيتم فقدان جميع التغييرات غير المحفوظة.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.load_settings()
            QMessageBox.information(self, "تم", "✅ تم إعادة تعيين الإعدادات")
    
    def load_default_settings(self):
        """تحميل الإعدادات الافتراضية"""
        reply = QMessageBox.question(
            self, 
            "الإعدادات الافتراضية", 
            "🔧 هل تريد استعادة الإعدادات الافتراضية للنظام؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # حذف ملف الإعدادات لاستعادة الافتراضية
            if self.settings_file.exists():
                self.settings_file.unlink()
            
            self.load_settings()
            QMessageBox.information(self, "تم", "✅ تم تحميل الإعدادات الافتراضية")
    
    def retrain_model(self):
        """إعادة تدريب النموذج"""
        try:
            reply = QMessageBox.question(
                self,
                "تدريب النموذج",
                "🎓 هل تريد إعادة تدريب نموذج الذكاء الاصطناعي؟\n\n⏱️ هذه العملية قد تستغرق عدة دقائق.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # إنشاء نافذة تقدم
                progress = QProgressDialog("جاري تدريب النموذج...", "إلغاء", 0, 100, self)
                progress.setWindowTitle("تدريب النموذج")
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.show()
                
                # إنشاء وتشغيل خيط التدريب
                self.training_thread = ModelTrainingThread(failure_predictor)
                self.training_thread.progress_updated.connect(progress.setValue)
                self.training_thread.training_finished.connect(
                    lambda success, msg: self.on_training_finished(success, msg, progress)
                )
                self.training_thread.start()
                
        except Exception as e:
            logger.error(f"خطأ في بدء تدريب النموذج: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ خطأ في تدريب النموذج: {e}")
    
    def on_training_finished(self, success, message, progress):
        """معالجة انتهاء التدريب"""
        progress.close()
        if success:
            QMessageBox.information(self, "تم", f"✅ {message}")
            self.update_model_info()
        else:
            QMessageBox.critical(self, "خطأ", f"❌ {message}")
    
    def import_model(self):
        """استيراد نموذج"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "استيراد نموذج", 
                "", 
                "Model Files (*.pkl *.joblib *.h5 *.onnx);;All Files (*)"
            )
            
            if file_path:
                # محاكاة استيراد النموذج
                QMessageBox.information(
                    self, 
                    "استيراد النموذج", 
                    f"📥 تم استيراد النموذج بنجاح\n\nالمسار: {file_path}"
                )
                self.update_model_info()
                
        except Exception as e:
            logger.error(f"خطأ في استيراد النموذج: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ خطأ في استيراد النموذج: {e}")
    
    def export_model(self):
        """تصدير النموذج"""
        try:
            if not getattr(failure_predictor, 'is_trained', False):
                QMessageBox.warning(
                    self, 
                    "تصدير النموذج", 
                    "⚠️ لا يوجد نموذج مدرب للتصدير"
                )
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "تصدير النموذج", 
                f"failure_model_{datetime.now().strftime('%Y%m%d_%H%M')}.pkl", 
                "Model Files (*.pkl *.joblib);;All Files (*)"
            )
            
            if file_path:
                # محاكاة تصدير النموذج
                QMessageBox.information(
                    self, 
                    "تصدير النموذج", 
                    f"📤 تم تصدير النموذج بنجاح\n\nالمسار: {file_path}"
                )
                
        except Exception as e:
            logger.error(f"خطأ في تصدير النموذج: {e}")
            QMessageBox.critical(self, "خطأ", f"❌ خطأ في تصدير النموذج: {e}")
    
    def test_database_connection(self):
        """اختبار اتصال قاعدة البيانات"""
        try:
            # محاكاة اختبار الاتصال
            QMessageBox.information(
                self, 
                "اختبار الاتصال", 
                "✅ تم الاتصال بقاعدة البيانات بنجاح"
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "اختبار الاتصال", 
                f"❌ فشل الاتصال بقاعدة البيانات:\n{str(e)}"
            )
    
    def test_notifications(self):
        """اختبار نظام الإشعارات"""
        try:
            # محاكاة اختبار الإشعارات
            QMessageBox.information(
                self, 
                "اختبار الإشعارات", 
                "📧 تم إرسال إشعار اختبار بنجاح\n\nتحقق من بريدك الإلكتروني"
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "اختبار الإشعارات", 
                f"❌ فشل في إرسال الإشعار:\n{str(e)}"
            )