"""
Centralized logging configuration for MVP-Fusion.
Provides structured logging with multiple verbosity levels.
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime


class FusionLogLevel:
    """Custom log levels for fusion-specific messages."""
    PERFORMANCE = 35  # Between INFO (20) and WARNING (30)
    STAGE = 25        # Between INFO and PERFORMANCE
    ENTITY = 15       # Between DEBUG (10) and INFO (20)
    

def setup_logging(
    verbosity: int = 0,
    log_file: Optional[Path] = None,
    use_colors: bool = True,
    json_format: bool = False
) -> None:
    """
    Configure logging for the entire application.
    
    Args:
        verbosity: Verbosity level
            0: QUIET (ERROR only + critical performance metrics)
            1: NORMAL (INFO + stage progress)
            2: VERBOSE (DEBUG + detailed metrics)
            3: DEBUG (Everything including entity processing)
        log_file: Optional file path for logging output
        use_colors: Whether to use colored output in terminal
        json_format: Use JSON structured logging (for production)
    """
    # Add custom levels
    logging.addLevelName(FusionLogLevel.PERFORMANCE, "PERF")
    logging.addLevelName(FusionLogLevel.STAGE, "STAGE")
    logging.addLevelName(FusionLogLevel.ENTITY, "ENTITY")
    
    # Map verbosity to log levels
    level_map = {
        0: logging.WARNING,     # QUIET: Errors and critical info only
        1: FusionLogLevel.STAGE, # NORMAL: Stage progress + important info
        2: FusionLogLevel.ENTITY,# VERBOSE: Detailed processing info
        3: logging.DEBUG         # DEBUG: Everything
    }
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level_map.get(verbosity, logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = create_console_formatter(verbosity, use_colors)
    
    # Console handler (with colors if enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified) - ALWAYS without colors for clean files
    if log_file:
        file_handler = logging.FileHandler(log_file)
        # Create clean formatter without ANSI colors for file output
        file_formatter = create_console_formatter(verbosity, use_colors=False)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_module_loggers(verbosity)


def create_console_formatter(verbosity: int, use_colors: bool) -> logging.Formatter:
    """
    Create a console formatter based on verbosity level.
    
    Args:
        verbosity: Current verbosity level
        use_colors: Whether to use ANSI colors
    
    Returns:
        Configured formatter
    """
    if verbosity == 0:  # QUIET
        # Minimal format - just the message
        format_str = '%(message)s'
    elif verbosity == 1:  # NORMAL
        # Include emoji indicators for different message types
        format_str = '%(message)s'
    elif verbosity == 2:  # VERBOSE
        # Add component names
        format_str = '[%(name)s] %(message)s'
    else:  # DEBUG
        # Full details
        format_str = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    
    if use_colors:
        return ColoredFormatter(format_str)
    else:
        return logging.Formatter(format_str, datefmt='%H:%M:%S')


class ColoredFormatter(logging.Formatter):
    """Formatter that adds colors to log output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'ENTITY': '\033[35m',      # Magenta
        'INFO': '\033[0m',         # Default
        'STAGE': '\033[32m',       # Green
        'PERF': '\033[33m',        # Yellow
        'WARNING': '\033[33m',     # Yellow
        'ERROR': '\033[31m',       # Red
        'CRITICAL': '\033[1;31m',  # Bold Red
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color codes
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            record.msg = f"{self.COLORS[levelname]}{record.msg}{self.RESET}"
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        import json
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)
        
        return json.dumps(log_obj)


def configure_module_loggers(verbosity: int) -> None:
    """
    Configure specific module loggers based on verbosity.
    
    Args:
        verbosity: Current verbosity level
    """
    # Suppress verbose third-party loggers unless in DEBUG
    if verbosity < 3:
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('pdfplumber').setLevel(logging.WARNING)
        logging.getLogger('pdfminer').setLevel(logging.WARNING)
        
    # Configure fusion module loggers
    if verbosity == 0:  # QUIET
        # Only show critical errors from submodules
        logging.getLogger('fusion').setLevel(logging.ERROR)
        logging.getLogger('pipeline').setLevel(logging.ERROR)
        logging.getLogger('knowledge').setLevel(logging.ERROR)
    elif verbosity == 1:  # NORMAL
        # Show important progress messages
        logging.getLogger('fusion').setLevel(FusionLogLevel.STAGE)
        logging.getLogger('pipeline').setLevel(FusionLogLevel.STAGE)
        logging.getLogger('knowledge').setLevel(logging.WARNING)
    elif verbosity == 2:  # VERBOSE
        # Show detailed metrics and entity counts
        logging.getLogger('fusion').setLevel(FusionLogLevel.ENTITY)
        logging.getLogger('pipeline').setLevel(FusionLogLevel.ENTITY)
        logging.getLogger('knowledge').setLevel(logging.INFO)


class LoggerAdapter:
    """
    Adapter for transitioning from print statements to logging.
    Provides methods that map common output patterns to appropriate log levels.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def stage(self, message: str, **kwargs) -> None:
        """Log a processing stage message."""
        from .worker_utils import get_worker_prefix
        self.logger.log(FusionLogLevel.STAGE, f"{get_worker_prefix()} {message}", **kwargs)
    
    def performance(self, message: str, metrics: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics."""
        extra = {'extra_fields': metrics} if metrics else {}
        self.logger.log(FusionLogLevel.PERFORMANCE, message, extra=extra)
    
    def entity(self, message: str, count: Optional[int] = None) -> None:
        """Log entity extraction details."""
        from .worker_utils import get_worker_prefix
        if count is not None:
            message = f"{message} ({count} items)"
        self.logger.log(FusionLogLevel.ENTITY, f"{get_worker_prefix()} {message}")
    
    def success(self, message: str) -> None:
        """Log success messages (maps to INFO)."""
        self.logger.info(f"✅ {message}")
    
    def progress(self, message: str) -> None:
        """Log progress updates."""
        self.logger.log(FusionLogLevel.STAGE, f"🔄 {message}")
    
    def summary(self, title: str, details: Dict[str, Any]) -> None:
        """Log a formatted summary."""
        lines = [f"📊 {title}:"]
        for key, value in details.items():
            lines.append(f"   {key}: {value}")
        self.logger.log(FusionLogLevel.PERFORMANCE, '\n'.join(lines))


def get_fusion_logger(name: str) -> LoggerAdapter:
    """
    Get a logger configured for fusion modules.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        LoggerAdapter with fusion-specific methods
    """
    logger = logging.getLogger(name)
    return LoggerAdapter(logger)


# Convenience functions for one-time logging
def log_performance(message: str, **metrics) -> None:
    """Log a performance message at the appropriate level."""
    logging.log(FusionLogLevel.PERFORMANCE, message, extra={'metrics': metrics})


def log_stage(message: str) -> None:
    """Log a stage/progress message."""
    logging.log(FusionLogLevel.STAGE, message)


def log_entity(message: str, count: Optional[int] = None) -> None:
    """Log entity-related information."""
    if count is not None:
        message = f"{message}: {count}"
    logging.log(FusionLogLevel.ENTITY, message)