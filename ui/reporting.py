"""
وحدة التقارير لتطبيق iPump
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

# استيراد الوحدات مع معالجة الاستثناءات
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
            return {'risk_level': 'منخفض', 'probability': 0.1}

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
        """تهيئة واجهة التقارير"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # شريط التحكم
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("نوع التقرير:"))
        self.report_type = QComboBox()
        self.report_type.addItems([
            "تقرير الأداء اليومي",
            "تقرير الصيانة الشهري", 
            "تقرير التنبؤ بالفشل",
            "تقرير التحليلات الإحصائية",
            "تقرير التكاليف"
        ])
        control_layout.addWidget(self.report_type)
        
        control_layout.addWidget(QLabel("الفترة:"))
        self.report_date = QDateEdit()
        self.report_date.setDate(QDate.currentDate())
        self.report_date.setCalendarPopup(True)
        control_layout.addWidget(self.report_date)
        
        self.generate_btn = QPushButton("إنشاء التقرير")
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
        
        self.export_btn = QPushButton("تصدير PDF")
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
        
        # منطقة عرض التقرير
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
        
        # شريط التقدم
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
        """تحميل البيانات الأولية"""
        try:
            # يمكن إضافة تحميل البيانات الأولية هنا إذا لزم الأمر
            pass
        except Exception as e:
            print(f"خطأ في تحميل البيانات الأولية: {e}")
    
    def _generate_report_task(self, report_type, report_date):
        """دالة ثقيلة تعمل في الخلفية وتُرجع نص التقرير"""
        if report_type == "تقرير الأداء اليومي":
            return self.generate_daily_performance_report(report_date)
        elif report_type == "تقرير الصيانة الشهري":
            return self.generate_maintenance_report(report_date)
        elif report_type == "تقرير التنبؤ بالفشل":
            return self.generate_failure_prediction_report(report_date)
        elif report_type == "تقرير التحليلات الإحصائية":
            return self.generate_statistical_report(report_date)
        elif report_type == "تقرير التكاليف":
            return self.generate_cost_report(report_date)
        return "<html><body><p>نوع تقرير غير معروف</p></body></html>"

    def generate_report(self):
        """إنشاء التقرير في خلفية لمنع تجميد الواجهة"""
        try:
            # منع إطلاق أكثر من عملية توليد تقرير واحدة
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
            worker.signals.error.connect(lambda e: QMessageBox.warning(self, "خطأ", f"خطأ في توليد التقرير: {e}"))
            worker.signals.finished.connect(lambda: self.progress_bar.setVisible(False))
            worker.signals.finished.connect(thread.quit)
            worker.signals.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)

            self._report_thread = thread
            self._report_worker = worker

            thread.start()
            # تقدم مرحلي إن أردنا: اجعل شريط التقدم متحركًا إلى أن يتلقى result
            self.progress_bar.setValue(30)

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.warning(self, "خطأ", f"خطأ بدء توليد التقرير: {e}")
    
    def generate_daily_performance_report(self, date):
        """إنشاء تقرير الأداء اليومي"""
        try:
            # محاكاة بيانات الأداء
            pumps_data = [
                {"name": "مضخة المصفاة الرئيسية", "status": "تعمل", "efficiency": "95%", "alerts": 0},
                {"name": "مضخة النقل رقم 1", "status": "تعمل", "efficiency": "92%", "alerts": 1},
                {"name": "مضخة التغذية الرئيسية", "status": "صيانة", "efficiency": "0%", "alerts": 0},
                {"name": "مضخة الخدمة المساعدة", "status": "تعمل", "efficiency": "88%", "alerts": 2}
            ]
            
            # حساب الإحصائيات
            operating_pumps = [p for p in pumps_data if p["status"] == "تعمل"]
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
                    <h1>تقرير الأداء اليومي</h1>
                    <h2>لتاريخ: {date.strftime('%Y-%m-%d')}</h2>
                    <h3>نظام iPump للتنبؤ بفشل المضخات</h3>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>ملخص الأداء</h3>
                    <table class='summary-table'>
                        <tr>
                            <th>إجمالي المضخات</th>
                            <th>المضخات العاملة</th>
                            <th>متوسط الكفاءة</th>
                            <th>إجمالي الإنذارات</th>
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
                    <h3 class='section-title'>أداء المضخات التفصيلي</h3>
                    <table>
                        <tr>
                            <th>اسم المضخة</th>
                            <th>الحالة</th>
                            <th>الكفاءة</th>
                            <th>عدد الإنذارات</th>
                            <th>التقييم</th>
                        </tr>
            """
            
            for pump in pumps_data:
                status_class = "good" if pump["status"] == "تعمل" else "warning"
                efficiency_value = float(pump["efficiency"].strip('%'))
                efficiency_class = "good" if efficiency_value > 90 else "warning" if efficiency_value > 70 else "alert"
                alerts_class = "alert" if pump["alerts"] > 0 else "good"
                
                if efficiency_value > 95:
                    rating = "ممتاز"
                elif efficiency_value > 85:
                    rating = "جيد"
                elif efficiency_value > 70:
                    rating = "مقبول"
                else:
                    rating = "يحتاج تحسين"
                
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
                    <h3 class='section-title'>التوصيات</h3>
                    <ul>
                        <li>فحص مضخة الخدمة المساعدة due to low efficiency</li>
                        <li>معالجة الإنذارات في مضخة النقل رقم 1</li>
                        <li>إكمال صيانة مضخة التغذية الرئيسية</li>
                        <li>مراجعة إعدادات مضخة المصفاة الرئيسية للحفاظ على الكفاءة العالية</li>
                    </ul>
                </div>
                
                <div class='section'>
                    <p><strong>تاريخ الإنشاء:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                    <p><strong>تم الإنشاء بواسطة:</strong> نظام iPump الذكي</p>
                </div>
            </body>
            </html>
            """
            
            return report
            
        except Exception as e:
            return f"<html><body><h1>خطأ في إنشاء التقرير</h1><p>{str(e)}</p></body></html>"
    
    def generate_maintenance_report(self, date):
        """إنشاء تقرير الصيانة الشهري"""
        try:
            # محاكاة بيانات الصيانة
            maintenance_data = [
                {"pump": "مضخة المصفاة الرئيسية", "type": "صيانة دورية", "status": "مكتملة", "cost": "1500", "date": "2024-01-15"},
                {"pump": "مضخة النقل رقم 1", "type": "استبدال زيت", "status": "قيد التنفيذ", "cost": "800", "date": "2024-01-20"},
                {"pump": "مضخة التغذية الرئيسية", "type": "فحص محامل", "status": "مجدولة", "cost": "1200", "date": "2024-01-25"},
                {"pump": "مضخة الخدمة المساعدة", "type": "تنظيف فلاتر", "status": "متأخرة", "cost": "600", "date": "2024-01-10"}
            ]
            
            # حساب الإحصائيات
            completed_maintenance = [m for m in maintenance_data if m["status"] == "مكتملة"]
            in_progress_maintenance = [m for m in maintenance_data if m["status"] == "قيد التنفيذ"]
            overdue_maintenance = [m for m in maintenance_data if m["status"] == "متأخرة"]
            
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
                    <h1>تقرير الصيانة الشهري</h1>
                    <h2>لشهر: {date.strftime('%Y-%m')}</h2>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>ملخص الصيانة</h3>
                    <table class='summary-table'>
                        <tr>
                            <th>إجمالي عمليات الصيانة</th>
                            <th>المكتملة</th>
                            <th>قيد التنفيذ</th>
                            <th>المتأخرة</th>
                            <th>إجمالي التكلفة</th>
                        </tr>
                        <tr>
                            <td>{len(maintenance_data)}</td>
                            <td>{len(completed_maintenance)}</td>
                            <td>{len(in_progress_maintenance)}</td>
                            <td>{len(overdue_maintenance)}</td>
                            <td>{total_cost} ريال</td>
                        </tr>
                    </table>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>تفاصيل عمليات الصيانة</h3>
                    <table>
                        <tr>
                            <th>المضخة</th>
                            <th>نوع الصيانة</th>
                            <th>الحالة</th>
                            <th>التكلفة (ريال)</th>
                            <th>التاريخ</th>
                        </tr>
            """
            
            for maintenance in maintenance_data:
                status_class = ""
                if maintenance["status"] == "مكتملة":
                    status_class = "completed"
                elif maintenance["status"] == "قيد التنفيذ":
                    status_class = "in-progress"
                elif maintenance["status"] == "مجدولة":
                    status_class = "scheduled"
                elif maintenance["status"] == "متأخرة":
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
                    <h3 class='section-title'>تحليل التكاليف</h3>
                    <p>• متوسط تكلفة الصيانة: {total_cost/len(maintenance_data):.0f} ريال</p>
                    <p>• نسبة الإنجاز: {(len(completed_maintenance)/len(maintenance_data))*100:.1f}%</p>
                    <p>• التوفير المحتمل من الصيانة الوقائية: 25% من تكاليف الإصلاحات الطارئة</p>
                </div>
            </body>
            </html>
            """
            
            return report
            
        except Exception as e:
            return f"<html><body><h1>خطأ في إنشاء التقرير</h1><p>{str(e)}</p></body></html>"
    
    def generate_failure_prediction_report(self, date):
        """إنشاء تقرير التنبؤ بالفشل"""
        try:
            # محاكاة تنبؤات الفشل
            predictions = [
                {"pump": "مضخة المصفاة الرئيسية", "risk": "منخفض", "probability": "15%", "recommendation": "متابعة المراقبة"},
                {"pump": "مضخة النقل رقم 1", "risk": "متوسط", "probability": "45%", "recommendation": "جدولة صيانة وقائية"},
                {"pump": "مضخة التغذية الرئيسية", "risk": "مرتفع", "probability": "72%", "recommendation": "فحص عاجل"},
                {"pump": "مضخة الخدمة المساعدة", "risk": "مرتفع", "probability": "68%", "recommendation": "إيقاف وتفقد"}
            ]
            
            high_risk_count = sum(1 for p in predictions if p["risk"] == "مرتفع")
            medium_risk_count = sum(1 for p in predictions if p["risk"] == "متوسط")
            low_risk_count = sum(1 for p in predictions if p["risk"] == "منخفض")
            
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
                    <h1>تقرير التنبؤ بالفشل</h1>
                    <h2>لتاريخ: {date.strftime('%Y-%m-%d')}</h2>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>ملخص المخاطر</h3>
                    <table class='summary-table'>
                        <tr>
                            <th>إجمالي المضخات</th>
                            <th>مخاطر منخفضة</th>
                            <th>مخاطر متوسطة</th>
                            <th>مخاطر مرتفعة</th>
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
                    <h3 class='section-title'>تفاصيل التنبؤات</h3>
                    <table>
                        <tr>
                            <th>المضخة</th>
                            <th>مستوى الخطورة</th>
                            <th>احتمالية الفشل</th>
                            <th>التوصية</th>
                        </tr>
            """
            
            for pred in predictions:
                risk_class = ""
                if pred["risk"] == "منخفض":
                    risk_class = "low-risk"
                elif pred["risk"] == "متوسط":
                    risk_class = "medium-risk"
                elif pred["risk"] == "مرتفع":
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
                    <h3 class='section-title'>توصيات عامة</h3>
                    <ul>
                        <li>إعطاء أولوية للمضخات ذات المخاطر المرتفعة</li>
                        <li>مراجعة برنامج الصيانة الوقائية</li>
                        <li>تحسين نظام المراقبة المستمرة</li>
                        <li>تدريب الفنيين على التعامل مع حالات الطوارئ</li>
                    </ul>
                </div>
            </body>
            </html>
            """
            
            return report
            
        except Exception as e:
            return f"<html><body><h1>خطأ في إنشاء التقرير</h1><p>{str(e)}</p></body></html>"
    
    def generate_statistical_report(self, date):
        """إنشاء تقرير التحليلات الإحصائية"""
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
                    <h1>تقرير التحليلات الإحصائية</h1>
                    <h2>لشهر: {date.strftime('%Y-%m')}</h2>
                </div>
                
                <div class='section'>
                    <h3>الإحصائيات الرئيسية</h3>
                    <p>• متوسط كفاءة المضخات: 89.5%</p>
                    <p>• معدل الإتاحة: 96.2%</p>
                    <p>• متوسط وقت التشغيل بين الأعطال: 2450 ساعة</p>
                    <p>• تكلفة الصيانة لكل ساعة تشغيل: 12.5 ريال</p>
                </div>
                
                <div class='section'>
                    <h3>الاتجاهات</h3>
                    <p>• تحسن في كفاءة الطاقة بنسبة 8% عن الشهر الماضي</p>
                    <p>• انخفاض في تكاليف الصيانة بنسبة 15%</p>
                    <p>• زيادة في وقت التشغيل بين الأعطال بنسبة 12%</p>
                </div>
            </body>
            </html>
            """
            return report
        except Exception as e:
            return f"<html><body><h1>خطأ في إنشاء التقرير</h1><p>{str(e)}</p></body></html>"
    
    def generate_cost_report(self, date):
        """إنشاء تقرير التكاليف"""
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
                    <h1>تقرير التكاليف</h1>
                    <h2>لشهر: {date.strftime('%Y-%m')}</h2>
                </div>
                
                <div class='section'>
                    <h3>تفاصيل التكاليف</h3>
                    <table>
                        <tr>
                            <th>البند</th>
                            <th>اتكلفة (دولار)</th>
                            <th>النسبة</th>
                        </tr>
                        <tr>
                            <td>صيانة وقائية</td>
                            <td>45,000</td>
                            <td>45%</td>
                        </tr>
                        <tr>
                            <td>قطع غيار</td>
                            <td>25,000</td>
                            <td>25%</td>
                        </tr>
                        <tr>
                            <td>طاقة</td>
                            <td>20,000</td>
                            <td>20%</td>
                        </tr>
                        <tr>
                            <td>عمالة</td>
                            <td>10,000</td>
                            <td>10%</td>
                        </tr>
                        <tr>
                            <td><strong>الإجمالي</strong></td>
                            <td><strong>100,000</strong></td>
                            <td><strong>100%</strong></td>
                        </tr>
                    </table>
                </div>
                
                <div class='section'>
                    <h3>تحليل التكاليف</h3>
                    <p>• انخفاض في تكاليف الصيانة الطارئة بنسبة 30%</p>
                    <p>• زيادة في كفاءة استهلاك الطاقة بنسبة 12%</p>
                    <p>• توفير قدره 15,000 ريال من الصيانة الوقائية</p>
                </div>
            </body>
            </html>
            """
            return report
        except Exception as e:
            return f"<html><body><h1>خطأ في إنشاء التقرير</h1><p>{str(e)}</p></body></html>"
    
    def export_to_pdf(self):
        """تصدير التقرير إلى PDF"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "حفظ التقرير كـ PDF", 
                f"iPump_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                # في التطبيق الحقيقي، سيتم استخدام مكتبة like reportlab أو weasyprint
                # هنا نستخدم رسالة توضيحية
                QMessageBox.information(
                    self, 
                    "تصدير PDF", 
                    f"سيتم تطوير ميزة التصدير إلى PDF في النسخة القادمة\n\nالمسار المحدد: {file_path}"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في التصدير: {str(e)}")
    
    def refresh_data(self):
        """تحديث البيانات"""
        try:
            self.load_initial_data()
        except Exception as e:
            print(f"خطأ في تحديث البيانات: {e}")