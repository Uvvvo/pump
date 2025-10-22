"""
وحدة إدارة قاعدة البيانات لتطبيق iPump - مع إضافة جداول المضخات والحساسات
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
from PyQt6.QtCore import QSize

from config import DATABASE_CONFIG, BASE_DIR

class DatabaseManager:
    def __init__(self):
        self.db_path = BASE_DIR / "data" / "ipump.db"
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """تهيئة قاعدة البيانات وإنشاء الجداول"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # جدول المضخات
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS pumps (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        location TEXT NOT NULL,
                        type TEXT NOT NULL,
                        installation_date DATE NOT NULL,
                        status TEXT DEFAULT 'operational',
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # جدول الحساسات
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS sensors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pump_id INTEGER NOT NULL,
                        sensor_type TEXT NOT NULL,
                        sensor_id TEXT UNIQUE NOT NULL,
                        model TEXT,
                        manufacturer TEXT,
                        measurement_range TEXT,
                        accuracy TEXT,
                        installation_date DATE,
                        calibration_date DATE,
                        sampling_rate INTEGER DEFAULT 10,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (pump_id) REFERENCES pumps (id) ON DELETE CASCADE,
                        UNIQUE(pump_id, sensor_type)
                    )
                ''')
                
                # جدول قراءات المستشعرات
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS sensor_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pump_id INTEGER NOT NULL,
                        sensor_id INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        vibration_x REAL,
                        vibration_y REAL,
                        vibration_z REAL,
                        temperature REAL,
                        pressure REAL,
                        flow_rate REAL,
                        power_consumption REAL,
                        bearing_temperature REAL,
                        oil_level REAL,
                        oil_quality REAL,
                        operating_hours REAL,
                        FOREIGN KEY (pump_id) REFERENCES pumps (id) ON DELETE CASCADE,
                        FOREIGN KEY (sensor_id) REFERENCES sensors (id) ON DELETE SET NULL
                    )
                ''')
                
                # جدول التنبؤات
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pump_id INTEGER NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        failure_probability REAL,
                        predicted_failure_type TEXT,
                        confidence REAL,
                        risk_level TEXT,
                        recommendations TEXT,
                        FOREIGN KEY (pump_id) REFERENCES pumps (id) ON DELETE CASCADE
                    )
                ''')
                
                # جدول الصيانة
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS maintenance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pump_id INTEGER NOT NULL,
                        scheduled_date DATE NOT NULL,
                        completed_date DATE,
                        maintenance_type TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'scheduled',
                        technician TEXT,
                        cost REAL,
                        parts_used TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (pump_id) REFERENCES pumps (id) ON DELETE CASCADE
                    )
                ''')
                
                # جدول الإنذارات
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pump_id INTEGER NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolved_at TIMESTAMP,
                        resolved_by TEXT,
                        FOREIGN KEY (pump_id) REFERENCES pumps (id) ON DELETE CASCADE
                    )
                ''')
                
                # جدول سجل العمليات
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS operation_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pump_id INTEGER,
                        action_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        user_id TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (pump_id) REFERENCES pumps (id) ON DELETE SET NULL
                    )
                ''')
                
                # إنشاء الفهارس لتحسين الأداء
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sensor_data_pump_id ON sensor_data(pump_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON sensor_data(timestamp)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sensors_pump_id ON sensors(pump_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_predictions_pump_id ON predictions(pump_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_pump_id ON maintenance(pump_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_pump_id ON alerts(pump_id)')
                
                # إدخال بيانات نموذجية للمضخات
                self._insert_sample_data(conn)
                
            self.logger.info("تم تهيئة قاعدة البيانات بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
            raise
    
    def _insert_sample_data(self, conn):
        """إدخال بيانات نموذجية للمضخات والحساسات"""
        try:
            # التحقق من وجود مضخات مسبقاً
            result = conn.execute("SELECT COUNT(*) FROM pumps").fetchone()
            if result[0] == 0:
                sample_pumps = [
                    ('مضخة المصفاة الرئيسية', 'الموقع أ', 'طرد مركزي', '2023-01-15', 'operational', 'المضخة الرئيسية للمصفاة'),
                    ('مضخة النقل رقم 1', 'الموقع ب', 'مكبسية', '2023-02-20', 'operational', 'مضخة نقل رئيسية'),
                    ('مضخة التغذية الرئيسية', 'الموقع ج', 'طرد مركزي', '2023-03-10', 'maintenance', 'تحت الصيانة الدورية'),
                    ('مضخة الخدمة المساعدة', 'الموقع د', 'تغذية', '2023-04-05', 'operational', 'مضخة خدمة مساعدة')
                ]
                
                conn.executemany('''
                    INSERT INTO pumps (name, location, type, installation_date, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', sample_pumps)
                
                self.logger.info("تم إدخال بيانات المضخات النموذجية")
            
            # التحقق من وجود حساسات مسبقاً
            result = conn.execute("SELECT COUNT(*) FROM sensors").fetchone()
            if result[0] == 0:
                sample_sensors = [
                    (1, 'vibration_x', 'VIB_X_001', 'VIB-1000X', 'Siemens', '0-20 m/s²', '±0.5%', '2023-01-15', '2024-01-15', 10),
                    (1, 'vibration_y', 'VIB_Y_001', 'VIB-1000Y', 'Siemens', '0-20 m/s²', '±0.5%', '2023-01-15', '2024-01-15', 10),
                    (1, 'vibration_z', 'VIB_Z_001', 'VIB-1000Z', 'Siemens', '0-20 m/s²', '±0.5%', '2023-01-15', '2024-01-15', 10),
                    (1, 'temperature', 'TEMP_001', 'TEMP-2000', 'ABB', '0-150°C', '±1°C', '2023-01-15', '2024-01-15', 5),
                    (2, 'vibration_x', 'VIB_X_002', 'VIB-1000X', 'Siemens', '0-20 m/s²', '±0.5%', '2023-02-20', '2024-02-20', 10),
                    (2, 'temperature', 'TEMP_002', 'TEMP-2000', 'ABB', '0-150°C', '±1°C', '2023-02-20', '2024-02-20', 5),
                    (3, 'pressure', 'PRESS_003', 'PRESS-3000', 'Emerson', '0-300 bar', '±0.1%', '2023-03-10', '2024-03-10', 2),
                ]
                
                conn.executemany('''
                    INSERT INTO sensors (pump_id, sensor_type, sensor_id, model, manufacturer, 
                                      measurement_range, accuracy, installation_date, calibration_date, sampling_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', sample_sensors)
                
                self.logger.info("تم إدخال بيانات الحساسات النموذجية")
                
        except Exception as e:
            self.logger.error(f"خطأ في إدخال البيانات النموذجية: {e}")
    
    # دوال إدارة المضخات
    def add_pump(self, pump_data: Dict[str, Any]) -> int:
        """إضافة مضخة جديدة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO pumps (name, location, type, installation_date, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    pump_data['name'],
                    pump_data['location'],
                    pump_data['type'],
                    pump_data['installation_date'],
                    pump_data.get('status', 'operational'),
                    pump_data.get('notes', '')
                ))
                
                pump_id = cursor.lastrowid
                
                # تسجيل العملية في السجل
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'ADD_PUMP', ?)
                ''', (pump_id, f'تم إضافة مضخة جديدة: {pump_data["name"]}'))
                
                self.logger.info(f"تم إضافة مضخة جديدة بالمعرف: {pump_id}")
                return pump_id
                
        except sqlite3.IntegrityError:
            self.logger.error(f"خطأ: اسم المضخة '{pump_data['name']}' موجود مسبقاً")
            return -1
        except Exception as e:
            self.logger.error(f"خطأ في إضافة المضخة: {e}")
            return -1
    
    def update_pump(self, pump_id: int, pump_data: Dict[str, Any]) -> bool:
        """تحديث بيانات المضخة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE pumps 
                    SET name = ?, location = ?, type = ?, installation_date = ?, 
                        status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    pump_data['name'],
                    pump_data['location'], 
                    pump_data['type'],
                    pump_data['installation_date'],
                    pump_data.get('status', 'operational'),
                    pump_data.get('notes', ''),
                    pump_id
                ))
                
                # تسجيل العملية في السجل
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'UPDATE_PUMP', ?)
                ''', (pump_id, f'تم تحديث بيانات المضخة: {pump_data["name"]}'))
                
                self.logger.info(f"تم تحديث المضخة بالمعرف: {pump_id}")
                return True
                
        except sqlite3.IntegrityError:
            self.logger.error(f"خطأ: اسم المضخة '{pump_data['name']}' موجود مسبقاً")
            return False
        except Exception as e:
            self.logger.error(f"خطأ في تحديث المضخة: {e}")
            return False
    
    def delete_pump(self, pump_id: int) -> bool:
        """حذف مضخة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # الحصول على اسم المضخة قبل الحذف للتسجيل
                pump_name = conn.execute('SELECT name FROM pumps WHERE id = ?', (pump_id,)).fetchone()
                
                conn.execute('DELETE FROM pumps WHERE id = ?', (pump_id,))
                
                # تسجيل العملية في السجل
                if pump_name:
                    conn.execute('''
                        INSERT INTO operation_logs (action_type, description)
                        VALUES ('DELETE_PUMP', ?)
                    ''', (f'تم حذف المضخة: {pump_name[0]}',))
                
                self.logger.info(f"تم حذف المضخة بالمعرف: {pump_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"خطأ في حذف المضخة: {e}")
            return False
    
    def get_pump(self, pump_id: int) -> pd.DataFrame:
        """الحصول على بيانات مضخة محددة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('SELECT * FROM pumps WHERE id = ?', conn, params=(pump_id,))
        except Exception as e:
            self.logger.error(f"خطأ في جلب بيانات المضخة: {e}")
            return pd.DataFrame()
    
    def get_pumps(self) -> pd.DataFrame:
        """الحصول على قائمة جميع المضخات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT *, 
                    CASE 
                        WHEN status = 'operational' THEN 'تعمل'
                        WHEN status = 'maintenance' THEN 'صيانة' 
                        ELSE 'متوقفة'
                    END as status_text
                    FROM pumps 
                    ORDER BY name
                ''', conn)
        except Exception as e:
            self.logger.error(f"خطأ في جلب بيانات المضخات: {e}")
            return pd.DataFrame()
    
    def get_pumps_with_stats(self) -> pd.DataFrame:
        """الحصول على قائمة المضخات مع إحصائيات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT p.*, 
                    COUNT(DISTINCT s.id) as sensor_count,
                    COUNT(DISTINCT a.id) as active_alerts,
                    (SELECT MAX(timestamp) FROM sensor_data sd WHERE sd.pump_id = p.id) as last_reading
                    FROM pumps p
                    LEFT JOIN sensors s ON p.id = s.pump_id AND s.status = 'active'
                    LEFT JOIN alerts a ON p.id = a.pump_id AND a.resolved = FALSE
                    GROUP BY p.id
                    ORDER BY p.name
                ''', conn)
        except Exception as e:
            self.logger.error(f"خطأ في جلب إحصائيات المضخات: {e}")
            return pd.DataFrame()
    
    # دوال إدارة الحساسات
    def add_sensor(self, sensor_data: Dict[str, Any]) -> int:
        """إضافة حساس جديد"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO sensors (pump_id, sensor_type, sensor_id, model, manufacturer, 
                                      measurement_range, accuracy, installation_date, calibration_date, sampling_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sensor_data['pump_id'],
                    sensor_data['sensor_type'],
                    sensor_data['sensor_id'],
                    sensor_data.get('model', ''),
                    sensor_data.get('manufacturer', ''),
                    sensor_data.get('measurement_range', ''),
                    sensor_data.get('accuracy', ''),
                    sensor_data.get('installation_date', datetime.now().strftime('%Y-%m-%d')),
                    sensor_data.get('calibration_date', datetime.now().strftime('%Y-%m-%d')),
                    sensor_data.get('sampling_rate', 10)
                ))
                
                sensor_id = cursor.lastrowid
                
                # تسجيل العملية في السجل
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'ADD_SENSOR', ?)
                ''', (sensor_data['pump_id'], f'تم إضافة حساس: {sensor_data["sensor_id"]}'))
                
                self.logger.info(f"تم إضافة حساس جديد بالمعرف: {sensor_id}")
                return sensor_id
                
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed: sensors.sensor_id' in str(e):
                self.logger.error(f"خطأ: معرف الحساس '{sensor_data['sensor_id']}' موجود مسبقاً")
            elif 'UNIQUE constraint failed: sensors.pump_id, sensors.sensor_type' in str(e):
                self.logger.error(f"خطأ: نوع الحساس '{sensor_data['sensor_type']}' موجود مسبقاً للمضخة {sensor_data['pump_id']}")
            return -1
        except Exception as e:
            self.logger.error(f"خطأ في إضافة الحساس: {e}")
            return -1
    
    def update_sensor(self, sensor_id: int, sensor_data: Dict[str, Any]) -> bool:
        """تحديث بيانات الحساس"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE sensors 
                    SET sensor_type = ?, model = ?, manufacturer = ?, measurement_range = ?,
                        accuracy = ?, calibration_date = ?, sampling_rate = ?, status = ?
                    WHERE id = ?
                ''', (
                    sensor_data.get('sensor_type'),
                    sensor_data.get('model'),
                    sensor_data.get('manufacturer'),
                    sensor_data.get('measurement_range'),
                    sensor_data.get('accuracy'),
                    sensor_data.get('calibration_date'),
                    sensor_data.get('sampling_rate', 10),
                    sensor_data.get('status', 'active'),
                    sensor_id
                ))
                
                self.logger.info(f"تم تحديث الحساس بالمعرف: {sensor_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"خطأ في تحديث الحساس: {e}")
            return False
    
    def delete_sensor(self, sensor_id: int) -> bool:
        """حذف حساس"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM sensors WHERE id = ?', (sensor_id,))
                self.logger.info(f"تم حذف الحساس بالمعرف: {sensor_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"خطأ في حذف الحساس: {e}")
            return False
    
    def get_sensor(self, sensor_id: int) -> pd.DataFrame:
        """الحصول على بيانات حساس محدد"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT s.*, p.name as pump_name 
                    FROM sensors s 
                    JOIN pumps p ON s.pump_id = p.id 
                    WHERE s.id = ?
                ''', conn, params=(sensor_id,))
        except Exception as e:
            self.logger.error(f"خطأ في جلب بيانات الحساس: {e}")
            return pd.DataFrame()
    
    def get_pump_sensors(self, pump_id: int) -> pd.DataFrame:
        """الحصول على الحساسات المرتبطة بمضخة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT s.*, 
                    CASE 
                        WHEN s.status = 'active' THEN 'نشط'
                        ELSE 'غير نشط'
                    END as status_text
                    FROM sensors s 
                    WHERE s.pump_id = ? 
                    ORDER BY s.sensor_type
                ''', conn, params=(pump_id,))
        except Exception as e:
            self.logger.error(f"خطأ في جلب حساسات المضخة: {e}")
            return pd.DataFrame()
    
    def get_all_sensors(self) -> pd.DataFrame:
        """الحصول على جميع الحساسات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT s.*, p.name as pump_name, p.location
                    FROM sensors s 
                    JOIN pumps p ON s.pump_id = p.id 
                    ORDER BY p.name, s.sensor_type
                ''', conn)
        except Exception as e:
            self.logger.error(f"خطأ في جلب جميع الحساسات: {e}")
            return pd.DataFrame()
    
    def link_sensors_to_pump(self, pump_id: int, sensors_data: List[Dict[str, Any]]) -> bool:
        """ربط مجموعة حساسات بمضخة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for sensor_data in sensors_data:
                    conn.execute('''
                        INSERT OR REPLACE INTO sensors 
                        (pump_id, sensor_type, sensor_id, model, installation_date, calibration_date, sampling_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pump_id,
                        sensor_data['sensor_type'],
                        sensor_data['sensor_id'],
                        sensor_data.get('model', 'Generic'),
                        datetime.now().strftime('%Y-%m-%d'),
                        datetime.now().strftime('%Y-%m-%d'),
                        sensor_data.get('sampling_rate', 10)
                    ))
                
                # تسجيل العملية في السجل
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'LINK_SENSORS', ?)
                ''', (pump_id, f'تم ربط {len(sensors_data)} حساس بالمضخة'))
                
                self.logger.info(f"تم ربط {len(sensors_data)} حساس بالمضخة {pump_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"خطأ في ربط الحساسات: {e}")
            return False
    
    def get_available_sensor_types(self) -> List[str]:
        """الحصول على أنواع الحساسات المتاحة"""
        return [
            'vibration_x', 'vibration_y', 'vibration_z',
            'temperature', 'pressure', 'flow_rate',
            'power_consumption', 'oil_level', 'oil_quality',
            'bearing_temperature'
        ]
    
    # دوال بيانات المستشعرات
    def save_sensor_data(self, pump_id: int, data: Dict[str, float], sensor_id: int = None):
        """حفظ بيانات المستشعرات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO sensor_data 
                    (pump_id, sensor_id, vibration_x, vibration_y, vibration_z, temperature, 
                     pressure, flow_rate, power_consumption, bearing_temperature, 
                     oil_level, oil_quality, operating_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pump_id, 
                    sensor_id,
                    data.get('vibration_x'),
                    data.get('vibration_y'),
                    data.get('vibration_z'),
                    data.get('temperature'),
                    data.get('pressure'),
                    data.get('flow_rate'),
                    data.get('power_consumption'),
                    data.get('bearing_temperature'),
                    data.get('oil_level'),
                    data.get('oil_quality'),
                    data.get('operating_hours')
                ))
                
        except Exception as e:
            self.logger.error(f"خطأ في حفظ بيانات المستشعرات: {e}")
    
    def get_latest_sensor_data(self, pump_id: int) -> pd.DataFrame:
        """الحصول على أحدث بيانات المستشعرات لمضخة محددة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM sensor_data 
                    WHERE pump_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                '''
                return pd.read_sql(query, conn, params=(pump_id,))
        except Exception as e:
            self.logger.error(f"خطأ في جلب أحدث بيانات المستشعرات: {e}")
            return pd.DataFrame()
    
    def get_sensor_data_history(self, pump_id: int, hours: int = 24) -> pd.DataFrame:
        """الحصول على التاريخ الزمني لبيانات المستشعرات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM sensor_data 
                    WHERE pump_id = ? AND timestamp >= datetime('now', ?)
                    ORDER BY timestamp ASC
                '''
                return pd.read_sql(query, conn, params=(pump_id, f'-{hours} hours'))
        except Exception as e:
            self.logger.error(f"خطأ في جلب التاريخ الزمني للبيانات: {e}")
            return pd.DataFrame()
    
    # دوال التنبؤات
    def save_prediction(self, pump_id: int, prediction_data: Dict[str, Any]):
        """حفظ نتائج التنبؤ"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO predictions 
                    (pump_id, failure_probability, predicted_failure_type, 
                     confidence, risk_level, recommendations)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    pump_id, 
                    prediction_data.get('failure_probability', 0),
                    prediction_data.get('predicted_failure_type', ''),
                    prediction_data.get('confidence', 0),
                    prediction_data.get('risk_level', 'low'),
                    json.dumps(prediction_data.get('recommendations', []))
                ))
                
        except Exception as e:
            self.logger.error(f"خطأ في حفظ التنبؤ: {e}")
    
    def get_predictions(self, pump_id: int = None, days: int = 30) -> pd.DataFrame:
        """الحصول على التنبؤات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if pump_id:
                    query = '''
                        SELECT p.*, pump.name as pump_name 
                        FROM predictions p
                        JOIN pumps pump ON p.pump_id = pump.id
                        WHERE p.pump_id = ? AND date(p.timestamp) >= date('now', ?)
                        ORDER BY p.timestamp DESC
                    '''
                    return pd.read_sql(query, conn, params=(pump_id, f'-{days} days'))
                else:
                    query = '''
                        SELECT p.*, pump.name as pump_name 
                        FROM predictions p
                        JOIN pumps pump ON p.pump_id = pump.id
                        WHERE date(p.timestamp) >= date('now', ?)
                        ORDER BY p.timestamp DESC
                    '''
                    return pd.read_sql(query, conn, params=(f'-{days} days',))
        except Exception as e:
            self.logger.error(f"خطأ في جلب التنبؤات: {e}")
            return pd.DataFrame()
    
    # دوال الإنذارات
    def create_alert(self, pump_id: int, alert_type: str, severity: str, message: str):
        """إنشاء إنذار جديد"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO alerts (pump_id, alert_type, severity, message)
                    VALUES (?, ?, ?, ?)
                ''', (pump_id, alert_type, severity, message))
                
                # تسجيل العملية في السجل
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'CREATE_ALERT', ?)
                ''', (pump_id, f'إنذار {severity}: {message}'))
                
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء الإنذار: {e}")
    
    def get_active_alerts(self) -> pd.DataFrame:
        """الحصول على الإنذارات النشطة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT a.*, p.name as pump_name, p.location
                    FROM alerts a 
                    JOIN pumps p ON a.pump_id = p.id 
                    WHERE a.resolved = FALSE 
                    ORDER BY a.timestamp DESC
                ''', conn)
        except Exception as e:
            self.logger.error(f"خطأ في جلب الإنذارات النشطة: {e}")
            return pd.DataFrame()
    
    def resolve_alert(self, alert_id: int, resolved_by: str = "System"):
        """حل الإنذار"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE alerts 
                    SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                    WHERE id = ?
                ''', (resolved_by, alert_id))
                
        except Exception as e:
            self.logger.error(f"خطأ في حل الإنذار: {e}")
    
    # دوال الصيانة
    def schedule_maintenance(self, maintenance_data: Dict[str, Any]) -> int:
        """جدولة صيانة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO maintenance 
                    (pump_id, scheduled_date, maintenance_type, description, technician, cost)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    maintenance_data['pump_id'],
                    maintenance_data['scheduled_date'],
                    maintenance_data['maintenance_type'],
                    maintenance_data.get('description', ''),
                    maintenance_data.get('technician', ''),
                    maintenance_data.get('cost', 0)
                ))
                
                maintenance_id = cursor.lastrowid
                
                # تسجيل العملية في السجل
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'SCHEDULE_MAINTENANCE', ?)
                ''', (maintenance_data['pump_id'], f'تم جدولة صيانة: {maintenance_data["maintenance_type"]}'))
                
                return maintenance_id
                
        except Exception as e:
            self.logger.error(f"خطأ في جدولة الصيانة: {e}")
            return -1
    
    def get_maintenance_schedule(self, pump_id: int = None) -> pd.DataFrame:
        """الحصول على جدول الصيانة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if pump_id:
                    query = '''
                        SELECT m.*, p.name as pump_name 
                        FROM maintenance m
                        JOIN pumps p ON m.pump_id = p.id
                        WHERE m.pump_id = ?
                        ORDER BY m.scheduled_date DESC
                    '''
                    return pd.read_sql(query, conn, params=(pump_id,))
                else:
                    query = '''
                        SELECT m.*, p.name as pump_name 
                        FROM maintenance m
                        JOIN pumps p ON m.pump_id = p.id
                        ORDER BY m.scheduled_date DESC
                    '''
                    return pd.read_sql(query, conn)
        except Exception as e:
            self.logger.error(f"خطأ في جلب جدول الصيانة: {e}")
            return pd.DataFrame()
    
    # دوال السجل والاحصائيات
    def get_operation_logs(self, days: int = 7) -> pd.DataFrame:
        """الحصول على سجل العمليات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT l.*, p.name as pump_name 
                    FROM operation_logs l
                    LEFT JOIN pumps p ON l.pump_id = p.id
                    WHERE date(l.timestamp) >= date('now', ?)
                    ORDER BY l.timestamp DESC
                ''', conn, params=(f'-{days} days',))
        except Exception as e:
            self.logger.error(f"خطأ في جلب سجل العمليات: {e}")
            return pd.DataFrame()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات النظام"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # عدد المضخات
                result = conn.execute("SELECT COUNT(*) FROM pumps").fetchone()
                stats['total_pumps'] = result[0]
                
                # عدد المضخات العاملة
                result = conn.execute("SELECT COUNT(*) FROM pumps WHERE status = 'operational'").fetchone()
                stats['operational_pumps'] = result[0]
                
                # عدد الحساسات النشطة
                result = conn.execute("SELECT COUNT(*) FROM sensors WHERE status = 'active'").fetchone()
                stats['active_sensors'] = result[0]
                
                # عدد الإنذارات النشطة
                result = conn.execute("SELECT COUNT(*) FROM alerts WHERE resolved = FALSE").fetchone()
                stats['active_alerts'] = result[0]
                
                # عدد عمليات الصيانة المجدولة
                result = conn.execute("SELECT COUNT(*) FROM maintenance WHERE status = 'scheduled'").fetchone()
                stats['scheduled_maintenance'] = result[0]
                
                # آخر تحديث للبيانات
                result = conn.execute("SELECT MAX(timestamp) FROM sensor_data").fetchone()
                stats['last_data_update'] = result[0]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"خطأ في جلب إحصائيات النظام: {e}")
            return {}
    
    # أدوات مساعدة للقاعدة البيانات
    def backup_database(self, backup_path: Path) -> bool:
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"تم إنشاء نسخة احتياطية في: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            return False
    
    def optimize_database(self):
        """تحسين أداء قاعدة البيانات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                self.logger.info("تم تحسين قاعدة البيانات")
        except Exception as e:
            self.logger.error(f"خطأ في تحسين قاعدة البيانات: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """تنظيف البيانات القديمة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # حذف بيانات المستشعرات القديمة
                conn.execute('''
                    DELETE FROM sensor_data 
                    WHERE timestamp < datetime('now', ?)
                ''', (f'-{days_to_keep} days',))
                
                # حذف التنبؤات القديمة
                conn.execute('''
                    DELETE FROM predictions 
                    WHERE timestamp < datetime('now', ?)
                ''', (f'-{days_to_keep} days',))
                
                # حذف الإنذارات المحلولة القديمة
                conn.execute('''
                    DELETE FROM alerts 
                    WHERE resolved = TRUE AND resolved_at < datetime('now', ?)
                ''', (f'-{days_to_keep} days',))
                
                # حذف سجل العمليات القديم
                conn.execute('''
                    DELETE FROM operation_logs 
                    WHERE timestamp < datetime('now', ?)
                ''', (f'-{days_to_keep * 2} days',))
                
                self.logger.info(f"تم تنظيف البيانات الأقدم من {days_to_keep} يوم")
                
        except Exception as e:
            self.logger.error(f"خطأ في تنظيف البيانات القديمة: {e}")

# إنشاء نسخة عامة من مدير قاعدة البيانات
db_manager = DatabaseManager()