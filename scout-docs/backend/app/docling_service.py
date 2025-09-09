import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel
# Use installed docling package

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, VlmPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel import vlm_model_specs

from app.logger import setup_logger
from app.progressive_pdf_processor import ProgressiveDocumentConverter
from app.torch_config import get_compute_info, set_compute_mode_for_request
from app.pipeline_configs import PipelineRegistry, PipelineProfile

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
    compute_type: str  # "CPU" or "GPU"
    compute_details: str  # Details about the compute environment

class ProcessingResult(BaseModel):
    success: bool
    output_content: str
    output_format: str
    error_message: Optional[str] = None
    metrics: Optional[ProcessingMetrics] = None
    metadata: Dict[str, Any] = {}

class DoclingProcessor:
    def __init__(self):
        self.progressive_converter = None
        self._initialize_progressive_converter()
    
    def _initialize_progressive_converter(self):
        """Initialize progressive converter for large PDFs"""
        try:
            start_time = time.perf_counter()
            self.progressive_converter = ProgressiveDocumentConverter()
            init_time = time.perf_counter() - start_time
            logger.info(f"🔧 Docling progressive converter initialized in {init_time:.3f}s")
        except Exception as e:
            logger.error(f"❌ Failed to initialize progressive converter: {e}")
            raise
    
    def _create_converter_with_accelerator(self, compute_mode: str, pipeline: str, use_vllm: bool = False):
        """Create DocumentConverter with proper accelerator configuration"""
        
        # Handle VLM pipeline separately (legacy support)
        if pipeline == "vlm":
            return self._create_vlm_converter(compute_mode, use_vllm)
        
        # Use new pipeline configuration system
        try:
            profile = PipelineProfile(pipeline)
        except ValueError:
            # Fallback for unknown pipeline names - use standard
            profile = PipelineProfile.STANDARD
        
        # Get pipeline configuration
        config = PipelineRegistry.get_config(profile)
        pipeline_options, backend_class = PipelineRegistry.create_pipeline_options(profile, compute_mode)
        
        # Create converter with configured options
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=backend_class
                )
            }
        )
        
        return converter
    
    def _create_vlm_converter(self, compute_mode: str, use_vllm: bool = False):
        """Create VLM converter (legacy method for VLM pipeline)"""
        
        # Configure accelerator options
        if compute_mode.lower() == "gpu":
            accelerator_options = AcceleratorOptions(
                device=AcceleratorDevice.CUDA,
                num_threads=4,
                cuda_use_flash_attention2=False  # Disable flash attention - not installed
            )
        else:
            accelerator_options = AcceleratorOptions(
                device=AcceleratorDevice.CPU,
                num_threads=8
            )
        
        # Configure VLM options
        if compute_mode.lower() == "gpu":
            if use_vllm:
                vlm_options = vlm_model_specs.SMOLDOCLING_VLLM  # 256M, CUDA-only, fastest
            else:
                vlm_options = vlm_model_specs.SMOLDOCLING_TRANSFORMERS  # 256M, CPU+CUDA
        else:
            vlm_options = vlm_model_specs.SMOLDOCLING_TRANSFORMERS  # 256M, supports CPU+CUDA
        
        pipeline_options = VlmPipelineOptions(
            vlm_options=vlm_options
        )
        pipeline_options.accelerator_options = accelerator_options
        pipeline_options.generate_page_images = True
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                )
            }
        )
        
        return converter
    
    async def process_document(
        self,
        source: str,
        pipeline: str = "standard",
        output_format: str = "markdown",
        compute_mode: str = "cpu",
        log_capture=None,
        progress_callback=None
    ) -> ProcessingResult:
        """Process document with detailed timing and logging"""
        
        def log(message: str):
            logger.info(message)
            if log_capture:
                log_capture.add_log(message)
        
        total_start = time.perf_counter()
        
        # Get compute environment info
        compute_info = get_compute_info()
        
        metrics = ProcessingMetrics(
            total_time=0,
            document_loading_time=0,
            conversion_time=0,
            output_generation_time=0,
            document_pages=0,
            document_size_bytes=0,
            words_processed=0,
            pipeline_used=pipeline,
            compute_type=compute_info["compute_type"],
            compute_details=compute_info["compute_details"]
        )
        
        try:
            # Set compute mode for this specific request
            actual_mode, compute_details = set_compute_mode_for_request(compute_mode)
            if actual_mode == "cpu_fallback":
                log("⚠️ GPU requested but not available, falling back to CPU")
            
            log(f"🖥️ Compute: {actual_mode.upper().replace('_FALLBACK', '')} ({compute_details})")
            
            # Update metrics with actual compute mode used
            metrics.compute_type = actual_mode.upper().replace('_FALLBACK', '')
            metrics.compute_details = compute_details
            
            # Phase 1: Document Loading
            log("📖 Phase 1: Loading document...")
            loading_start = time.perf_counter()
            
            # Get file size if local file
            if Path(source).exists():
                file_path = Path(source)
                metrics.document_size_bytes = file_path.stat().st_size
                file_size_mb = metrics.document_size_bytes / (1024 * 1024)
                log(f"📁 Local file: {file_path.name} ({file_size_mb:.1f} MB)")
                log(f"📊 File type: {file_path.suffix.upper()}")
            else:
                log(f"🌐 Processing URL: {source}")
            
            loading_time = time.perf_counter() - loading_start
            metrics.document_loading_time = loading_time
            log(f"⏱️ Document loaded in {loading_time:.3f}s")
            
            # Phase 2: Docling Conversion
            log("🔄 Phase 2: Docling conversion...")
            conversion_start = time.perf_counter()
            
            # Create converter with proper acceleration settings
            use_vllm = (compute_mode.lower() == "gpu" and pipeline == "vlm")
            converter = self._create_converter_with_accelerator(compute_mode, pipeline, use_vllm=use_vllm)
            
            # Log pipeline details
            if pipeline == "vlm":
                if use_vllm:
                    log("🚀 Using VLM pipeline with VLLM (maximum GPU performance)")
                else:
                    log("🤖 Using VLM pipeline with Transformers framework")
            else:
                # Get pipeline configuration for logging
                try:
                    profile = PipelineProfile(pipeline)
                    config = PipelineRegistry.get_config(profile)
                    log(f"⚙️ Pipeline: {config.name} ({config.performance} performance)")
                    log(f"   Features: {', '.join(config.features)}")
                    log(f"   Backend: {config.pdf_backend.value}")
                    log(f"   Compute: {actual_mode.upper()}")
                except ValueError:
                    log(f"⚙️ Using standard pipeline with {actual_mode.upper()} acceleration")
            
            # Check if this is a PDF for progressive processing (only for very large files)
            is_large_pdf = (Path(source).exists() and 
                           Path(source).suffix.lower() == '.pdf' and 
                           Path(source).stat().st_size > 10 * 1024 * 1024)  # > 10MB PDFs get progressive processing
            
            if is_large_pdf and pipeline != "vlm":  # VLM pipeline doesn't use progressive processing
                log("📄 Large PDF detected - using progressive processing")
                
                # Define progress callback
                def on_progress(phase: str, current: int, total: int, elapsed: float):
                    if phase == "analyzing":
                        log("🔍 Analyzing document structure...")
                        if progress_callback:
                            progress_callback(20, f"🔍 Analyzing document structure...")
                    elif phase == "converting":
                        if total > 0:
                            progress_pct = 20 + int((current / total) * 60)  # 20-80% range
                            log(f"🔄 Processing page {current}/{total} ({progress_pct}%)")
                            if progress_callback:
                                progress_callback(progress_pct, f"🔄 Processing page {current}/{total}")
                    elif phase == "completed":
                        log("✅ Progressive processing completed")
                        if progress_callback:
                            progress_callback(80, "✅ Document conversion completed")
                
                # Use progressive converter for large PDFs
                result = await self.progressive_converter.convert_with_progress(
                    source=source,
                    progress_callback=on_progress,
                    log_callback=log
                )
            else:
                # Use the configured converter with proper acceleration
                log(f"🔄 Starting {'VLM' if pipeline == 'vlm' else 'standard'} conversion...")
                parse_start = time.perf_counter()
                
                # Run conversion in executor to avoid blocking
                result = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    converter.convert, 
                    source
                )
                
                parse_time = time.perf_counter() - parse_start
                log(f"🔄 {'VLM' if pipeline == 'vlm' else 'Standard'} conversion completed in {parse_time:.3f}s")
            
            conversion_time = time.perf_counter() - conversion_start
            metrics.conversion_time = conversion_time
            
            # Extract document metadata
            doc = result.document
            metrics.document_pages = len(result.pages) if result.pages else 1
            
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
            if metrics.document_size_bytes > 0:
                mb_per_sec = (metrics.document_size_bytes / (1024 * 1024)) / total_time
                log(f"   💾 Throughput: {mb_per_sec:.1f} MB/second")
            if metrics.document_pages > 1:
                pages_per_sec = metrics.document_pages / total_time
                log(f"   📄 Page rate: {pages_per_sec:.1f} pages/second")
            
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
    
