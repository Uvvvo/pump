"""
الدوال المساعدة لتطبيق iPump
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging
from pathlib import Path

def format_timestamp(timestamp: datetime) -> str:
    """تنسيق التاريخ والوقت"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def calculate_trend(current: float, previous: float) -> str:
    """حساب الاتجاه"""
    if previous == 0:
        return "ثابت"
    
    change = ((current - previous) / previous) * 100
    
    if change > 5:
        return "↑ مرتفع"
    elif change < -5:
        return "↓ منخفض"
    else:
        return "→ ثابت"

def safe_divide(numerator: float, denominator: float) -> float:
    """قسمة آمنة (تجنب القسمة على صفر)"""
    return numerator / denominator if denominator != 0 else 0

def generate_sample_sensor_data(pump_id: int) -> Dict[str, float]:
    """توليد بيانات مستشعرات عشوائية"""
    np.random.seed(pump_id)
    
    return {
        'vibration_x': np.random.normal(2.5, 0.8),
        'vibration_y': np.random.normal(2.8, 0.9),
        'vibration_z': np.random.normal(2.2, 0.7),
        'temperature': np.random.normal(70, 10),
        'pressure': np.random.normal(150, 20),
        'flow_rate': np.random.normal(100, 15),
        'power_consumption': np.random.normal(80, 12),
        'bearing_temperature': np.random.normal(72, 8),
        'oil_level': np.random.uniform(0.6, 1.0),
        'oil_quality': np.random.uniform(0.7, 0.95),
        'operating_hours': np.random.uniform(1000, 4000)
    }

def validate_sensor_data(data: Dict[str, float]) -> bool:
    """التحقق من صحة بيانات المستشعرات"""
    required_fields = [
        'vibration_x', 'vibration_y', 'vibration_z',
        'temperature', 'pressure', 'flow_rate',
        'power_consumption', 'oil_level'
    ]
    
    # التحقق من وجود الحقول المطلوبة
    if not all(field in data for field in required_fields):
        return False
    
    # التحقق من نطاقات القيم
    if not (0 <= data.get('vibration_x', 0) <= 20):
        return False
    if not (0 <= data.get('temperature', 0) <= 150):
        return False
    if not (0 <= data.get('pressure', 0) <= 300):
        return False
    if not (0 <= data.get('oil_level', 0) <= 1):
        return False
    
    return True

def calculate_efficiency(flow_rate: float, power_consumption: float) -> float:
    """حساب كفاءة المضخة"""
    if power_consumption == 0:
        return 0
    
    # معادلة مبسطة لحساب الكفاءة
    theoretical_power = flow_rate * 2.5  # ثابت افتراضي
    efficiency = (theoretical_power / power_consumption) * 100
    
    return min(max(efficiency, 0), 100)  # التأكد من أن الكفاءة بين 0 و 100

def format_currency(amount: float) -> str:
    """تنسيق العملة"""
    return f"{amount:,.2f} ريال"

def get_time_ago(timestamp: datetime) -> str:
    """الحصول على الوقت المنقضي بصيغة مقروءة"""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"قبل {diff.days} يوم"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"قبل {hours} ساعة"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"قبل {minutes} دقيقة"
    else:
        return "الآن"

def create_backup(file_path: Path) -> bool:
    """إنشاء نسخة احتياطية للملف"""
    try:
        if not file_path.exists():
            return False
        
        backup_path = file_path.parent / f"{file_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M')}{file_path.suffix}"
        
        import shutil
        shutil.copy2(file_path, backup_path)
        
        return backup_path.exists()
    except Exception as e:
        logging.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
        return False

def load_config(config_path: Path) -> Dict[str, Any]:
    """تحميل ملف التكوين"""
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"خطأ في تحميل التكوين: {e}")
        return {}

def save_config(config_path: Path, config: Dict[str, Any]):
    """حفظ ملف التكوين"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"خطأ في حفظ التكوين: {e}")

def format_duration(hours: float) -> str:
    """تنسيق المدة الزمنية"""
    if hours < 1:
        minutes = hours * 60
        return f"{minutes:.0f} دقيقة"
    elif hours < 24:
        return f"{hours:.1f} ساعة"
    else:
        days = hours / 24
        return f"{days:.1f} يوم"

def calculate_remaining_life(operating_hours: float, avg_failure_hours: float = 10000) -> float:
    """حساب العمر المتبقي للمضخة"""
    if operating_hours >= avg_failure_hours:
        return 0
    
    remaining_life = ((avg_failure_hours - operating_hours) / avg_failure_hours) * 100
    return max(0, min(remaining_life, 100))