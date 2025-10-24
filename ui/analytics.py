"""
Advanced analytics module for the iPump application
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QGroupBox, QLabel, QComboBox, QPushButton,
                           QDateEdit, QTableWidget, QTableWidgetItem,
                           QHeaderView, QTabWidget, QTextEdit, QProgressBar)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QDate
import pyqtgraph as pg
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from database import db_manager
from ai_models import failure_predictor, anomaly_detector
from config import PUMP_CONFIG

class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_pump_id = 1
        self.historical_data = pd.DataFrame()
        self.setup_ui()
        self.load_initial_data()
        
    def setup_ui(self):
        """Initialize analytics interface."""
        main_layout = QVBoxLayout(self)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Pump:"))
        self.pump_selector = QComboBox()
        self.pump_selector.currentIndexChanged.connect(self.on_pump_changed)
        control_layout.addWidget(self.pump_selector)
        
        control_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        control_layout.addWidget(self.date_from)
        
        control_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        control_layout.addWidget(self.date_to)
        
        self.load_btn = QPushButton("Load data")
        self.load_btn.clicked.connect(self.load_historical_data)
        control_layout.addWidget(self.load_btn)
        
        self.export_btn = QPushButton("Export report")
        self.export_btn.clicked.connect(self.export_report)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Analytics tabs
        self.analytics_tabs = QTabWidget()
        
        # Time analysis tab
        self.time_analysis_tab = self.create_time_analysis_tab()
        self.analytics_tabs.addTab(self.time_analysis_tab, "Time analysis")
        
        # Statistical analysis tab
        self.stats_analysis_tab = self.create_stats_analysis_tab()
        self.analytics_tabs.addTab(self.stats_analysis_tab, "Statistical analysis")
        
        # Pattern analysis tab
        self.pattern_analysis_tab = self.create_pattern_analysis_tab()
        self.analytics_tabs.addTab(self.pattern_analysis_tab, "Pattern analysis")
        
        # Failure analysis tab
        self.failure_analysis_tab = self.create_failure_analysis_tab()
        self.analytics_tabs.addTab(self.failure_analysis_tab, "Failure analysis")
        
        main_layout.addWidget(self.analytics_tabs)
        
    def create_time_analysis_tab(self):
        """Create time analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Multi-axis chart
        self.time_plot_widget = pg.PlotWidget()
        self.time_plot_widget.setBackground('#0f172a')
        self.time_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.time_plot_widget.setLabel('left', 'Values')
        self.time_plot_widget.setLabel('bottom', 'Time')
        self.time_plot_widget.addLegend()
        
        layout.addWidget(self.time_plot_widget)
        
        # Plot controls
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Variables:"))
        self.variables_selector = QComboBox()
        self.variables_selector.addItems([
            "All variables",
            "Temperature and pressure",
            "Vibrations",
            "Overall performance"
        ])
        self.variables_selector.currentTextChanged.connect(self.update_time_plot)
        control_layout.addWidget(self.variables_selector)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        return widget
    
    def create_stats_analysis_tab(self):
        """Create statistical analysis tab."""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Descriptive statistics
        stats_group = QGroupBox("Descriptive statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_text)
        layout.addWidget(stats_group, 0, 0, 1, 2)
        
        # Correlation chart
        correlation_group = QGroupBox("Correlation matrix")
        correlation_layout = QVBoxLayout(correlation_group)
        self.correlation_plot = pg.PlotWidget()
        self.correlation_plot.setBackground('#0f172a')
        correlation_layout.addWidget(self.correlation_plot)
        layout.addWidget(correlation_group, 1, 0, 1, 2)
        
        # Data distribution chart
        distribution_group = QGroupBox("Data distribution")
        distribution_layout = QVBoxLayout(distribution_group)
        self.distribution_plot = pg.PlotWidget()
        self.distribution_plot.setBackground('#0f172a')
        distribution_layout.addWidget(self.distribution_plot)
        layout.addWidget(distribution_group, 0, 2, 2, 1)
        
        return widget
    
    def create_pattern_analysis_tab(self):
        """Create pattern analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Anomaly detection
        anomaly_group = QGroupBox("Anomaly and pattern detection")
        anomaly_layout = QVBoxLayout(anomaly_group)
        
        self.anomaly_plot = pg.PlotWidget()
        self.anomaly_plot.setBackground('#0f172a')
        self.anomaly_plot.showGrid(x=True, y=True, alpha=0.3)
        anomaly_layout.addWidget(self.anomaly_plot)
        
        # Anomaly detection results
        self.anomaly_results = QTextEdit()
        self.anomaly_results.setReadOnly(True)
        self.anomaly_results.setMaximumHeight(150)
        anomaly_layout.addWidget(self.anomaly_results)
        
        layout.addWidget(anomaly_group)
        
        return widget
    
    def create_failure_analysis_tab(self):
        """Create failure analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Failure trend analysis
        trend_group = QGroupBox("Failure trend analysis")
        trend_layout = QVBoxLayout(trend_group)
        
        self.failure_trend_plot = pg.PlotWidget()
        self.failure_trend_plot.setBackground('#0f172a')
        self.failure_trend_plot.showGrid(x=True, y=True, alpha=0.3)
        self.failure_trend_plot.setLabel('left', 'Failure probability')
        self.failure_trend_plot.setLabel('bottom', 'Time')
        trend_layout.addWidget(self.failure_trend_plot)
        
        layout.addWidget(trend_group)
        
        # Risk factors
        risk_group = QGroupBox("Key risk factors")
        risk_layout = QVBoxLayout(risk_group)
        
        self.risk_factors_text = QTextEdit()
        self.risk_factors_text.setReadOnly(True)
        risk_layout.addWidget(self.risk_factors_text)
        
        layout.addWidget(risk_group)
        
        return widget
    
    def load_initial_data(self):
        """Load initial data."""
        pumps = db_manager.get_pumps()
        self.pump_selector.clear()
        
        for _, pump in pumps.iterrows():
            self.pump_selector.addItem(pump['name'], pump['id'])
        
        self.load_historical_data()
    
    def on_pump_changed(self, index):
        """Handle pump selection change."""
        if index >= 0:
            self.selected_pump_id = self.pump_selector.itemData(index)
            self.load_historical_data()
    
    def load_historical_data(self):
        """Load historical data."""
        try:
            # In the real application, data would come from the database
            # Simulate data in this demo
            self.generate_sample_historical_data()
            
            # Update all charts
            self.update_time_plot()
            self.update_stats_analysis()
            self.update_pattern_analysis()
            self.update_failure_analysis()
            
        except Exception as e:
            print(f"Error loading historical data: {e}")
    
    def generate_sample_historical_data(self):
        """Generate sample historical data."""
        dates = pd.date_range(
            start=self.date_from.date().toPyDate(),
            end=self.date_to.date().toPyDate(),
            freq='H'
        )
        
        np.random.seed(42)
        n_points = len(dates)
        
        self.historical_data = pd.DataFrame({
            'timestamp': dates,
            'vibration_x': np.random.normal(2.5, 1.0, n_points) + 
                          np.sin(np.arange(n_points) * 0.1) * 0.5,
            'vibration_y': np.random.normal(2.8, 1.2, n_points) + 
                          np.sin(np.arange(n_points) * 0.1) * 0.6,
            'vibration_z': np.random.normal(2.2, 0.8, n_points) + 
                          np.sin(np.arange(n_points) * 0.1) * 0.4,
            'temperature': np.random.normal(70, 8, n_points) + 
                          np.arange(n_points) * 0.01,
            'pressure': np.random.normal(150, 15, n_points),
            'flow_rate': np.random.normal(100, 12, n_points),
            'power_consumption': np.random.normal(80, 10, n_points),
            'oil_level': np.random.uniform(0.6, 1.0, n_points) - 
                        np.arange(n_points) * 0.0001,
            'oil_quality': np.random.uniform(0.7, 1.0, n_points) - 
                          np.arange(n_points) * 0.00005
        })
        
        # Inject a few anomalies
        n_anomalies = n_points // 50
        anomaly_indices = np.random.choice(n_points, n_anomalies, replace=False)
        
        for idx in anomaly_indices:
            if np.random.random() > 0.5:
                self.historical_data.loc[idx, 'temperature'] += np.random.normal(20, 5)
                self.historical_data.loc[idx, 'vibration_x'] += np.random.normal(3, 1)
    
    def update_time_plot(self):
        """Update the time-series plot."""
        if self.historical_data.empty:
            return
        
        self.time_plot_widget.clear()
        
        selected_vars = self.variables_selector.currentText()
        
        if selected_vars == "All variables" or selected_vars == "Temperature and pressure":
            # Plot temperature and pressure
            temp_curve = self.time_plot_widget.plot(
                self.historical_data['timestamp'], 
                self.historical_data['temperature'],
                pen=pg.mkPen(color='#ff6b6b', width=2),
                name='Temperature'
            )
            
            pressure_curve = self.time_plot_widget.plot(
                self.historical_data['timestamp'], 
                self.historical_data['pressure'],
                pen=pg.mkPen(color='#1e88e5', width=2),
                name='Pressure'
            )
        
        if selected_vars == "All variables" or selected_vars == "Vibrations":
            # Plot vibrations
            vib_x_curve = self.time_plot_widget.plot(
                self.historical_data['timestamp'], 
                self.historical_data['vibration_x'],
                pen=pg.mkPen(color='#51cf66', width=2),
                name='Vibration X'
            )
            
            vib_y_curve = self.time_plot_widget.plot(
                self.historical_data['timestamp'], 
                self.historical_data['vibration_y'],
                pen=pg.mkPen(color='#f59f00', width=2),
                name='Vibration Y'
            )
    
    def update_stats_analysis(self):
        """Update statistical analysis."""
        if self.historical_data.empty:
            return
        
        # Descriptive statistics
        numeric_cols = self.historical_data.select_dtypes(include=[np.number]).columns
        stats = self.historical_data[numeric_cols].describe()
        
        stats_text = "Descriptive statistics:\n\n"
        for col in stats.columns:
            stats_text += f"{col}:\n"
            stats_text += f"  Mean: {stats[col]['mean']:.2f}\n"
            stats_text += f"  Std dev: {stats[col]['std']:.2f}\n"
            stats_text += f"  Min: {stats[col]['min']:.2f}\n"
            stats_text += f"  Max: {stats[col]['max']:.2f}\n\n"
        
        self.stats_text.setText(stats_text)
        
        # Correlation matrix
        self.update_correlation_plot()
        
        # Data distribution chart
        self.update_distribution_plot()
    
    def update_correlation_plot(self):
        """Update correlation heatmap."""
        if self.historical_data.empty:
            return
        
        numeric_data = self.historical_data.select_dtypes(include=[np.number])
        correlation_matrix = numeric_data.corr()
        
        self.correlation_plot.clear()
        
        # Create correlation heatmap
        img = pg.ImageItem(correlation_matrix.values)
        self.correlation_plot.addItem(img)
        
        # Configure axes
        ticks = [(i, col) for i, col in enumerate(correlation_matrix.columns)]
        self.correlation_plot.getAxis('left').setTicks([ticks])
        self.correlation_plot.getAxis('bottom').setTicks([ticks])
    
    def update_distribution_plot(self):
        """Update distribution plot."""
        if self.historical_data.empty:
            return
        
        self.distribution_plot.clear()
        
        # Temperature distribution
        temperature_data = self.historical_data['temperature'].dropna()
        y, x = np.histogram(temperature_data, bins=30)
        
        self.distribution_plot.plot(x, y, stepMode=True, fillLevel=0, 
                                  brush=(30, 144, 255, 150))
        self.distribution_plot.setLabel('left', 'Frequency')
        self.distribution_plot.setLabel('bottom', 'Temperature')
    
    def update_pattern_analysis(self):
        """Update pattern analysis."""
        if self.historical_data.empty:
            return
        
        self.anomaly_plot.clear()
        
        # Apply anomaly detection
        try:
            anomalies = anomaly_detector.detect_anomalies(self.historical_data)
            
            # Plot normal data points
            normal_data = anomalies[~anomalies['anomaly']]
            anomaly_data = anomalies[anomalies['anomaly']]
            
            # Plot temperature anomalies
            self.anomaly_plot.plot(normal_data['timestamp'], normal_data['temperature'],
                                 pen=None, symbol='o', symbolSize=5,
                                 symbolBrush='#1e88e5')
            
            if not anomaly_data.empty:
                self.anomaly_plot.plot(anomaly_data['timestamp'], anomaly_data['temperature'],
                                     pen=None, symbol='o', symbolSize=8,
                                     symbolBrush='#ff6b6b')
            
            # Update anomaly results text
            n_anomalies = len(anomaly_data)
            total_points = len(anomalies)
            anomaly_percentage = (n_anomalies / total_points) * 100
            
            results_text = "Anomaly detection results:\n"
            results_text += f"Anomaly count: {n_anomalies}\n"
            results_text += f"Anomaly rate: {anomaly_percentage:.2f}%\n"
            results_text += f"Total points: {total_points}"
            
            self.anomaly_results.setText(results_text)
            
        except Exception as e:
            print(f"Error in pattern analysis: {e}")
    
    def update_failure_analysis(self):
        """Update failure analysis."""
        if self.historical_data.empty:
            return
        
        self.failure_trend_plot.clear()
        
        # Simulate failure probabilities over time
        failure_probs = []
        for _, row in self.historical_data.iterrows():
            sensor_data = row.to_dict()
            prediction = failure_predictor.predict_failure(sensor_data)
            failure_probs.append(prediction['failure_probability'])
        
        # Plot failure probability trend
        self.failure_trend_plot.plot(self.historical_data['timestamp'], failure_probs,
                                   pen=pg.mkPen(color='#ff6b6b', width=3))
        
        # Add alert threshold line
        alert_line = pg.InfiniteLine(pos=0.7, angle=0, pen=pg.mkPen('y', width=2, style=Qt.PenStyle.DashLine))
        self.failure_trend_plot.addItem(alert_line)
        
        # Update risk factors text
        self.update_risk_factors()
    
    def update_risk_factors(self):
        """Update risk factors."""
        if self.historical_data.empty:
            return
        
        # Compute risk factors
        risk_factors = []
        
        avg_temperature = self.historical_data['temperature'].mean()
        if avg_temperature > 75:
            risk_factors.append(f"Elevated average temperature: {avg_temperature:.1f} C")
        
        max_vibration = self.historical_data[['vibration_x', 'vibration_y', 'vibration_z']].max().max()
        if max_vibration > 5.0:
            risk_factors.append(f"High vibration level: {max_vibration:.1f} m/s^2")
        
        min_oil_level = self.historical_data['oil_level'].min()
        if min_oil_level < 0.4:
            risk_factors.append(f"Low oil level: {min_oil_level*100:.1f}%")
        
        avg_oil_quality = self.historical_data['oil_quality'].mean()
        if avg_oil_quality < 0.7:
            risk_factors.append(f"Declining oil quality: {avg_oil_quality*100:.1f}%")
        
        if not risk_factors:
            risk_factors.append("No significant risk factors")
        
        risk_text = "Key risk factors:\n\n" + "\n".join([f"- {factor}" for factor in risk_factors])
        self.risk_factors_text.setText(risk_text)
    
    def export_report(self):
        """Export analytics report."""
        try:
            # In the real application a PDF or Excel report would be generated
            print('Exporting report...')
            
            # Simulate export process
            report_data = {
                'report_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'pump': self.pump_selector.currentText(),
                'range': f"{self.date_from.date().toString('yyyy-MM-dd')} to {self.date_to.date().toString('yyyy-MM-dd')}",
                'performance_summary': 'Detailed report is being prepared...'
            }
            
            print('Report exported successfully')
            
        except Exception as e:
            print(f"Error exporting report: {e}")
    
    def refresh_data(self):
        """Refresh analytics data."""
        self.load_historical_data()
