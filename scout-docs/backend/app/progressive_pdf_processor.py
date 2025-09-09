"""
Progressive PDF processor with real-time progress updates.
Intercepts Docling's page-by-page processing to provide live feedback.
"""
import asyncio
import time
import logging
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.settings import settings

from app.logger import setup_logger

logger = setup_logger(__name__)

class ProgressiveDocumentConverter:
    """
    Wrapper around DocumentConverter that provides page-by-page progress updates
    for PDF processing.
    """
    
    def __init__(self):
        self.converter = DocumentConverter()
    
    async def convert_with_progress(
        self, 
        source: str,
        progress_callback: Optional[Callable[[str, int, int, float], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Convert document with real-time progress updates.
        
        Args:
            source: Path to PDF or URL
            progress_callback: Called with (phase, current_page, total_pages, elapsed_time)
            log_callback: Called with log messages
        """
        
        def log(message: str):
            logger.info(message)
            if log_callback:
                log_callback(message)
        
        start_time = time.perf_counter()
        
        try:
            # Phase 1: Initial setup and page count detection
            log("🔍 Analyzing document structure...")
            if progress_callback:
                progress_callback("analyzing", 0, 0, 0)
            
            # Get page count by quickly opening the PDF
            if Path(source).exists() and Path(source).suffix.lower() == '.pdf':
                page_count = await self._get_pdf_page_count(source)
                log(f"📄 Detected {page_count} pages")
            else:
                page_count = 1  # For non-PDF files
                log("📄 Processing single document")
            
            # Phase 2: Progressive conversion
            log("🔄 Starting progressive conversion...")
            if progress_callback:
                progress_callback("converting", 0, page_count, time.perf_counter() - start_time)
            
            # Configure smaller page batch size for more frequent updates
            original_batch_size = settings.perf.page_batch_size
            settings.perf.page_batch_size = min(2, max(1, page_count // 10))  # Process in smaller batches
            
            try:
                # Run conversion with progress monitoring
                result = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    self._convert_with_monitoring,
                    source, page_count, progress_callback, log_callback, start_time
                )
                
                total_time = time.perf_counter() - start_time
                log(f"✅ Conversion completed in {total_time:.2f}s")
                if progress_callback:
                    progress_callback("completed", page_count, page_count, total_time)
                
                return result
                
            finally:
                # Restore original batch size
                settings.perf.page_batch_size = original_batch_size
                
        except Exception as e:
            error_time = time.perf_counter() - start_time
            log(f"❌ Conversion failed after {error_time:.2f}s: {str(e)}")
            if progress_callback:
                progress_callback("failed", 0, page_count, error_time)
            raise
    
    def _convert_with_monitoring(self, source: str, page_count: int, progress_callback, log_callback, start_time):
        """
        Synchronous conversion with progress monitoring via monkey patching.
        """
        
        # Store original methods
        from docling.pipeline.base_pipeline import PaginatedPipeline
        original_build = PaginatedPipeline._build_document
        
        processed_pages = 0
        
        def monitored_build_document(self, conv_res):
            nonlocal processed_pages
            
            # Monkey patch the page processing loop
            original_apply = self._apply_on_pages
            
            def monitored_apply_on_pages(conv_res_inner, page_batch):
                nonlocal processed_pages
                
                # Count pages in this batch
                batch_pages = list(page_batch)
                batch_size = len(batch_pages)
                
                # Log progress before processing
                current_time = time.perf_counter() - start_time
                processed_pages += batch_size
                
                if log_callback:
                    log_callback(f"🔄 Processing pages {processed_pages-batch_size+1}-{processed_pages} of {page_count}")
                
                if progress_callback:
                    progress_callback("converting", processed_pages, page_count, current_time)
                
                # Process the batch
                return original_apply(conv_res_inner, batch_pages)
            
            # Temporarily replace the method
            self._apply_on_pages = monitored_apply_on_pages
            try:
                return original_build(self, conv_res)
            finally:
                # Restore original method
                self._apply_on_pages = original_apply
        
        # Monkey patch the build method
        PaginatedPipeline._build_document = monitored_build_document
        
        try:
            # Run the actual conversion
            return self.converter.convert(source)
        finally:
            # Restore original method
            PaginatedPipeline._build_document = original_build
    
    async def _get_pdf_page_count(self, pdf_path: str) -> int:
        """Get page count from PDF without full processing."""
        try:
            # Use a lightweight method to get page count
            import fitz  # PyMuPDF - if available
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            return page_count
        except ImportError:
            # Fallback to pypdfium2 if PyMuPDF not available
            try:
                import pypdfium2 as pdfium
                pdf = pdfium.PdfDocument(pdf_path)
                page_count = len(pdf)
                pdf.close()
                return page_count
            except ImportError:
                # Final fallback - estimate based on file size (very rough)
                file_size = Path(pdf_path).stat().st_size
                estimated_pages = max(1, file_size // (50 * 1024))  # ~50KB per page estimate
                logger.warning(f"Could not determine exact page count, estimating {estimated_pages} pages")
                return estimated_pages
        except Exception as e:
            logger.warning(f"Error getting page count: {e}")
            return 1  # Safe fallback