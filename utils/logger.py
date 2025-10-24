"""
Logging system for the iPump application.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config import LOGS_DIR

def setup_logger(name: str = "iPump") -> logging.Logger:
    """Configure and initialize the logging system."""

    # Create the logger instance
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate configuration when the logger already exists
    if logger.handlers:
        return logger

    # Format log messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = LOGS_DIR / f"ipump_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "iPump") -> logging.Logger:
    """Return a previously configured logger."""
    return logging.getLogger(name)
