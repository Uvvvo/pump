"""
Database management module for the iPump application with pump and sensor tables.
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
        """Initialize the database and create tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Pumps table
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
                
                # Sensors table
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
                
                # Sensor readings table
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
                
                # Predictions table
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
                
                # Maintenance table
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
                
                # Alerts table
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
                
                # Operation logs table
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
                
                # Create indexes to improve performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sensor_data_pump_id ON sensor_data(pump_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON sensor_data(timestamp)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sensors_pump_id ON sensors(pump_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_predictions_pump_id ON predictions(pump_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_pump_id ON maintenance(pump_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_pump_id ON alerts(pump_id)')
                
                # Insert sample pump data
                self._insert_sample_data(conn)
                
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
    
    def _insert_sample_data(self, conn):
        """Insert sample pump and sensor data."""
        try:
            # Check if pumps already exist
            result = conn.execute("SELECT COUNT(*) FROM pumps").fetchone()
            if result[0] == 0:
                sample_pumps = [
                    ('Refinery Main Pump', 'Site A', 'Centrifugal', '2023-01-15', 'operational', 'Primary refinery pump'),
                    ('Transfer Pump 1', 'Site B', 'Reciprocating', '2023-02-20', 'operational', 'Primary transfer pump'),
                    ('Main Feed Pump', 'Site C', 'Centrifugal', '2023-03-10', 'maintenance', 'Under routine maintenance'),
                    ('Auxiliary Service Pump', 'Site D', 'Feed', '2023-04-05', 'operational', 'Auxiliary service pump')
                ]
                
                conn.executemany('''
                    INSERT INTO pumps (name, location, type, installation_date, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', sample_pumps)
                
                self.logger.info("Inserted sample pump data")
            
            # Check if sensors already exist
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
                
                self.logger.info("Inserted sample sensor data")
                
        except Exception as e:
            self.logger.error(f"Sample data insertion error: {e}")
    
    # Pump management methods
    def add_pump(self, pump_data: Dict[str, Any]) -> int:
        """Add a new pump."""
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
                
                # Record the action in the log
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'ADD_PUMP', ?)
                ''', (pump_id, f'Added new pump: {pump_data["name"]}'))
                
                self.logger.info(f"Added new pump with id: {pump_id}")
                return pump_id
                
        except sqlite3.IntegrityError:
            self.logger.error(f"Error: Pump name '{pump_data['name']}' already exists")
            return -1
        except Exception as e:
            self.logger.error(f"Pump insertion error: {e}")
            return -1
    
    def update_pump(self, pump_id: int, pump_data: Dict[str, Any]) -> bool:
        """Update pump information."""
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
                
                # Record the action in the log
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'UPDATE_PUMP', ?)
                ''', (pump_id, f'Updated pump: {pump_data["name"]}'))
                
                self.logger.info(f"Updated pump with id: {pump_id}")
                return True
                
        except sqlite3.IntegrityError:
            self.logger.error(f"Error: Pump name '{pump_data['name']}' already exists")
            return False
        except Exception as e:
            self.logger.error(f"Pump update error: {e}")
            return False
    
    def delete_pump(self, pump_id: int) -> bool:
        """Delete a pump."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Retrieve the pump name before deletion for logging
                pump_name = conn.execute('SELECT name FROM pumps WHERE id = ?', (pump_id,)).fetchone()
                
                conn.execute('DELETE FROM pumps WHERE id = ?', (pump_id,))
                
                # Record the action in the log
                if pump_name:
                    conn.execute('''
                        INSERT INTO operation_logs (action_type, description)
                        VALUES ('DELETE_PUMP', ?)
                    ''', (f'Deleted pump: {pump_name[0]}',))
                
                self.logger.info(f"Deleted pump with id: {pump_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Pump deletion error: {e}")
            return False
    
    def get_pump(self, pump_id: int) -> pd.DataFrame:
        """Fetch data for a specific pump."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('SELECT * FROM pumps WHERE id = ?', conn, params=(pump_id,))
        except Exception as e:
            self.logger.error(f"Pump retrieval error: {e}")
            return pd.DataFrame()
    
    def get_pumps(self) -> pd.DataFrame:
        """Retrieve all pumps."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT *, 
                    CASE 
                        WHEN status = 'operational' THEN 'Operational'
                        WHEN status = 'maintenance' THEN 'Maintenance' 
                        ELSE 'Stopped'
                    END as status_text
                    FROM pumps 
                    ORDER BY name
                ''', conn)
        except Exception as e:
            self.logger.error(f"Pump list retrieval error: {e}")
            return pd.DataFrame()
    
    def get_pumps_with_stats(self) -> pd.DataFrame:
        """Retrieve pumps with statistics."""
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
            self.logger.error(f"Pump statistics retrieval error: {e}")
            return pd.DataFrame()
    
    # Sensor management methods
    def add_sensor(self, sensor_data: Dict[str, Any]) -> int:
        """Add a new sensor."""
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
                
                # Record the action in the log
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'ADD_SENSOR', ?)
                ''', (sensor_data['pump_id'], f'Added sensor: {sensor_data["sensor_id"]}'))
                
                self.logger.info(f"Added new sensor with id: {sensor_id}")
                return sensor_id
                
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed: sensors.sensor_id' in str(e):
                self.logger.error(f"Error: Sensor identifier '{sensor_data['sensor_id']}' already exists")
            elif 'UNIQUE constraint failed: sensors.pump_id, sensors.sensor_type' in str(e):
                self.logger.error(f"Error: Sensor type '{sensor_data['sensor_type']}' already exists for pump {sensor_data['pump_id']}")
            return -1
        except Exception as e:
            self.logger.error(f"Sensor insertion error: {e}")
            return -1
    
    def update_sensor(self, sensor_id: int, sensor_data: Dict[str, Any]) -> bool:
        """Update sensor information."""
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
                
                self.logger.info(f"Updated sensor with id: {sensor_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Sensor update error: {e}")
            return False
    
    def delete_sensor(self, sensor_id: int) -> bool:
        """Delete a sensor."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM sensors WHERE id = ?', (sensor_id,))
                self.logger.info(f"Deleted sensor with id: {sensor_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Sensor deletion error: {e}")
            return False
    
    def get_sensor(self, sensor_id: int) -> pd.DataFrame:
        """Fetch data for a specific sensor."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT s.*, p.name as pump_name 
                    FROM sensors s 
                    JOIN pumps p ON s.pump_id = p.id 
                    WHERE s.id = ?
                ''', conn, params=(sensor_id,))
        except Exception as e:
            self.logger.error(f"Sensor retrieval error: {e}")
            return pd.DataFrame()
    
    def get_pump_sensors(self, pump_id: int) -> pd.DataFrame:
        """Retrieve sensors linked to a pump."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT s.*, 
                    CASE 
                        WHEN s.status = 'active' THEN 'Active'
                        ELSE 'Inactive'
                    END as status_text
                    FROM sensors s 
                    WHERE s.pump_id = ? 
                    ORDER BY s.sensor_type
                ''', conn, params=(pump_id,))
        except Exception as e:
            self.logger.error(f"Pump sensors retrieval error: {e}")
            return pd.DataFrame()
    
    def get_all_sensors(self) -> pd.DataFrame:
        """Retrieve all sensors."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql('''
                    SELECT s.*, p.name as pump_name, p.location
                    FROM sensors s 
                    JOIN pumps p ON s.pump_id = p.id 
                    ORDER BY p.name, s.sensor_type
                ''', conn)
        except Exception as e:
            self.logger.error(f"All sensors retrieval error: {e}")
            return pd.DataFrame()
    
    def link_sensors_to_pump(self, pump_id: int, sensors_data: List[Dict[str, Any]]) -> bool:
        """Link multiple sensors to a pump."""
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
                
                # Record the action in the log
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'LINK_SENSORS', ?)
                ''', (pump_id, f'Linked {len(sensors_data)} sensors to the pump'))
                
                self.logger.info(f"Linked {len(sensors_data)} sensors to pump {pump_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Sensor linking error: {e}")
            return False
    
    def get_available_sensor_types(self) -> List[str]:
        """Retrieve available sensor types."""
        return [
            'vibration_x', 'vibration_y', 'vibration_z',
            'temperature', 'pressure', 'flow_rate',
            'power_consumption', 'oil_level', 'oil_quality',
            'bearing_temperature'
        ]
    
    # Sensor data methods
    def save_sensor_data(self, pump_id: int, data: Dict[str, float], sensor_id: int = None):
        """Save sensor data."""
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
            self.logger.error(f"Sensor data save error: {e}")
    
    def get_latest_sensor_data(self, pump_id: int) -> pd.DataFrame:
        """Fetch the latest sensor data for a pump."""
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
            self.logger.error(f"Latest sensor data retrieval error: {e}")
            return pd.DataFrame()
    
    def get_sensor_data_history(self, pump_id: int, hours: int = 24) -> pd.DataFrame:
        """Retrieve sensor data history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM sensor_data 
                    WHERE pump_id = ? AND timestamp >= datetime('now', ?)
                    ORDER BY timestamp ASC
                '''
                return pd.read_sql(query, conn, params=(pump_id, f'-{hours} hours'))
        except Exception as e:
            self.logger.error(f"Sensor data history retrieval error: {e}")
            return pd.DataFrame()
    
    # Prediction methods
    def save_prediction(self, pump_id: int, prediction_data: Dict[str, Any]):
        """Save prediction results."""
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
            self.logger.error(f"Prediction save error: {e}")
    
    def get_predictions(self, pump_id: int = None, days: int = 30) -> pd.DataFrame:
        """Retrieve predictions."""
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
            self.logger.error(f"Prediction retrieval error: {e}")
            return pd.DataFrame()
    
    # Alert methods
    def create_alert(self, pump_id: int, alert_type: str, severity: str, message: str):
        """Create a new alert."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO alerts (pump_id, alert_type, severity, message)
                    VALUES (?, ?, ?, ?)
                ''', (pump_id, alert_type, severity, message))
                
                # Record the action in the log
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'CREATE_ALERT', ?)
                ''', (pump_id, f'Alert {severity}: {message}'))
                
        except Exception as e:
            self.logger.error(f"Alert creation error: {e}")
    
    def get_active_alerts(self) -> pd.DataFrame:
        """Retrieve active alerts."""
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
            self.logger.error(f"Active alerts retrieval error: {e}")
            return pd.DataFrame()
    
    def resolve_alert(self, alert_id: int, resolved_by: str = "System"):
        """Resolve an alert."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE alerts 
                    SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                    WHERE id = ?
                ''', (resolved_by, alert_id))
                
        except Exception as e:
            self.logger.error(f"Alert resolution error: {e}")
    
    # Maintenance methods
    def schedule_maintenance(self, maintenance_data: Dict[str, Any]) -> int:
        """Schedule maintenance."""
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
                
                # Record the action in the log
                conn.execute('''
                    INSERT INTO operation_logs (pump_id, action_type, description)
                    VALUES (?, 'SCHEDULE_MAINTENANCE', ?)
                ''', (maintenance_data['pump_id'], f'Scheduled maintenance: {maintenance_data["maintenance_type"]}'))
                
                return maintenance_id
                
        except Exception as e:
            self.logger.error(f"Maintenance scheduling error: {e}")
            return -1
    
    def get_maintenance_schedule(self, pump_id: int = None) -> pd.DataFrame:
        """Retrieve the maintenance schedule."""
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
            self.logger.error(f"Maintenance schedule retrieval error: {e}")
            return pd.DataFrame()
    
    # Log and statistics methods
    def get_operation_logs(self, days: int = 7) -> pd.DataFrame:
        """Retrieve the operation log."""
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
            self.logger.error(f"Operation log retrieval error: {e}")
            return pd.DataFrame()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Retrieve system statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Total pumps
                result = conn.execute("SELECT COUNT(*) FROM pumps").fetchone()
                stats['total_pumps'] = result[0]
                
                # Operational pumps
                result = conn.execute("SELECT COUNT(*) FROM pumps WHERE status = 'operational'").fetchone()
                stats['operational_pumps'] = result[0]
                
                # Active sensors
                result = conn.execute("SELECT COUNT(*) FROM sensors WHERE status = 'active'").fetchone()
                stats['active_sensors'] = result[0]
                
                # Active alerts
                result = conn.execute("SELECT COUNT(*) FROM alerts WHERE resolved = FALSE").fetchone()
                stats['active_alerts'] = result[0]
                
                # Scheduled maintenance tasks
                result = conn.execute("SELECT COUNT(*) FROM maintenance WHERE status = 'scheduled'").fetchone()
                stats['scheduled_maintenance'] = result[0]
                
                # Last data update
                result = conn.execute("SELECT MAX(timestamp) FROM sensor_data").fetchone()
                stats['last_data_update'] = result[0]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"System statistics retrieval error: {e}")
            return {}
    
    # Database utilities
    def backup_database(self, backup_path: Path) -> bool:
        """Create a database backup."""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Created backup at: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Database backup error: {e}")
            return False
    
    def optimize_database(self):
        """Optimize database performance."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                self.logger.info("Database optimized")
        except Exception as e:
            self.logger.error(f"Database optimization error: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove old sensor data
                conn.execute('''
                    DELETE FROM sensor_data 
                    WHERE timestamp < datetime('now', ?)
                ''', (f'-{days_to_keep} days',))
                
                # Remove old predictions
                conn.execute('''
                    DELETE FROM predictions 
                    WHERE timestamp < datetime('now', ?)
                ''', (f'-{days_to_keep} days',))
                
                # Remove old resolved alerts
                conn.execute('''
                    DELETE FROM alerts 
                    WHERE resolved = TRUE AND resolved_at < datetime('now', ?)
                ''', (f'-{days_to_keep} days',))
                
                # Remove old operation logs
                conn.execute('''
                    DELETE FROM operation_logs 
                    WHERE timestamp < datetime('now', ?)
                ''', (f'-{days_to_keep * 2} days',))
                
                self.logger.info(f"Removed data older than {days_to_keep} days")
                
        except Exception as e:
            self.logger.error(f"Old data cleanup error: {e}")

# Expose a shared database manager instance
db_manager = DatabaseManager()