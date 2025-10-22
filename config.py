"""
إعدادات تطبيق iPump
"""

import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import QSize

# المسارات
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# إنشاء المجلدات الضرورية
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# إعدادات قاعدة البيانات
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ipump_db',
    'user': 'ipump_user',
    'password': 'ipump_password'
}

# إعدادات نماذج الذكاء الاصطناعي
AI_MODELS_CONFIG = {
    'failure_prediction': {
        'model_path': MODELS_DIR / 'failure_model.pkl',
        'features': [
            'vibration_x', 'vibration_y', 'vibration_z',
            'temperature', 'pressure', 'flow_rate',
            'power_consumption', 'operating_hours',
            'bearing_temperature', 'oil_level', 'oil_quality'
        ],
        'threshold': 0.85
    },
    'anomaly_detection': {
        'model_path': MODELS_DIR / 'anomaly_model.pkl',
        'sensitivity': 0.9
    }
}

# إعدادات الواجهة
UI_CONFIG = {
    'theme': 'dark',
    'language': 'ar',
    'refresh_interval': 5000,  # مللي ثانية
    'chart_points': 100
}

# إعدادات النظام
SYSTEM_CONFIG = {
    'max_log_files': 10,
    'log_level': 'INFO',
    'backup_interval': 24,  # ساعة
    'data_retention_days': 365
}

# إعدادات المضخات
PUMP_CONFIG = {
    'critical_temperature': 85,  # درجة مئوية
    'max_vibration': 7.5,  # م/ث²
    'min_oil_level': 0.2,  # 20%
    'maintenance_interval': 720  # ساعة
}

SENSOR_CONFIG = {
    'default_sampling_rate': 10,  # هرتز
    'calibration_interval': 90,   # يوم
    'sensor_types': [
        'vibration_x', 'vibration_y', 'vibration_z',
        'temperature', 'pressure', 'flow_rate',
        'power_consumption', 'oil_level', 'oil_quality',
        'bearing_temperature'
    ],
    'measurement_units': {
        'vibration': 'm/s²',
        'temperature': '°C',
        'pressure': 'bar',
        'flow_rate': 'm³/h',
        'power_consumption': 'kW',
        'oil_level': '%',
        'oil_quality': '%'
    }
}

APP_CONFIG = {
    'name': 'iPump - نظام التنبؤ بفشل المضخات النفطية',
    'version': '1.0.0',
    'description': 'نظام متكامل للتنبؤ بفشل المضخات النفطية باستخدام الذكاء الاصطناعي',
    'company': 'شركة الهندسة المتطورة',
    'copyright': f'© {datetime.now().year} جميع الحقوق محفوظة'
}