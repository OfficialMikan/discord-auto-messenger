"""
Logging System
"""
import os
from datetime import datetime
from typing import Optional


class Logger:
    """Handles application logging"""
    
    def __init__(self, log_file: str = "auto_log.txt"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True) if os.path.dirname(log_file) else None
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _write_log(self, level: str, message: str, console_only: bool = False):
        """Write log entry"""
        timestamped = f"[{self._get_timestamp()}] [{level}] {message}"
        print(timestamped)
        if not console_only:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(timestamped + "\n")
            except Exception:
                pass
    
    def info(self, message: str, console_only: bool = False):
        """Log info message"""
        self._write_log("INFO", message, console_only)
    
    def success(self, message: str, console_only: bool = False):
        """Log success message"""
        self._write_log("SUCCESS", message, console_only)
    
    def warning(self, message: str, console_only: bool = False):
        """Log warning message"""
        self._write_log("WARNING", message, console_only)
    
    def error(self, message: str, console_only: bool = False):
        """Log error message"""
        self._write_log("ERROR", message, console_only)


# Global logger instance
logger_instance = Logger()


def get_logger() -> Logger:
    """Get global logger instance"""
    return logger_instance
