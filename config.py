"""
iPump Application Settings
"""

import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import QSize

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# Create necessary directories
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# Database Settings
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ipump_db',
    'user': 'ipump_user',
    'password': 'ipump_password'
}

# AI Models Settings
AI_MODELS_CONFIG = {
    'failure_prediction': {
        'model_path': MODELS_DIR / 'failure_model.pkl',
        'features': [
            'vibration_x', 'vibration_y', 'vibration_z',
            'temperature', 'pressure', 'flow_rate',
            'power_consumption', 'operating_hours',
            'bearing_temperature', 'oil_level', 'oil_quality'
        ],
        'threshold': 0.85,
        # Path to the real training data file (CSV format for example)
        'training_data_file': DATA_DIR / 'training_data.csv'
    },
    'anomaly_detection': {
        'model_path': MODELS_DIR / 'anomaly_model.pkl',
        'sensitivity': 0.9
    }
}

# UI Settings
UI_CONFIG = {
    'theme': 'dark',
    'language': 'en',  # Changed default language to English
    'refresh_interval': 5000,  # milliseconds
    'chart_points': 100,
    # Window size settings for a real application
    'window': {
        'default_size': (1200, 800),   # width, height
        'presets': {
            'small': (800, 600),
            'medium': (1024, 768),
            'large': (1366, 900),
            'default': (1200, 800)
        },
        'min_size': (640, 480),
        'max_size': (3840, 2160)
    }
}

# System Settings
SYSTEM_CONFIG = {
    'max_log_files': 10,
    'log_level': 'INFO',
    'backup_interval': 24,  # hours
    'data_retention_days': 365
}

# Pump Settings
PUMP_CONFIG = {
    'critical_temperature': 85,  # Celsius
    'max_vibration': 7.5,  # m/s^2
    'min_oil_level': 0.2,  # 20%
    'maintenance_interval': 720  # hours
}

SENSOR_CONFIG = {
    'default_sampling_rate': 10,  # Hz
    'calibration_interval': 90,   # days
    'sensor_types': [
        'vibration_x', 'vibration_y', 'vibration_z',
        'temperature', 'pressure', 'flow_rate',
        'power_consumption', 'oil_level', 'oil_quality',
        'bearing_temperature'
    ],
    'measurement_units': {
        'vibration': 'm/s^2',
        'temperature': 'C',
        'pressure': 'bar',
        'flow_rate': 'm3/h',
        'power_consumption': 'kW',
        'oil_level': '%',
        'oil_quality': '%'
    }
}

APP_CONFIG = {
    'name': 'iPump - Intelligent Pump Failure Prediction System',
    'version': '1.0.0',
    'description': 'An integrated system for predicting pump failure using AI.',
    'developer': 'Hussein Abdullah',
    'phone': '07813563139',
    'location': 'Dhi Qar, Iraq',
    'email': 'ah343238@gmail.com',
    'company': 'Hussein Abdullah',
    'copyright': f'Copyright {datetime.now().year} Hussein Abdullah'
}