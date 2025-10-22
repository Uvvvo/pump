"""
نظام التسجيل لتطبيق iPump
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config import LOGS_DIR

def setup_logger(name: str = "iPump") -> logging.Logger:
    """إعداد وتكوين نظام التسجيل"""
    
    # إنشاء المسجل
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # منع التكرار إذا كان المسجل مُعداً مسبقاً
    if logger.handlers:
        return logger
    
    # تنسيق الرسائل
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # معالج وحدة التحكم
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # معالج الملفات
    log_file = LOGS_DIR / f"ipump_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "iPump") -> logging.Logger:
    """الحصول على مسجل مكون مسبقاً"""
    return logging.getLogger(name)