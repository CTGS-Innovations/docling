"""
Phase-aware logging manager for MVP-Fusion pipeline.
Automatically assigns appropriate log levels based on current processing phase.
Includes performance tracking for each processing phase.
"""

import logging
import time
from typing import Optional, Dict, Any
from .logging_config import FusionLogLevel


class PhaseManager:
    """
    Manages the current processing phase and automatically assigns 
    appropriate log levels for each operation.
    """
    
    def __init__(self):
        self.current_phase: Optional[str] = None
        
        # Performance tracking for each phase
        self.phase_timings: Dict[str, float] = {}
        self.phase_start_times: Dict[str, float] = {}
        self.phase_page_counts: Dict[str, int] = {}
        self.phase_file_counts: Dict[str, int] = {}
        self.total_pages_processed: int = 0
        
        # Map processing phases to their appropriate log levels
        self.phase_to_level = {
            'initialization': FusionLogLevel.CONFIG,        # 19 - Hidden in normal mode
            'memory_management': FusionLogLevel.CONFIG,     # 19 - Hidden in normal mode  
            'pdf_conversion': FusionLogLevel.CONVERSION,    # 25 - Hidden in normal mode
            'document_processing': FusionLogLevel.SEMANTICS, # 20 - Hidden in normal mode
            'classification': FusionLogLevel.CLASSIFICATION, # 23 - Hidden in normal mode
            'entity_extraction': FusionLogLevel.ENRICHMENT, # 21 - Hidden in normal mode
            'normalization': FusionLogLevel.NORMALIZATION, # 22 - Hidden in normal mode (NEW)
            'semantic_analysis': FusionLogLevel.SEMANTICS,  # 20 - Hidden in normal mode
            'file_writing': FusionLogLevel.WRITER,          # 18 - Hidden in normal mode
            'service_coordination': FusionLogLevel.SEMANTICS, # 20 - Hidden in normal mode
            'queue_management': FusionLogLevel.CONFIG,      # 19 - Hidden in normal mode
            'performance': FusionLogLevel.PERFORMANCE       # 35 - Always visible
        }
        
        # Default fallback level
        self.default_level = logging.INFO
    
    def set_phase(self, phase_name: str) -> None:
        """Set the current processing phase and start timing."""
        # End timing for previous phase
        if self.current_phase and self.current_phase in self.phase_start_times:
            elapsed = time.time() - self.phase_start_times[self.current_phase]
            self.phase_timings[self.current_phase] = elapsed
            
        # Start timing for new phase
        self.current_phase = phase_name
        self.phase_start_times[phase_name] = time.time()
        
        # Initialize counters if not exist
        if phase_name not in self.phase_page_counts:
            self.phase_page_counts[phase_name] = 0
            self.phase_file_counts[phase_name] = 0
    
    def get_current_level(self) -> int:
        """Get the log level for the current phase."""
        if not self.current_phase:
            return self.default_level
        return self.phase_to_level.get(self.current_phase, self.default_level)
    
    def log(self, logger_name: str, message: str, **kwargs) -> None:
        """
        Log a message at the appropriate level for the current phase.
        
        Args:
            logger_name: Name of the logger to use
            message: Message to log
            **kwargs: Additional logging arguments
        """
        level = self.get_current_level()
        logger = logging.getLogger(logger_name)
        logger.log(level, message, **kwargs)
    
    def staging(self, logger_name: str, message: str, **kwargs) -> None:
        """Force staging level log (for service coordination)."""
        logger = logging.getLogger(logger_name)
        logger.log(FusionLogLevel.STAGING, message, **kwargs)
    
    def conversion(self, logger_name: str, message: str, **kwargs) -> None:
        """Force conversion level log (for file operations)."""
        logger = logging.getLogger(logger_name)
        logger.log(FusionLogLevel.CONVERSION, message, **kwargs)
    
    def classification(self, logger_name: str, message: str, **kwargs) -> None:
        """Force classification level log."""
        logger = logging.getLogger(logger_name)
        logger.log(FusionLogLevel.CLASSIFICATION, message, **kwargs)
    
    def enrichment(self, logger_name: str, message: str, **kwargs) -> None:
        """Force enrichment level log (for entity extraction)."""
        logger = logging.getLogger(logger_name)
        logger.log(FusionLogLevel.ENRICHMENT, message, **kwargs)
    
    def semantics(self, logger_name: str, message: str, **kwargs) -> None:
        """Force semantics level log."""
        logger = logging.getLogger(logger_name)
        logger.log(FusionLogLevel.SEMANTICS, message, **kwargs)
    
    def writer(self, logger_name: str, message: str, **kwargs) -> None:
        """Force writer level log (for disk operations)."""
        logger = logging.getLogger(logger_name)
        logger.log(FusionLogLevel.WRITER, message, **kwargs)
    
    def performance(self, logger_name: str, message: str, **kwargs) -> None:
        """Force performance level log."""
        logger = logging.getLogger(logger_name)
        logger.log(FusionLogLevel.PERFORMANCE, message, **kwargs)
    
    def add_pages_processed(self, pages: int) -> None:
        """Add pages processed to current phase."""
        if self.current_phase:
            self.phase_page_counts[self.current_phase] += pages
            self.total_pages_processed += pages
    
    def add_files_processed(self, files: int) -> None:
        """Add files processed to current phase."""
        if self.current_phase:
            self.phase_file_counts[self.current_phase] += files
    
    def get_phase_performance_report(self) -> str:
        """Generate detailed phase-by-phase performance report."""
        # End timing for current phase if active
        if self.current_phase and self.current_phase in self.phase_start_times:
            elapsed = time.time() - self.phase_start_times[self.current_phase]
            self.phase_timings[self.current_phase] = elapsed
        
        report_lines = []
        report_lines.append("\n📊 PHASE PERFORMANCE:")
        
        # Define phase display order and names
        phase_display = {
            'pdf_conversion': '🔄 PDF Conversion',
            'document_processing': '📄 Document Processing', 
            'classification': '🏷️  Classification',
            'entity_extraction': '🔍 Entity Extraction',
            'normalization': '🔄 Normalization',
            'semantic_analysis': '🧠 Semantic Analysis',
            'file_writing': '💾 File Writing'
        }
        
        for phase_key, phase_name in phase_display.items():
            if phase_key in self.phase_timings:
                timing = self.phase_timings[phase_key]
                pages = self.phase_page_counts.get(phase_key, 0)
                files = self.phase_file_counts.get(phase_key, 0)
                
                if timing > 0:
                    pages_per_sec = pages / timing if pages > 0 else 0
                    files_per_sec = files / timing if files > 0 else 0
                    
                    # Use total pages processed across all phases for consistency
                    total_pages = self.total_pages_processed
                    if total_pages > 0 and timing > 0:
                        pages_per_sec_total = total_pages / timing
                        # Estimate MB/sec (assume ~1MB per 20 pages average)
                        mb_per_sec = (total_pages / 20) / timing if timing > 0 else 0
                        
                        # Dynamic unit scaling for throughput
                        if mb_per_sec >= 1000000:  # >= 1TB/sec
                            throughput_value = mb_per_sec / 1000000
                            throughput_unit = "TB/sec"
                        elif mb_per_sec >= 1000:  # >= 1GB/sec
                            throughput_value = mb_per_sec / 1000
                            throughput_unit = "GB/sec"
                        else:  # MB/sec
                            throughput_value = mb_per_sec
                            throughput_unit = "MB/sec"
                        
                        report_lines.append(f"   {phase_name}: {pages_per_sec_total:.0f} pages/sec, {throughput_value:.0f} {throughput_unit} ({total_pages} pages, {timing*1000:.4f}ms)")
                    else:
                        report_lines.append(f"   {phase_name}: {timing*1000:.4f}ms")
        
        return "\n".join(report_lines)


# Global phase manager instance
_phase_manager = PhaseManager()


def get_phase_manager() -> PhaseManager:
    """Get the global phase manager instance."""
    return _phase_manager


def set_current_phase(phase_name: str) -> None:
    """Set the current processing phase globally."""
    _phase_manager.set_phase(phase_name)


def phase_log(logger_name: str, message: str, **kwargs) -> None:
    """Log a message at the appropriate level for the current phase."""
    _phase_manager.log(logger_name, message, **kwargs)


def add_pages_processed(pages: int) -> None:
    """Add pages processed to current phase."""
    _phase_manager.add_pages_processed(pages)


def add_files_processed(files: int) -> None:
    """Add files processed to current phase."""
    _phase_manager.add_files_processed(files)


def get_phase_performance_report() -> str:
    """Get formatted phase-by-phase performance report."""
    return _phase_manager.get_phase_performance_report()