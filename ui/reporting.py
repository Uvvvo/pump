"""
Reporting module for the iPump application.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QGroupBox, QLabel, QPushButton, QComboBox,
                           QDateEdit, QTextEdit, QCheckBox, QProgressBar,
                           QTabWidget, QFileDialog, QMessageBox, QTableWidget,
                           QTableWidgetItem, QHeaderView)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QDate, QTimer, QThread
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# Import modules with exception handling
try:
    from database import db_manager
except ImportError:
    class db_manager:
        @staticmethod
        def get_pumps():
            return pd.DataFrame()
        
        @staticmethod
        def get_maintenance_data():
            return pd.DataFrame()

try:
    from ai_models import failure_predictor
except ImportError:
    class failure_predictor:
        @staticmethod
        def predict_failure(data):
            return {'risk_level': 'Low', 'probability': 0.1}

try:
    from config import REPORTS_DIR
except ImportError:
    REPORTS_DIR = "reports"

try:
    from ui.workers import BackgroundWorker
except ImportError:
    class BackgroundWorkerSignals:
        result = None
        error = None
        finished = None
    
    class BackgroundWorker:
        def __init__(self, func, *args, **kwargs):
            self.func = func
            self.args = args
            self.kwargs = kwargs
            self.signals = BackgroundWorkerSignals()
        
        def run(self):
            try:
                result = self.func(*self.args, **self.kwargs)
                if self.signals.result:
                    self.signals.result.emit(result)
            except Exception as e:
                if self.signals.error:
                    self.signals.error.emit(str(e))
            finally:
                if self.signals.finished:
                    self.signals.finished.emit()

class ReportingTab(QWidget):
    def __init__(self):
        super().__init__()
        self._report_thread = None
        self._report_worker = None
        self.setup_ui()
        self.load_initial_data()
        
    def setup_ui(self):
        """Set up the reporting interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Report type:"))
        self.report_type = QComboBox()
        self.report_type.addItems([
            "Daily performance report",
            "Monthly maintenance report", 
            "Failure prediction report",
            "Statistical analytics report",
            "Cost report"
        ])
        control_layout.addWidget(self.report_type)
        
        control_layout.addWidget(QLabel("Period:"))
        self.report_date = QDateEdit()
        self.report_date.setDate(QDate.currentDate())
        self.report_date.setCalendarPopup(True)
        control_layout.addWidget(self.report_date)
        
        self.generate_btn = QPushButton("Generate report")
        self.generate_btn.clicked.connect(self.generate_report)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e88e5;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        control_layout.addWidget(self.generate_btn)
        
        self.export_btn = QPushButton("Export PDF")
        self.export_btn.clicked.connect(self.export_to_pdf)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40a94c;
            }
        """)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Report display area
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        font = QFont()
        font.setPointSize(10)
        self.report_display.setFont(font)
        self.report_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        main_layout.addWidget(self.report_display)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 5px;
                background-color: #0f172a;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1e88e5, stop: 1 #0d47a1);
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
    def load_initial_data(self):
        """Load initial data."""
        try:
            # Load initial data here if needed
            pass
        except Exception as e:
            print(f"Error loading initial data: {e}")
    
    def _generate_report_task(self, report_type, report_date):
        """Long-running background task that returns the report text."""
        if report_type == "Daily performance report":
            return self.generate_daily_performance_report(report_date)
        elif report_type == "Monthly maintenance report":
            return self.generate_maintenance_report(report_date)
        elif report_type == "Failure prediction report":
            return self.generate_failure_prediction_report(report_date)
        elif report_type == "Statistical analytics report":
            return self.generate_statistical_report(report_date)
        elif report_type == "Cost report":
            return self.generate_cost_report(report_date)
        return "<html><body><p>Unknown report type</p></body></html>"

    def generate_report(self):
        """Generate the report in the background to keep the UI responsive."""
        try:
            # Prevent launching multiple report generations
            if self._report_thread is not None and self._report_thread.isRunning():
                return

            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            report_type = self.report_type.currentText()
            report_date = self.report_date.date().toPyDate()

            thread = QThread()
            worker = BackgroundWorker(self._generate_report_task, report_type, report_date)
            worker.moveToThread(thread)
            thread.started.connect(worker.run)

            def on_result(report_content):
                self.report_display.setHtml(report_content)
                self.progress_bar.setValue(100)

            worker.signals.result.connect(on_result)
            worker.signals.error.connect(lambda e: QMessageBox.warning(self, "Error", f"Error generating report: {e}"))
            worker.signals.finished.connect(lambda: self.progress_bar.setVisible(False))
            worker.signals.finished.connect(thread.quit)
            worker.signals.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)

            self._report_thread = thread
            self._report_worker = worker

            thread.start()
            # Optional progress updates: animate the progress bar until a result is received
            self.progress_bar.setValue(30)

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.warning(self, "Error", f"Error starting report generation: {e}")
    
    def generate_daily_performance_report(self, date):
        """Build the daily performance report."""
        try:
            # Simulated performance data
            pumps_data = [
                {"name": "Refinery main pump", "status": "Operational", "efficiency": "95%", "alerts": 0},
                {"name": "Transfer pump 1", "status": "Operational", "efficiency": "92%", "alerts": 1},
                {"name": "Main feed pump", "status": "Maintenance", "efficiency": "0%", "alerts": 0},
                {"name": "Auxiliary service pump", "status": "Operational", "efficiency": "88%", "alerts": 2}
            ]
            
            # Calculate statistics
            operating_pumps = [p for p in pumps_data if p["status"] == "Operational"]
            if operating_pumps:
                avg_efficiency = np.mean([float(p["efficiency"].strip('%')) for p in operating_pumps])
            else:
                avg_efficiency = 0
                
            total_alerts = sum(pump["alerts"] for pump in pumps_data)
            
            report = f"""
            <html dir='rtl'>
            <head>
                <style>
                    body {{ font-family: 'Arial', sans-serif; margin: 20px; direction: rtl; }}
                    .header {{ text-align: center; color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
                    .section {{ margin: 20px 0; }}
                    .section-title {{ color: #0d47a1; border-right: 4px solid #1e88e5; padding-right: 10px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; direction: rtl; }}
                    th, td {{ padding: 12px; text-align: right; border: 1px solid #ddd; }}
                    th {{ background-color: #1e88e5; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    .alert {{ color: #ff6b6b; font-weight: bold; }}
                    .good {{ color: #51cf66; }}
                    .warning {{ color: #f59f00; }}
                    .summary-table {{ width: 80%; margin: 20px auto; }}
                </style>
            </head>
            <body>
                <div class='header'>
                    <h1>Daily performance report</h1>
                    <h2>For date: {date.strftime('%Y-%m-%d')}</h2>
                    <h3>iPump pump failure prediction system</h3>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>Performance summary</h3>
                    <table class='summary-table'>
                        <tr>
                            <th>Total pumps</th>
                            <th>Operational pumps</th>
                            <th>Average efficiency</th>
                            <th>Total alerts</th>
                        </tr>
                        <tr>
                            <td>{len(pumps_data)}</td>
                            <td>{len(operating_pumps)}</td>
                            <td>{avg_efficiency:.1f}%</td>
                            <td class='{'alert' if total_alerts > 0 else 'good'}>{total_alerts}</td>
                        </tr>
                    </table>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>Detailed pump performance</h3>
                    <table>
                        <tr>
                            <th>Pump name</th>
                            <th>Status</th>
                            <th>Efficiency</th>
                            <th>Alert count</th>
                            <th>Rating</th>
                        </tr>
            """
            
            for pump in pumps_data:
                status_class = "good" if pump["status"] == "Operational" else "warning"
                efficiency_value = float(pump["efficiency"].strip('%'))
                efficiency_class = "good" if efficiency_value > 90 else "warning" if efficiency_value > 70 else "alert"
                alerts_class = "alert" if pump["alerts"] > 0 else "good"
                
                if efficiency_value > 95:
                    rating = "Excellent"
                elif efficiency_value > 85:
                    rating = "Good"
                elif efficiency_value > 70:
                    rating = "Acceptable"
                else:
                    rating = "Needs improvement"
                
                report += f"""
                        <tr>
                            <td>{pump['name']}</td>
                            <td class='{status_class}'>{pump['status']}</td>
                            <td class='{efficiency_class}'>{pump['efficiency']}</td>
                            <td class='{alerts_class}'>{pump['alerts']}</td>
                            <td>{rating}</td>
                        </tr>
                """
            
            report += """
                    </table>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>Recommendations</h3>
                    <ul>
                        <li>Inspect Auxiliary service pump due to low efficiency</li>
                        <li>Resolve alerts for Transfer pump 1</li>
                        <li>Complete maintenance for Main feed pump</li>
                        <li>Review settings for Refinery main pump to maintain high efficiency</li>
                    </ul>
                </div>
                
                <div class='section'>
                    <p><strong>Generated on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                    <p><strong>Generated by:</strong> iPump smart system</p>
                </div>
            </body>
            </html>
            """
            
            return report
            
        except Exception as e:
            return f"<html><body><h1>Error generating report</h1><p>{str(e)}</p></body></html>"
    
    def generate_maintenance_report(self, date):
        """Build the monthly maintenance report."""
        try:
            # Simulate maintenance data
            maintenance_data = [
                {"pump": "Refinery main pump", "type": "Routine maintenance", "status": "Completed", "cost": "1500", "date": "2024-01-15"},
                {"pump": "Transfer pump 1", "type": "Oil replacement", "status": "In progress", "cost": "800", "date": "2024-01-20"},
                {"pump": "Main feed pump", "type": "Bearing inspection", "status": "Scheduled", "cost": "1200", "date": "2024-01-25"},
                {"pump": "Auxiliary service pump", "type": "Filter cleaning", "status": "Overdue", "cost": "600", "date": "2024-01-10"}
            ]
            
            # Calculate statistics
            completed_maintenance = [m for m in maintenance_data if m["status"] == "Completed"]
            in_progress_maintenance = [m for m in maintenance_data if m["status"] == "In progress"]
            overdue_maintenance = [m for m in maintenance_data if m["status"] == "Overdue"]
            
            total_cost = sum(int(m["cost"]) for m in completed_maintenance + in_progress_maintenance)
            
            report = f"""
            <html dir='rtl'>
            <head>
                <style>
                    body {{ font-family: 'Arial', sans-serif; margin: 20px; direction: rtl; }}
                    .header {{ text-align: center; color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
                    .section {{ margin: 20px 0; }}
                    .section-title {{ color: #0d47a1; border-right: 4px solid #1e88e5; padding-right: 10px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; direction: rtl; }}
                    th, td {{ padding: 12px; text-align: right; border: 1px solid #ddd; }}
                    th {{ background-color: #1e88e5; color: white; }}
                    .completed {{ background-color: #d4edda; }}
                    .in-progress {{ background-color: #fff3cd; }}
                    .scheduled {{ background-color: #d1ecf1; }}
                    .overdue {{ background-color: #f8d7da; }}
                    .summary-table {{ width: 80%; margin: 20px auto; }}
                </style>
            </head>
            <body>
                <div class='header'>
                    <h1>Monthly maintenance report</h1>
                    <h2>For month: {date.strftime('%Y-%m')}</h2>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>Maintenance summary</h3>
                    <table class='summary-table'>
                        <tr>
                            <th>Total maintenance actions</th>
                            <th>Completed</th>
                            <th>In progress</th>
                            <th>Overdue</th>
                            <th>Total cost</th>
                        </tr>
                        <tr>
                            <td>{len(maintenance_data)}</td>
                            <td>{len(completed_maintenance)}</td>
                            <td>{len(in_progress_maintenance)}</td>
                            <td>{len(overdue_maintenance)}</td>
                            <td>{total_cost} SAR</td>
                        </tr>
                    </table>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>Maintenance operation details</h3>
                    <table>
                        <tr>
                            <th>Pump</th>
                            <th>Maintenance type</th>
                            <th>Status</th>
                            <th>Cost (SAR)</th>
                            <th>Date</th>
                        </tr>
            """
            
            for maintenance in maintenance_data:
                status_class = ""
                if maintenance["status"] == "Completed":
                    status_class = "completed"
                elif maintenance["status"] == "In progress":
                    status_class = "in-progress"
                elif maintenance["status"] == "Scheduled":
                    status_class = "scheduled"
                elif maintenance["status"] == "Overdue":
                    status_class = "overdue"
                
                report += f"""
                        <tr class='{status_class}'>
                            <td>{maintenance['pump']}</td>
                            <td>{maintenance['type']}</td>
                            <td>{maintenance['status']}</td>
                            <td>{maintenance['cost']}</td>
                            <td>{maintenance['date']}</td>
                        </tr>
                """
            
            report += """
                    </table>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>Cost analysis</h3>
                    <p>• Average maintenance cost: {total_cost/len(maintenance_data):.0f} SAR</p>
                    <p>• Completion rate: {(len(completed_maintenance)/len(maintenance_data))*100:.1f}%</p>
                    <p>• Potential savings from preventive maintenance: 25% of emergency repair costs</p>
                </div>
            </body>
            </html>
            """
            
            return report
            
        except Exception as e:
            return f"<html><body><h1>Error generating report</h1><p>{str(e)}</p></body></html>"
    
    def generate_failure_prediction_report(self, date):
        """Build the failure prediction report."""
        try:
            # Simulate failure predictions
            predictions = [
                {"pump": "Refinery main pump", "risk": "Low", "probability": "15%", "recommendation": "Continue monitoring"},
                {"pump": "Transfer pump 1", "risk": "Medium", "probability": "45%", "recommendation": "Schedule preventive maintenance"},
                {"pump": "Main feed pump", "risk": "High", "probability": "72%", "recommendation": "Immediate inspection"},
                {"pump": "Auxiliary service pump", "risk": "High", "probability": "68%", "recommendation": "Shutdown and inspect"}
            ]
            
            high_risk_count = sum(1 for p in predictions if p["risk"] == "High")
            medium_risk_count = sum(1 for p in predictions if p["risk"] == "Medium")
            low_risk_count = sum(1 for p in predictions if p["risk"] == "Low")
            
            report = f"""
            <html dir='rtl'>
            <head>
                <style>
                    body {{ font-family: 'Arial', sans-serif; margin: 20px; direction: rtl; }}
                    .header {{ text-align: center; color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
                    .section {{ margin: 20px 0; }}
                    .section-title {{ color: #0d47a1; border-right: 4px solid #1e88e5; padding-right: 10px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; direction: rtl; }}
                    th, td {{ padding: 12px; text-align: right; border: 1px solid #ddd; }}
                    th {{ background-color: #1e88e5; color: white; }}
                    .low-risk {{ background-color: #d4edda; }}
                    .medium-risk {{ background-color: #fff3cd; }}
                    .high-risk {{ background-color: #f8d7da; }}
                    .summary-table {{ width: 80%; margin: 20px auto; }}
                </style>
            </head>
            <body>
                <div class='header'>
                    <h1>Failure prediction report</h1>
                    <h2>For date: {date.strftime('%Y-%m-%d')}</h2>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>Risk summary</h3>
                    <table class='summary-table'>
                        <tr>
                            <th>Total pumps</th>
                            <th>Low risk</th>
                            <th>Medium risk</th>
                            <th>High risk</th>
                        </tr>
                        <tr>
                            <td>{len(predictions)}</td>
                            <td>{low_risk_count}</td>
                            <td>{medium_risk_count}</td>
                            <td>{high_risk_count}</td>
                        </tr>
                    </table>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>Prediction details</h3>
                    <table>
                        <tr>
                            <th>Pump</th>
                            <th>Risk level</th>
                            <th>Failure probability</th>
                            <th>Recommendation</th>
                        </tr>
            """
            
            for pred in predictions:
                risk_class = ""
                if pred["risk"] == "Low":
                    risk_class = "low-risk"
                elif pred["risk"] == "Medium":
                    risk_class = "medium-risk"
                elif pred["risk"] == "High":
                    risk_class = "high-risk"
                
                report += f"""
                        <tr class='{risk_class}'>
                            <td>{pred['pump']}</td>
                            <td>{pred['risk']}</td>
                            <td>{pred['probability']}</td>
                            <td>{pred['recommendation']}</td>
                        </tr>
                """
            
            report += """
                    </table>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>General recommendations</h3>
                    <ul>
                        <li>Prioritize pumps with high risk levels</li>
                        <li>Review the preventive maintenance program</li>
                        <li>Improve continuous monitoring systems</li>
                        <li>Train technicians to handle emergency situations</li>
                    </ul>
                </div>
            </body>
            </html>
            """
            
            return report
            
        except Exception as e:
            return f"<html><body><h1>Error generating report</h1><p>{str(e)}</p></body></html>"
    
    def generate_statistical_report(self, date):
        """Build the statistical analytics report."""
        try:
            report = f"""
            <html dir='rtl'>
            <head>
                <style>
                    body {{ font-family: 'Arial', sans-serif; margin: 20px; direction: rtl; }}
                    .header {{ text-align: center; color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
                    .section {{ margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class='header'>
                    <h1>Statistical analytics report</h1>
                    <h2>For month: {date.strftime('%Y-%m')}</h2>
                </div>
                
                <div class='section'>
                    <h3>Key statistics</h3>
                    <p>• Medium Average pump efficiency: 89.5%</p>
                    <p>• Availability rate: 96.2%</p>
                    <p>• Medium Mean time between failures: 2450 hours</p>
                    <p>• Maintenance cost per operating hour: 12.5 SAR</p>
                </div>
                
                <div class='section'>
                    <h3>Trends</h3>
                    <p>• Energy efficiency improved by 8% over last month</p>
                    <p>• Maintenance costs decreased by 15%</p>
                    <p>• Mean time between failures increased by 12%</p>
                </div>
            </body>
            </html>
            """
            return report
        except Exception as e:
            return f"<html><body><h1>Error generating report</h1><p>{str(e)}</p></body></html>"
    
    def generate_cost_report(self, date):
        """Build the cost report."""
        try:
            report = f"""
            <html dir='rtl'>
            <head>
                <style>
                    body {{ font-family: 'Arial', sans-serif; margin: 20px; direction: rtl; }}
                    .header {{ text-align: center; color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
                    .section {{ margin: 20px 0; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; direction: rtl; }}
                    th, td {{ padding: 12px; text-align: right; border: 1px solid #ddd; }}
                    th {{ background-color: #1e88e5; color: white; }}
                </style>
            </head>
            <body>
                <div class='header'>
                    <h1>Cost report</h1>
                    <h2>For month: {date.strftime('%Y-%m')}</h2>
                </div>
                
                <div class='section'>
                    <h3>Cost breakdown</h3>
                    <table>
                        <tr>
                            <th>Item</th>
                            <th>Cost (USD)</th>
                            <th>Percentage</th>
                        </tr>
                        <tr>
                            <td>Preventive maintenance</td>
                            <td>45,000</td>
                            <td>45%</td>
                        </tr>
                        <tr>
                            <td>Spare parts</td>
                            <td>25,000</td>
                            <td>25%</td>
                        </tr>
                        <tr>
                            <td>Energy</td>
                            <td>20,000</td>
                            <td>20%</td>
                        </tr>
                        <tr>
                            <td>Labor</td>
                            <td>10,000</td>
                            <td>10%</td>
                        </tr>
                        <tr>
                            <td><strong>Total</strong></td>
                            <td><strong>100,000</strong></td>
                            <td><strong>100%</strong></td>
                        </tr>
                    </table>
                </div>
                
                <div class='section'>
                    <h3>Cost analysis</h3>
                    <p>• 30% reduction in emergency maintenance costs</p>
                    <p>• Energy consumption efficiency increased by 12%</p>
                    <p>• Savings of 15,000 SAR from preventive maintenance</p>
                </div>
            </body>
            </html>
            """
            return report
        except Exception as e:
            return f"<html><body><h1>Error generating report</h1><p>{str(e)}</p></body></html>"
    
    def export_to_pdf(self):
        """Export report to PDF"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save report as PDF", 
                f"iPump_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                # In a real application use a library such as reportlab or weasyprint
                # Here we show an informational message
                QMessageBox.information(
                    self, 
                    "Export PDF", 
                    f"PDF export will be developed in the next release\n\nSelected path: {file_path}"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error during export: {str(e)}")
    
    def refresh_data(self):
        """Refresh data."""
        try:
            self.load_initial_data()
        except Exception as e:
            print(f"Error refreshing data: {e}")