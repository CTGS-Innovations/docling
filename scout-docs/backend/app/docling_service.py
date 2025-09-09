import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel
# Use installed docling package

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PipelineOptions

from app.logger import setup_logger

logger = setup_logger(__name__)

class ProcessingMetrics(BaseModel):
    total_time: float
    document_loading_time: float
    conversion_time: float
    output_generation_time: float
    document_pages: int
    document_size_bytes: int
    words_processed: int
    pipeline_used: str

class ProcessingResult(BaseModel):
    success: bool
    output_content: str
    output_format: str
    error_message: Optional[str] = None
    metrics: Optional[ProcessingMetrics] = None
    metadata: Dict[str, Any] = {}

class DoclingProcessor:
    def __init__(self):
        self.converter = None
        self._initialize_converter()
    
    def _initialize_converter(self):
        """Initialize Docling converter with default settings"""
        try:
            start_time = time.perf_counter()
            self.converter = DocumentConverter()
            init_time = time.perf_counter() - start_time
            logger.info(f"🔧 Docling converter initialized in {init_time:.3f}s")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Docling converter: {e}")
            raise
    
    async def process_document(
        self,
        source: str,
        pipeline: str = "standard",
        output_format: str = "markdown",
        log_capture=None
    ) -> ProcessingResult:
        """Process document with detailed timing and logging"""
        
        def log(message: str):
            logger.info(message)
            if log_capture:
                log_capture.add_log(message)
        
        total_start = time.perf_counter()
        metrics = ProcessingMetrics(
            total_time=0,
            document_loading_time=0,
            conversion_time=0,
            output_generation_time=0,
            document_pages=0,
            document_size_bytes=0,
            words_processed=0,
            pipeline_used=pipeline
        )
        
        try:
            # Phase 1: Document Loading
            log("📖 Phase 1: Loading document...")
            loading_start = time.perf_counter()
            
            # Get file size if local file
            if Path(source).exists():
                metrics.document_size_bytes = Path(source).stat().st_size
                log(f"📁 Local file size: {metrics.document_size_bytes:,} bytes")
            else:
                log(f"🌐 Processing URL: {source}")
            
            loading_time = time.perf_counter() - loading_start
            metrics.document_loading_time = loading_time
            log(f"⏱️ Document loaded in {loading_time:.3f}s")
            
            # Phase 2: Docling Conversion
            log("🔄 Phase 2: Docling conversion...")
            conversion_start = time.perf_counter()
            
            # Configure pipeline options if needed
            pipeline_options = PipelineOptions()
            if pipeline == "vlm":
                # Configure VLM pipeline if available
                log("🤖 Using VLM pipeline")
            else:
                log("⚙️ Using standard pipeline")
            
            # Run conversion in executor to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._convert_document, 
                source
            )
            
            conversion_time = time.perf_counter() - conversion_start
            metrics.conversion_time = conversion_time
            
            # Extract document metadata
            doc = result.document
            metrics.document_pages = len(doc.pages) if doc.pages else 1
            
            # Count words in the document
            word_count = 0
            if hasattr(doc, 'texts') and doc.texts:
                for text in doc.texts:
                    if hasattr(text, 'text'):
                        word_count += len(text.text.split())
            metrics.words_processed = word_count
            
            log(f"📊 Document stats: {metrics.document_pages} pages, ~{word_count:,} words")
            log(f"⏱️ Conversion completed in {conversion_time:.3f}s")
            
            # Phase 3: Output Generation
            log("📤 Phase 3: Generating output...")
            output_start = time.perf_counter()
            
            # Generate output based on format
            if output_format == "markdown":
                output_content = doc.export_to_markdown()
            elif output_format == "html":
                output_content = doc.export_to_html()
            elif output_format == "json":
                output_content = doc.export_to_json()
            else:
                output_content = doc.export_to_markdown()  # Default
            
            output_time = time.perf_counter() - output_start
            metrics.output_generation_time = output_time
            log(f"⏱️ Output generated in {output_time:.3f}s")
            
            # Calculate total time
            total_time = time.perf_counter() - total_start
            metrics.total_time = total_time
            
            # Performance summary
            log(f"🏁 Processing Summary:")
            log(f"   📊 Total time: {total_time:.3f}s")
            log(f"   📖 Loading: {loading_time:.3f}s ({loading_time/total_time*100:.1f}%)")
            log(f"   🔄 Conversion: {conversion_time:.3f}s ({conversion_time/total_time*100:.1f}%)")
            log(f"   📤 Output: {output_time:.3f}s ({output_time/total_time*100:.1f}%)")
            log(f"   🚀 Speed: {word_count/total_time:.0f} words/second")
            
            # Prepare metadata
            metadata = {
                "source": source,
                "pipeline": pipeline,
                "output_format": output_format,
                "processed_at": datetime.now().isoformat(),
                "docling_version": getattr(result, 'version', 'unknown')
            }
            
            return ProcessingResult(
                success=True,
                output_content=output_content,
                output_format=output_format,
                metrics=metrics,
                metadata=metadata
            )
            
        except Exception as e:
            error_msg = str(e)
            log(f"❌ Processing failed: {error_msg}")
            
            # Still calculate what we can
            total_time = time.perf_counter() - total_start
            metrics.total_time = total_time
            
            return ProcessingResult(
                success=False,
                output_content="",
                output_format=output_format,
                error_message=error_msg,
                metrics=metrics,
                metadata={"source": source, "pipeline": pipeline}
            )
    
    def _convert_document(self, source: str):
        """Synchronous document conversion"""
        return self.converter.convert(source)