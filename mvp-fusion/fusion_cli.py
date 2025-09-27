#!/usr/bin/env python3
"""
MVP-Fusion Command Line Interface
=================================

High-performance document processing with MVP-Hyper output compatibility.
Process individual files or entire directories at 10,000+ pages/sec.

Usage:
    python fusion_cli.py --file document.pdf
    python fusion_cli.py --directory ~/documents/ --batch-size 32
    python fusion_cli.py --config custom_config.yaml --performance-test
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import json
import requests
from urllib.parse import urlparse
import tempfile

# Import our centralized logging configuration
from utils.logging_config import setup_logging, get_fusion_logger
from utils.phase_manager import get_phase_performance_report
from utils.deployment_manager import DeploymentManager
from utils.configurable_markdown_converter import convert_html_to_markdown_configurable


class PipelinePhase:
    """Represents a single phase in the processing pipeline."""
    
    def __init__(self, name: str, processor, config: Dict[str, Any] = None):
        self.name = name
        self.processor = processor
        self.config = config or {}
        self.timing_ms = 0.0
        self.success = True
        self.error_message = None
    
    def execute(self, input_data: Any, metadata: Dict[str, Any] = None) -> Any:
        """Execute this phase of the pipeline."""
        logger = get_fusion_logger(__name__)
        metadata = metadata or {}
        
        start_time = time.perf_counter()
        try:
            # Log phase start
            logger.stage(f"🔄 Starting phase: {self.name}")
            
            # Execute the processor
            if hasattr(self.processor, 'process_files_service'):
                # ServiceProcessor interface
                result = self.processor.process_files_service(input_data, metadata.get('output_dir', Path.cwd()))
            elif hasattr(self.processor, 'process'):
                # Generic processor interface
                result = self.processor.process(input_data, metadata)
            else:
                # Direct callable
                result = self.processor(input_data, metadata)
            
            self.success = True
            return result
            
        except Exception as e:
            self.success = False
            self.error_message = str(e)
            logger.logger.error(f"❌ Phase '{self.name}' failed: {e}")
            raise
        finally:
            self.timing_ms = (time.perf_counter() - start_time) * 1000
            logger.stage(f"✅ Phase '{self.name}' completed in {self.timing_ms:.2f}ms")


class CleanFusionPipeline:
    """Clean pipeline architecture for MVP-Fusion with configurable phases and A/B testing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.phases = []
        self.sidecar_tests = {}
        self.logger = get_fusion_logger(__name__)
        self.logger.stage("🏗️ Initializing Clean Pipeline Architecture")
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the orchestrated pipeline wrapper."""
        # Initialize the service processor once during pipeline initialization
        from pipeline.legacy.service_processor import ServiceProcessor
        from utils.deployment_manager import DeploymentManager
        
        # Get correct worker count from deployment profile
        deployment_manager = DeploymentManager(self.config)
        max_workers = deployment_manager.get_max_workers()
        
        self.service_processor = ServiceProcessor(self.config, max_workers)
        
        # Use orchestrated pipeline wrapper as the default system
        from pipeline.orchestrated_pipeline_wrapper import OrchestratedPipelineWrapper
        self.orchestrated_pipeline = OrchestratedPipelineWrapper(self.config, self.service_processor)
        self.phases = []  # No individual phases needed - orchestrated handles all
        # Using orchestrated pipeline architecture
    
    def _setup_sidecar_test(self, sidecar_config: str):
        """Setup sidecar A/B testing for performance comparison."""
        self.logger.stage(f"🧪 Setting up sidecar test: {sidecar_config}")
        
        try:
            if sidecar_config == 'fusion_pipeline':
                from pipeline.legacy.fusion_pipeline import FusionPipeline as LegacyFusionPipeline
                sidecar_processor = LegacyFusionPipeline(self.config)
                self.sidecar_tests['fusion_pipeline'] = sidecar_processor
                self.logger.stage(f"✅ Sidecar '{sidecar_config}' activated successfully")
                
            elif sidecar_config == 'optimized_doc_processor':
                # Try to import optimized processor directly (bypass factory issues)
                try:
                    import sys
                    from pathlib import Path
                    sys.path.insert(0, str(Path(__file__).parent / 'pipeline'))
                    from optimized_doc_processor import OptimizedDocProcessorWrapper
                    
                    sidecar_processor = OptimizedDocProcessorWrapper(self.config)
                    self.sidecar_tests['optimized_doc_processor'] = sidecar_processor
                    self.logger.stage(f"✅ Sidecar '{sidecar_config}' activated successfully")
                    
                except Exception as import_error:
                    self.logger.stage(f"❌ Sidecar '{sidecar_config}' failed to load: {import_error}")
                    self.logger.stage(f"   Sidecar A/B testing disabled for this run")
                    
            else:
                self.logger.stage(f"❌ Unknown sidecar processor: {sidecar_config}")
                self.logger.stage(f"   Available: fusion_pipeline, optimized_doc_processor")
                
        except Exception as e:
            self.logger.stage(f"❌ Sidecar setup failed: {e}")
            self.logger.stage(f"   Sidecar A/B testing disabled for this run")
    
    def process(self, input_data: Any, metadata: Dict[str, Any] = None) -> tuple[Any, Dict[str, Any]]:
        """Process input through all pipeline phases."""
        metadata = metadata or {}
        
        # Check if using orchestrated pipeline
        if hasattr(self, 'orchestrated_pipeline') and self.orchestrated_pipeline:
            # Use the orchestrated pipeline
            results = self.orchestrated_pipeline.process(input_data, metadata)
            
            # Convert to expected format
            return results['final_output'], {
                'pipeline_timing_ms': results['total_pipeline_ms'],
                'phase_results': results['stage_results'],
                'sidecar_results': {},
                'processor_type': 'orchestrated_pipeline'
            }
        
        # Legacy pipeline processing
        current_data = input_data
        
        # Track overall pipeline timing
        pipeline_start = time.perf_counter()
        results = []
        
        # Execute each phase
        for phase in self.phases:
            try:
                phase_result = phase.execute(current_data, metadata)
                
                # Handle different result formats
                if isinstance(phase_result, tuple) and len(phase_result) == 2:
                    current_data, phase_timing = phase_result
                else:
                    current_data = phase_result
                
                # Store phase results for reporting
                results.append({
                    'phase': phase.name,
                    'timing_ms': phase.timing_ms,
                    'success': phase.success,
                    'error': phase.error_message
                })
                
            except Exception as e:
                self.logger.logger.error(f"❌ Pipeline failed at phase '{phase.name}': {e}")
                raise
        
        # Run sidecar tests if configured
        sidecar_results = {}
        if self.sidecar_tests and not metadata.get('skip_sidecar', False):
            sidecar_results = self._run_sidecar_tests(input_data, metadata)
        
        total_time_ms = (time.perf_counter() - pipeline_start) * 1000
        
        # Prepare metadata for response
        pipeline_metadata = {
            'pipeline_timing_ms': total_time_ms,
            'phase_results': results,
            'sidecar_results': sidecar_results,
            'processor_type': self.config.get('pipeline', {}).get('document_processing', {}).get('processor', 'service_processor')
        }
        
        return current_data, pipeline_metadata
    
    def _run_sidecar_tests(self, input_data: Any, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Run sidecar A/B tests for performance comparison."""
        sidecar_results = {}
        
        for test_name, test_processor in self.sidecar_tests.items():
            try:
                self.logger.stage(f"🧪 Running sidecar test: {test_name}")
                
                start_time = time.perf_counter()
                if hasattr(test_processor, 'process_files_service'):
                    sidecar_result = test_processor.process_files_service(input_data, metadata.get('output_dir', Path.cwd()))
                else:
                    sidecar_result = test_processor.process(input_data, metadata)
                
                timing_ms = (time.perf_counter() - start_time) * 1000
                
                sidecar_results[test_name] = {
                    'timing_ms': timing_ms,
                    'success': True,
                    'processor': test_name
                }
                
                self.logger.stage(f"✅ Sidecar test '{test_name}' completed in {timing_ms:.2f}ms")
                
            except Exception as e:
                sidecar_results[test_name] = {
                    'timing_ms': 0,
                    'success': False,
                    'error': str(e),
                    'processor': test_name
                }
                self.logger.stage(f"❌ Sidecar test '{test_name}' failed: {e}")
        
        return sidecar_results
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of the pipeline."""
        total_timing = sum(phase.timing_ms for phase in self.phases)
        
        return {
            'total_pipeline_ms': total_timing,
            'phases': [
                {
                    'name': phase.name,
                    'timing_ms': phase.timing_ms,
                    'percentage': (phase.timing_ms / total_timing * 100) if total_timing > 0 else 0,
                    'success': phase.success
                }
                for phase in self.phases
            ],
            'sidecar_tests': len(self.sidecar_tests)
        }


class ConversionSuccess:
    """Defines success criteria for different input types before classification stage"""
    
    @staticmethod
    def validate_file(file_path: Path, content_size: int) -> tuple[bool, str, Dict]:
        """Validate file conversion success"""
        if not file_path.exists():
            return False, "File does not exist", {}
        if content_size == 0:
            return False, "File is empty", {}
        return True, "File ready for classification", {"source_type": "file"}
    
    @staticmethod 
    def validate_url(response_code: int, content_size: int, content_type: str) -> tuple[bool, str, Dict]:
        """Validate URL conversion success"""
        if response_code != 200:
            return False, f"HTTP {response_code} - not processable", {"http_status": response_code}
        if content_size == 0:
            return False, "Empty content received", {"http_status": response_code}
        if content_type and not any(t in content_type.lower() for t in ['html', 'text', 'pdf', 'json']):
            return False, f"Unsupported content type: {content_type}", {"http_status": response_code, "content_type": content_type}
        return True, "URL ready for classification", {"http_status": response_code, "content_type": content_type}


# Import extraction architecture
from extraction import (
    BaseExtractor,
    HighSpeed_Markdown_General_Extractor,
    HighAccuracy_Markdown_General_Extractor,
    HighSpeed_JSON_PDF_Extractor,
    Specialized_Markdown_Legal_Extractor
)


def get_available_extractors():
    """Return mapping of extractor names to classes."""
    return {
        'highspeed_markdown_general': HighSpeed_Markdown_General_Extractor,
        'highaccuracy_markdown_general': HighAccuracy_Markdown_General_Extractor,
        'highspeed_json_pdf': HighSpeed_JSON_PDF_Extractor,
        'specialized_markdown_legal': Specialized_Markdown_Legal_Extractor
    }

def create_extractor(extractor_name: str, config: dict = None):
    """Factory function to create extractor by name."""
    extractors = get_available_extractors()
    
    if extractor_name not in extractors:
        available = list(extractors.keys())
        raise ValueError(f"Unknown extractor '{extractor_name}'. Available: {available}")
    
    extractor_class = extractors[extractor_name]
    
    # Pass config parameters if the extractor supports them
    if config and extractor_name == 'highspeed_markdown_general':
        page_limit = config.get('page_limit', 100)
        return extractor_class(page_limit=page_limit)
    else:
        return extractor_class()



def process_single_file(extractor: BaseExtractor, file_path: Path, output_dir: Path = None, quiet: bool = False) -> Dict[str, Any]:
    """Process a single file and return results."""
    logger = get_fusion_logger(__name__)
    if not quiet:
        logger.stage(f"Processing: {file_path.name}")
    
    result = extractor.extract_single(file_path, output_dir or Path.cwd())
    
    if not quiet and not result.success:
        logger.logger.error(f"❌ Error: {result.error}")
    
    return result


def download_url_content(url: str, max_size_mb: int = 10, timeout_seconds: int = 15, session: requests.Session = None) -> tuple[bytes, str, str, int, Dict]:
    """Download URL content to memory with size limit. 
    
    Returns: 
        content: Downloaded bytes
        content_type: MIME type from response headers  
        file_ext: Appropriate file extension
        status_code: HTTP response code
        headers: Response headers dict
    """
    logger = get_fusion_logger(__name__)
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme in ['http', 'https']:
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
        
        # Set headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        logger.entity(f"🌐 Downloading: {url}")
        
        # Stream download to check size before loading into memory
        # Use provided session or fall back to requests.get
        if session:
            response = session.get(url, headers=headers, timeout=timeout_seconds, stream=True)
        else:
            response = requests.get(url, headers=headers, timeout=timeout_seconds, stream=True)
        
        # Capture response metadata immediately
        status_code = response.status_code
        response_headers = dict(response.headers)
        
        # Check status code before processing content
        if status_code != 200:
            response.close()
            logger.logger.error(f"❌ HTTP {status_code} response from {url}")
            return b'', '', '.html', status_code, response_headers
        
        response.raise_for_status()
        
        # Check content length header if available
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > max_size_bytes:
            response.close()
            raise ValueError(f"Content too large: {int(content_length)/1024/1024:.1f}MB > {max_size_mb}MB limit")
        
        # Download content with size checking
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_size_bytes:
                response.close()
                raise ValueError(f"Content too large: >{max_size_mb}MB limit reached during download")
        
        content_type = response.headers.get('content-type', 'text/html').lower()
        
        # Determine appropriate file extension based on content type
        if 'pdf' in content_type:
            file_ext = '.pdf'
        elif 'html' in content_type:
            file_ext = '.html'
        elif 'text/plain' in content_type:
            file_ext = '.txt'
        elif 'json' in content_type:
            file_ext = '.json'
        elif 'xml' in content_type:
            file_ext = '.xml'
        elif 'csv' in content_type:
            file_ext = '.csv'
        elif 'word' in content_type or 'msword' in content_type:
            file_ext = '.docx'
        elif 'excel' in content_type or 'spreadsheet' in content_type:
            file_ext = '.xlsx'
        else:
            file_ext = '.html'  # Default to HTML for unknown types
        
        logger.success(f"✅ Downloaded {len(content)} bytes ({len(content)/1024/1024:.1f}MB) - Type: {content_type}")
        
        return content, content_type, file_ext, status_code, response_headers
        
    except requests.exceptions.RequestException as e:
        logger.logger.error(f"❌ Failed to download {url}: {e}")
        raise
    except ValueError as e:
        logger.logger.error(f"❌ {e}")
        raise
    except Exception as e:
        logger.logger.error(f"❌ Error processing {url}: {e}")
        raise


def create_filename_from_url(url: str) -> str:
    """Create a safe filename from URL that preserves the full URL information."""
    # Remove protocol
    clean_url = url.replace('https://', '').replace('http://', '')
    
    # Replace problematic characters with safe ones
    safe_chars = {
        '/': '_',
        '?': '_',
        '&': '_and_',
        '=': '_eq_',
        '#': '_hash_',
        '%': '_pct_',
        '+': '_plus_',
        ' ': '_',
        ':': '_',
        ';': '_',
        '<': '_lt_',
        '>': '_gt_',
        '"': '_quote_',
        '|': '_pipe_',
        '*': '_star_',
        '\\': '_'
    }
    
    filename = clean_url
    for char, replacement in safe_chars.items():
        filename = filename.replace(char, replacement)
    
    # Limit length but preserve meaningful parts
    if len(filename) > 200:
        # Keep domain and truncate path
        parts = filename.split('_')
        domain = parts[0] if parts else filename[:50]
        rest = '_'.join(parts[1:])
        if len(rest) > 150:
            rest = rest[:150] + '_truncated'
        filename = f"{domain}_{rest}"
    
    # Ensure it doesn't end with period or space
    filename = filename.rstrip('. ')
    
    return filename


def process_single_url(extractor: BaseExtractor, url: str, output_dir: Path = None, config: dict = None, quiet: bool = False, session: requests.Session = None) -> Dict[str, Any]:
    """Process a single URL through the complete fusion pipeline (convert → classify → enrich → extract)."""
    logger = get_fusion_logger(__name__)
    temp_file = None
    
    try:
        if not quiet:
            logger.stage(f"🌐 Processing URL: {url}")
        
        # Download URL content to memory with configurable timeout
        url_timeout = config.get('inputs', {}).get('url_timeout_seconds', 15) if config else 15
        max_size_mb = config.get('inputs', {}).get('max_file_size_mb', 10.0) if config else 10.0
        content, content_type, file_ext, status_code, headers = download_url_content(url, max_size_mb=max_size_mb, timeout_seconds=url_timeout, session=session)
        
        # Validate URL conversion success before proceeding to classification
        success, message, validation_metadata = ConversionSuccess.validate_url(
            status_code, len(content), content_type
        )
        
        # Always log validation results (success or failure)
        if not success:
            logger.logger.error(f"❌ URL validation failed: {message}")
            logger.logger.error(f"📊 Status: {status_code}, Size: {len(content)} bytes, Type: {content_type}")
        else:
            logger.success(f"✅ {message} - Status: {status_code}")
        
        # Create safe filename from URL for final output
        safe_filename = create_filename_from_url(url)
        
        # Convert HTML to markdown content (IN MEMORY - no temp files)
        if success and 'html' in content_type.lower():
            logger.entity(f"🔄 Converting HTML to Markdown for: {content_type}")
            try:
                # Convert HTML content to markdown
                html_content = content.decode('utf-8', errors='ignore')
                markdown_content = convert_html_to_markdown_configurable(html_content, base_url=url, config=config)
                logger.success(f"✅ HTML converted to markdown ({len(markdown_content)} chars)")
            except Exception as e:
                logger.logger.warning(f"⚠️ HTML-to-markdown conversion failed: {e}")
                # Fall back to raw content
                markdown_content = content.decode('utf-8', errors='ignore')
        else:
            # For non-HTML or failed URLs, use raw content
            markdown_content = content.decode('utf-8', errors='ignore') if content else f"Failed to fetch URL: {message}"
        
        # Create InMemoryDocument directly (NO temp files)
        from pipeline.in_memory_document import InMemoryDocument
        
        # Create in-memory document with URL as source
        doc = InMemoryDocument(source_file_path=url, source_url=url)
        doc.markdown_content = markdown_content
        doc.source_filename = f"{safe_filename}.md"
        doc.source_stem = safe_filename
        
        # Add Path-like attributes for pipeline compatibility
        doc.name = doc.source_filename
        doc.suffix = '.md'
        doc.stem = safe_filename
        
        # Add URL metadata
        doc.url_metadata = {
            'source_url': url,
            'content_type': content_type,
            'original_size': len(content),
            'safe_filename': safe_filename,
            'http_status': status_code,
            'response_headers': headers,
            'validation_success': success,
            'validation_message': message
        }
        
        # Process through the COMPLETE PIPELINE (same as files) with all stages
        logger.entity(f"🔄 Processing markdown through complete pipeline like files")
        
        # Create a temporary path-like object that the pipeline expects
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        temp_filename = f"{safe_filename}.md"
        temp_path = temp_dir / temp_filename
        
        # Write our converted markdown to the temp file
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Use the EXACT SAME PIPELINE as regular files - CleanFusionPipeline (not legacy)
        logger.entity(f"🔄 Using Clean Pipeline Architecture for URL (same as files)")
        from fusion_cli import CleanFusionPipeline
        pipeline = CleanFusionPipeline(config or {})
        
        # Process single file through clean pipeline (same as files)
        deployment_manager = DeploymentManager(config or {})
        max_workers = deployment_manager.get_max_workers()
        
        # Use the same process method that files use
        pipeline_metadata = {'output_dir': output_dir or Path.cwd(), 'max_workers': max_workers}
        file_results, pipeline_info = pipeline.process([temp_path], pipeline_metadata)
        
        # Get the result (should be single item)
        if file_results:
            result = file_results[0]
        else:
            raise Exception("Pipeline returned no results")
        
        # The CleanFusionPipeline works with InMemoryDocuments and generates final output
        # Fix the in-memory document to show URL as source instead of temp file
        if hasattr(result, 'markdown_content') and result.markdown_content:
            # Fix the source_file to show URL and add source_type
            import re
            result.markdown_content = re.sub(r'(source_file:\s*)[^\n]+', f'source_file: {url}', result.markdown_content)
            # Add source_type: url right after source_file
            if 'source_type:' not in result.markdown_content:
                result.markdown_content = re.sub(r'(source_file: [^\n]+)', f'\\1\n  source_type: url', result.markdown_content)
            
            # Generate final files with corrected content
            output_dir_path = output_dir or Path.cwd()
            
            # Write corrected markdown file
            markdown_output = output_dir_path / f"{safe_filename}.md"
            with open(markdown_output, 'w', encoding='utf-8') as f:
                f.write(result.markdown_content)
            logger.success(f"📝 Created markdown: {markdown_output.name}")
            
            # Write JSON knowledge file if semantic data exists
            if hasattr(result, 'semantic_json') and result.semantic_json:
                json_output = output_dir_path / f"{safe_filename}.json"
                with open(json_output, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(result.semantic_json, f, indent=2)
                logger.success(f"📊 Created knowledge: {json_output.name}")
        
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()
        
        return result
        
    except Exception as e:
        logger.logger.error(f"❌ Failed to process URL {url}: {e}")
        # Create a failed result object
        from extraction.base_extractor import ExtractionResult
        return ExtractionResult(
            success=False,
            file_path=url,
            pages=0,
            error=str(e)
        )
    finally:
        # Clean up minimal temporary file and metadata file
        if temp_file and Path(temp_file.name).exists():
            try:
                temp_path = Path(temp_file.name)
                # Clean up main temp file
                temp_path.unlink()
                # Clean up metadata file if it still exists
                metadata_file = temp_path.parent / f"{temp_path.stem}_url_metadata.json"
                if metadata_file.exists():
                    metadata_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors


def process_url_file(extractor: BaseExtractor, url_file_path: Path, output_dir: Path = None, config: dict = None) -> List[Dict[str, Any]]:
    """Process URLs from a file (one URL per line)."""
    logger = get_fusion_logger(__name__)
    
    if not url_file_path.exists():
        logger.logger.error(f"❌ URL file not found: {url_file_path}")
        return []
    
    # Read URLs from file
    urls = []
    with open(url_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith('#'):  # Skip empty lines and comments
                urls.append(line)
    
    if not urls:
        logger.logger.warning(f"No URLs found in {url_file_path}")
        return []
    
    logger.stage(f"🔗 Found {len(urls)} URLs in {url_file_path.name}")
    logger.stage(f"🚀 Processing {len(urls)} URLs...")
    
    results = []
    start_time = time.time()
    
    # Get parallel processing configuration from deployment manager
    deployment_manager = DeploymentManager(config)
    max_workers = deployment_manager.get_max_workers()
    
    # Process URLs in parallel using ThreadPoolExecutor (same pattern as file processing)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from requests.adapters import HTTPAdapter
    
    logger.stage(f"🔧 Using {max_workers} parallel workers for URL processing")
    
    # Create optimized session for parallel downloads
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=max_workers * 2,  # Scale with worker count
        pool_maxsize=max_workers * 4,      # Allow more connections per pool
        max_retries=1
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all URL processing tasks with shared session
        future_to_url = {
            executor.submit(process_single_url, extractor, url, output_dir, config, True, session): url
            for url in urls
        }
        
        # Process results as they complete with clean logging
        completed_count = 0
        successful_count = 0
        failed_count = 0
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            completed_count += 1
            
            try:
                result = future.result()
                results.append(result)
                
                # Count successes/failures without verbose logging
                if hasattr(result, 'success') and result.success:
                    successful_count += 1
                else:
                    failed_count += 1
                
                # Show clean progress every 10 URLs
                if completed_count % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = completed_count / elapsed
                    logger.entity(f"📊 Progress: {completed_count}/{len(urls)} URLs processed ({rate:.1f}/sec) - {successful_count} successful, {failed_count} failed")
                    
            except KeyboardInterrupt:
                logger.logger.warning(f"\n⚠️ Processing interrupted by user at URL {completed_count}/{len(urls)}")
                break
            except Exception as e:
                logger.logger.error(f"❌ Error processing URL {url}: {e}")
                failed_count += 1
                continue
    
    # Final summary
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    rate = len(results) / total_time if total_time > 0 else 0
    
    logger.success(f"Completed: {successful} successful, {failed} failed ({rate:.1f} URLs/sec)")
    
    logger.stage(f"\n📊 URL Processing Complete:")
    logger.stage(f"   Total URLs: {len(results)}")
    logger.stage(f"   Successful: {successful}")
    logger.stage(f"   Failed: {failed}")
    logger.stage(f"   Total time: {total_time:.2f}s")
    logger.stage(f"   Average rate: {rate:.1f} URLs/sec")
    
    return results


def process_directory(extractor: BaseExtractor, directory: Path, 
                     file_extensions: List[str] = None, output_dir: Path = None, config: dict = None):
    """Process all files in a directory using full pipeline (not just extraction)."""
    logger = get_fusion_logger(__name__)
    if file_extensions is None:
        file_extensions = ['.txt', '.md', '.pdf', '.docx', '.doc']
    
    # Find all files
    files = []
    for ext in file_extensions:
        files.extend(directory.glob(f"**/*{ext}"))
    
    if not files:
        logger.logger.warning(f"No files found in {directory} with extensions {file_extensions}")
        return []
    
    logger.stage(f"📁 Found {len(files)} files in {directory.name}")
    
    # Show progress indicator for large batches
    if len(files) > 100:
        logger.stage(f"🚀 Processing {len(files)} files (progress shown every 100 files)...")
    else:
        logger.stage(f"🚀 Processing {len(files)} files...")
    
    start_time = time.time()
    
    # Use new clean pipeline architecture (with orchestrated pipeline wrapper)
    pipeline = CleanFusionPipeline(config or {})
    
    # Process through clean pipeline with configurable processors
    pipeline_metadata = {'output_dir': output_dir or Path.cwd(), 'max_workers': 2}
    file_results, pipeline_info = pipeline.process(files, pipeline_metadata)
    batch_result = (file_results, pipeline_info.get('pipeline_timing_ms', 0) / 1000)
    
    # Handle different return signatures (some extractors return resource summary)
    if len(batch_result) == 3:
        results, total_time, resource_summary = batch_result
    else:
        results, total_time = batch_result
        resource_summary = None
    
    # Clean summary
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    rate = len(files) / total_time if total_time > 0 else 0
    
    logger.success(f"Completed: {successful} successful, {failed} failed ({rate:.0f} files/sec)")
    
    # Final statistics
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    logger.stage(f"\n📊 Processing Complete:")
    logger.stage(f"   Total files: {len(results)}")
    logger.stage(f"   Successful: {successful}")
    logger.stage(f"   Failed: {failed}")
    logger.stage(f"   Total time: {total_time:.2f}s")
    logger.stage(f"   Average rate: {len(results)/total_time:.1f} files/sec")
    
    return results


def run_performance_test(extractor: BaseExtractor, max_workers: int) -> Dict[str, Any]:
    """Run performance benchmark test using the configured extractor."""
    logger = get_fusion_logger(__name__)
    logger.stage("🚀 Running MVP-Fusion Performance Test...")
    
    # Create test content
    test_content = """
    OSHA regulation 29 CFR 1926.95 requires all construction workers to wear 
    appropriate personal protective equipment (PPE) including hard hats, 
    safety glasses, and high-visibility clothing when working in designated areas.
    
    For training information, contact safety-coordinator@company.com or call 
    (555) 123-4567 to schedule a session. Training costs $2,500 per group 
    and must be completed by March 15, 2024 at 2:30 PM.
    
    Environmental compliance is monitored by the EPA under regulation 
    40 CFR 261.1. All hazardous materials must be properly disposed of 
    to prevent soil and groundwater contamination.
    
    Temperature monitoring systems must maintain readings between 65-75°F 
    in all work areas. Version 2.1.3 of the monitoring software is required 
    for compliance reporting.
    
    Workers exposed to noise levels above 85 dB must wear hearing protection.
    The permissible exposure limit (PEL) for chemical substances varies by 
    material but must not exceed NIOSH recommended levels.
    
    Emergency procedures require immediate notification of supervisors and 
    evacuation following posted routes. All incidents must be reported 
    within 24 hours to comply with OSHA recordkeeping requirements.
    """
    
    # Test different scenarios
    test_scenarios = [
        ("Small document", test_content[:500], 100),
        ("Medium document", test_content, 50),  
        ("Large document", test_content * 3, 25),
        ("Complex document", test_content * 5, 10)
    ]
    
    results = {}
    
    for scenario_name, content, iterations in test_scenarios:
        logger.stage(f"\n📋 Testing {scenario_name} ({len(content)} chars, {iterations} iterations)...")
        
        start_time = time.time()
        scenario_results = []
        
        # Create temporary test file
        test_file = Path(f"temp_test_doc.txt")
        test_file.write_text(content)
        
        try:
            for i in range(iterations):
                result = extractor.extract_single(test_file, Path.cwd())
                scenario_results.append(result)
        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()
            
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                logger.entity(f"  Progress: {i+1}/{iterations} ({rate:.1f} docs/sec)")
        
        # Calculate statistics
        total_time = time.time() - start_time
        successful = sum(1 for r in scenario_results if r.success)
        
        if successful > 0:
            avg_processing_time = sum(
                r.extraction_time_ms 
                for r in scenario_results if r.success
            ) / successful
            
            total_pages = sum(
                r.page_count
                for r in scenario_results if r.success
            )
            
            docs_per_sec = iterations / total_time
            chars_per_sec = (len(content) * iterations) / total_time
            
            results[scenario_name] = {
                'iterations': iterations,
                'successful': successful,
                'total_time': total_time,
                'docs_per_sec': docs_per_sec,
                'chars_per_sec': chars_per_sec,
                'avg_processing_time_ms': avg_processing_time,
                'total_pages': total_pages,
                'chars_per_doc': len(content)
            }
            
            logger.success(f"{successful}/{iterations} successful")
            logger.entity(f"📊 Rate: {docs_per_sec:.1f} docs/sec")
            logger.entity(f"⚡ Speed: {chars_per_sec:,.0f} chars/sec")
            logger.entity(f"📚 Pages: {total_pages} total")
        else:
            results[scenario_name] = {'error': 'All tests failed'}
    
    return results


def print_performance_summary(extractor: BaseExtractor, max_workers: int):
    """Print comprehensive performance summary."""
    logger = get_fusion_logger(__name__)
    perf = extractor.get_performance_summary()
    
    logger.stage("\n" + "="*60)
    logger.stage("🎯 MVP-FUSION PERFORMANCE SUMMARY")
    logger.stage("="*60)
    logger.stage(f"🔧 Engine: {extractor.__class__.__name__}")
    logger.stage(f"⚡ Peak Performance: {perf.get('pages_per_second', 0):.0f} pages/sec")
    logger.stage(f"📊 Efficiency: {perf.get('success_rate', 0)*100:.1f}% success rate")
    logger.stage(f"🔧 Configuration: {max_workers} workers, {perf.get('total_files', 0)} files processed")
    return
    
    logger.stage(f"\n" + "="*60)
    logger.stage(f"🎯 MVP-FUSION PERFORMANCE SUMMARY")
    logger.stage(f"="*60)
    
    # Pipeline performance
    logger.stage(f"📄 Documents processed: {metrics['documents_processed']}")
    logger.stage(f"⏱️  Average time per doc: {metrics.get('avg_processing_time_per_doc', 0):.3f}s")
    logger.stage(f"🚀 Pages per second: {metrics.get('pages_per_second', 0):.1f}")
    logger.logger.error(f"❌ Error rate: {metrics.get('error_rate', 0):.1%}")
    
    # Engine performance
    fusion_metrics = metrics.get('fusion_engine_metrics', {})
    if fusion_metrics:
        logger.stage(f"\n🔧 Engine Performance:")
        logger.stage(f"   Pages/sec: {fusion_metrics.get('pages_per_second', 0):.1f}")
        logger.stage(f"   Entities/doc: {fusion_metrics.get('entities_per_document', 0):.1f}")
        logger.stage(f"   Engine usage: {fusion_metrics.get('engine_usage', {})}")
    
    # Batch processor performance
    batch_metrics = metrics.get('batch_processor_metrics', {})
    if batch_metrics:
        logger.stage(f"\n📦 Batch Processing:")
        logger.stage(f"   Docs/sec: {batch_metrics.get('documents_per_second', 0):.1f}")
        logger.stage(f"   Parallel efficiency: {batch_metrics.get('parallel_efficiency', 0):.1%}")
        logger.stage(f"   Avg docs/batch: {batch_metrics.get('avg_docs_per_batch', 0):.1f}")
    
    logger.stage(f"\n" + "="*60)


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(
        description="MVP-Fusion: High-Performance Document Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Verbosity Levels:
  -q, --quiet     : Minimal output (errors and final results only)
  (default)       : Normal output (stage progress and key metrics)  
  -v, --verbose   : Detailed output (includes entity counts, memory usage)
  -vv             : Debug output (full diagnostic info with timestamps)

Examples:
  # Basic file processing
  python fusion_cli.py --file document.pdf                    # Normal output
  python fusion_cli.py --file document.pdf -q                 # Quiet mode
  python fusion_cli.py --file document.pdf -v                 # Verbose mode
  python fusion_cli.py --file document.pdf -vv                # Debug mode
  
  # Directory processing with options
  python fusion_cli.py --directory ~/documents/ --extensions .pdf .docx
  python fusion_cli.py --directory ~/documents/ -q            # Process quietly
  python fusion_cli.py --directory ~/documents/ -v --log-file process.log
  
  # URL processing
  python fusion_cli.py --url https://example.com/article      # Single URL
  python fusion_cli.py --url-file urls.txt                    # Multiple URLs from file
  python fusion_cli.py --url-file MVP-FOUNDERS-JOURNEY-50-URLS.md  # Process founder URLs
  
  # Config file processing (NEW: directories by default, URLs opt-in)
  python fusion_cli.py --config config.yaml                   # Process directories only (DEFAULT)
  python fusion_cli.py --config config.yaml --urls            # Process URLs from config
  python fusion_cli.py --config config.yaml --urls -v         # Process URLs with verbose output
  
  # Pipeline control
  python fusion_cli.py --config config/fusion_config.yaml --stages all
  python fusion_cli.py --config config/fusion_config.yaml --convert-only -v
  python fusion_cli.py --config config/fusion_config.yaml --stages convert classify
  
  # Performance testing
  python fusion_cli.py --performance-test                     # Normal output
  python fusion_cli.py --performance-test -vv                 # Full debug info
  
  # Additional output options
  python fusion_cli.py --file doc.pdf --no-color              # Disable colors
  python fusion_cli.py --file doc.pdf --json-logs             # JSON format
  python fusion_cli.py --file doc.pdf -v --log-file out.log   # Log to file
        """
    )
    
    # Input options (optional if config file has directories)
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--file', '-f', type=str, help='Process single file')
    input_group.add_argument('--directory', '-d', type=str, help='Process directory')
    input_group.add_argument('--url', '-u', type=str, help='Process single URL')
    input_group.add_argument('--url-file', type=str, help='Process URLs from file (one URL per line)')
    input_group.add_argument('--config-directories', action='store_true',
                           help='Process all directories specified in config file')
    input_group.add_argument('--performance-test', '-t', action='store_true', 
                           help='Run performance benchmark')
    
    # Configuration options
    parser.add_argument('--config', '-c', type=str, default='config/config.yaml',
                       help='Configuration file path (default: config/config.yaml)')
    parser.add_argument('--urls', action='store_true',
                       help='Process URLs from config file (directories are processed by default)')
    parser.add_argument('--output', '-o', type=str, help='Output directory')
    parser.add_argument('--batch-size', '-b', type=int, default=32, 
                       help='Batch size for parallel processing')
    
    # File options
    parser.add_argument('--extensions', nargs='+', default=['.txt', '.md', '.pdf', '.docx'],
                       help='File extensions to process')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Process directories recursively')
    
    # Performance options
    parser.add_argument('--workers', '-w', type=int, 
                       help='Workers (cores): 1=524 p/s, 4=2014 p/s, 8=3454 p/s (sweet spot), 16=4160 p/s')
    parser.add_argument('--memory-limit', type=int, help='Memory limit in GB')
    parser.add_argument('--profile', '-p', type=str,
                       choices=['local', 'cloudflare', 'aws', 'gcp', 'docker', 'disabled'],
                       help='Deployment profile: local, cloudflare, aws, gcp, docker, disabled')
    parser.add_argument('--list-profiles', action='store_true',
                       help='List all available deployment profiles and exit')
    parser.add_argument('--extractor', '-e', type=str,
                       choices=['highspeed_markdown_general', 'highaccuracy_markdown_general', 
                               'highspeed_json_pdf', 'specialized_markdown_legal'],
                       help='Extraction engine (default: from config file)')
    
    # Pipeline stage options
    parser.add_argument('--stages', nargs='+', 
                       choices=['convert', 'classify', 'enrich', 'normalize', 'extract', 'all'],
                       default=['all'],
                       help='Pipeline stages to run (default: all)')
    parser.add_argument('--convert-only', action='store_true',
                       help='Run only conversion stage (PDF -> Markdown)')
    parser.add_argument('--classify-only', action='store_true', 
                       help='Run only classification stage')
    parser.add_argument('--enrich-only', action='store_true',
                       help='Run only enrichment stage')
    parser.add_argument('--normalize-only', action='store_true',
                       help='Run only entity normalization stage')
    parser.add_argument('--extract-only', action='store_true',
                       help='Run only semantic extraction stage')
    
    # Output options
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('--quiet', '-q', action='store_true',
                                help='Quiet mode: minimal output showing only errors and final results (PAGES/SEC, SUCCESS RATE)')
    verbosity_group.add_argument('--verbose', '-v', action='count', default=0,
                                help='Increase verbosity (use -v for detailed progress with entity counts, -vv for full debug with timestamps)')
    parser.add_argument('--log-file', type=str, 
                       help='Save all output to specified file (useful with -v or -vv for debugging)')
    parser.add_argument('--no-color', action='store_true', 
                       help='Disable colored terminal output (useful for log files or CI/CD pipelines)')
    parser.add_argument('--json-logs', action='store_true', 
                       help='Output logs in JSON format for structured logging systems')
    parser.add_argument('--export-metrics', type=str, help='Export metrics to JSON file')
    
    args = parser.parse_args()
    
    # Load base configuration first to get logging defaults
    config = _load_and_override_config(args)
    
    # Handle profile listing (early exit)
    if args.list_profiles:
        print("🚀 Available Deployment Profiles:")
        print("=" * 60)
        profiles = DeploymentManager.list_available_profiles(config)
        for profile_name, profile_info in profiles.items():
            status = "✅ Enabled" if profile_info['enabled'] else "❌ Disabled"
            print(f"\n📦 {profile_name.upper()}")
            print(f"   Name: {profile_info['name']}")
            print(f"   Description: {profile_info['description']}")
            print(f"   Workers: {profile_info['max_workers']}")
            print(f"   Memory: {profile_info['memory_mb']}MB" if isinstance(profile_info['memory_mb'], int) else f"   Memory: {profile_info['memory_mb']}")
            print(f"   Status: {status}")
        
        current_profile = config.get('deployment', {}).get('active_profile', 'local')
        print(f"\n🔧 Current Active Profile: {current_profile}")
        print(f"\n💡 Usage: python fusion_cli.py --profile {current_profile} [other options]")
        sys.exit(0)
    
    # Setup logging with proper verbosity levels
    # Priority: CLI flags > config file > defaults
    if args.quiet:
        verbosity = 0  # QUIET mode
    elif args.verbose:
        verbosity = min(args.verbose + 1, 3)  # -v=2 (VERBOSE), -vv=3 (DEBUG)
    else:
        # Use config file setting or default to NORMAL (1)
        verbosity = config.get('logging', {}).get('verbosity', 1)
    
    # Get logging options from config or CLI
    log_file_config = config.get('logging', {}).get('file')
    log_file = Path(args.log_file) if args.log_file else (Path(log_file_config) if log_file_config else None)
    
    use_colors_config = config.get('logging', {}).get('use_colors', True)
    use_colors = not args.no_color and use_colors_config
    
    json_format_config = config.get('logging', {}).get('json_format', False)
    json_format = args.json_logs or json_format_config
    
    setup_logging(
        verbosity=verbosity,
        log_file=log_file,
        use_colors=use_colors,
        json_format=json_format
    )
    
    # Get logger for CLI module
    logger = get_fusion_logger(__name__)
    
    try:
        # Config was already loaded above for logging setup
        # No need to reload here
        
        # Initialize configured extractor
        extractor_name = args.extractor or config.get('extractor', {}).get('name', 'highspeed_markdown_general')
        extractor_config = {
            'page_limit': config.get('performance', {}).get('page_limit', 100)
        }
        extractor = create_extractor(extractor_name, extractor_config)
        
        # Initialize deployment manager with optional profile override
        deployment_manager = DeploymentManager(config, args.profile)
        max_workers = deployment_manager.get_max_workers(args.workers)
        
        logger.staging(f"MVP-Fusion Engine: {extractor.name}")
        logger.staging(f"Performance: {extractor.description}")
        logger.staging(f"Workers: {max_workers} | Formats: {len(extractor.get_supported_formats())}")
        
        # Display deployment profile summary
        profile_summary = deployment_manager.get_profile_summary()
        if profile_summary['memory_management_enabled']:
            memory_info = f" | Memory: {profile_summary['memory_limit_mb']}MB" if profile_summary['memory_limit_mb'] else " | Memory: Unlimited"
        else:
            memory_info = " | Memory Management: Disabled"
        logger.staging(f"Profile: {profile_summary['name']}{memory_info}")
        
        # Determine output directory
        output_dir = None
        if args.output:
            output_dir = Path(args.output)
        elif config.get('output', {}).get('base_directory'):
            output_dir = Path(config['output']['base_directory']).expanduser()
        
        if output_dir:
            logger.staging(f"Output directory: {output_dir}")
        
        # Execute command
        if args.file:
            # Process single file through full pipeline (not just extraction)
            file_path = Path(args.file)
            if not file_path.exists():
                logger.logger.error(f"❌ File not found: {file_path}")
                sys.exit(1)
            
            # Use new clean pipeline architecture for single file processing
            pipeline = CleanFusionPipeline(config)
            
            # Process single file through clean pipeline with configurable processors
            pipeline_metadata = {'output_dir': output_dir or Path.cwd(), 'max_workers': max_workers}
            file_results, pipeline_info = pipeline.process([file_path], pipeline_metadata)
            
            # Extract timing information
            extraction_time = pipeline_info.get('pipeline_timing_ms', 0) / 1000  # Convert to seconds
            resource_summary = pipeline_info  # Pipeline provides detailed performance metrics
            
            # Get the result (should be single item)
            results = file_results
            result = results[0] if results else None
            
        elif args.url:
            # Process single URL
            result = process_single_url(extractor, args.url, output_dir, config)
            
        elif args.url_file:
            # Process URLs from file
            url_file_path = Path(args.url_file)
            if not url_file_path.exists():
                logger.logger.error(f"❌ URL file not found: {url_file_path}")
                sys.exit(1)
            
            results = process_url_file(extractor, url_file_path, output_dir, config)
            
        elif args.directory:
            # Process directory
            directory = Path(args.directory).expanduser()
            if not directory.exists():
                logger.logger.error(f"❌ Directory not found: {directory}")
                sys.exit(1)
            
            results = process_directory(extractor, directory, args.extensions, output_dir, config)
            
        elif args.config_directories:
            # Process all directories from config
            config_dirs = config.get('inputs', {}).get('directories', [])
            if not config_dirs:
                logger.logger.error(f"❌ No directories specified in config file")
                sys.exit(1)
            
            logger.stage(f"🗂️  Processing {len(config_dirs)} directories from config:")
            for config_dir in config_dirs:
                logger.stage(f"   - {config_dir}")
            
            all_results = []
            for config_dir in config_dirs:
                directory = Path(config_dir).expanduser()
                if not directory.exists():
                    logger.logger.warning(f"⚠️  Directory not found: {directory} (skipping)")
                    continue
                    
                logger.stage(f"\n📂 Processing directory: {directory}")
                extensions = config.get('files', {}).get('supported_extensions', args.extensions)
                results = process_directory(extractor, directory, extensions, output_dir, config)
                all_results.extend(results if isinstance(results, list) else [results])
            
            logger.success(f"\n✅ Processed {len(all_results)} total files across all directories")
            
        elif args.config and not args.file and not args.directory and not args.url and not args.url_file and not args.performance_test:
            # Auto-process from config file when only --config is provided
            # DIRECTORIES ARE DEFAULT - URLs only processed if --urls flag provided
            config_dirs = config.get('inputs', {}).get('directories', [])
            config_urls = config.get('inputs', {}).get('urls', []) if args.urls else []
            config_url_files = config.get('inputs', {}).get('url_files', []) if args.urls else []
            
            if (config_dirs and not args.urls) or (args.urls and (config_urls or config_url_files)):
                all_files = []
                all_urls = []
                
                # Process directories if specified (DEFAULT behavior) BUT NOT if --urls flag is provided
                if config_dirs and not args.urls:
                    logger.staging(f"Processing {len(config_dirs)} directories from config (default):")
                    for config_dir in config_dirs:
                        logger.staging(f"   - {config_dir}")
                    
                    extensions = config.get('files', {}).get('supported_extensions', args.extensions)
                
                    for config_dir in config_dirs:
                        directory = Path(config_dir).expanduser()
                        if not directory.exists():
                            logger.logger.warning(f"⚠️  Directory not found: {directory} (skipping)")
                            continue
                        
                        # Collect files from this directory
                        files = []
                        for ext in extensions:
                            files.extend(directory.glob(f"**/*{ext}"))
                        all_files.extend(files)
                elif config_dirs and args.urls:
                    logger.staging(f"⚪ Skipping {len(config_dirs)} directories (--urls flag provided - URLs only)")
                    for config_dir in config_dirs:
                        logger.staging(f"   - {config_dir} (skipped)")  
                
                # Process URLs if specified (EXPLICIT --urls flag required)
                if args.urls and config_urls:
                    logger.stage(f"🔗 Processing {len(config_urls)} URLs from config (--urls flag provided):")
                    all_urls.extend(config_urls)
                
                # Process URL files if specified (EXPLICIT --urls flag required)
                if args.urls and config_url_files:
                    logger.stage(f"📄 Processing {len(config_url_files)} URL files from config (--urls flag provided):")
                    for url_file_path in config_url_files:
                        url_file = Path(url_file_path).expanduser()
                        if not url_file.exists():
                            logger.logger.warning(f"⚠️  URL file not found: {url_file} (skipping)")
                            continue
                        
                        # Read URLs from file
                        with open(url_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    all_urls.append(line)
                
                if not all_files and not all_urls:
                    if not config_dirs and not args.urls:
                        logger.logger.error(f"❌ No directories found in config. Use --urls flag to process URLs.")
                    elif args.urls and not config_urls and not config_url_files:
                        logger.logger.error(f"❌ No URLs found in config despite --urls flag.")
                    elif config_dirs and args.urls:
                        logger.logger.error(f"❌ Directories ignored due to --urls flag, but no URLs found in config.")
                    else:
                        logger.logger.error(f"❌ No files or URLs found")
                    sys.exit(1)
                
                # Show summary before processing
                file_types = {}
                for file_path in all_files:
                    ext = file_path.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
                
                logger.staging(f"📊 PROCESSING SUMMARY:")
                logger.staging(f"   Total files: {len(all_files)}")
                if file_types:
                    logger.staging(f"   File types: {dict(file_types)}")
                logger.staging(f"   Total URLs: {len(all_urls)}")
                logger.staging(f"   Workers: {max_workers}")
                
                # Process files and URLs
                all_results = []
                start_time = time.time()
                
                # Process files in batch if any
                if all_files:
                    logger.staging(f"Starting file batch processing with clean pipeline architecture...")
                
                    # Use new clean pipeline architecture
                    pipeline = CleanFusionPipeline(config)
                    
                    # Process files through clean pipeline with configurable processors
                    pipeline_metadata = {'output_dir': output_dir or Path.cwd(), 'max_workers': max_workers}
                    file_results, pipeline_info = pipeline.process(all_files, pipeline_metadata)
                    extraction_time = pipeline_info.get('pipeline_timing_ms', 0) / 1000  # Convert to seconds
                    
                    all_results.extend(file_results)
                    resource_summary = pipeline_info  # Pipeline provides detailed performance metrics
                
                # Process URLs in batch if any (same as files)
                if all_urls:
                    logger.stage(f"\n🌐 Processing {len(all_urls)} URLs...")
                    
                    # First, download and convert all URLs to markdown temp files
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir())
                    url_temp_files = []
                    url_metadata_map = {}
                    
                    for i, url in enumerate(all_urls, 1):
                        try:
                            logger.entity(f"📋 Downloading URL {i}/{len(all_urls)}: {url[:60]}...")
                            
                            # Download URL content
                            url_timeout = config.get('inputs', {}).get('url_timeout_seconds', 15)
                            max_size_mb = config.get('inputs', {}).get('max_file_size_mb', 10.0)
                            content, content_type, file_ext, status_code, headers = download_url_content(
                                url, max_size_mb=max_size_mb, timeout_seconds=url_timeout
                            )
                            
                            # Validate URL
                            success, message, validation_metadata = ConversionSuccess.validate_url(
                                status_code, len(content), content_type
                            )
                            
                            if success and 'html' in content_type.lower():
                                # Convert HTML to markdown
                                logger.entity(f"🔄 Converting HTML to Markdown")
                                html_content = content.decode('utf-8', errors='ignore')
                                markdown_content = convert_html_to_markdown_configurable(html_content, base_url=url, config=config)
                            else:
                                markdown_content = content.decode('utf-8', errors='ignore') if content else f"Failed: {message}"
                            
                            # Create temp file for this URL
                            safe_filename = create_filename_from_url(url)
                            temp_filename = f"{safe_filename}.md"
                            temp_path = temp_dir / temp_filename
                            
                            # Write markdown to temp file
                            with open(temp_path, 'w', encoding='utf-8') as f:
                                f.write(markdown_content)
                            
                            url_temp_files.append(temp_path)
                            url_metadata_map[str(temp_path)] = {
                                'url': url,
                                'safe_filename': safe_filename,
                                'content_type': content_type,
                                'original_size': len(content)
                            }
                            
                        except Exception as e:
                            logger.logger.error(f"❌ Error downloading URL {i}: {e}")
                            continue
                    
                    # Now process all URL temp files through a SINGLE pipeline instance
                    if url_temp_files:
                        logger.stage(f"🚀 Processing {len(url_temp_files)} URLs through pipeline...")
                        
                        # Use the SAME pipeline instance as files (or create one if not exists)
                        if 'pipeline' not in locals():
                            pipeline = CleanFusionPipeline(config)
                        
                        # Process all URL markdown files in batch
                        pipeline_metadata = {'output_dir': output_dir or Path.cwd(), 'max_workers': max_workers}
                        url_results, url_pipeline_info = pipeline.process(url_temp_files, pipeline_metadata)
                        
                        # Fix YAML frontmatter and rename files for each result
                        for result, temp_path in zip(url_results, url_temp_files):
                            metadata = url_metadata_map.get(str(temp_path), {})
                            url = metadata.get('url', '')
                            safe_filename = metadata.get('safe_filename', temp_path.stem)
                            
                            # Find and fix the output files
                            output_dir_path = output_dir or Path.cwd()
                            temp_stem = temp_path.stem
                            
                            # Find the generated files
                            potential_md = output_dir_path / f"{temp_stem}.md"
                            potential_json = output_dir_path / f"{temp_stem}.json"
                            
                            if potential_md.exists():
                                # Read and fix YAML
                                with open(potential_md, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                import re
                                content = re.sub(r'(source_file:\s*)[^\n]+', f'source_file: {url}', content)
                                # Add source_type: url right after source_file if not present
                                if 'source_type:' not in content:
                                    content = re.sub(r'(source_file: [^\n]+)', f'\\1\n  source_type: url', content)
                                
                                with open(potential_md, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                
                                # Rename files if needed
                                new_md_output = potential_md.parent / f"{safe_filename}.md"
                                if potential_md != new_md_output:
                                    potential_md.rename(new_md_output)
                                
                                if potential_json.exists():
                                    new_json_output = potential_json.parent / f"{safe_filename}.json"
                                    potential_json.rename(new_json_output)
                        
                        # Clean up temp files
                        for temp_path in url_temp_files:
                            if temp_path.exists():
                                temp_path.unlink()
                        
                        all_results.extend(url_results)
                
                results = all_results
                    
                # TIMING FIX: Use actual processing time, not total elapsed time
                if 'extraction_time' in locals():
                    processing_time = extraction_time
                    initialization_time = (time.time() - start_time) - extraction_time
                else:
                    processing_time = time.time() - start_time  # Fallback
                    initialization_time = 0
                
                # Calculate comprehensive metrics (works with both InMemoryDocument and ExtractionResult objects)
                successful = sum(1 for doc in results if getattr(doc, 'success', True))
                failed = len(results) - successful
                total_pages = sum(getattr(doc, 'pages_processed', getattr(doc, 'pages', 1)) for doc in results if getattr(doc, 'success', True))
                
                # Calculate input data sizes by scanning all attempted files directly
                total_input_bytes = 0
                skipped_large = 0
                
                # Scan all files that were attempted (not just results)
                for file_path in all_files:
                    try:
                        input_size = file_path.stat().st_size
                        total_input_bytes += input_size
                    except:
                        pass
                
                # Add estimated size for URLs (can't measure precisely)
                if all_urls:
                    estimated_url_bytes = len(all_urls) * 50000  # Estimate 50KB per URL
                    total_input_bytes += estimated_url_bytes
                
                # Count skipped files from results
                for doc in results:
                    if not getattr(doc, 'success', True) and getattr(doc, 'error_message', None) and "pages (>100 limit)" in getattr(doc, 'error_message', ""):
                        skipped_large += 1
                
                # Calculate output size from in-memory documents (exact calculation)
                total_output_bytes = 0
                output_file_count = 0
                total_memory_mb = 0
                
                for doc in results:
                    if getattr(doc, 'success', True):
                        # Handle both InMemoryDocument and ExtractionResult objects
                        if hasattr(doc, 'get_memory_footprint'):
                            # InMemoryDocument - get memory footprint
                            doc_memory = doc.get_memory_footprint()
                            total_output_bytes += doc_memory
                            total_memory_mb += doc_memory / 1024 / 1024
                        elif hasattr(doc, 'output_path') and doc.output_path:
                            # ExtractionResult - get file size on disk
                            try:
                                output_path = Path(doc.output_path)
                                if output_path.exists():
                                    file_size = output_path.stat().st_size
                                    total_output_bytes += file_size
                                    total_memory_mb += file_size / 1024 / 1024
                            except:
                                # If we can't get file size, skip it
                                pass
                        output_file_count += 1
                
                logger.entity(f"   💾 In-memory processing: {total_memory_mb:.1f}MB total document memory")
                
                # Calculate metrics
                input_mb = total_input_bytes / 1024 / 1024
                output_mb = total_output_bytes / 1024 / 1024
                throughput_mb_sec = input_mb / processing_time if processing_time > 0 else 0
                compression_ratio = input_mb / output_mb if output_mb > 0 else 0
                pages_per_sec = total_pages / processing_time if processing_time > 0 else 0
                
                # True failures vs skips and warnings
                true_failures = failed - skipped_large
                warnings_count = sum(1 for doc in results if getattr(doc, 'success', True) and getattr(doc, 'error_message', None))
                
                # Show phase-by-phase performance breakdown (skip if using orchestrated pipeline)
                if 'pipeline' in locals() and (not hasattr(pipeline, 'orchestrated_pipeline') or not pipeline.orchestrated_pipeline):
                    phase_report = get_phase_performance_report()
                    if phase_report and "📊 PHASE PERFORMANCE:" in phase_report:
                        logger.stage(phase_report)
                
                logger.stage(f"\n🚀 PROCESSING PERFORMANCE:")
                logger.stage(f"   🚀 PAGES/SEC: {pages_per_sec:.0f} (overall pipeline)")
                logger.stage(f"   ⚡ THROUGHPUT: {throughput_mb_sec:.1f} MB/sec raw document processing")
                
                # Add pipeline performance breakdown if available
                if 'resource_summary' in locals() and resource_summary and 'phase_results' in resource_summary:
                    logger.stage(f"\n🔧 CLEAN PIPELINE PERFORMANCE:")
                    phase_results = resource_summary['phase_results']
                    total_pipeline_ms = resource_summary.get('pipeline_timing_ms', 0)
                    processor_type = resource_summary.get('processor_type', 'unknown')
                    
                    logger.stage(f"   🏗️  Pipeline Architecture: Clean Phase Separation")
                    logger.stage(f"   🔧 Primary Processor: {processor_type}")
                    logger.stage(f"   ⚡ Pipeline Execution Time: {total_pipeline_ms:.2f}ms")
                    
                    for phase in phase_results:
                        phase_name = phase['phase']
                        timing_ms = phase['timing_ms']
                        success_status = '✅' if phase['success'] else '❌'
                        percentage = (timing_ms / total_pipeline_ms * 100) if total_pipeline_ms > 0 else 0
                        
                        if timing_ms > 0:
                            pages_sec = total_pages / (timing_ms / 1000) if timing_ms > 0 else 0
                            logger.stage(f"   • {success_status} {phase_name}: {timing_ms:.2f}ms ({percentage:.1f}%) - {pages_sec:.0f} pages/sec")
                        else:
                            logger.stage(f"   • {success_status} {phase_name}: <1ms ({percentage:.1f}%)")
                    
                    # Show sidecar test results if available
                    sidecar_results = resource_summary.get('sidecar_results', {})
                    if sidecar_results:
                        logger.stage(f"\n🧪 SIDECAR A/B TEST RESULTS:")
                        for test_name, test_result in sidecar_results.items():
                            if test_result['success']:
                                timing_ms = test_result['timing_ms']
                                comparison = "faster" if timing_ms < total_pipeline_ms else "slower"
                                diff_ms = abs(timing_ms - total_pipeline_ms)
                                logger.stage(f"   • {test_name}: {timing_ms:.2f}ms ({diff_ms:.2f}ms {comparison})")
                            else:
                                logger.stage(f"   • {test_name}: ❌ Failed - {test_result.get('error', 'Unknown error')}")
                
                # Legacy stage timing support (fallback)
                elif 'resource_summary' in locals() and resource_summary and 'stage_timings' in resource_summary:
                    logger.stage(f"\n📊 LEGACY STAGE-BY-STAGE PERFORMANCE:")
                    stage_timings = resource_summary['stage_timings']
                    total_pages_for_stages = resource_summary.get('total_pages', total_pages)
                    
                    # Define stage display names
                    stage_names = {
                        'load': 'Conversion',
                        'classify': 'Classification',
                        'enrich': 'Enrichment',
                        'extract': 'Extraction',
                        'write': 'Writing'
                    }
                    
                    for stage_key, display_name in stage_names.items():
                        if stage_key in stage_timings:
                            timing = stage_timings[stage_key]
                            time_s = timing['time_ms'] / 1000
                            pages_sec = timing['pages_per_sec']
                            logger.stage(f"   • {display_name}: ~{pages_sec:,.0f} pages/sec ({time_s:.1f}s for {total_pages_for_stages:,} pages)")
                
                logger.success(f"\n✅ DATA TRANSFORMATION SUMMARY:")
                logger.stage(f"   📊 INPUT: {input_mb:.0f} MB across {len(results)} files ({total_pages:,} pages)")
                logger.stage(f"   📊 OUTPUT: {output_mb:.1f} MB in {output_file_count} markdown files")
                if output_mb > 0:
                    compression_percent = ((input_mb - output_mb) / input_mb) * 100
                    logger.stage(f"   🗜️  COMPRESSION: {compression_percent:.1f}% smaller (eliminated formatting, images, bloat)")
                else:
                    logger.stage(f"   🗜️  COMPRESSION: Unable to calculate (output scanning issue)")
                logger.stage(f"   📁 RESULTS: {successful} successful")
                if skipped_large > 0:
                    logger.stage(f"   ⏭️  SKIPPED: {skipped_large} files (>100 pages, too large for this mode)")
                if true_failures > 0:
                    logger.logger.error(f"   ❌ FAILED: {true_failures} files (corrupted or unsupported)")
                if warnings_count > 0:
                    logger.logger.warning(f"   ⚠️  WARNINGS: {warnings_count} files (minor PDF issues, but text extracted successfully)")
                logger.stage(f"   ⚡ PIPELINE PROCESSING TIME: {processing_time:.2f}s")
                if initialization_time > 0:
                    logger.stage(f"   🔧 INITIALIZATION TIME: {initialization_time:.2f}s")
                total_time = processing_time + initialization_time
                logger.stage(f"   ⏱️  TOTAL TIME: {total_time:.2f}s")
                
                # Add system resource information if available
                if 'resource_summary' in locals() and resource_summary:
                    logger.stage(f"\n💻 PROCESSING FOOTPRINT:")
                    if 'shared_memory_architecture' in resource_summary:
                        # Shared memory architecture stats
                        logger.stage(f"   🏊 SHARED MEMORY: {resource_summary['current_memory_mb']:.1f}MB")
                        logger.stage(f"   ⚡ MEMORY SAVINGS: {resource_summary['memory_efficiency_gain_percent']:.1f}%")
                        logger.stage(f"   📊 DOCUMENTS IN POOL: {resource_summary['documents_in_shared_pool']}")
                        logger.stage(f"   🌐 EDGE READY: {'✅ CloudFlare compatible' if resource_summary['edge_deployment_ready']['cloudflare_workers_compatible'] else '❌ Too large'}")
                    elif 'cpu_workers_used' in resource_summary:
                        # Traditional architecture stats
                        logger.stage(f"   🖥️  WORKERS: {resource_summary['cpu_workers_used']}/{resource_summary['cpu_cores_total']} cores (1 worker = 1 core)")
                        logger.entity(f"   🧠 MEMORY: {resource_summary['memory_peak_mb']:.1f} MB peak usage")
                        if resource_summary.get('memory_used_mb', 0) > 0:
                            logger.entity(f"   📈 PROCESSING MEMORY: {resource_summary['memory_used_mb']:.1f} MB during extraction")
                        logger.stage(f"   ⚡ EFFICIENCY: {resource_summary['efficiency_pages_per_worker']:.0f} pages/worker, {resource_summary['efficiency_mb_per_worker']:.1f} MB/worker")
                
                # Add sidecar status reporting
                if 'pipeline' in locals():
                    if hasattr(pipeline, 'sidecar_tests') and pipeline.sidecar_tests:
                        logger.stage(f"\n🧪 SIDECAR A/B TESTING STATUS:")
                        for sidecar_name, sidecar_processor in pipeline.sidecar_tests.items():
                            processor_type = type(sidecar_processor).__name__
                            logger.stage(f"   ✅ {sidecar_name}: ACTIVATED ({processor_type})")
                            logger.stage(f"      └─ Phase: document_processing")
                    elif hasattr(pipeline, 'config') and pipeline.config.get('pipeline', {}).get('document_processing', {}).get('sidecar_test'):
                        configured_sidecar = pipeline.config['pipeline']['document_processing']['sidecar_test']
                        logger.stage(f"\n🧪 SIDECAR A/B TESTING STATUS:")
                        logger.stage(f"   ❌ {configured_sidecar}: CONFIGURED BUT FAILED TO ACTIVATE")
                        logger.stage(f"      └─ Phase: document_processing (check import errors above)")
                    else:
                        logger.stage(f"\n🧪 SIDECAR A/B TESTING STATUS:")
                        logger.stage(f"   ⚪ No sidecars configured")
                else:
                    logger.stage(f"\n🧪 SIDECAR A/B TESTING STATUS:")
                    logger.stage(f"   ⚪ No pipeline created (URLs only processing)")
                
                logger.success(f"   ✅ SUCCESS RATE: {(successful/len(results)*100):.1f}% ({successful}/{len(results)})")
            else:
                logger.logger.error(f"❌ No directories found in config file. Add directories to config or use --file, --directory, --url, or --url-file.")
                logger.logger.info(f"💡 Tip: Use --urls flag to process URLs from config file.")
                sys.exit(1)
            
        elif args.performance_test:
            # Run performance test
            test_results = run_performance_test(extractor, max_workers)
            
            logger.stage(f"\n🏆 Performance Test Results:")
            for scenario, result in test_results.items():
                if 'error' not in result:
                    logger.stage(f"   {scenario}:")
                    logger.stage(f"     Rate: {result['docs_per_sec']:.1f} docs/sec")
                    logger.stage(f"     Speed: {result['chars_per_sec']:,.0f} chars/sec")
        
        # Processing complete - no additional summary needed
        
        # Export metrics if requested (UltraFastFusion doesn't have built-in metrics export)
        if args.export_metrics:
            metrics_data = {
                'extractor_workers': max_workers,
                'performance_metrics': extractor.get_performance_summary()
            }
            with open(args.export_metrics, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            logger.stage(f"📊 Basic metrics exported to {args.export_metrics}")
        
        
    except KeyboardInterrupt:
        logger.logger.warning(f"\n⚠️ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.logger.error(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _load_and_override_config(args) -> dict:
    """Load config file and apply CLI overrides (industry best practice)."""
    import yaml
    from pathlib import Path
    
    # Step 1: Load base configuration
    config = {}
    config_path = Path(args.config)
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        print(f"📋 Config: {config_path}")  # Keep this as print since logger isn't available yet
    else:
        if args.config == 'config/config.yaml':  # Default config missing
            print(f"❌ Default configuration file not found: {args.config}")
            print(f"💡 Please create config/config.yaml or specify a config file with --config")
            print(f"💡 Example: python fusion_cli.py --config /path/to/your/config.yaml")
        else:  # User-specified config missing
            print(f"❌ Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Step 2: Apply CLI overrides to config
    
    # Override pipeline stages based on CLI arguments
    if not config.get('pipeline'):
        config['pipeline'] = {}
    if not config['pipeline'].get('stages'):
        config['pipeline']['stages'] = {}
    
    # Determine which stages to run from CLI args
    if args.convert_only:
        stages_to_run = ['convert']
    elif args.classify_only:
        stages_to_run = ['classify']
    elif args.enrich_only:
        stages_to_run = ['enrich']
    elif args.normalize_only:
        stages_to_run = ['normalize']
    elif args.extract_only:
        stages_to_run = ['extract']
    elif 'all' in args.stages:
        stages_to_run = ['convert', 'classify', 'enrich', 'normalize', 'extract']
    else:
        stages_to_run = args.stages
    
    # Set stage flags in config
    for stage in ['convert', 'classify', 'enrich', 'normalize', 'extract']:
        config['pipeline']['stages'][stage] = stage in stages_to_run
    
    # Store stages list for reference
    config['pipeline']['stages_to_run'] = stages_to_run
    
    # Override other settings
    if args.batch_size:
        if not config.get('performance'):
            config['performance'] = {}
        config['performance']['batch_size'] = args.batch_size
    
    if args.workers:
        if not config.get('performance'):
            config['performance'] = {}
        config['performance']['max_workers'] = args.workers
    
    if args.memory_limit:
        if not config.get('performance'):
            config['performance'] = {}
        config['performance']['max_memory_usage_gb'] = args.memory_limit
    
    return config


if __name__ == "__main__":
    main()