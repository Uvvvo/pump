"""
وحدة إدارة الصيانة لتطبيق iPump - مع إضافة إدارة المضخات
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QGroupBox, QLabel, QPushButton, QComboBox,
                           QDateEdit, QTableWidget, QTableWidgetItem,
                           QHeaderView, QTextEdit, QLineEdit, QSpinBox,
                           QDoubleSpinBox, QCheckBox, QMessageBox, QTabWidget,
                           QDialog, QDialogButtonBox, QFormLayout, QListWidget,
                           QListWidgetItem, QSplitter)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QDate, QTimer
import pandas as pd
from datetime import datetime, timedelta

from database import db_manager
from config import PUMP_CONFIG

class MaintenanceTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_maintenance_data()
        
    def setup_ui(self):
        """تهيئة واجهة إدارة الصيانة مع إضافة إدارة المضخات"""
        main_layout = QVBoxLayout(self)
        
        # شريط التحكم
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("المضخة:"))
        self.pump_selector = QComboBox()
        self.pump_selector.currentIndexChanged.connect(self.on_pump_changed)
        control_layout.addWidget(self.pump_selector)
        
        # أزرار إدارة المضخات الجديدة
        self.add_pump_btn = QPushButton("إضافة مضخة جديدة")
        self.add_pump_btn.clicked.connect(self.show_add_pump_dialog)
        self.add_pump_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e88e5;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        control_layout.addWidget(self.add_pump_btn)
        
        self.link_sensors_btn = QPushButton("ربط الحساسات")
        self.link_sensors_btn.clicked.connect(self.show_link_sensors_dialog)
        self.link_sensors_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40a94c;
            }
        """)
        control_layout.addWidget(self.link_sensors_btn)
        
        self.add_maintenance_btn = QPushButton("إضافة صيانة جديدة")
        self.add_maintenance_btn.clicked.connect(self.show_add_maintenance_dialog)
        control_layout.addWidget(self.add_maintenance_btn)
        
        self.refresh_btn = QPushButton("تحديث")
        self.refresh_btn.clicked.connect(self.load_maintenance_data)
        control_layout.addWidget(self.refresh_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # تبويبات الصيانة مع إضافة تبويب إدارة المضخات
        self.maintenance_tabs = QTabWidget()
        
        # تبويب إدارة المضخات (جديد)
        self.pumps_management_tab = self.create_pumps_management_tab()
        self.maintenance_tabs.addTab(self.pumps_management_tab, "إدارة المضخات")
        
        # تبويب جدول الصيانة
        self.schedule_tab = self.create_schedule_tab()
        self.maintenance_tabs.addTab(self.schedule_tab, "جدول الصيانة")
        
        # تبويب سجل الصيانة
        self.history_tab = self.create_history_tab()
        self.maintenance_tabs.addTab(self.history_tab, "سجل الصيانة")
        
        # تبويب التحليل الوقائي
        self.predictive_tab = self.create_predictive_tab()
        self.maintenance_tabs.addTab(self.predictive_tab, "التحليل الوقائي")
        
        main_layout.addWidget(self.maintenance_tabs)
        
    def create_pumps_management_tab(self):
        """إنشاء تبويب إدارة المضخات الجديد"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # تقسيم الشاشة إلى قسمين
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # القسم الأيسر: قائمة المضخات
        pumps_list_group = QGroupBox("قائمة المضخات")
        pumps_list_layout = QVBoxLayout(pumps_list_group)
        
        # أزرار التحكم في المضخات
        pumps_control_layout = QHBoxLayout()
        
        self.refresh_pumps_btn = QPushButton("تحديث القائمة")
        self.refresh_pumps_btn.clicked.connect(self.load_pumps_list)
        pumps_control_layout.addWidget(self.refresh_pumps_btn)
        
        self.export_pumps_btn = QPushButton("تصدير البيانات")
        self.export_pumps_btn.clicked.connect(self.export_pumps_data)
        pumps_control_layout.addWidget(self.export_pumps_btn)
        
        pumps_control_layout.addStretch()
        pumps_list_layout.addLayout(pumps_control_layout)
        
        # جدول المضخات
        self.pumps_table = QTableWidget()
        self.pumps_table.setColumnCount(6)
        self.pumps_table.setHorizontalHeaderLabels([
            "المعرف", "اسم المضخة", "الموقع", "النوع", 
            "تاريخ التركيب", "الحالة"
        ])
        self.pumps_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pumps_table.doubleClicked.connect(self.on_pump_double_clicked)
        pumps_list_layout.addWidget(self.pumps_table)
        
        splitter.addWidget(pumps_list_group)
        
        # القسم الأيمن: تفاصيل المضخة والحساسات
        details_group = QGroupBox("تفاصيل المضخة والحساسات")
        details_layout = QVBoxLayout(details_group)
        
        # معلومات المضخة
        pump_info_group = QGroupBox("معلومات المضخة")
        pump_info_layout = QFormLayout(pump_info_group)
        
        self.selected_pump_name = QLabel("--")
        self.selected_pump_location = QLabel("--")
        self.selected_pump_type = QLabel("--")
        self.selected_pump_installation = QLabel("--")
        self.selected_pump_status = QLabel("--")
        
        pump_info_layout.addRow("اسم المضخة:", self.selected_pump_name)
        pump_info_layout.addRow("الموقع:", self.selected_pump_location)
        pump_info_layout.addRow("النوع:", self.selected_pump_type)
        pump_info_layout.addRow("تاريخ التركيب:", self.selected_pump_installation)
        pump_info_layout.addRow("الحالة:", self.selected_pump_status)
        
        details_layout.addWidget(pump_info_group)
        
        # الحساسات المرتبطة
        sensors_group = QGroupBox("الحساسات المرتبطة")
        sensors_layout = QVBoxLayout(sensors_group)
        
        self.sensors_list = QListWidget()
        sensors_layout.addWidget(self.sensors_list)
        
        # أزرار إدارة الحساسات
        sensors_buttons_layout = QHBoxLayout()
        
        self.add_sensor_btn = QPushButton("إضافة حساس")
        self.add_sensor_btn.clicked.connect(self.show_add_sensor_dialog)
        sensors_buttons_layout.addWidget(self.add_sensor_btn)
        
        self.remove_sensor_btn = QPushButton("إزالة حساس")
        self.remove_sensor_btn.clicked.connect(self.remove_sensor)
        sensors_buttons_layout.addWidget(self.remove_sensor_btn)
        
        sensors_buttons_layout.addStretch()
        sensors_layout.addLayout(sensors_buttons_layout)
        
        details_layout.addWidget(sensors_group)
        
        splitter.addWidget(details_group)
        
        # تعيين نسب التقسيم
        splitter.setSizes([400, 300])
        layout.addWidget(splitter)
        
        return widget
    
    def create_schedule_tab(self):
        """إنشاء تبويب جدول الصيانة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # جدول الصيانة المجدولة
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(7)
        self.schedule_table.setHorizontalHeaderLabels([
            "المعرف", "المضخة", "نوع الصيانة", "التاريخ المجدول",
            "الحالة", "الفني", "الإجراءات"
        ])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.schedule_table)
        
        # إحصائيات الصيانة
        stats_layout = QHBoxLayout()
        
        self.maintenance_stats_group = QGroupBox("إحصائيات الصيانة")
        stats_inner_layout = QGridLayout(self.maintenance_stats_group)
        
        self.scheduled_count = QLabel("0")
        self.in_progress_count = QLabel("0")
        self.completed_count = QLabel("0")
        self.overdue_count = QLabel("0")
        
        stats_inner_layout.addWidget(QLabel("المجداولة:"), 0, 0)
        stats_inner_layout.addWidget(self.scheduled_count, 0, 1)
        stats_inner_layout.addWidget(QLabel("قيد التنفيذ:"), 0, 2)
        stats_inner_layout.addWidget(self.in_progress_count, 0, 3)
        stats_inner_layout.addWidget(QLabel("المكتملة:"), 1, 0)
        stats_inner_layout.addWidget(self.completed_count, 1, 1)
        stats_inner_layout.addWidget(QLabel("المتأخرة:"), 1, 2)
        stats_inner_layout.addWidget(self.overdue_count, 1, 3)
        
        stats_layout.addWidget(self.maintenance_stats_group)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        return widget
    
    def create_history_tab(self):
        """إنشاء تبويب سجل الصيانة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # فلتر السجل
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("من:"))
        self.history_date_from = QDateEdit()
        self.history_date_from.setDate(QDate.currentDate().addMonths(-6))
        self.history_date_from.setCalendarPopup(True)
        filter_layout.addWidget(self.history_date_from)
        
        filter_layout.addWidget(QLabel("إلى:"))
        self.history_date_to = QDateEdit()
        self.history_date_to.setDate(QDate.currentDate())
        self.history_date_to.setCalendarPopup(True)
        filter_layout.addWidget(self.history_date_to)
        
        self.filter_btn = QPushButton("تصفية")
        self.filter_btn.clicked.connect(self.load_maintenance_history)
        filter_layout.addWidget(self.filter_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # جدول سجل الصيانة
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "المعرف", "المضخة", "نوع الصيانة", "التاريخ المجدول",
            "تاريخ الإنجاز", "التكلفة", "الأجزاء المستبدلة", "الفني"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.history_table)
        
        return widget
    
    def create_predictive_tab(self):
        """إنشاء تبويب التحليل الوقائي"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # توصيات الصيانة الوقائية
        recommendations_group = QGroupBox("توصيات الصيانة الوقائية")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(self.recommendations_text)
        
        layout.addWidget(recommendations_group)
        
        # تحليل تكاليف الصيانة
        cost_analysis_group = QGroupBox("تحليل تكاليف الصيانة")
        cost_layout = QVBoxLayout(cost_analysis_group)
        
        self.cost_analysis_text = QTextEdit()
        self.cost_analysis_text.setReadOnly(True)
        cost_layout.addWidget(self.cost_analysis_text)
        
        layout.addWidget(cost_analysis_group)
        
        return widget
    
    def load_maintenance_data(self):
        """تحميل بيانات الصيانة"""
        self.load_pumps()
        self.load_pumps_list()
        self.load_maintenance_schedule()
        self.load_maintenance_history()
        self.update_predictive_analysis()
        self.update_maintenance_stats()
    
    def load_pumps(self):
        """تحميل قائمة المضخات للكومبوبوكس"""
        pumps = db_manager.get_pumps()
        self.pump_selector.clear()
        
        for _, pump in pumps.iterrows():
            self.pump_selector.addItem(pump['name'], pump['id'])
    
    def load_pumps_list(self):
        """تحميل قائمة المضخات للجدول"""
        try:
            pumps = db_manager.get_pumps()
            self.pumps_table.setRowCount(len(pumps))
            
            for row, (_, pump) in enumerate(pumps.iterrows()):
                self.pumps_table.setItem(row, 0, QTableWidgetItem(str(pump['id'])))
                self.pumps_table.setItem(row, 1, QTableWidgetItem(pump['name']))
                self.pumps_table.setItem(row, 2, QTableWidgetItem(pump['location']))
                self.pumps_table.setItem(row, 3, QTableWidgetItem(pump['type']))
                self.pumps_table.setItem(row, 4, QTableWidgetItem(pump['installation_date']))
                
                status_item = QTableWidgetItem(pump['status'])
                if pump['status'] == 'operational':
                    status_item.setBackground(QColor(81, 207, 102, 100))
                    status_item.setText("تعمل")
                elif pump['status'] == 'maintenance':
                    status_item.setBackground(QColor(255, 179, 0, 100))
                    status_item.setText("صيانة")
                else:
                    status_item.setBackground(QColor(255, 107, 107, 100))
                    status_item.setText("متوقفة")
                
                self.pumps_table.setItem(row, 5, status_item)
                
        except Exception as e:
            print(f"خطأ في تحميل قائمة المضخات: {e}")
    
    def on_pump_changed(self, index):
        """عند تغيير المضخة المحددة"""
        if index >= 0:
            self.load_maintenance_schedule()
    
    def on_pump_double_clicked(self, index):
        """عند النقر المزدوج على مضخة في الجدول"""
        row = index.row()
        pump_id = self.pumps_table.item(row, 0).text()
        self.load_pump_details(int(pump_id))
    
    def load_pump_details(self, pump_id):
        """تحميل تفاصيل المضخة المحددة"""
        try:
            pumps = db_manager.get_pumps()
            pump = pumps[pumps['id'] == pump_id].iloc[0]
            
            self.selected_pump_name.setText(pump['name'])
            self.selected_pump_location.setText(pump['location'])
            self.selected_pump_type.setText(pump['type'])
            self.selected_pump_installation.setText(pump['installation_date'])
            
            status_text = "تعمل" if pump['status'] == 'operational' else "صيانة" if pump['status'] == 'maintenance' else "متوقفة"
            status_color = "#51cf66" if pump['status'] == 'operational' else "#f59f00" if pump['status'] == 'maintenance' else "#ff6b6b"
            
            self.selected_pump_status.setText(status_text)
            self.selected_pump_status.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            
            # تحميل الحساسات المرتبطة
            self.load_pump_sensors(pump_id)
            
        except Exception as e:
            print(f"خطأ في تحميل تفاصيل المضخة: {e}")
    
    def load_pump_sensors(self, pump_id):
        """تحميل الحساسات المرتبطة بالمضخة"""
        try:
            self.sensors_list.clear()
            
            # محاكاة بيانات الحساسات (في التطبيق الحقيقي، سيتم جلبها من قاعدة البيانات)
            sample_sensors = [
                f"حساس الاهتزاز X (SENSOR_VIB_X_{pump_id})",
                f"حساس الاهتزاز Y (SENSOR_VIB_Y_{pump_id})",
                f"حساس الاهتزاز Z (SENSOR_VIB_Z_{pump_id})",
                f"حساس درجة الحرارة (SENSOR_TEMP_{pump_id})",
                f"حساس الضغط (SENSOR_PRESS_{pump_id})",
                f"حساس التدفق (SENSOR_FLOW_{pump_id})",
                f"حساس مستوى الزيت (SENSOR_OIL_{pump_id})"
            ]
            
            for sensor in sample_sensors:
                item = QListWidgetItem(sensor)
                item.setData(Qt.ItemDataRole.UserRole, pump_id)
                self.sensors_list.addItem(item)
                
        except Exception as e:
            print(f"خطأ في تحميل الحساسات: {e}")
    
    def show_add_pump_dialog(self):
        """عرض نافذة إضافة مضخة جديدة"""
        dialog = AddPumpDialog(self)
        if dialog.exec():
            self.load_maintenance_data()
            QMessageBox.information(self, "تم", "تم إضافة المضخة بنجاح")
    
    def show_link_sensors_dialog(self):
        """عرض نافذة ربط الحساسات"""
        dialog = LinkSensorsDialog(self)
        if dialog.exec():
            QMessageBox.information(self, "تم", "تم ربط الحساسات بنجاح")
    
    def show_add_sensor_dialog(self):
        """عرض نافذة إضافة حساس"""
        if self.sensors_list.count() == 0:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد مضخة أولاً")
            return
        
        dialog = AddSensorDialog(self)
        if dialog.exec():
            # إعادة تحميل الحساسات للمضخة المحددة
            current_item = self.sensors_list.currentItem()
            if current_item:
                pump_id = current_item.data(Qt.ItemDataRole.UserRole)
                self.load_pump_sensors(pump_id)
    
    def remove_sensor(self):
        """إزالة الحساس المحدد"""
        current_item = self.sensors_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد حساس لإزالته")
            return
        
        sensor_name = current_item.text()
        reply = QMessageBox.question(
            self, 
            "تأكيد الإزالة", 
            f"هل تريد إزالة الحساس '{sensor_name}'؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            row = self.sensors_list.row(current_item)
            self.sensors_list.takeItem(row)
            QMessageBox.information(self, "تم", "تم إزالة الحساس بنجاح")
    
    def export_pumps_data(self):
        """تصدير بيانات المضخات"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "تصدير بيانات المضخات", 
                f"pumps_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "CSV Files (*.csv)"
            )
            
            if file_path:
                pumps = db_manager.get_pumps()
                pumps.to_csv(file_path, index=False, encoding='utf-8')
                QMessageBox.information(self, "تم", f"تم تصدير البيانات إلى: {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تصدير البيانات: {e}")
    
    # باقي الدوال تبقى كما هي (مع بعض التعديلات الطفيفة)
    def load_maintenance_schedule(self):
        """تحميل جدول الصيانة"""
        try:
            # محاكاة بيانات الصيانة المجدولة
            sample_schedule = [
                (1, "مضخة المصفاة الرئيسية", "صيانة دورية", "2024-01-15", "مجدولة", "أحمد محمد", ""),
                (2, "مضخة النقل رقم 1", "استبدال زيت", "2024-01-20", "قيد التنفيذ", "محمد علي", ""),
                (3, "مضخة التغذية الرئيسية", "فحص محامل", "2024-01-25", "مجدولة", "فادي أحمد", ""),
                (4, "مضخة الخدمة المساعدة", "تنظيف فلاتر", "2024-02-01", "متأخرة", "خالد حسن", "")
            ]
            
            self.schedule_table.setRowCount(len(sample_schedule))
            
            for row, (id, pump, mtype, date, status, technician, actions) in enumerate(sample_schedule):
                self.schedule_table.setItem(row, 0, QTableWidgetItem(str(id)))
                self.schedule_table.setItem(row, 1, QTableWidgetItem(pump))
                self.schedule_table.setItem(row, 2, QTableWidgetItem(mtype))
                self.schedule_table.setItem(row, 3, QTableWidgetItem(date))
                
                status_item = QTableWidgetItem(status)
                if status == "متأخرة":
                    status_item.setBackground(QColor(255, 107, 107, 100))
                elif status == "قيد التنفيذ":
                    status_item.setBackground(QColor(255, 179, 0, 100))
                elif status == "مجدولة":
                    status_item.setBackground(QColor(81, 207, 102, 100))
                
                self.schedule_table.setItem(row, 4, status_item)
                self.schedule_table.setItem(row, 5, QTableWidgetItem(technician))
                
                # أزرار الإجراءات
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                
                if status == "مجدولة":
                    start_btn = QPushButton("بدء")
                    start_btn.clicked.connect(lambda checked, r=row: self.start_maintenance(r))
                    actions_layout.addWidget(start_btn)
                
                complete_btn = QPushButton("إكمال")
                complete_btn.clicked.connect(lambda checked, r=row: self.complete_maintenance(r))
                actions_layout.addWidget(complete_btn)
                
                delete_btn = QPushButton("حذف")
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_maintenance(r))
                actions_layout.addWidget(delete_btn)
                
                actions_layout.setContentsMargins(0, 0, 0, 0)
                self.schedule_table.setCellWidget(row, 6, actions_widget)
                
        except Exception as e:
            print(f"خطأ في تحميل جدول الصيانة: {e}")
    
    def load_maintenance_history(self):
        """تحميل سجل الصيانة"""
        try:
            # محاكاة سجل الصيانة
            sample_history = [
                (1, "مضخة المصفاة الرئيسية", "صيانة دورية", "2023-12-15", "2023-12-15", "1500", "فلتر زيت، شمعات", "أحمد محمد"),
                (2, "مضخة النقل رقم 1", "استبدال محامل", "2023-11-20", "2023-11-21", "3500", "محامل، أختام", "محمد علي"),
                (3, "مضخة التغذية الرئيسية", "تنظيف نظام", "2023-10-10", "2023-10-10", "800", "مواد تنظيف", "فادي أحمد"),
                (4, "مضخة الخدمة المساعدة", "صيانة وقائية", "2023-09-05", "2023-09-05", "1200", "زيت، فلاتر", "خالد حسن")
            ]
            
            self.history_table.setRowCount(len(sample_history))
            
            for row, (id, pump, mtype, scheduled, completed, cost, parts, technician) in enumerate(sample_history):
                self.history_table.setItem(row, 0, QTableWidgetItem(str(id)))
                self.history_table.setItem(row, 1, QTableWidgetItem(pump))
                self.history_table.setItem(row, 2, QTableWidgetItem(mtype))
                self.history_table.setItem(row, 3, QTableWidgetItem(scheduled))
                self.history_table.setItem(row, 4, QTableWidgetItem(completed))
                self.history_table.setItem(row, 5, QTableWidgetItem(cost))
                self.history_table.setItem(row, 6, QTableWidgetItem(parts))
                self.history_table.setItem(row, 7, QTableWidgetItem(technician))
                
        except Exception as e:
            print(f"خطأ في تحميل سجل الصيانة: {e}")
    
    def update_predictive_analysis(self):
        """تحديث التحليل الوقائي"""
        try:
            # توليد توصيات الصيانة الوقائية
            recommendations = [
                "• فحص وتغيير زيت المضخة كل 2000 ساعة تشغيل",
                "• تنظيف الفلاتر كل 500 ساعة تشغيل",
                "• فحص المحامل والاهتزازات أسبوعياً",
                "• معايرة أجهزة الاستشعار شهرياً",
                "• فحص نظام التبريد والتهوية أسبوعياً"
            ]
            
            recommendations_text = "التوصيات الوقائية:\n\n" + "\n".join(recommendations)
            self.recommendations_text.setText(recommendations_text)
            
            # تحليل التكاليف
            cost_analysis = """
تحليل تكاليف الصيانة:

• متوسط تكلفة الصيانة الدورية: 1,200 ريال
• متوسط تكلفة الإصلاحات الطارئة: 3,500 ريال
• توفير وقائي محتمل: 40% من تكاليف الإصلاحات الطارئة
• العمر الافتراضي المتوقع للمضخات: 5 سنوات مع الصيانة الوقائية

التوصية: تنفيذ برنامج الصيانة الوقائية يمكن أن يخفض التكاليف بنسبة 25%
            """
            
            self.cost_analysis_text.setText(cost_analysis)
            
        except Exception as e:
            print(f"خطأ في تحديث التحليل الوقائي: {e}")
    
    def update_maintenance_stats(self):
        """تحديث إحصائيات الصيانة"""
        try:
            # محاكاة الإحصائيات
            self.scheduled_count.setText("3")
            self.in_progress_count.setText("1")
            self.completed_count.setText("12")
            self.overdue_count.setText("1")
            
        except Exception as e:
            print(f"خطأ في تحديث إحصائيات الصيانة: {e}")
    
    def show_add_maintenance_dialog(self):
        """عرض نافذة إضافة صيانة جديدة"""
        dialog = AddMaintenanceDialog(self)
        if dialog.exec():
            self.load_maintenance_schedule()
    
    def start_maintenance(self, row):
        """بدء عملية صيانة"""
        try:
            pump_name = self.schedule_table.item(row, 1).text()
            QMessageBox.information(self, "بدء الصيانة", f"تم بدء صيانة {pump_name}")
            
            # تحديث الحالة في الواجهة
            status_item = QTableWidgetItem("قيد التنفيذ")
            status_item.setBackground(QColor(255, 179, 0, 100))
            self.schedule_table.setItem(row, 4, status_item)
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في بدء الصيانة: {e}")
    
    def complete_maintenance(self, row):
        """إكمال عملية صيانة"""
        try:
            pump_name = self.schedule_table.item(row, 1).text()
            
            reply = QMessageBox.question(self, "إكمال الصيانة",
                                       f"هل تريد تأكيد إكمال صيانة {pump_name}؟",
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                QMessageBox.information(self, "تم الإكمال", f"تم إكمال صيانة {pump_name}")
                # إزالة من الجدول وإضافة إلى السجل
                self.schedule_table.removeRow(row)
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في إكمال الصيانة: {e}")
    
    def delete_maintenance(self, row):
        """حذف عملية صيانة"""
        try:
            pump_name = self.schedule_table.item(row, 1).text()
            
            reply = QMessageBox.question(self, "حذف الصيانة",
                                       f"هل تريد تأكيد حذف صيانة {pump_name}؟",
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.schedule_table.removeRow(row)
                QMessageBox.information(self, "تم الحذف", f"تم حذف صيانة {pump_name}")
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في حذف الصيانة: {e}")
    
    def refresh_data(self):
        """تحديث البيانات"""
        self.load_maintenance_data()

class AddPumpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة مضخة جديدة")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        """تهيئة واجهة إضافة مضخة"""
        layout = QFormLayout(self)
        
        # حقل اسم المضخة
        self.pump_name = QLineEdit()
        self.pump_name.setPlaceholderText("أدخل اسم المضخة")
        layout.addRow("اسم المضخة:", self.pump_name)
        
        # حقل الموقع
        self.pump_location = QLineEdit()
        self.pump_location.setPlaceholderText("أدخل موقع المضخة")
        layout.addRow("الموقع:", self.pump_location)
        
        # حقل النوع
        self.pump_type = QComboBox()
        self.pump_type.addItems(["طرد مركزي", "مكبسية", "تغذية", "خدمة مساعدة", "نقل"])
        layout.addRow("نوع المضخة:", self.pump_type)
        
        # حقل تاريخ التركيب
        self.installation_date = QDateEdit()
        self.installation_date.setDate(QDate.currentDate())
        self.installation_date.setCalendarPopup(True)
        layout.addRow("تاريخ التركيب:", self.installation_date)
        
        # حقل الحالة
        self.pump_status = QComboBox()
        self.pump_status.addItems(["تعمل", "صيانة", "متوقفة"])
        layout.addRow("الحالة:", self.pump_status)
        
        # حقل معلومات إضافية
        self.pump_notes = QTextEdit()
        self.pump_notes.setMaximumHeight(100)
        self.pump_notes.setPlaceholderText("ملاحظات إضافية عن المضخة...")
        layout.addRow("ملاحظات:", self.pump_notes)
        
        # أزرار الحفظ والإلغاء
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
    def get_pump_data(self):
        """الحصول على بيانات المضخة المدخلة"""
        return {
            'name': self.pump_name.text(),
            'location': self.pump_location.text(),
            'type': self.pump_type.currentText(),
            'installation_date': self.installation_date.date().toString("yyyy-MM-dd"),
            'status': 'operational' if self.pump_status.currentText() == "تعمل" else 'maintenance' if self.pump_status.currentText() == "صيانة" else 'stopped',
            'notes': self.pump_notes.toPlainText()
        }
    
    def accept(self):
        """عند النقر على موافق"""
        if not self.pump_name.text().strip():
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم المضخة")
            return
        
        if not self.pump_location.text().strip():
            QMessageBox.warning(self, "تحذير", "يرجى إدخال موقع المضخة")
            return
        
        super().accept()

class LinkSensorsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ربط الحساسات بالمضخات")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        """تهيئة واجهة ربط الحساسات"""
        layout = QVBoxLayout(self)
        
        # قسم اختيار المضخة
        pump_group = QGroupBox("اختيار المضخة")
        pump_layout = QFormLayout(pump_group)
        
        self.pump_selector = QComboBox()
        # تحميل المضخات من قاعدة البيانات
        pumps = db_manager.get_pumps()
        for _, pump in pumps.iterrows():
            self.pump_selector.addItem(pump['name'], pump['id'])
        
        pump_layout.addRow("المضخة:", self.pump_selector)
        layout.addWidget(pump_group)
        
        # قسم الحساسات المتاحة
        sensors_group = QGroupBox("الحساسات المتاحة للربط")
        sensors_layout = QVBoxLayout(sensors_group)
        
        # قائمة الحساسات
        self.sensors_list = QListWidget()
        
        # إضافة أنواع الحساسات المتاحة
        available_sensors = [
            "حساس الاهتزاز X - قياس الاهتزاز في المحور X",
            "حساس الاهتزاز Y - قياس الاهتزاز في المحور Y", 
            "حساس الاهتزاز Z - قياس الاهتزاز في المحور Z",
            "حساس درجة الحرارة - قياس درجة حرارة المضخة",
            "حساس الضغط - قياس ضغط التشغيل",
            "حساس التدفق - قياس معدل التدفق",
            "حساس مستوى الزيت - قياس مستوى زيت التشحيم",
            "حساس جودة الزيت - قياس جودة زيت التشحيم",
            "حساس استهلاك الطاقة - قياس استهلاك الطاقة",
            "حساس حرارة المحامل - قياس درجة حرارة المحامل"
        ]
        
        for sensor in available_sensors:
            item = QListWidgetItem(sensor)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.sensors_list.addItem(item)
        
        sensors_layout.addWidget(self.sensors_list)
        layout.addWidget(sensors_group)
        
        # قسم إعدادات الحساسات
        settings_group = QGroupBox("إعدادات الحساس")
        settings_layout = QFormLayout(settings_group)
        
        self.sensor_id = QLineEdit()
        self.sensor_id.setPlaceholderText("سيتم توليده تلقائياً")
        settings_layout.addRow("معرف الحساس:", self.sensor_id)
        
        self.sampling_rate = QSpinBox()
        self.sampling_rate.setRange(1, 1000)
        self.sampling_rate.setValue(10)
        self.sampling_rate.setSuffix(" هرتز")
        settings_layout.addRow("معدل أخذ العينات:", self.sampling_rate)
        
        self.calibration_date = QDateEdit()
        self.calibration_date.setDate(QDate.currentDate())
        self.calibration_date.setCalendarPopup(True)
        settings_layout.addRow("تاريخ المعايرة:", self.calibration_date)
        
        layout.addWidget(settings_group)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("تحديد الكل")
        self.select_all_btn.clicked.connect(self.select_all_sensors)
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("إلغاء التحديد")
        self.deselect_all_btn.clicked.connect(self.deselect_all_sensors)
        button_layout.addWidget(self.deselect_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # أزرار الحفظ والإلغاء
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def select_all_sensors(self):
        """تحديد جميع الحساسات"""
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def deselect_all_sensors(self):
        """إلغاء تحديد جميع الحساسات"""
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
    
    def get_selected_sensors(self):
        """الحصول على الحساسات المحددة"""
        selected_sensors = []
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_sensors.append(item.text())
        return selected_sensors
    
    def accept(self):
        """عند النقر على موافق"""
        selected_sensors = self.get_selected_sensors()
        if not selected_sensors:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد حساس واحد على الأقل")
            return
        
        pump_name = self.pump_selector.currentText()
        pump_id = self.pump_selector.currentData()
        
        # عرض ملخص الربط
        summary = f"""
        ملخص عملية الربط:
        
        المضخة: {pump_name}
        عدد الحساسات المحددة: {len(selected_sensors)}
        معدل أخذ العينات: {self.sampling_rate.value()} هرتز
        تاريخ المعايرة: {self.calibration_date.date().toString("yyyy-MM-dd")}
        
        الحساسات المحددة:
        {chr(10).join(['• ' + sensor for sensor in selected_sensors])}
        """
        
        reply = QMessageBox.question(
            self, 
            "تأكيد الربط", 
            summary + "\nهل تريد متابعة عملية الربط؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # هنا سيتم تنفيذ عملية الربط الفعلية مع قاعدة البيانات
            super().accept()

class AddSensorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة حساس جديد")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        """تهيئة واجهة إضافة حساس"""
        layout = QFormLayout(self)
        
        # نوع الحساس
        self.sensor_type = QComboBox()
        self.sensor_type.addItems([
            "اهتزاز X", "اهتزاز Y", "اهتزاز Z",
            "درجة حرارة", "ضغط", "تدفق",
            "مستوى زيت", "جودة زيت", "استهلاك طاقة",
            "حرارة محامل"
        ])
        layout.addRow("نوع الحساس:", self.sensor_type)
        
        # معرف الحساس
        self.sensor_id = QLineEdit()
        self.sensor_id.setPlaceholderText("مثال: SENSOR_VIB_X_001")
        layout.addRow("معرف الحساس:", self.sensor_id)
        
        # النموذج
        self.sensor_model = QLineEdit()
        self.sensor_model.setPlaceholderText("مثال: VIB-1000X")
        layout.addRow("النموذج:", self.sensor_model)
        
        # الشركة المصنعة
        self.sensor_manufacturer = QLineEdit()
        self.sensor_manufacturer.setPlaceholderText("مثال: Siemens")
        layout.addRow("الشركة المصنعة:", self.sensor_manufacturer)
        
        # نطاق القياس
        self.measurement_range = QLineEdit()
        self.measurement_range.setPlaceholderText("مثال: 0-100 m/s²")
        layout.addRow("نطاق القياس:", self.measurement_range)
        
        # الدقة
        self.accuracy = QLineEdit()
        self.accuracy.setPlaceholderText("مثال: ±0.5%")
        layout.addRow("الدقة:", self.accuracy)
        
        # تاريخ التركيب
        self.installation_date = QDateEdit()
        self.installation_date.setDate(QDate.currentDate())
        self.installation_date.setCalendarPopup(True)
        layout.addRow("تاريخ التركيب:", self.installation_date)
        
        # أزرار الحفظ والإلغاء
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def accept(self):
        """عند النقر على موافق"""
        if not self.sensor_id.text().strip():
            QMessageBox.warning(self, "تحذير", "يرجى إدخال معرف الحساس")
            return
        
        if not self.sensor_model.text().strip():
            QMessageBox.warning(self, "تحذير", "يرجى إدخال نموذج الحساس")
            return
        
        super().accept()

class AddMaintenanceDialog(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة صيانة جديدة")
        self.setText("سيتم تطوير نافذة إضافة صيانة جديدة في النسخة القادمة")
        self.setInformativeText("هذه الميزة قيد التطوير حالياً")
        self.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)