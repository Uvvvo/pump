"""User interface package for the iPump application."""

from .main_window import MainWindow
from .dashboard import DashboardTab
from .analytics import AnalyticsTab
from .maintenance import MaintenanceTab
from .reporting import ReportingTab
from .settings import SettingsTab

__all__ = [
    'MainWindow',
    'DashboardTab', 
    'AnalyticsTab',
    'MaintenanceTab',
    'ReportingTab',
    'SettingsTab'
]