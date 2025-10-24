"""
Maintenance management module for the iPump application with pump administration.
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
        """Set up the maintenance interface with pump management features."""
        main_layout = QVBoxLayout(self)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Pump:"))
        self.pump_selector = QComboBox()
        self.pump_selector.currentIndexChanged.connect(self.on_pump_changed)
        control_layout.addWidget(self.pump_selector)
        
        # New pump management buttons
        self.add_pump_btn = QPushButton("Add new pump")
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
        
        self.link_sensors_btn = QPushButton("Link sensors")
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
        
        self.add_maintenance_btn = QPushButton("Add new maintenance")
        self.add_maintenance_btn.clicked.connect(self.show_add_maintenance_dialog)
        control_layout.addWidget(self.add_maintenance_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_maintenance_data)
        control_layout.addWidget(self.refresh_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Maintenance tabs with the additional pump management tab
        self.maintenance_tabs = QTabWidget()
        
        # Pump management tab (new)
        self.pumps_management_tab = self.create_pumps_management_tab()
        self.maintenance_tabs.addTab(self.pumps_management_tab, "Pump management")
        
        # Maintenance schedule tab
        self.schedule_tab = self.create_schedule_tab()
        self.maintenance_tabs.addTab(self.schedule_tab, "Maintenance schedule")
        
        # Maintenance history tab
        self.history_tab = self.create_history_tab()
        self.maintenance_tabs.addTab(self.history_tab, "Maintenance history")
        
        # Preventive analysis tab
        self.predictive_tab = self.create_predictive_tab()
        self.maintenance_tabs.addTab(self.predictive_tab, "Preventive analysis")
        
        main_layout.addWidget(self.maintenance_tabs)
        
    def create_pumps_management_tab(self):
        """Create the pump management tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Split the view into two sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left section: pump list
        pumps_list_group = QGroupBox("Pump list")
        pumps_list_layout = QVBoxLayout(pumps_list_group)
        
        # Pump control buttons
        pumps_control_layout = QHBoxLayout()
        
        self.refresh_pumps_btn = QPushButton("Refresh list")
        self.refresh_pumps_btn.clicked.connect(self.load_pumps_list)
        pumps_control_layout.addWidget(self.refresh_pumps_btn)
        
        self.export_pumps_btn = QPushButton("Export data")
        self.export_pumps_btn.clicked.connect(self.export_pumps_data)
        pumps_control_layout.addWidget(self.export_pumps_btn)
        
        pumps_control_layout.addStretch()
        pumps_list_layout.addLayout(pumps_control_layout)
        
        # Pumps table
        self.pumps_table = QTableWidget()
        self.pumps_table.setColumnCount(6)
        self.pumps_table.setHorizontalHeaderLabels([
            "ID", "Pump name", "Location", "Type", 
            "Installation date", "Status"
        ])
        self.pumps_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pumps_table.doubleClicked.connect(self.on_pump_double_clicked)
        pumps_list_layout.addWidget(self.pumps_table)
        
        splitter.addWidget(pumps_list_group)
        
        # Right section: pump and sensor details
        details_group = QGroupBox("Pump and sensor details")
        details_layout = QVBoxLayout(details_group)
        
        # Pump information
        pump_info_group = QGroupBox("Pump information")
        pump_info_layout = QFormLayout(pump_info_group)
        
        self.selected_pump_name = QLabel("--")
        self.selected_pump_location = QLabel("--")
        self.selected_pump_type = QLabel("--")
        self.selected_pump_installation = QLabel("--")
        self.selected_pump_status = QLabel("--")
        
        pump_info_layout.addRow("Pump name:", self.selected_pump_name)
        pump_info_layout.addRow("Location:", self.selected_pump_location)
        pump_info_layout.addRow("Type:", self.selected_pump_type)
        pump_info_layout.addRow("Installation date:", self.selected_pump_installation)
        pump_info_layout.addRow("Status:", self.selected_pump_status)
        
        details_layout.addWidget(pump_info_group)
        
        # Linked sensors
        sensors_group = QGroupBox("Linked sensors")
        sensors_layout = QVBoxLayout(sensors_group)
        
        self.sensors_list = QListWidget()
        sensors_layout.addWidget(self.sensors_list)
        
        # Sensor management buttons
        sensors_buttons_layout = QHBoxLayout()
        
        self.add_sensor_btn = QPushButton("Add sensor")
        self.add_sensor_btn.clicked.connect(self.show_add_sensor_dialog)
        sensors_buttons_layout.addWidget(self.add_sensor_btn)
        
        self.remove_sensor_btn = QPushButton("Remove sensor")
        self.remove_sensor_btn.clicked.connect(self.remove_sensor)
        sensors_buttons_layout.addWidget(self.remove_sensor_btn)
        
        sensors_buttons_layout.addStretch()
        sensors_layout.addLayout(sensors_buttons_layout)
        
        details_layout.addWidget(sensors_group)
        
        splitter.addWidget(details_group)
        
        # Set splitter ratios
        splitter.setSizes([400, 300])
        layout.addWidget(splitter)
        
        return widget
    
    def create_schedule_tab(self):
        """Create the scheduled maintenance tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Maintenance schedule
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(7)
        self.schedule_table.setHorizontalHeaderLabels([
            "ID", "Pump", "Maintenance type", "Scheduled date",
            "Status", "Technician", "Actions"
        ])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.schedule_table)
        
        # Maintenance statistics
        stats_layout = QHBoxLayout()
        
        self.maintenance_stats_group = QGroupBox("Maintenance statistics")
        stats_inner_layout = QGridLayout(self.maintenance_stats_group)
        
        self.scheduled_count = QLabel("0")
        self.in_progress_count = QLabel("0")
        self.completed_count = QLabel("0")
        self.overdue_count = QLabel("0")
        
        stats_inner_layout.addWidget(QLabel("Scheduled:"), 0, 0)
        stats_inner_layout.addWidget(self.scheduled_count, 0, 1)
        stats_inner_layout.addWidget(QLabel("In progress:"), 0, 2)
        stats_inner_layout.addWidget(self.in_progress_count, 0, 3)
        stats_inner_layout.addWidget(QLabel("Completed:"), 1, 0)
        stats_inner_layout.addWidget(self.completed_count, 1, 1)
        stats_inner_layout.addWidget(QLabel("Overdue:"), 1, 2)
        stats_inner_layout.addWidget(self.overdue_count, 1, 3)
        
        stats_layout.addWidget(self.maintenance_stats_group)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        return widget
    
    def create_history_tab(self):
        """Create the maintenance history tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # History filters
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("From:"))
        self.history_date_from = QDateEdit()
        self.history_date_from.setDate(QDate.currentDate().addMonths(-6))
        self.history_date_from.setCalendarPopup(True)
        filter_layout.addWidget(self.history_date_from)
        
        filter_layout.addWidget(QLabel("To:"))
        self.history_date_to = QDateEdit()
        self.history_date_to.setDate(QDate.currentDate())
        self.history_date_to.setCalendarPopup(True)
        filter_layout.addWidget(self.history_date_to)
        
        self.filter_btn = QPushButton("Filter")
        self.filter_btn.clicked.connect(self.load_maintenance_history)
        filter_layout.addWidget(self.filter_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Maintenance history table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Pump", "Maintenance type", "Scheduled date",
            "Completion date", "Cost", "Replaced parts", "Technician"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.history_table)
        
        return widget
    
    def create_predictive_tab(self):
        """Create the preventive analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Preventive maintenance recommendations
        recommendations_group = QGroupBox("Preventive maintenance recommendations")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(self.recommendations_text)
        
        layout.addWidget(recommendations_group)
        
        # Maintenance cost analysis
        cost_analysis_group = QGroupBox("Maintenance cost analysis")
        cost_layout = QVBoxLayout(cost_analysis_group)
        
        self.cost_analysis_text = QTextEdit()
        self.cost_analysis_text.setReadOnly(True)
        cost_layout.addWidget(self.cost_analysis_text)
        
        layout.addWidget(cost_analysis_group)
        
        return widget
    
    def load_maintenance_data(self):
        """Load maintenance data."""
        self.load_pumps()
        self.load_pumps_list()
        self.load_maintenance_schedule()
        self.load_maintenance_history()
        self.update_predictive_analysis()
        self.update_maintenance_stats()
    
    def load_pumps(self):
        """Load pumps into the combo box."""
        pumps = db_manager.get_pumps()
        self.pump_selector.clear()
        
        for _, pump in pumps.iterrows():
            self.pump_selector.addItem(pump['name'], pump['id'])
    
    def load_pumps_list(self):
        """Load pumps into the table."""
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
                    status_item.setText("Operational")
                elif pump['status'] == 'maintenance':
                    status_item.setBackground(QColor(255, 179, 0, 100))
                    status_item.setText("Maintenance")
                else:
                    status_item.setBackground(QColor(255, 107, 107, 100))
                    status_item.setText("Stopped")
                
                self.pumps_table.setItem(row, 5, status_item)
                
        except Exception as e:
            print(f"Error loading pump list: {e}")
    
    def on_pump_changed(self, index):
        """Handle selected pump changes."""
        if index >= 0:
            self.load_maintenance_schedule()
    
    def on_pump_double_clicked(self, index):
        """Handle pump double-clicks in the table."""
        row = index.row()
        pump_id = self.pumps_table.item(row, 0).text()
        self.load_pump_details(int(pump_id))
    
    def load_pump_details(self, pump_id):
        """Load details for the selected pump."""
        try:
            pumps = db_manager.get_pumps()
            pump = pumps[pumps['id'] == pump_id].iloc[0]
            
            self.selected_pump_name.setText(pump['name'])
            self.selected_pump_location.setText(pump['location'])
            self.selected_pump_type.setText(pump['type'])
            self.selected_pump_installation.setText(pump['installation_date'])
            
            status_text = "Operational" if pump['status'] == 'operational' else "Maintenance" if pump['status'] == 'maintenance' else "Stopped"
            status_color = "#51cf66" if pump['status'] == 'operational' else "#f59f00" if pump['status'] == 'maintenance' else "#ff6b6b"
            
            self.selected_pump_status.setText(status_text)
            self.selected_pump_status.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            
            # Load linked sensors
            self.load_pump_sensors(pump_id)
            
        except Exception as e:
            print(f"Error loading pump details: {e}")
    
    def load_pump_sensors(self, pump_id):
        """Load sensors linked to the pump."""
        try:
            self.sensors_list.clear()
            
            # Simulate sensor data (replace with database queries in production)
            sample_sensors = [
                f"Sensor Vibration X (SENSOR_VIB_X_{pump_id})",
                f"Sensor Vibration Y (SENSOR_VIB_Y_{pump_id})",
                f"Sensor Vibration Z (SENSOR_VIB_Z_{pump_id})",
                f"Temperature sensor (SENSOR_TEMP_{pump_id})",
                f"Pressure sensor (SENSOR_PRESS_{pump_id})",
                f"Sensor Flow (SENSOR_FLOW_{pump_id})",
                f"Oil level sensor (SENSOR_OIL_{pump_id})"
            ]
            
            for sensor in sample_sensors:
                item = QListWidgetItem(sensor)
                item.setData(Qt.ItemDataRole.UserRole, pump_id)
                self.sensors_list.addItem(item)
                
        except Exception as e:
            print(f"Error loading sensors: {e}")
    
    def show_add_pump_dialog(self):
        """Show the add pump dialog."""
        dialog = AddPumpDialog(self)
        if dialog.exec():
            self.load_maintenance_data()
            QMessageBox.information(self, "Done", "Pump added successfully")
    
    def show_link_sensors_dialog(self):
        """Show the sensor linking dialog."""
        dialog = LinkSensorsDialog(self)
        if dialog.exec():
            QMessageBox.information(self, "Done", "Sensors linked successfully")
    
    def show_add_sensor_dialog(self):
        """Show the add sensor dialog."""
        if self.sensors_list.count() == 0:
            QMessageBox.warning(self, "Warning", "Please select a pump first")
            return
        
        dialog = AddSensorDialog(self)
        if dialog.exec():
            # Reload sensors for the selected pump
            current_item = self.sensors_list.currentItem()
            if current_item:
                pump_id = current_item.data(Qt.ItemDataRole.UserRole)
                self.load_pump_sensors(pump_id)
    
    def remove_sensor(self):
        """Remove the selected sensor."""
        current_item = self.sensors_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a sensor to remove")
            return
        
        sensor_name = current_item.text()
        reply = QMessageBox.question(
            self, 
            "Confirm removal", 
            f"Do you want to remove the sensor '{sensor_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            row = self.sensors_list.row(current_item)
            self.sensors_list.takeItem(row)
            QMessageBox.information(self, "Done", "Sensor removed successfully")
    
    def export_pumps_data(self):
        """Export pump data."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Export pump data", 
                f"pumps_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "CSV Files (*.csv)"
            )
            
            if file_path:
                pumps = db_manager.get_pumps()
                pumps.to_csv(file_path, index=False, encoding='utf-8')
                QMessageBox.information(self, "Done", f"Done Export data To: {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error exporting data: {e}")
    
    # Remaining methods stay the same with minor adjustments
    def load_maintenance_schedule(self):
        """Load the maintenance schedule."""
        try:
            # Simulate scheduled maintenance data
            sample_schedule = [
                (1, "Refinery main pump", "Routine maintenance", "2024-01-15", "Scheduled", "Ahmed Mohammed", ""),
                (2, "Transfer pump 1", "Oil replacement", "2024-01-20", "In progress", "Mohammed Ali", ""),
                (3, "Main feed pump", "Bearing inspection", "2024-01-25", "Scheduled", "Fadi Ahmed", ""),
                (4, "Auxiliary service pump", "Filter cleaning", "2024-02-01", "Overdue", "Khalid Hassan", "")
            ]
            
            self.schedule_table.setRowCount(len(sample_schedule))
            
            for row, (id, pump, mtype, date, status, technician, actions) in enumerate(sample_schedule):
                self.schedule_table.setItem(row, 0, QTableWidgetItem(str(id)))
                self.schedule_table.setItem(row, 1, QTableWidgetItem(pump))
                self.schedule_table.setItem(row, 2, QTableWidgetItem(mtype))
                self.schedule_table.setItem(row, 3, QTableWidgetItem(date))
                
                status_item = QTableWidgetItem(status)
                if status == "Overdue":
                    status_item.setBackground(QColor(255, 107, 107, 100))
                elif status == "In progress":
                    status_item.setBackground(QColor(255, 179, 0, 100))
                elif status == "Scheduled":
                    status_item.setBackground(QColor(81, 207, 102, 100))
                
                self.schedule_table.setItem(row, 4, status_item)
                self.schedule_table.setItem(row, 5, QTableWidgetItem(technician))
                
                # Action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                
                if status == "Scheduled":
                    start_btn = QPushButton("Start")
                    start_btn.clicked.connect(lambda checked, r=row: self.start_maintenance(r))
                    actions_layout.addWidget(start_btn)
                
                complete_btn = QPushButton("Complete")
                complete_btn.clicked.connect(lambda checked, r=row: self.complete_maintenance(r))
                actions_layout.addWidget(complete_btn)
                
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_maintenance(r))
                actions_layout.addWidget(delete_btn)
                
                actions_layout.setContentsMargins(0, 0, 0, 0)
                self.schedule_table.setCellWidget(row, 6, actions_widget)
                
        except Exception as e:
            print(f"Error loading maintenance schedule: {e}")
    
    def load_maintenance_history(self):
        """Load maintenance history"""
        try:
            # Simulate maintenance history
            sample_history = [
                (1, "Refinery main pump", "Routine maintenance", "2023-12-15", "2023-12-15", "1500", "Oil filter, cartridges", "Ahmed Mohammed"),
                (2, "Transfer pump 1", "Bearing replacement", "2023-11-20", "2023-11-21", "3500", "Bearings, seals", "Mohammed Ali"),
                (3, "Main feed pump", "System cleaning", "2023-10-10", "2023-10-10", "800", "Cleaning materials", "Fadi Ahmed"),
                (4, "Auxiliary service pump", "Preventive maintenance", "2023-09-05", "2023-09-05", "1200", "Oil, filters", "Khalid Hassan")
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
            print(f"Error loading maintenance history: {e}")
    
    def update_predictive_analysis(self):
        """Refresh the preventive analysis."""
        try:
            # Generate preventive maintenance recommendations
            recommendations = [
                "• Inspect and replace pump oil every 2000 operating hours",
                "• Clean filters every 500 operating hours",
                "• Inspect bearings and vibrations weekly",
                "• Calibrate sensors monthly",
                "• Check the cooling and ventilation system weekly"
            ]
            
            recommendations_text = "Preventive recommendations:\n\n" + "\n".join(recommendations)
            self.recommendations_text.setText(recommendations_text)
            
            # Analyze costs
            cost_analysis = """
Maintenance cost analysis:

• Average routine maintenance cost: 1,200 SAR
• Average emergency repair cost: 3,500 SAR
• Potential preventive savings: 40% of emergency repair costs
• Estimated pump lifespan: 5 years with preventive maintenance

Recommendation: Implementing the preventive maintenance program can reduce costs by 25%
            """
            
            self.cost_analysis_text.setText(cost_analysis)
            
        except Exception as e:
            print(f"Error refreshing preventive analysis: {e}")
    
    def update_maintenance_stats(self):
        """Refresh maintenance statistics."""
        try:
            # Simulate statistics
            self.scheduled_count.setText("3")
            self.in_progress_count.setText("1")
            self.completed_count.setText("12")
            self.overdue_count.setText("1")
            
        except Exception as e:
            print(f"Error refreshing maintenance statistics: {e}")
    
    def show_add_maintenance_dialog(self):
        """Show the add maintenance dialog."""
        dialog = AddMaintenanceDialog(self)
        if dialog.exec():
            self.load_maintenance_schedule()
    
    def start_maintenance(self, row):
        """Start a maintenance operation."""
        try:
            pump_name = self.schedule_table.item(row, 1).text()
            QMessageBox.information(self, "Start maintenance", f"Maintenance started for {pump_name}")
            
            # Refresh UI status
            status_item = QTableWidgetItem("In progress")
            status_item.setBackground(QColor(255, 179, 0, 100))
            self.schedule_table.setItem(row, 4, status_item)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error starting maintenance: {e}")
    
    def complete_maintenance(self, row):
        """Complete a maintenance operation."""
        try:
            pump_name = self.schedule_table.item(row, 1).text()
            
            reply = QMessageBox.question(self, "Complete maintenance",
                                       f"Confirm completing maintenance for {pump_name}?",
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                QMessageBox.information(self, "Completed", f"Maintenance for {pump_name} completed")
                # Remove from table and add to history
                self.schedule_table.removeRow(row)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error completing maintenance: {e}")
    
    def delete_maintenance(self, row):
        """Delete a maintenance operation."""
        try:
            pump_name = self.schedule_table.item(row, 1).text()
            
            reply = QMessageBox.question(self, "Delete maintenance",
                                       f"Confirm deleting maintenance for {pump_name}?",
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.schedule_table.removeRow(row)
                QMessageBox.information(self, "Deleted", f"Deleted maintenance for {pump_name}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error deleting maintenance: {e}")
    
    def refresh_data(self):
        """Refresh data."""
        self.load_maintenance_data()

class AddPumpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add new pump")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the add pump interface."""
        layout = QFormLayout(self)
        
        # Pump name field
        self.pump_name = QLineEdit()
        self.pump_name.setPlaceholderText("Enter pump name")
        layout.addRow("Pump name:", self.pump_name)
        
        # Location field
        self.pump_location = QLineEdit()
        self.pump_location.setPlaceholderText("Enter pump location")
        layout.addRow("Location:", self.pump_location)
        
        # Type field
        self.pump_type = QComboBox()
        self.pump_type.addItems(["Centrifugal", "Reciprocating", "Feed", "Service support", "Transfer"])
        layout.addRow("Pump type:", self.pump_type)
        
        # Installation date field
        self.installation_date = QDateEdit()
        self.installation_date.setDate(QDate.currentDate())
        self.installation_date.setCalendarPopup(True)
        layout.addRow("Installation date:", self.installation_date)
        
        # Status field
        self.pump_status = QComboBox()
        self.pump_status.addItems(["Operational", "Maintenance", "Stopped"])
        layout.addRow("Status:", self.pump_status)
        
        # Additional information field
        self.pump_notes = QTextEdit()
        self.pump_notes.setMaximumHeight(100)
        self.pump_notes.setPlaceholderText("Additional notes about the pump...")
        layout.addRow("Notes:", self.pump_notes)
        
        # Save and cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
    def get_pump_data(self):
        """Retrieve the entered pump data."""
        return {
            'name': self.pump_name.text(),
            'location': self.pump_location.text(),
            'type': self.pump_type.currentText(),
            'installation_date': self.installation_date.date().toString("yyyy-MM-dd"),
            'status': 'operational' if self.pump_status.currentText() == "Operational" else 'maintenance' if self.pump_status.currentText() == "Maintenance" else 'stopped',
            'notes': self.pump_notes.toPlainText()
        }
    
    def accept(self):
        """Handle confirmation clicks."""
        if not self.pump_name.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter a pump name")
            return
        
        if not self.pump_location.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter a pump location")
            return
        
        super().accept()

class LinkSensorsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Link sensors to pumps")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the sensor linking interface."""
        layout = QVBoxLayout(self)
        
        # Pump selection section
        pump_group = QGroupBox("Select pump")
        pump_layout = QFormLayout(pump_group)
        
        self.pump_selector = QComboBox()
        # Load pumps from the database
        pumps = db_manager.get_pumps()
        for _, pump in pumps.iterrows():
            self.pump_selector.addItem(pump['name'], pump['id'])
        
        pump_layout.addRow("Pump:", self.pump_selector)
        layout.addWidget(pump_group)
        
        # Available sensors section
        sensors_group = QGroupBox("Sensors available for linking")
        sensors_layout = QVBoxLayout(sensors_group)
        
        # Sensor list
        self.sensors_list = QListWidget()
        
        # Add available sensor types
        available_sensors = [
            "Sensor Vibration X - measures vibration on the X axis",
            "Sensor Vibration Y - measures vibration on the Y axis", 
            "Sensor Vibration Z - measures vibration on the Z axis",
            "Temperature sensor - measures pump temperature",
            "Pressure sensor - measures operating pressure",
            "Flow sensor - measures flow rate",
            "Oil level sensor - measures lubricant level",
            "Oil quality sensor - measures lubricant quality",
            "Energy consumption sensor - measures energy usage",
            "Bearing temperature sensor - measures bearing temperature"
        ]
        
        for sensor in available_sensors:
            item = QListWidgetItem(sensor)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.sensors_list.addItem(item)
        
        sensors_layout.addWidget(self.sensors_list)
        layout.addWidget(sensors_group)
        
        # Sensor settings section
        settings_group = QGroupBox("Sensor settings")
        settings_layout = QFormLayout(settings_group)
        
        self.sensor_id = QLineEdit()
        self.sensor_id.setPlaceholderText("Will be generated automatically")
        settings_layout.addRow("Sensor ID:", self.sensor_id)
        
        self.sampling_rate = QSpinBox()
        self.sampling_rate.setRange(1, 1000)
        self.sampling_rate.setValue(10)
        self.sampling_rate.setSuffix(" Hz")
        settings_layout.addRow("Sampling rate:", self.sampling_rate)
        
        self.calibration_date = QDateEdit()
        self.calibration_date.setDate(QDate.currentDate())
        self.calibration_date.setCalendarPopup(True)
        settings_layout.addRow("Calibration date:", self.calibration_date)
        
        layout.addWidget(settings_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Select all")
        self.select_all_btn.clicked.connect(self.select_all_sensors)
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Clear selection")
        self.deselect_all_btn.clicked.connect(self.deselect_all_sensors)
        button_layout.addWidget(self.deselect_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Save and cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def select_all_sensors(self):
        """Select all sensors."""
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def deselect_all_sensors(self):
        """Deselect all sensors."""
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
    
    def get_selected_sensors(self):
        """Retrieve the selected sensors."""
        selected_sensors = []
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_sensors.append(item.text())
        return selected_sensors
    
    def accept(self):
        """Handle confirmation clicks."""
        selected_sensors = self.get_selected_sensors()
        if not selected_sensors:
            QMessageBox.warning(self, "Warning", "Please select at least one sensor")
            return
        
        pump_name = self.pump_selector.currentText()
        pump_id = self.pump_selector.currentData()
        
        # Show link summary
        summary = f"""
        Link summary:
        
        Pump: {pump_name}
        Selected sensors: {len(selected_sensors)}
        Sampling rate: {self.sampling_rate.value()} Hz
        Calibration date: {self.calibration_date.date().toString("yyyy-MM-dd")}
        
        Selected sensors:
        {chr(10).join(['• ' + sensor for sensor in selected_sensors])}
        """
        
        reply = QMessageBox.question(
            self, 
            "Confirm linking", 
            summary + "\nDo you want to continue linking?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Execute the actual linking with the database here
            super().accept()

class AddSensorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add sensor")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the add sensor interface."""
        layout = QFormLayout(self)
        
        # Sensor type field
        self.sensor_type = QComboBox()
        self.sensor_type.addItems([
            "Vibration X", "Vibration Y", "Vibration Z",
            "Temperature", "Pressure", "Flow",
            "Oil level", "Oil quality", "Energy consumption",
            "Bearing temperature"
        ])
        layout.addRow("Sensor type:", self.sensor_type)
        
        # Sensor ID field
        self.sensor_id = QLineEdit()
        self.sensor_id.setPlaceholderText("Example: SENSOR_VIB_X_001")
        layout.addRow("Sensor ID:", self.sensor_id)
        
        # Model field
        self.sensor_model = QLineEdit()
        self.sensor_model.setPlaceholderText("Example: VIB-1000X")
        layout.addRow("Model:", self.sensor_model)
        
        # Manufacturer field
        self.sensor_manufacturer = QLineEdit()
        self.sensor_manufacturer.setPlaceholderText("Example: Siemens")
        layout.addRow("Manufacturer:", self.sensor_manufacturer)
        
        # Measurement range field
        self.measurement_range = QLineEdit()
        self.measurement_range.setPlaceholderText("Example: 0-100 m/s²")
        layout.addRow("Measurement range:", self.measurement_range)
        
        # Accuracy field
        self.accuracy = QLineEdit()
        self.accuracy.setPlaceholderText("Example: ±0.5%")
        layout.addRow("Accuracy:", self.accuracy)
        
        # Installation date
        self.installation_date = QDateEdit()
        self.installation_date.setDate(QDate.currentDate())
        self.installation_date.setCalendarPopup(True)
        layout.addRow("Installation date:", self.installation_date)
        
        # Save and cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def accept(self):
        """Handle confirmation clicks."""
        if not self.sensor_id.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter a sensor ID")
            return
        
        if not self.sensor_model.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter a sensor model")
            return
        
        super().accept()

class AddMaintenanceDialog(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add new maintenance")
        self.setText("The add maintenance window will be developed in the next release")
        self.setInformativeText("This feature is currently under development")
        self.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)