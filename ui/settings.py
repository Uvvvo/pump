"""
وحدة الإعدادات لتطبيق iPump
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QGroupBox, QLabel, QPushButton, QComboBox,
                           QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
                           QSlider, QTabWidget, QMessageBox, QFileDialog,
                           QListWidget, QListWidgetItem, QScrollArea)
from PyQt6.QtGui import QFont, QIntValidator, QDoubleValidator
from PyQt6.QtCore import Qt, QTimer
import json
from pathlib import Path

from config import APP_CONFIG, UI_CONFIG, PUMP_CONFIG, AI_MODELS_CONFIG
from database import db_manager
from ai_models import failure_predictor

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """تهيئة واجهة الإعدادات"""
        main_layout = QVBoxLayout(self)
        
        # تبويبات الإعدادات
        self.settings_tabs = QTabWidget()
        
        # إعدادات عامة
        self.general_tab = self.create_general_tab()
        self.settings_tabs.addTab(self.general_tab, "عام")
        
        # إعدادات المضخات
        self.pumps_tab = self.create_pumps_tab()
        self.settings_tabs.addTab(self.pumps_tab, "المضخات")
        
        # إعدادات الذكاء الاصطناعي
        self.ai_tab = self.create_ai_tab()
        self.settings_tabs.addTab(self.ai_tab, "الذكاء الاصطناعي")
        
        # إعدادات النظام
        self.system_tab = self.create_system_tab()
        self.settings_tabs.addTab(self.system_tab, "النظام")
        
        main_layout.addWidget(self.settings_tabs)
        
        # أزرار الحفظ والإعادة
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("حفظ الإعدادات")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("إعادة التعيين")
        self.reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_btn)
        
        self.defaults_btn = QPushButton("الإعدادات الافتراضية")
        self.defaults_btn.clicked.connect(self.load_default_settings)
        button_layout.addWidget(self.defaults_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
    def create_general_tab(self):
        """إنشاء تبويب الإعدادات العامة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # إعدادات الواجهة
        interface_group = QGroupBox("إعدادات الواجهة")
        interface_layout = QGridLayout(interface_group)
        
        interface_layout.addWidget(QLabel("اللغة:"), 0, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["العربية", "English"])
        interface_layout.addWidget(self.language_combo, 0, 1)
        
        interface_layout.addWidget(QLabel("السمة:"), 1, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["داكن", "فاتح", "تلقائي"])
        interface_layout.addWidget(self.theme_combo, 1, 1)
        
        interface_layout.addWidget(QLabel("معدل التحديث (مللي ثانية):"), 2, 0)
        self.refresh_rate = QSpinBox()
        self.refresh_rate.setRange(1000, 30000)
        self.refresh_rate.setSingleStep(1000)
        interface_layout.addWidget(self.refresh_rate, 2, 1)
        
        layout.addWidget(interface_group)
        
        # إعدادات الشركة
        company_group = QGroupBox("معلومات الشركة")
        company_layout = QGridLayout(company_group)
        
        company_layout.addWidget(QLabel("اسم الشركة:"), 0, 0)
        self.company_name = QLineEdit()
        company_layout.addWidget(self.company_name, 0, 1)
        
        company_layout.addWidget(QLabel("العنوان:"), 1, 0)
        self.company_address = QLineEdit()
        company_layout.addWidget(self.company_address, 1, 1)
        
        company_layout.addWidget(QLabel("الهاتف:"), 2, 0)
        self.company_phone = QLineEdit()
        company_layout.addWidget(self.company_phone, 2, 1)
        
        company_layout.addWidget(QLabel("البريد الإلكتروني:"), 3, 0)
        self.company_email = QLineEdit()
        company_layout.addWidget(self.company_email, 3, 1)
        
        layout.addWidget(company_group)
        
        layout.addStretch()
        return widget
    
    def create_pumps_tab(self):
        """إنشاء تبويب إعدادات المضخات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # عتبات الإنذار
        thresholds_group = QGroupBox("عتبات الإنذار")
        thresholds_layout = QGridLayout(thresholds_group)
        
        thresholds_layout.addWidget(QLabel("درجة الحرارة القصوى (°C):"), 0, 0)
        self.max_temperature = QDoubleSpinBox()
        self.max_temperature.setRange(0, 150)
        self.max_temperature.setDecimals(1)
        thresholds_layout.addWidget(self.max_temperature, 0, 1)
        
        thresholds_layout.addWidget(QLabel("الاهتزاز الأقصى (m/s²):"), 1, 0)
        self.max_vibration = QDoubleSpinBox()
        self.max_vibration.setRange(0, 20)
        self.max_vibration.setDecimals(1)
        thresholds_layout.addWidget(self.max_vibration, 1, 1)
        
        thresholds_layout.addWidget(QLabel("أقل مستوى زيت (%):"), 2, 0)
        self.min_oil_level = QDoubleSpinBox()
        self.min_oil_level.setRange(0, 100)
        self.min_oil_level.setDecimals(1)
        thresholds_layout.addWidget(self.min_oil_level, 2, 1)
        
        thresholds_layout.addWidget(QLabel("فترة الصيانة (ساعة):"), 3, 0)
        self.maintenance_interval = QSpinBox()
        self.maintenance_interval.setRange(100, 5000)
        self.maintenance_interval.setSingleStep(100)
        thresholds_layout.addWidget(self.maintenance_interval, 3, 1)
        
        layout.addWidget(thresholds_group)
        
        # إعدادات المراقبة
        monitoring_group = QGroupBox("إعدادات المراقبة")
        monitoring_layout = QGridLayout(monitoring_group)
        
        monitoring_layout.addWidget(QLabel("نقاط البيانات في الرسوم:"), 0, 0)
        self.chart_points = QSpinBox()
        self.chart_points.setRange(50, 1000)
        self.chart_points.setSingleStep(50)
        monitoring_layout.addWidget(self.chart_points, 0, 1)
        
        monitoring_layout.addWidget(QLabel("تفعيل المراقبة المستمرة:"), 1, 0)
        self.continuous_monitoring = QCheckBox()
        monitoring_layout.addWidget(self.continuous_monitoring, 1, 1)
        
        monitoring_layout.addWidget(QLabel("إشعارات البريد الإلكتروني:"), 2, 0)
        self.email_notifications = QCheckBox()
        monitoring_layout.addWidget(self.email_notifications, 2, 1)
        
        layout.addWidget(monitoring_group)
        
        layout.addStretch()
        return widget
    
    def create_ai_tab(self):
        """إنشاء تبويب إعدادات الذكاء الاصطناعي"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # إعدادات النموذج
        model_group = QGroupBox("إعدادات نموذج التنبؤ")
        model_layout = QGridLayout(model_group)
        
        model_layout.addWidget(QLabel("عتبة التنبؤ (%):"), 0, 0)
        self.prediction_threshold = QDoubleSpinBox()
        self.prediction_threshold.setRange(0, 100)
        self.prediction_threshold.setDecimals(1)
        model_layout.addWidget(self.prediction_threshold, 0, 1)
        
        model_layout.addWidget(QLabel("حساسية كشف الشذوذ:"), 1, 0)
        self.anomaly_sensitivity = QSlider(Qt.Orientation.Horizontal)
        self.anomaly_sensitivity.setRange(1, 10)
        self.anomaly_sensitivity.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.anomaly_sensitivity.setTickInterval(1)
        model_layout.addWidget(self.anomaly_sensitivity, 1, 1)
        
        model_layout.addWidget(QLabel("تحديث النموذج التلقائي:"), 2, 0)
        self.auto_model_update = QCheckBox()
        model_layout.addWidget(self.auto_model_update, 2, 1)
        
        layout.addWidget(model_group)
        
        # إدارة النماذج
        management_group = QGroupBox("إدارة النماذج")
        management_layout = QVBoxLayout(management_group)
        
        self.train_model_btn = QPushButton("تدريب النموذج من جديد")
        self.train_model_btn.clicked.connect(self.retrain_model)
        management_layout.addWidget(self.train_model_btn)
        
        self.import_model_btn = QPushButton("استيراد نموذج")
        self.import_model_btn.clicked.connect(self.import_model)
        management_layout.addWidget(self.import_model_btn)
        
        self.export_model_btn = QPushButton("تصدير النموذج")
        self.export_model_btn.clicked.connect(self.export_model)
        management_layout.addWidget(self.export_model_btn)
        
        # معلومات النموذج
        self.model_info = QLabel("جاري تحميل معلومات النموذج...")
        self.model_info.setWordWrap(True)
        self.model_info.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 5px;")
        management_layout.addWidget(self.model_info)
        
        layout.addWidget(management_group)
        
        layout.addStretch()
        return widget
    
    def create_system_tab(self):
        """إنشاء تبويب إعدادات النظام"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # إعدادات قاعدة البيانات
        database_group = QGroupBox("إعدادات قاعدة البيانات")
        database_layout = QGridLayout(database_group)
        
        database_layout.addWidget(QLabel("نوع قاعدة البيانات:"), 0, 0)
        self.db_type = QComboBox()
        self.db_type.addItems(["SQLite", "PostgreSQL", "MySQL"])
        database_layout.addWidget(self.db_type, 0, 1)
        
        database_layout.addWidget(QLabel("اسم المضيف:"), 1, 0)
        self.db_host = QLineEdit()
        database_layout.addWidget(self.db_host, 1, 1)
        
        database_layout.addWidget(QLabel("اسم المستخدم:"), 2, 0)
        self.db_user = QLineEdit()
        database_layout.addWidget(self.db_user, 2, 1)
        
        database_layout.addWidget(QLabel("كلمة المرور:"), 3, 0)
        self.db_password = QLineEdit()
        self.db_password.setEchoMode(QLineEdit.EchoMode.Password)
        database_layout.addWidget(self.db_password, 3, 1)
        
        database_layout.addWidget(QLabel("نسخ احتياطي تلقائي:"), 4, 0)
        self.auto_backup = QCheckBox()
        database_layout.addWidget(self.auto_backup, 4, 1)
        
        layout.addWidget(database_group)
        
        # إعدادات الأمان
        security_group = QGroupBox("إعدادات الأمان")
        security_layout = QGridLayout(security_group)
        
        security_layout.addWidget(QLabel("تفعيل المصادقة:"), 0, 0)
        self.enable_auth = QCheckBox()
        security_layout.addWidget(self.enable_auth, 0, 1)
        
        security_layout.addWidget(QLabel("مستوى التسجيل:"), 1, 0)
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        security_layout.addWidget(self.log_level, 1, 1)
        
        security_layout.addWidget(QLabel("أيام احتفاظ البيانات:"), 2, 0)
        self.data_retention = QSpinBox()
        self.data_retention.setRange(30, 1095)  # 3 سنوات كحد أقصى
        security_layout.addWidget(self.data_retention, 2, 1)
        
        layout.addWidget(security_group)
        
        # معلومات النظام
        system_info_group = QGroupBox("معلومات النظام")
        system_info_layout = QVBoxLayout(system_info_group)
        
        self.system_info = QLabel()
        self.system_info.setWordWrap(True)
        self.system_info.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 5px;")
        system_info_layout.addWidget(self.system_info)
        
        self.update_system_info()
        
        layout.addWidget(system_info_group)
        
        layout.addStretch()
        return widget
    
    def load_settings(self):
        """تحميل الإعدادات الحالية"""
        try:
            # الإعدادات العامة
            self.language_combo.setCurrentText("العربية")
            self.theme_combo.setCurrentText("داكن")
            self.refresh_rate.setValue(UI_CONFIG['refresh_interval'])
            
            # معلومات الشركة
            self.company_name.setText(APP_CONFIG['company'])
            self.company_address.setText("الرياض، المملكة العربية السعودية")
            self.company_phone.setText("+966112345678")
            self.company_email.setText("info@company.com")
            
            # إعدادات المضخات
            self.max_temperature.setValue(PUMP_CONFIG['critical_temperature'])
            self.max_vibration.setValue(PUMP_CONFIG['max_vibration'])
            self.min_oil_level.setValue(PUMP_CONFIG['min_oil_level'] * 100)
            self.maintenance_interval.setValue(PUMP_CONFIG['maintenance_interval'])
            self.chart_points.setValue(UI_CONFIG['chart_points'])
            self.continuous_monitoring.setChecked(True)
            self.email_notifications.setChecked(True)
            
            # إعدادات الذكاء الاصطناعي
            self.prediction_threshold.setValue(AI_MODELS_CONFIG['failure_prediction']['threshold'] * 100)
            self.anomaly_sensitivity.setValue(int(AI_MODELS_CONFIG['anomaly_detection']['sensitivity'] * 10))
            self.auto_model_update.setChecked(True)
            
            # إعدادات النظام
            self.db_type.setCurrentText("SQLite")
            self.db_host.setText("localhost")
            self.db_user.setText("ipump_user")
            self.auto_backup.setChecked(True)
            self.enable_auth.setChecked(True)
            self.log_level.setCurrentText("INFO")
            self.data_retention.setValue(365)
            
            # تحديث معلومات النموذج
            self.update_model_info()
            
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {e}")
    
    def update_model_info(self):
        """تحديث معلومات النموذج"""
        try:
            model_info = f"""
            <b>معلومات نموذج الذكاء الاصطناعي:</b><br>
            • النموذج: XGBoost Classifier<br>
            • الحالة: {failure_predictor.is_trained and 'مدرب' or 'غير مدرب'}<br>
            • عدد الميزات: {len(AI_MODELS_CONFIG['failure_prediction']['features'])}<br>
            • عتبة التنبؤ: {AI_MODELS_CONFIG['failure_prediction']['threshold'] * 100}%<br>
            • آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            self.model_info.setText(model_info)
        except Exception as e:
            self.model_info.setText(f"خطأ في تحميل معلومات النموذج: {e}")
    
    def update_system_info(self):
        """تحديث معلومات النظام"""
        try:
            import platform
            import psutil
            
            system_info = f"""
            <b>معلومات النظام:</b><br>
            • نظام التشغيل: {platform.system()} {platform.release()}<br>
            • المعالج: {platform.processor()}<br>
            • الذاكرة: {psutil.virtual_memory().total // (1024**3)} GB<br>
            • المساحة: {psutil.disk_usage('/').total // (1024**3)} GB<br>
            • إصدار Python: {platform.python_version()}<br>
            • إصدار التطبيق: {APP_CONFIG['version']}
            """
            self.system_info.setText(system_info)
        except Exception as e:
            self.system_info.setText(f"خطأ في تحميل معلومات النظام: {e}")
    
    def save_settings(self):
        """حفظ الإعدادات"""
        try:
            # في التطبيق الحقيقي، سيتم حفظ الإعدادات في ملف تكوين
            # هنا نستخدم رسالة توضيحية
            
            QMessageBox.information(
                self, 
                "حفظ الإعدادات", 
                "تم حفظ الإعدادات بنجاح\n\nسيتم تطبيق التغييرات بعد إعادة تشغيل التطبيق"
            )
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في حفظ الإعدادات: {e}")
    
    def reset_settings(self):
        """إعادة تعيين الإعدادات"""
        reply = QMessageBox.question(
            self, 
            "إعادة التعيين", 
            "هل أنت متأكد من أنك تريد إعادة تعيين جميع الإعدادات؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.load_default_settings()
    
    def load_default_settings(self):
        """تحميل الإعدادات الافتراضية"""
        reply = QMessageBox.question(
            self, 
            "الإعدادات الافتراضية", 
            "هل تريد استعادة الإعدادات الافتراضية؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.load_settings()
            QMessageBox.information(self, "تم", "تم تحميل الإعدادات الافتراضية")
    
    def retrain_model(self):
        """إعادة تدريب النموذج"""
        try:
            reply = QMessageBox.question(
                self,
                "تدريب النموذج",
                "هل تريد إعادة تدريب نموذج الذكاء الاصطناعي؟\n\nهذه العملية قد تستغرق عدة دقائق.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                failure_predictor.train_model()
                self.update_model_info()
                QMessageBox.information(self, "تم", "تم تدريب النموذج بنجاح")
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تدريب النموذج: {e}")
    
    def import_model(self):
        """استيراد نموذج"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "استيراد نموذج", 
                "", 
                "Model Files (*.pkl *.joblib)"
            )
            
            if file_path:
                QMessageBox.information(
                    self, 
                    "استيراد النموذج", 
                    f"سيتم تطوير ميزة استيراد النماذج في النسخة القادمة\n\nالمسار: {file_path}"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في استيراد النموذج: {e}")
    
    def export_model(self):
        """تصدير النموذج"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "تصدير النموذج", 
                f"ipump_model_{datetime.now().strftime('%Y%m%d_%H%M')}.pkl",
                "Model Files (*.pkl)"
            )
            
            if file_path:
                QMessageBox.information(
                    self, 
                    "تصدير النموذج", 
                    f"سيتم تطوير ميزة تصدير النماذج في النسخة القادمة\n\nالمسار: {file_path}"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تصدير النموذج: {e}")
    
    def refresh_data(self):
        """تحديث البيانات"""
        self.update_model_info()
        self.update_system_info()