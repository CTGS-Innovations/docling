import logging
import sys
from datetime import datetime
from typing import List

def setup_logger(name: str) -> logging.Logger:
    """Setup a clean, readable logger"""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create console handler with custom formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Custom formatter for clean, readable logs
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-5s | %(name)-20s | %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger

class LogCapture:
    """Capture logs for real-time display in frontend"""
    
    def __init__(self):
        self.logs: List[str] = []
        self.start_time = datetime.now()
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add a log entry with timestamp"""
        timestamp = datetime.now()
        elapsed = (timestamp - self.start_time).total_seconds()
        
        log_entry = f"[+{elapsed:06.3f}s] {message}"
        self.logs.append(log_entry)
        
        # Keep only last 100 logs to prevent memory issues
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
    
    def get_logs(self) -> List[str]:
        """Get all captured logs"""
        return self.logs.copy()
    
    def clear(self):
        """Clear all logs"""
        self.logs = []
        self.start_time = datetime.now()