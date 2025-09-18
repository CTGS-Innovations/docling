"""
Centralized logging configuration for MVP-Fusion.
Provides structured logging with multiple verbosity levels.
"""

import logging
import sys
import threading
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def get_system_metrics() -> str:
    """Get lightweight system metrics for queue handoff logging."""
    if not PSUTIL_AVAILABLE:
        return ""
    
    try:
        # Get non-blocking cached values
        ram_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking, uses cached value
        return f"ram: {ram_percent:.0f}%, cpu: {cpu_percent:.0f}%"
    except:
        return ""


class FusionLogLevel:
    """Custom log levels for fusion-specific messages."""
    PERFORMANCE = 35     # Between INFO (20) and WARNING (30)
    STAGING = 25         # Service coordination and pipeline phases
    CONVERSION = 24      # File operations and PDF conversion
    QUEUE = 23           # Work queue operations with metrics
    CLASSIFICATION = 22  # Document type detection
    ENRICHMENT = 21      # Entity enhancement
    SEMANTICS = 20       # Entity extraction and semantic analysis
    WRITER = 19          # Disk persistence operations
    ENTITY = 15          # Legacy entity level (for compatibility)
    

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
    logging.addLevelName(FusionLogLevel.STAGING, "STAGING")
    logging.addLevelName(FusionLogLevel.CONVERSION, "CONVERSION")
    logging.addLevelName(FusionLogLevel.QUEUE, "QUEUE")
    logging.addLevelName(FusionLogLevel.CLASSIFICATION, "CLASSIFICATION")
    logging.addLevelName(FusionLogLevel.ENRICHMENT, "ENRICHMENT")
    logging.addLevelName(FusionLogLevel.SEMANTICS, "SEMANTICS")
    logging.addLevelName(FusionLogLevel.WRITER, "WRITER")
    logging.addLevelName(FusionLogLevel.ENTITY, "ENTITY")
    
    # Map verbosity to log levels
    level_map = {
        0: logging.WARNING,         # QUIET: Errors and critical info only
        1: FusionLogLevel.STAGING,  # NORMAL: Stage progress + important info
        2: FusionLogLevel.SEMANTICS,# VERBOSE: Detailed processing info
        3: logging.DEBUG            # DEBUG: Everything
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
        'DEBUG': '\033[36m',         # Cyan
        'ENTITY': '\033[35m',        # Magenta  
        'INFO': '\033[0m',           # Default
        'STAGING': '\033[32m',       # Green - Service coordination
        'CONVERSION': '\033[94m',    # Light Blue - File operations
        'QUEUE': '\033[96m',         # Light Cyan - Queue operations
        'CLASSIFICATION': '\033[93m', # Light Yellow - Classification
        'ENRICHMENT': '\033[95m',    # Light Magenta - Enrichment
        'SEMANTICS': '\033[97m',     # White - Semantic processing
        'WRITER': '\033[92m',        # Light Green - Writing operations
        'PERF': '\033[33m',          # Yellow
        'WARNING': '\033[33m',       # Yellow
        'ERROR': '\033[31m',         # Red
        'CRITICAL': '\033[1;31m',    # Bold Red
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Convert to phase-worker format: [PHASE-WORKER]
        worker_tag = self._get_worker_tag()
        phase = record.levelname
        
        # Create phase-worker combination
        if worker_tag == 'Main':
            if phase in ['STAGING', 'INFO', 'WARNING', 'ERROR']:
                record.levelname = f"[{phase}-MAIN]"
            else:
                record.levelname = f"[{phase}-MAIN]"
        else:
            record.levelname = f"[{phase}-{worker_tag}]"
        
        # Add color codes for the combined phase-worker
        levelname = record.levelname
        # Extract base phase for color lookup
        if levelname.startswith('[') and '-' in levelname:
            base_phase = levelname[1:].split('-')[0]
            color = self.COLORS.get(base_phase, '\033[0m')
            record.levelname = f"{color}{levelname}{self.RESET}"
            record.msg = f"{color}{record.msg}{self.RESET}"
        return super().format(record)
    
    def _get_worker_tag(self) -> str:
        """Generate compact worker tag from thread name for I/O + CPU architecture"""
        thread_name = threading.current_thread().name
        
        # Map thread patterns to clean worker types
        if thread_name == 'MainThread':
            return 'Main'
        elif 'IOWorker' in thread_name or thread_name.startswith('IO-'):
            # I/O worker for ingestion (downloads, file reads, PDF conversion)
            return 'I/O'
        elif 'CPUWorker' in thread_name or thread_name.startswith('CPU-'):
            # CPU workers for processing (entity extraction, classification)
            if '-' in thread_name:
                worker_num = thread_name.split('-')[-1]
                return f'CPU-{worker_num}'
            else:
                return 'CPU-?'
        elif thread_name.startswith('ThreadPoolExecutor'):
            # Map ThreadPoolExecutor threads to CPU workers
            if '_' in thread_name:
                worker_num = thread_name.split('_')[-1]
                return f'CPU-{worker_num}'
            else:
                return 'CPU-?'
        elif 'Worker' in thread_name:
            # Legacy worker patterns - map to CPU workers
            if '-' in thread_name:
                worker_num = thread_name.split('-')[-1]
                return f'CPU-{worker_num}'
            else:
                return 'CPU-?'
        else:
            # Fallback for unknown thread patterns
            return f'T-{thread_name[:3]}'


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        import json
        
        # Add worker tags for all levels in JSON too
        levelname = record.levelname
        worker_tag = self._get_worker_tag()
        if worker_tag != 'Main':  # Only tag non-main threads
            levelname = f"{levelname}:{worker_tag}"
        
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
    def _get_worker_tag(self) -> str:
        """Generate compact worker tag from thread name for I/O + CPU architecture"""
        thread_name = threading.current_thread().name
        
        # Map thread patterns to clean worker types
        if thread_name == 'MainThread':
            return 'Main'
        elif 'IOWorker' in thread_name or thread_name.startswith('IO-'):
            # I/O worker for ingestion (downloads, file reads, PDF conversion)
            return 'I/O'
        elif 'CPUWorker' in thread_name or thread_name.startswith('CPU-'):
            # CPU workers for processing (entity extraction, classification)
            if '-' in thread_name:
                worker_num = thread_name.split('-')[-1]
                return f'CPU-{worker_num}'
            else:
                return 'CPU-?'
        elif thread_name.startswith('ThreadPoolExecutor'):
            # Map ThreadPoolExecutor threads to CPU workers
            if '_' in thread_name:
                worker_num = thread_name.split('_')[-1]
                return f'CPU-{worker_num}'
            else:
                return 'CPU-?'
        elif 'Worker' in thread_name:
            # Legacy worker patterns - map to CPU workers
            if '-' in thread_name:
                worker_num = thread_name.split('-')[-1]
                return f'CPU-{worker_num}'
            else:
                return 'CPU-?'
        else:
            # Fallback for unknown thread patterns
            return f'T-{thread_name[:3]}'
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
        logging.getLogger('fusion').setLevel(FusionLogLevel.STAGING)
        logging.getLogger('pipeline').setLevel(FusionLogLevel.STAGING)
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
    
    def staging(self, message: str, **kwargs) -> None:
        """Log a service staging message."""
        self.logger.log(FusionLogLevel.STAGING, message, **kwargs)
    
    def conversion(self, message: str, **kwargs) -> None:
        """Log a file conversion message."""
        self.logger.log(FusionLogLevel.CONVERSION, message, **kwargs)
    
    def queue(self, message: str, queue_size: Optional[int] = None, queue_max: Optional[int] = None, **kwargs) -> None:
        """Log a queue operation message with optional system metrics."""
        if queue_size is not None and queue_max is not None:
            metrics = get_system_metrics()
            if metrics:
                message = f"{message} (queue: {queue_size}/{queue_max}, {metrics})"
            else:
                message = f"{message} (queue: {queue_size}/{queue_max})"
        self.logger.log(FusionLogLevel.QUEUE, message, **kwargs)
    
    def classification(self, message: str, **kwargs) -> None:
        """Log a classification message."""
        self.logger.log(FusionLogLevel.CLASSIFICATION, message, **kwargs)
        
    def enrichment(self, message: str, **kwargs) -> None:
        """Log an enrichment message."""
        self.logger.log(FusionLogLevel.ENRICHMENT, message, **kwargs)
        
    def semantics(self, message: str, **kwargs) -> None:
        """Log a semantic processing message."""
        self.logger.log(FusionLogLevel.SEMANTICS, message, **kwargs)
        
    def writer(self, message: str, **kwargs) -> None:
        """Log a writer operation message."""
        self.logger.log(FusionLogLevel.WRITER, message, **kwargs)
    
    def stage(self, message: str, **kwargs) -> None:
        """Log a processing stage message (legacy compatibility)."""
        self.logger.log(FusionLogLevel.STAGING, message, **kwargs)
    
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
    logging.log(FusionLogLevel.STAGING, message)


def log_entity(message: str, count: Optional[int] = None) -> None:
    """Log entity-related information."""
    if count is not None:
        message = f"{message}: {count}"
    logging.log(FusionLogLevel.ENTITY, message)