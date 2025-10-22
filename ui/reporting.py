"""
وحدة التقارير لتطبيق iPump
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QGroupBox, QLabel, QPushButton, QComboBox,
                           QDateEdit, QTextEdit, QCheckBox, QProgressBar,
                           QTabWidget, QFileDialog, QMessageBox, QTableWidget,
                           QTableWidgetItem, QHeaderView)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QDate, QTimer
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from database import db_manager
from ai_models import failure_predictor
from config import REPORTS_DIR

class ReportingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_initial_data()
        
    def setup_ui(self):
        """تهيئة واجهة التقارير"""
        main_layout = QVBoxLayout(self)
        
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
        control_layout.addWidget(self.generate_btn)
        
        self.export_btn = QPushButton("تصدير PDF")
        self.export_btn.clicked.connect(self.export_to_pdf)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # منطقة عرض التقرير
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        font = QFont()
        font.setPointSize(10)
        self.report_display.setFont(font)
        
        main_layout.addWidget(self.report_display)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        # يمكن إضافة تحميل البيانات الأولية هنا إذا لزم الأمر
        pass
    
    def generate_report(self):
        """إنشاء التقرير"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            report_type = self.report_type.currentText()
            report_date = self.report_date.date().toPyDate()
            
            self.progress_bar.setValue(30)
            
            if report_type == "تقرير الأداء اليومي":
                report_content = self.generate_daily_performance_report(report_date)
            elif report_type == "تقرير الصيانة الشهري":
                report_content = self.generate_maintenance_report(report_date)
            elif report_type == "تقرير التنبؤ بالفشل":
                report_content = self.generate_failure_prediction_report(report_date)
            elif report_type == "تقرير التحليلات الإحصائية":
                report_content = self.generate_statistical_report(report_date)
            elif report_type == "تقرير التكاليف":
                report_content = self.generate_cost_report(report_date)
            else:
                report_content = "نوع التقرير غير معروف"
            
            self.progress_bar.setValue(80)
            
            self.report_display.setHtml(report_content)
            
            self.progress_bar.setValue(100)
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.warning(self, "خطأ", f"خطأ في إنشاء التقرير: {e}")
    
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
            
            total_alerts = sum(pump["alerts"] for pump in pumps_data)
            avg_efficiency = np.mean([float(pump["efficiency"].strip('%')) for pump in pumps_data if pump["status"] == "تعمل"])
            
            report = f"""
            <html dir='rtl'>
            <head>
                <style>
                    body {{ font-family: 'Arial', sans-serif; margin: 20px; }}
                    .header {{ text-align: center; color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
                    .section {{ margin: 20px 0; }}
                    .section-title {{ color: #0d47a1; border-right: 4px solid #1e88e5; padding-right: 10px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    th, td {{ padding: 12px; text-align: right; border: 1px solid #ddd; }}
                    th {{ background-color: #1e88e5; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    .alert {{ color: #ff6b6b; font-weight: bold; }}
                    .good {{ color: #51cf66; }}
                    .warning {{ color: #f59f00; }}
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
                    <table>
                        <tr>
                            <th>إجمالي المضخات</th>
                            <th>المضخات العاملة</th>
                            <th>متوسط الكفاءة</th>
                            <th>إجمالي الإنذارات</th>
                        </tr>
                        <tr>
                            <td>{len(pumps_data)}</td>
                            <td>{sum(1 for p in pumps_data if p['status'] == 'تعمل')}</td>
                            <td>{avg_efficiency:.1f}%</td>
                            <td class='{'alert' if total_alerts > 0 else 'good'}'>{total_alerts}</td>
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
                efficiency_class = "good" if float(pump["efficiency"].strip('%')) > 90 else "warning"
                alerts_class = "alert" if pump["alerts"] > 0 else "good"
                
                report += f"""
                        <tr>
                            <td>{pump['name']}</td>
                            <td class='{status_class}'>{pump['status']}</td>
                            <td class='{efficiency_class}'>{pump['efficiency']}</td>
                            <td class='{alerts_class}'>{pump['alerts']}</td>
                            <td>{'ممتاز' if float(pump['efficiency'].strip('%')) > 95 else 'جيد' if float(pump['efficiency'].strip('%')) > 85 else 'يحتاج تحسين'}</td>
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
            
            total_cost = sum(int(m["cost"]) for m in maintenance_data if m["status"] in ["مكتملة", "قيد التنفيذ"])
            completed_count = sum(1 for m in maintenance_data if m["status"] == "مكتملة")
            
            report = f"""
            <html dir='rtl'>
            <head>
                <style>
                    body {{ font-family: 'Arial', sans-serif; margin: 20px; }}
                    .header {{ text-align: center; color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
                    .section {{ margin: 20px 0; }}
                    .section-title {{ color: #0d47a1; border-right: 4px solid #1e88e5; padding-right: 10px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    th, td {{ padding: 12px; text-align: right; border: 1px solid #ddd; }}
                    th {{ background-color: #1e88e5; color: white; }}
                    .completed {{ background-color: #d4edda; }}
                    .in-progress {{ background-color: #fff3cd; }}
                    .scheduled {{ background-color: #d1ecf1; }}
                    .overdue {{ background-color: #f8d7da; }}
                </style>
            </head>
            <body>
                <div class='header'>
                    <h1>تقرير الصيانة الشهري</h1>
                    <h2>لشهر: {date.strftime('%Y-%m')}</h2>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>ملخص الصيانة</h3>
                    <table>
                        <tr>
                            <th>إجمالي عمليات الصيانة</th>
                            <th>المكتملة</th>
                            <th>قيد التنفيذ</th>
                            <th>المتأخرة</th>
                            <th>إجمالي التكلفة</th>
                        </tr>
                        <tr>
                            <td>{len(maintenance_data)}</td>
                            <td>{completed_count}</td>
                            <td>{sum(1 for m in maintenance_data if m['status'] == 'قيد التنفيذ')}</td>
                            <td>{sum(1 for m in maintenance_data if m['status'] == 'متأخرة')}</td>
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
                    <p>• نسبة الإنجاز: {(completed_count/len(maintenance_data))*100:.1f}%</p>
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
            
            report = f"""
            <html dir='rtl'>
            <head>
                <style>
                    body {{ font-family: 'Arial', sans-serif; margin: 20px; }}
                    .header {{ text-align: center; color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
                    .section {{ margin: 20px 0; }}
                    .section-title {{ color: #0d47a1; border-right: 4px solid #1e88e5; padding-right: 10px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    th, td {{ padding: 12px; text-align: right; border: 1px solid #ddd; }}
                    th {{ background-color: #1e88e5; color: white; }}
                    .low-risk {{ background-color: #d4edda; }}
                    .medium-risk {{ background-color: #fff3cd; }}
                    .high-risk {{ background-color: #f8d7da; }}
                </style>
            </head>
            <body>
                <div class='header'>
                    <h1>تقرير التنبؤ بالفشل</h1>
                    <h2>لتاريخ: {date.strftime('%Y-%m-%d')}</h2>
                </div>
                
                <div class='section'>
                    <h3 class='section-title'>ملخص المخاطر</h3>
                    <table>
                        <tr>
                            <th>إجمالي المضخات</th>
                            <th>مخاطر منخفضة</th>
                            <th>مخاطر متوسطة</th>
                            <th>مخاطر مرتفعة</th>
                        </tr>
                        <tr>
                            <td>{len(predictions)}</td>
                            <td>{sum(1 for p in predictions if p['risk'] == 'منخفض')}</td>
                            <td>{sum(1 for p in predictions if p['risk'] == 'متوسط')}</td>
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
        # تنفيذ مشابه للتقارير السابقة
        return "<h1>تقرير التحليلات الإحصائية - قيد التطوير</h1>"
    
    def generate_cost_report(self, date):
        """إنشاء تقرير التكاليف"""
        # تنفيذ مشابه للتقارير السابقة
        return "<h1>تقرير التكاليف - قيد التطوير</h1>"
    
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
            QMessageBox.warning(self, "خطأ", f"خطأ في التصدير: {e}")
    
    def refresh_data(self):
        """تحديث البيانات"""
        self.load_initial_data()