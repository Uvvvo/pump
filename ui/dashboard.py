"""
Main dashboard for the iPump application.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                           QGroupBox, QLabel, QPushButton, QComboBox, 
                           QProgressBar, QFrame, QScrollArea)
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np
from datetime import datetime, timedelta
import random

from database import db_manager
from ai_models import failure_predictor
from config import PUMP_CONFIG

class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_pump_id = 1
        self.sensor_data = []
        self.setup_ui()
        self.load_pump_data()
        
    def setup_ui(self):
        """Initialize the dashboard interface."""
        main_layout = QVBoxLayout(self)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        # Pump selection
        control_layout.addWidget(QLabel("Select pump:"))
        self.pump_selector = QComboBox()
        self.pump_selector.currentIndexChanged.connect(self.on_pump_changed)
        control_layout.addWidget(self.pump_selector)
        
        control_layout.addStretch()
        
        # Control buttons
        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.clicked.connect(self.refresh_data)
        control_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(control_layout)
        
        # Main content area
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QGridLayout(content_widget)
        content_scroll.setWidget(content_widget)
        main_layout.addWidget(content_scroll)
        
        # Configure the grid layout
        self.setup_dashboard_grid()
        
    def setup_dashboard_grid(self):
        """Configure the main dashboard grid."""
        # Row 1: Key performance indicators
        self.setup_kpi_row(0)
        
        # Row 2: Live data charts
        self.setup_live_charts_row(1)
        
        # Row 3: Predictions and recommendations
        self.setup_predictions_row(2)
        
        # Row 4: Alerts and status
        self.setup_alerts_row(3)
    
    def setup_kpi_row(self, row):
        """Configure the key performance indicators."""
        kpis = [
            ("Temperature", "°C", "temperature", 0, 100),
            ("Pressure", "bar", "pressure", 0, 200),
            ("Flow rate", "m³/s", "flow_rate", 0, 150),
            ("Energy consumption", "kWh", "power_consumption", 0, 100)
        ]
        
        for col, (title, unit, key, min_val, max_val) in enumerate(kpis):
            kpi_box = self.create_kpi_widget(title, unit, key, min_val, max_val)
            self.content_layout.addWidget(kpi_box, row, col)
    
    def create_kpi_widget(self, title, unit, data_key, min_val, max_val):
        """Create a KPI widget."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e293b, stop: 1 #0f172a);
                border-radius: 10px;
                border: 1px solid #334155;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #e2e8f0;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel("--")
        value_label.setObjectName(f"kpi_{data_key}")
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet("color: #1e88e5;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Unit
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("color: #94a3b8;")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(unit_label)
        
        # Progress bar
        progress = QProgressBar()
        progress.setObjectName(f"progress_{data_key}")
        progress.setRange(min_val, max_val)
        progress.setTextVisible(False)
        progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 5px;
                background-color: #0f172a;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1e88e5, stop: 1 #0d47a1);
                border-radius: 4px;
            }
        """)
        layout.addWidget(progress)
        
        return frame
    
    def setup_live_charts_row(self, row):
        """Configure the live data charts."""
        # Chart for temperature and pressure
        temp_pressure_chart = self.create_live_chart("Temperature and Pressure", 
                                                   ["Temperature", "Pressure"])
        self.content_layout.addWidget(temp_pressure_chart, row, 0, 1, 2)
        
        # Chart for vibrations
        vibration_chart = self.create_live_chart("Vibrations", 
                                               ["Axis X", "Axis Y", "Axis Z"])
        self.content_layout.addWidget(vibration_chart, row, 2, 1, 2)
    
    def create_live_chart(self, title, legends):
        """Create a live data chart widget."""
        group_box = QGroupBox(title)
        layout = QVBoxLayout(group_box)
        
        # Create the chart widget
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('#0f172a')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.setLabel('left', 'Value')
        plot_widget.setLabel('bottom', 'Time')
        
        # Configure the curves
        curves = []
        colors = ['#1e88e5', '#ff6b6b', '#51cf66']
        for i, legend in enumerate(legends):
            curve = plot_widget.plot(pen=pg.mkPen(color=colors[i], width=2))
            curve.setData([], [])
            curves.append(curve)
        
        # Store references for later use
        if not hasattr(self, 'charts'):
            self.charts = {}
        self.charts[title] = curves
        
        layout.addWidget(plot_widget)
        return group_box
    
    def setup_predictions_row(self, row):
        """Configure the predictions and recommendations area."""
        # Failure prediction
        prediction_box = self.create_prediction_widget()
        self.content_layout.addWidget(prediction_box, row, 0, 1, 2)
        
        # Recommendations
        recommendations_box = self.create_recommendations_widget()
        self.content_layout.addWidget(recommendations_box, row, 2, 1, 2)
    
    def create_prediction_widget(self):
        """Create a failure prediction widget."""
        group_box = QGroupBox("Failure prediction")
        layout = QVBoxLayout(group_box)
        
        # Failure probability
        self.failure_prob_label = QLabel("--")
        self.failure_prob_label.setObjectName("failure_probability")
        prob_font = QFont()
        prob_font.setPointSize(32)
        prob_font.setBold(True)
        self.failure_prob_label.setFont(prob_font)
        self.failure_prob_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.failure_prob_label.setStyleSheet("color: #1e88e5;")
        layout.addWidget(self.failure_prob_label)
        
        # Risk level
        self.risk_level_label = QLabel("Unknown")
        self.risk_level_label.setObjectName("risk_level")
        self.risk_level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.risk_level_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.risk_level_label)
        
        # Predicted failure type
        self.failure_type_label = QLabel("No predictions available")
        self.failure_type_label.setObjectName("failure_type")
        self.failure_type_label.setWordWrap(True)
        self.failure_type_label.setStyleSheet("color: #94a3b8;")
        layout.addWidget(self.failure_type_label)
        
        return group_box
    
    def create_recommendations_widget(self):
        """Create a recommendations widget."""
        group_box = QGroupBox("Recommendations")
        layout = QVBoxLayout(group_box)
        
        self.recommendations_label = QLabel("Loading recommendations...")
        self.recommendations_label.setObjectName("recommendations")
        self.recommendations_label.setWordWrap(True)
        self.recommendations_label.setStyleSheet("""
            QLabel {
                color: #e2e8f0;
                font-size: 12px;
                padding: 10px;
                background-color: #1e293b;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.recommendations_label)
        
        return group_box
    
    def setup_alerts_row(self, row):
        """Configure the alerts and status area."""
        # Pump status
        status_box = self.create_pump_status_widget()
        self.content_layout.addWidget(status_box, row, 0, 1, 2)
        
        # Recent alerts
        alerts_box = self.create_recent_alerts_widget()
        self.content_layout.addWidget(alerts_box, row, 2, 1, 2)
    
    def create_pump_status_widget(self):
        """Create a pump status widget."""
        group_box = QGroupBox("Pump status")
        layout = QVBoxLayout(group_box)
        
        self.pump_status_label = QLabel("--")
        self.pump_status_label.setObjectName("pump_status")
        status_font = QFont()
        status_font.setPointSize(16)
        status_font.setBold(True)
        self.pump_status_label.setFont(status_font)
        self.pump_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pump_status_label)
        
        # Additional information
        info_layout = QGridLayout()
        
        labels = [
            ("Operating hours:", "operating_hours"),
            ("Oil level:", "oil_level"),
            ("Oil quality:", "oil_quality"),
            ("Last maintenance:", "last_maintenance")
        ]
        
        for i, (label_text, key) in enumerate(labels):
            info_layout.addWidget(QLabel(label_text), i, 0)
            value_label = QLabel("--")
            value_label.setObjectName(f"pump_{key}")
            value_label.setStyleSheet("color: #1e88e5;")
            info_layout.addWidget(value_label, i, 1)
        
        layout.addLayout(info_layout)
        return group_box
    
    def create_recent_alerts_widget(self):
        """Create a recent alerts widget."""
        group_box = QGroupBox("Recent alerts")
        layout = QVBoxLayout(group_box)
        
        self.alerts_text = QLabel("No alerts")
        self.alerts_text.setObjectName("recent_alerts")
        self.alerts_text.setWordWrap(True)
        self.alerts_text.setStyleSheet("""
            QLabel {
                color: #e2e8f0;
                font-size: 12px;
                padding: 10px;
                background-color: #1e293b;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.alerts_text)
        
        return group_box
    
    def load_pump_data(self):
        """Load pump data."""
        try:
            pumps = db_manager.get_pumps()
            self.pump_selector.clear()
            
            for _, pump in pumps.iterrows():
                self.pump_selector.addItem(pump['name'], pump['id'])
            
            # Refresh data for the selected pump
            self.update_pump_display()
            
        except Exception as e:
            print(f"Error loading pump data: {e}")
    
    def on_pump_changed(self, index):
        """Handle pump selection changes."""
        if index >= 0:
            self.selected_pump_id = self.pump_selector.itemData(index)
            self.update_pump_display()
    
    def update_pump_display(self):
        """Update the pump data display."""
        try:
            # Simulate sensor data
            sensor_data = self.generate_sensor_data()
            
            # Refresh KPIs
            self.update_kpi_values(sensor_data)
            
            # Update charts
            self.update_live_charts(sensor_data)
            
            # Update predictions
            self.update_predictions(sensor_data)
            
            # Update pump status
            self.update_pump_status(sensor_data)
            
        except Exception as e:
            print(f"Error updating pump display: {e}")
    
    def generate_sensor_data(self):
        """Generate simulated sensor data."""
        return {
            'vibration_x': random.uniform(1.5, 6.0),
            'vibration_y': random.uniform(1.8, 5.8),
            'vibration_z': random.uniform(1.2, 5.5),
            'temperature': random.uniform(60, 90),
            'pressure': random.uniform(120, 180),
            'flow_rate': random.uniform(80, 120),
            'power_consumption': random.uniform(70, 95),
            'bearing_temperature': random.uniform(65, 88),
            'oil_level': random.uniform(0.3, 1.0),
            'oil_quality': random.uniform(0.4, 0.95),
            'operating_hours': random.uniform(500, 4500)
        }
    
    def update_kpi_values(self, sensor_data):
        """Update KPI values."""
        kpi_mapping = {
            'temperature': sensor_data['temperature'],
            'pressure': sensor_data['pressure'],
            'flow_rate': sensor_data['flow_rate'],
            'power_consumption': sensor_data['power_consumption']
        }
        
        for key, value in kpi_mapping.items():
            label = self.findChild(QLabel, f"kpi_{key}")
            progress = self.findChild(QProgressBar, f"progress_{key}")
            
            if label:
                label.setText(f"{value:.1f}")
            if progress:
                progress.setValue(int(value))
    
    def update_live_charts(self, sensor_data):
        """Update live charts."""
        # Update vibration data
        if 'Vibrations' in self.charts:
            time_data = np.linspace(0, 10, 50)
            vib_data = [
                sensor_data['vibration_x'] + np.random.normal(0, 0.2, 50),
                sensor_data['vibration_y'] + np.random.normal(0, 0.2, 50),
                sensor_data['vibration_z'] + np.random.normal(0, 0.2, 50)
            ]
            
            for i, curve in enumerate(self.charts['Vibrations']):
                curve.setData(time_data, vib_data[i])
        
        # Update temperature and pressure data
        if 'Temperature and Pressure' in self.charts:
            time_data = np.linspace(0, 10, 50)
            temp_pressure_data = [
                sensor_data['temperature'] + np.random.normal(0, 1, 50),
                sensor_data['pressure'] + np.random.normal(0, 2, 50)
            ]
            
            for i, curve in enumerate(self.charts['Temperature and Pressure']):
                curve.setData(time_data, temp_pressure_data[i])
    
    def update_predictions(self, sensor_data):
        """Update predictions and recommendations."""
        try:
            # Retrieve prediction from the model
            prediction = failure_predictor.predict_failure(sensor_data)
            
            # Update failure probability
            prob_percent = prediction['failure_probability'] * 100
            self.failure_prob_label.setText(f"{prob_percent:.1f}%")
            
            # Update risk level
            risk_level = prediction['risk_level']
            self.risk_level_label.setText(risk_level)
            
            # Color the risk level
            if risk_level == "Low":
                color = "#51cf66"
            elif risk_level == "Medium":
                color = "#f59f00"
            else:
                color = "#ff6b6b"
            
            self.risk_level_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 16px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 5px;
                    background-color: {color};
                    color: white;
                }}
            """)
            
            # Update failure type
            self.failure_type_label.setText(prediction['predicted_failure_type'])
            
            # Update recommendations
            recommendations_text = "\n".join([f"• {rec}" for rec in prediction['recommendations']])
            self.recommendations_label.setText(recommendations_text)
            
        except Exception as e:
            print(f"Error updating predictions: {e}")
    
    def update_pump_status(self, sensor_data):
        """Update pump status."""
        try:
            # Update overall status
            status = "Operating normally"
            status_color = "#51cf66"
            
            if sensor_data['temperature'] > 80:
                status = "High temperature detected"
                status_color = "#f59f00"
            if sensor_data['oil_level'] < 0.4:
                status = "Low oil level"
                status_color = "#ff6b6b"
            if any(v > 5.0 for v in [sensor_data['vibration_x'], 
                                    sensor_data['vibration_y'], 
                                    sensor_data['vibration_z']]):
                status = "High vibrations"
                status_color = "#ff6b6b"
            
            self.pump_status_label.setText(status)
            self.pump_status_label.setStyleSheet(f"color: {status_color};")
            
            # Update additional information
            info_mapping = {
                'operating_hours': f"{sensor_data['operating_hours']:.0f} hours",
                'oil_level': f"{sensor_data['oil_level']*100:.1f}%",
                'oil_quality': f"{sensor_data['oil_quality']*100:.1f}%",
                'last_maintenance': "2 weeks ago"  # Simulation
            }
            
            for key, value in info_mapping.items():
                label = self.findChild(QLabel, f"pump_{key}")
                if label:
                    label.setText(value)
            
            # Update alerts
            self.update_alerts_display(sensor_data)
            
        except Exception as e:
            print(f"Error updating pump status: {e}")
    
    def update_alerts_display(self, sensor_data):
        """Update the alerts display."""
        alerts = []
        
        if sensor_data['temperature'] > 80:
            alerts.append("Temperature is high")
        if sensor_data['oil_level'] < 0.4:
            alerts.append("Oil level is low")
        if sensor_data['oil_quality'] < 0.6:
            alerts.append("Oil quality degraded")
        if sensor_data['bearing_temperature'] > 85:
            alerts.append("High bearing temperature")
        
        if alerts:
            alerts_text = "\n".join([f"• {alert}" for alert in alerts])
        else:
            alerts_text = "No alerts"
        
        self.alerts_text.setText(alerts_text)
    
    def refresh_data(self):
        """Refresh data manually."""
        self.update_pump_display()