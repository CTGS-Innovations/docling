#!/usr/bin/env python3
"""
High-Performance PDF Processing System
=====================================

Implements the dual-path architecture for ultra-fast document processing:
1. Fast text extraction (100+ pages/second)
2. Intelligent visual element queuing
3. Universal document tagging and classification
4. Progressive enhancement with GPU processing

This system delivers immediate text results while queuing visual elements
for enhanced processing, achieving enterprise-scale throughput.
"""

import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio
import concurrent.futures
import argparse

# Import our custom modules
from pdf_complexity_analyzer import PDFComplexityAnalyzer, ProcessingStrategy, ComplexityMetrics
from fast_text_extractor import FastTextExtractor, ExtractionResult
from universal_document_tagger import UniversalDocumentTagger, DocumentTags
from visual_queue_manager import VisualQueueManager, ElementType, Priority


@dataclass
class ProcessingResult:
    """Complete processing result for a document."""
    success: bool
    file_path: Path
    processing_strategy: ProcessingStrategy
    extraction_result: ExtractionResult
    document_tags: DocumentTags
    
    # Output content
    markdown_content: str
    metadata_header: str
    
    # Performance metrics
    total_processing_time: float
    text_extraction_time: float
    tagging_time: float
    complexity_analysis_time: float
    
    # Visual processing info
    visual_jobs_queued: int
    visual_jobs_completed: int
    pending_visual_jobs: List[str]
    
    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = None


@dataclass
class BatchProcessingStats:
    """Statistics for batch processing operations."""
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    
    # Strategy breakdown
    fast_text_files: int = 0
    vlm_files: int = 0
    hybrid_files: int = 0
    
    # Performance metrics
    total_time: float = 0.0
    average_time_per_file: float = 0.0
    throughput_files_per_minute: float = 0.0
    
    # Visual processing
    total_visual_jobs: int = 0
    completed_visual_jobs: int = 0
    
    # Text extraction performance
    total_pages_processed: int = 0
    pages_per_second: float = 0.0
    
    # File size performance
    total_bytes_processed: int = 0
    megabytes_per_second: float = 0.0


class HighPerformancePDFProcessor:
    """
    High-performance document processor with dual-path architecture.
    
    Combines fast text extraction with intelligent visual processing
    to achieve enterprise-scale throughput while maintaining quality.
    """
    
    def __init__(self, max_visual_workers: int = 2, visual_batch_timeout: float = 5.0,
                 enable_visual_processing: bool = True, enable_document_tagging: bool = True,
                 enable_tables: bool = True, enable_images: bool = True, 
                 text_only_mode: bool = False, force_strategy: Optional[str] = None):
        # Initialize components
        self.complexity_analyzer = PDFComplexityAnalyzer()
        self.text_extractor = FastTextExtractor(text_only_mode=text_only_mode)  # Pass text_only_mode flag
        self.document_tagger = UniversalDocumentTagger()
        
        # Configuration parameters
        self.enable_visual_processing = enable_visual_processing and not text_only_mode
        self.enable_document_tagging = enable_document_tagging
        self.enable_tables = enable_tables
        self.enable_images = enable_images
        self.text_only_mode = text_only_mode
        self.force_strategy = force_strategy
        self.fast_text_confidence_threshold = 0.8
        
        # Initialize visual queue only if visual processing is enabled
        if self.enable_visual_processing:
            self.visual_queue = VisualQueueManager(
                max_workers=max_visual_workers,
                batch_timeout=visual_batch_timeout
            )
            # Give worker threads a moment to start up
            import time
            time.sleep(0.1)
        else:
            self.visual_queue = None
        
        # Performance tracking
        self.processing_stats = BatchProcessingStats()
        
    def process_document(self, file_path: Path, output_dir: Optional[Path] = None) -> ProcessingResult:
        """
        Process a single document using the optimal strategy.
        
        Args:
            file_path: Path to document to process
            output_dir: Optional output directory (default: same as input)
        
        Returns:
            Complete processing result
        """
        start_time = time.time()
        
        if output_dir is None:
            output_dir = file_path.parent
        
        print(f"🚀 Processing: {file_path.name}")
        
        try:
            # Step 1: Analyze document complexity (target: <100ms)
            complexity_start = time.time()
            
            if file_path.suffix.lower() == '.pdf':
                try:
                    complexity_metrics = self.complexity_analyzer.analyze(file_path)
                    processing_strategy = complexity_metrics.processing_strategy
                except Exception as e:
                    print(f"   ⚠️  PDF analysis failed: {e}")
                    print(f"   🔄 Falling back to fast text extraction")
                    processing_strategy = ProcessingStrategy.FAST_TEXT
                    complexity_metrics = None
                
                # Override strategy if forced or in text-only mode
                if self.force_strategy:
                    strategy_map = {
                        'fast': ProcessingStrategy.FAST_TEXT,
                        'vlm': ProcessingStrategy.FULL_VLM,
                        'hybrid': ProcessingStrategy.HYBRID
                    }
                    processing_strategy = strategy_map.get(self.force_strategy.lower(), processing_strategy)
                elif self.text_only_mode:
                    processing_strategy = ProcessingStrategy.FAST_TEXT
            else:
                # Non-PDF files default to fast text extraction
                processing_strategy = ProcessingStrategy.FAST_TEXT
                complexity_metrics = None
            
            complexity_time = time.time() - complexity_start
            
            print(f"   📊 Strategy: {processing_strategy.value} ({complexity_time:.3f}s)")
            
            # Step 2: Fast text extraction (target: 100+ pages/sec for PDFs)
            extraction_start = time.time()
            try:
                extraction_result = self.text_extractor.extract(file_path)
                extraction_time = time.time() - extraction_start
                
                if not extraction_result.success:
                    return self._create_failed_result(
                        file_path, f"Text extraction failed: {extraction_result.error_message}",
                        complexity_time, extraction_time, 0.0
                    )
            except Exception as e:
                extraction_time = time.time() - extraction_start
                print(f"   ❌ Text extraction crashed: {e}")
                return self._create_failed_result(
                    file_path, f"Text extraction crashed: {e}",
                    complexity_time, extraction_time, 0.0
                )
            
            print(f"   📝 Extracted: {extraction_result.word_count:,} words ({extraction_time:.3f}s)")
            
            # Step 3: Document tagging (target: <1s)
            tagging_start = time.time()
            document_tags = None
            
            if self.enable_document_tagging:
                document_tags = self.document_tagger.tag_document(
                    extraction_result.text_content,
                    file_path,
                    extraction_result.metadata
                )
            
            tagging_time = time.time() - tagging_start
            
            if document_tags:
                print(f"   🏷️  Tagged: {document_tags.document_type.value} | {document_tags.domain.value} ({tagging_time:.3f}s)")
            
            # Step 4: Generate immediate markdown output
            markdown_content = self._generate_enhanced_markdown(
                extraction_result, document_tags, file_path
            )
            
            # Step 5: Queue visual processing if needed
            visual_jobs = []
            
            if (self.enable_visual_processing and 
                processing_strategy in [ProcessingStrategy.FULL_VLM, ProcessingStrategy.HYBRID] and
                extraction_result.visual_placeholders):
                
                # Filter visual placeholders based on settings
                filtered_placeholders = self._filter_visual_placeholders(extraction_result.visual_placeholders)
                
                if filtered_placeholders:
                    visual_jobs = self._queue_visual_processing(
                        file_path, filtered_placeholders, complexity_metrics
                    )
                    
                    print(f"   🎨 Queued: {len(visual_jobs)} visual jobs")
                else:
                    print(f"   🚫 Visual processing disabled by settings")
            elif self.text_only_mode:
                print(f"   📝 Text-only mode: skipping visual processing")
            
            # Step 6: Save immediate results to output/latest/
            output_latest_dir = Path('/home/corey/projects/docling/cli/output/latest')
            output_latest_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_latest_dir / f"{file_path.stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            total_time = time.time() - start_time
            
            # Create result
            result = ProcessingResult(
                success=True,
                file_path=file_path,
                processing_strategy=processing_strategy,
                extraction_result=extraction_result,
                document_tags=document_tags,
                markdown_content=markdown_content,
                metadata_header=self.document_tagger.generate_metadata_header(document_tags, file_path) if document_tags else "",
                total_processing_time=total_time,
                text_extraction_time=extraction_time,
                tagging_time=tagging_time,
                complexity_analysis_time=complexity_time,
                visual_jobs_queued=len(visual_jobs),
                visual_jobs_completed=0,
                pending_visual_jobs=visual_jobs,
                warnings=[]
            )
            
            # Calculate performance
            if extraction_result.page_count > 0 and extraction_time > 0:
                pages_per_sec = extraction_result.page_count / extraction_time
                files_per_min = 60 / total_time if total_time > 0 else 0
                print(f"   ⚡ Performance: {pages_per_sec:.1f} pages/sec | {files_per_min:.1f} files/min")
            
            # Optional: Wait for visual processing to complete (for demo purposes)
            if visual_jobs and len(visual_jobs) > 0 and self.visual_queue:
                print(f"   ⏳ Waiting for {len(visual_jobs)} visual jobs to complete...")
                
                # Debug: Check queue stats before waiting
                stats = self.visual_queue.get_queue_stats()
                print(f"   📊 Queue stats: {stats.queue_length} queued, {len(self.visual_queue.active_jobs)} active")
                
                # Give worker threads extra time to pick up jobs
                time.sleep(2.0)
                
                # Check again after brief wait
                stats = self.visual_queue.get_queue_stats()
                print(f"   📊 After 2s wait: {stats.queue_length} queued, {len(self.visual_queue.active_jobs)} active")
                
                completed_jobs = self.visual_queue.wait_for_document(file_path, timeout=120.0)
                
                if completed_jobs:
                    print(f"   ✅ Visual processing completed: {len(completed_jobs)} jobs")
                    result.visual_jobs_completed = len(completed_jobs)
                    
                    # Integrate enhanced visual content back into markdown
                    enhanced_markdown = self.text_extractor.integrate_visual_results(markdown_content, completed_jobs)
                    enhanced_markdown = enhanced_markdown + f"\n\n<!-- VLM Processing: {len(completed_jobs)} elements enhanced -->\n"
                    result.markdown_content = enhanced_markdown
                    
                    # Update output file with enhanced content
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(enhanced_markdown)
                    
                    print(f"   📁 Enhanced output saved: {output_file}")
                else:
                    print(f"   ⚠️  Visual processing timeout - jobs still pending")
            
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            print(f"   ❌ Error: {e}")
            
            return self._create_failed_result(
                file_path, str(e), 
                complexity_time if 'complexity_time' in locals() else 0.0,
                extraction_time if 'extraction_time' in locals() else 0.0,
                tagging_time if 'tagging_time' in locals() else 0.0
            )
    
    def process_batch(self, file_paths: List[Path], output_dir: Path,
                     max_workers: int = 4) -> List[ProcessingResult]:
        """
        Process multiple documents in parallel.
        
        Args:
            file_paths: List of files to process
            output_dir: Output directory for results
            max_workers: Number of parallel workers
        
        Returns:
            List of processing results
        """
        import time
        
        print(f"📦 BATCH PROCESSING: {len(file_paths)} files")
        print("=" * 60)
        
        batch_start_time = time.time()
        results = []
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_file = {
                executor.submit(self.process_document, file_path, output_dir): file_path
                for file_path in file_paths
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Add small delay between completions to prevent memory buildup
                    if len(results) % 10 == 0:  # Every 10 files
                        time.sleep(0.1)
                except Exception as e:
                    # Create failed result for exceptions during processing
                    failed_result = ProcessingResult(
                        success=False,
                        file_path=file_path,
                        processing_strategy=ProcessingStrategy.FAST_TEXT,
                        extraction_result=None,
                        document_tags=None,
                        markdown_content="",
                        metadata_header="",
                        total_processing_time=0.0,
                        text_extraction_time=0.0,
                        tagging_time=0.0,
                        complexity_analysis_time=0.0,
                        visual_jobs_queued=0,
                        visual_jobs_completed=0,
                        pending_visual_jobs=[],
                        error_message=str(e)
                    )
                    results.append(failed_result)
        
        # Calculate batch statistics
        batch_time = time.time() - batch_start_time
        self._update_batch_stats(results, batch_time)
        
        # Generate batch report
        self._generate_batch_report(results, output_dir, batch_time)
        
        print(f"\n📊 BATCH COMPLETE: {len(results)} files in {batch_time:.1f}s")
        self._print_batch_summary(results, batch_time)
        
        return results
    
    def wait_for_visual_processing(self, results: List[ProcessingResult], 
                                  timeout: float = 300.0) -> Dict[str, List[str]]:
        """
        Wait for visual processing to complete and update results.
        
        Returns:
            Dict mapping file paths to completed job IDs
        """
        
        print(f"\n🎨 Waiting for visual processing (timeout: {timeout}s)...")
        
        completed_jobs = {}
        
        for result in results:
            if result.pending_visual_jobs:
                file_completed_jobs = self.visual_queue.wait_for_document(
                    result.file_path, timeout
                )
                
                completed_jobs[str(result.file_path)] = [
                    job.job_id for job in file_completed_jobs
                ]
                
                result.visual_jobs_completed = len(file_completed_jobs)
                
                # Update markdown with enhanced content if available
                if file_completed_jobs:
                    self._update_markdown_with_visual_results(result, file_completed_jobs)
        
        return completed_jobs
    
    def shutdown(self):
        """Shutdown the processor and clean up resources."""
        print("🛑 Shutting down high-performance processor...")
        if self.visual_queue:
            self.visual_queue.shutdown()
        print("✅ Shutdown complete")
    
    def _queue_visual_processing(self, file_path: Path, placeholders: List[Dict], 
                               complexity_metrics: Optional[ComplexityMetrics]) -> List[str]:
        """Queue visual elements for enhanced processing."""
        
        job_ids = []
        
        for placeholder in placeholders:
            # Determine element type
            element_type_map = {
                'image': ElementType.IMAGE,
                'table': ElementType.TABLE,
                'formula': ElementType.FORMULA,
                'chart': ElementType.CHART,
                'diagram': ElementType.DIAGRAM
            }
            
            element_type = element_type_map.get(
                placeholder.get('element_type', 'image'), 
                ElementType.IMAGE
            )
            
            # Determine priority based on complexity and type
            priority = Priority.NORMAL
            if element_type == ElementType.TABLE:
                priority = Priority.HIGH  # Tables are important for structure
            elif element_type == ElementType.FORMULA:
                priority = Priority.HIGH  # Formulas are critical content
            
            # Queue the job
            job_id = self.visual_queue.add_job(
                document_path=file_path,
                element_type=element_type,
                page_number=placeholder.get('page_number', 1),
                priority=priority,
                estimated_time=self._estimate_processing_time(element_type),
                placeholder_id=placeholder.get('placeholder_id')
            )
            
            job_ids.append(job_id)
        
        return job_ids
    
    def _filter_visual_placeholders(self, placeholders: List[Dict]) -> List[Dict]:
        """Filter visual placeholders based on enabled settings."""
        filtered = []
        
        for placeholder in placeholders:
            element_type = placeholder.get('element_type', 'image').lower()
            
            # Check if this element type is enabled
            if element_type == 'table' and not self.enable_tables:
                continue
            elif element_type in ['image', 'chart', 'diagram'] and not self.enable_images:
                continue
            
            filtered.append(placeholder)
        
        return filtered
    
    def _estimate_processing_time(self, element_type: ElementType) -> float:
        """Estimate processing time for different element types."""
        time_estimates = {
            ElementType.IMAGE: 3.0,
            ElementType.TABLE: 5.0,
            ElementType.FORMULA: 4.0,
            ElementType.CHART: 6.0,
            ElementType.DIAGRAM: 8.0,
            ElementType.COMPLEX_LAYOUT: 10.0
        }
        
        return time_estimates.get(element_type, 5.0)
    
    def _generate_enhanced_markdown(self, extraction_result: ExtractionResult,
                                  document_tags: Optional[DocumentTags],
                                  file_path: Path) -> str:
        """Generate enhanced markdown with metadata and structure."""
        
        lines = []
        
        # Add metadata header if available
        if document_tags:
            metadata_header = self.document_tagger.generate_metadata_header(document_tags, file_path)
            lines.append(metadata_header)
        
        # Add processing information
        lines.append("<!-- High-Performance Processing -->")
        lines.append(f"<!-- Processed: {datetime.now().isoformat()} -->")
        lines.append(f"<!-- Method: {extraction_result.extraction_method.value} -->")
        lines.append(f"<!-- Speed: {extraction_result.extraction_time:.3f}s -->")
        
        if extraction_result.visual_placeholders:
            lines.append(f"<!-- Visual elements: {len(extraction_result.visual_placeholders)} queued -->")
        
        lines.append("")
        
        # Add main title
        title = file_path.stem.replace('_', ' ').replace('-', ' ').title()
        lines.append(f"# {title}")
        lines.append("")
        
        # Add enhanced document classification if available
        if document_tags:
            # Show top 3 document types
            lines.append("**Document Types (Top 3):**")
            for i, (doc_type, confidence) in enumerate(document_tags.document_types[:3]):
                confidence_pct = round(confidence * 100, 1)
                type_name = doc_type.value.replace('_', ' ').title()
                lines.append(f"  {i+1}. {type_name} ({confidence_pct}%)")
            
            lines.append("")
            
            # Show top 3 domains
            lines.append("**Domains (Top 3):**")
            for i, (domain, confidence) in enumerate(document_tags.domains[:3]):
                confidence_pct = round(confidence * 100, 1)
                domain_name = domain.value.replace('_', ' ').title()
                lines.append(f"  {i+1}. {domain_name} ({confidence_pct}%)")
            
            lines.append("")
            
            # Show enhanced keywords (up to 25 high-quality keywords)
            if document_tags.keywords:
                keyword_count = len(document_tags.keywords)
                lines.append(f"**Keywords ({keyword_count} high-quality terms):**")
                lines.append(f"{', '.join(document_tags.keywords)}")
            
            lines.append("")
        
        # Add main content
        if extraction_result.text_content:
            # Clean up the text content
            content = extraction_result.text_content.strip()
            
            # Add some basic structure improvements
            content = self._improve_text_structure(content)
            
            lines.append(content)
        else:
            lines.append("*No text content extracted*")
        
        # Add visual elements section if any
        if extraction_result.visual_placeholders:
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("## Visual Elements")
            lines.append("")
            lines.append("*The following visual elements are being processed for enhancement:*")
            lines.append("")
            
            for placeholder in extraction_result.visual_placeholders:
                element_type = placeholder.get('element_type', 'unknown').title()
                page_num = placeholder.get('page_number', '?')
                description = placeholder.get('description', 'Processing queued')
                placeholder_id = placeholder.get('placeholder_id', 'unknown')
                
                lines.append(f"- **{element_type}** (Page {page_num}): {description} `[{placeholder_id}]`")
            
            lines.append("")
            lines.append("*Enhanced content will be updated automatically when processing completes.*")
        
        # Add extraction statistics
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Processing Statistics")
        lines.append("")
        lines.append(f"- **Pages:** {extraction_result.page_count}")
        lines.append(f"- **Words:** {extraction_result.word_count:,}")
        lines.append(f"- **Characters:** {extraction_result.char_count:,}")
        lines.append(f"- **Extraction Time:** {extraction_result.extraction_time:.3f} seconds")
        
        if extraction_result.page_count > 0 and extraction_result.extraction_time > 0:
            pages_per_sec = extraction_result.page_count / extraction_result.extraction_time
            lines.append(f"- **Speed:** {pages_per_sec:.1f} pages/second")
        
        return "\n".join(lines)
    
    def _improve_text_structure(self, text: str) -> str:
        """Apply basic structural improvements to extracted text."""
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        
        improved_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Detect potential headers (short lines, often in caps)
            if (len(para) < 100 and 
                (para.isupper() or para.istitle()) and
                not para.endswith('.')):
                # Make it a header
                improved_paragraphs.append(f"## {para}")
            else:
                improved_paragraphs.append(para)
        
        return "\n\n".join(improved_paragraphs)
    
    def _update_markdown_with_visual_results(self, result: ProcessingResult, 
                                           completed_jobs: List[Any]):
        """Update markdown file with enhanced visual content."""
        
        if not completed_jobs:
            return
        
        # For now, just add a note that visual processing completed
        # In a full implementation, you would extract the enhanced content
        # from the completed jobs and integrate it into the markdown
        
        enhanced_note = f"\n\n<!-- Visual processing completed: {len(completed_jobs)} elements enhanced -->\n"
        result.markdown_content += enhanced_note
        
        # Write updated content to file
        output_file = result.file_path.parent / f"{result.file_path.stem}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.markdown_content)
    
    def _create_failed_result(self, file_path: Path, error_message: str,
                             complexity_time: float, extraction_time: float,
                             tagging_time: float) -> ProcessingResult:
        """Create a failed processing result."""
        
        return ProcessingResult(
            success=False,
            file_path=file_path,
            processing_strategy=ProcessingStrategy.FAST_TEXT,
            extraction_result=None,
            document_tags=None,
            markdown_content="",
            metadata_header="",
            total_processing_time=complexity_time + extraction_time + tagging_time,
            text_extraction_time=extraction_time,
            tagging_time=tagging_time,
            complexity_analysis_time=complexity_time,
            visual_jobs_queued=0,
            visual_jobs_completed=0,
            pending_visual_jobs=[],
            error_message=error_message
        )
    
    def _update_batch_stats(self, results: List[ProcessingResult], batch_time: float):
        """Update batch processing statistics."""
        
        self.processing_stats.total_files = len(results)
        self.processing_stats.successful_files = sum(1 for r in results if r.success)
        self.processing_stats.failed_files = sum(1 for r in results if not r.success)
        self.processing_stats.total_time = batch_time
        
        if len(results) > 0:
            self.processing_stats.average_time_per_file = batch_time / len(results)
            self.processing_stats.throughput_files_per_minute = len(results) / (batch_time / 60.0)
        
        # Strategy breakdown
        for result in results:
            if result.success:
                if result.processing_strategy == ProcessingStrategy.FAST_TEXT:
                    self.processing_stats.fast_text_files += 1
                elif result.processing_strategy == ProcessingStrategy.FULL_VLM:
                    self.processing_stats.vlm_files += 1
                elif result.processing_strategy == ProcessingStrategy.HYBRID:
                    self.processing_stats.hybrid_files += 1
                
                # Visual job stats
                self.processing_stats.total_visual_jobs += result.visual_jobs_queued
                
                # Page processing stats
                if result.extraction_result:
                    self.processing_stats.total_pages_processed += result.extraction_result.page_count
                
                # File size stats
                try:
                    file_size = result.file_path.stat().st_size
                    self.processing_stats.total_bytes_processed += file_size
                except:
                    pass  # Skip if file no longer exists or permission issues
        
        # Calculate pages per second
        total_extraction_time = sum(r.text_extraction_time for r in results if r.success)
        if total_extraction_time > 0:
            self.processing_stats.pages_per_second = self.processing_stats.total_pages_processed / total_extraction_time
        
        # Calculate megabytes per second
        if batch_time > 0 and self.processing_stats.total_bytes_processed > 0:
            megabytes = self.processing_stats.total_bytes_processed / (1024 * 1024)
            self.processing_stats.megabytes_per_second = megabytes / batch_time
    
    def _generate_batch_report(self, results: List[ProcessingResult], 
                             output_dir: Path, batch_time: float):
        """Generate detailed batch processing report."""
        
        report_data = {
            "batch_summary": {
                "total_files": len(results),
                "successful_files": sum(1 for r in results if r.success),
                "failed_files": sum(1 for r in results if not r.success),
                "processing_time": batch_time,
                "timestamp": datetime.now().isoformat()
            },
            "performance_metrics": {
                "throughput_files_per_minute": self.processing_stats.throughput_files_per_minute,
                "pages_per_second": self.processing_stats.pages_per_second,
                "megabytes_per_second": self.processing_stats.megabytes_per_second,
                "average_time_per_file": self.processing_stats.average_time_per_file,
                "total_megabytes_processed": self.processing_stats.total_bytes_processed / (1024 * 1024)
            },
            "strategy_breakdown": {
                "fast_text": self.processing_stats.fast_text_files,
                "vlm": self.processing_stats.vlm_files,
                "hybrid": self.processing_stats.hybrid_files
            },
            "file_results": []
        }
        
        # Add individual file results
        for result in results:
            file_data = {
                "file_name": result.file_path.name,
                "success": result.success,
                "strategy": result.processing_strategy.value if result.success else "failed",
                "processing_time": result.total_processing_time,
                "word_count": result.extraction_result.word_count if result.extraction_result else 0,
                "visual_jobs": result.visual_jobs_queued,
                "error": result.error_message
            }
            
            if result.document_tags:
                file_data["document_type"] = result.document_tags.document_type.value
                file_data["domain"] = result.document_tags.domain.value
                file_data["keywords"] = result.document_tags.keywords[:5]
            
            report_data["file_results"].append(file_data)
        
        # Save report
        report_file = output_dir / f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📋 Batch report saved: {report_file}")
    
    def _print_batch_summary(self, results: List[ProcessingResult], batch_time: float):
        """Print batch processing summary."""
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        print(f"   ⚡ Throughput: {self.processing_stats.throughput_files_per_minute:.1f} files/min")
        print(f"   📄 Pages/sec: {self.processing_stats.pages_per_second:.1f}")
        print(f"   💾 MB/s: {self.processing_stats.megabytes_per_second:.1f}")
        
        if self.processing_stats.total_visual_jobs > 0:
            print(f"   🎨 Visual jobs: {self.processing_stats.total_visual_jobs} queued")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="High-Performance PDF Processing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file with default settings
  python high_performance_pdf_processor.py document.pdf
  
  # Process directory in text-only mode (fastest)
  python high_performance_pdf_processor.py data/osha/ --text-only
  
  # Process with images but no tables
  python high_performance_pdf_processor.py document.pdf --no-tables
  
  # Force VLM strategy for maximum quality
  python high_performance_pdf_processor.py document.pdf --strategy vlm
  
  # Disable all visual processing
  python high_performance_pdf_processor.py data/ --no-visual
        """
    )
    
    # Required argument
    parser.add_argument(
        'input_path',
        type=str,
        help='Path to file or directory to process'
    )
    
    # Processing modes
    parser.add_argument(
        '--text-only',
        action='store_true',
        help='Text-only mode: fastest processing, no visual elements (overrides other visual options)'
    )
    
    parser.add_argument(
        '--strategy',
        choices=['fast', 'vlm', 'hybrid'],
        help='Force processing strategy (fast=text-only, vlm=full-VLM, hybrid=smart-selection)'
    )
    
    # Visual processing controls
    parser.add_argument(
        '--no-visual',
        action='store_true',
        help='Disable visual processing entirely'
    )
    
    parser.add_argument(
        '--no-tables',
        action='store_true',
        help='Disable table detection and processing'
    )
    
    parser.add_argument(
        '--no-images',
        action='store_true',
        help='Disable image, chart, and diagram processing'
    )
    
    parser.add_argument(
        '--no-tagging',
        action='store_true',
        help='Disable document classification and tagging'
    )
    
    # Performance settings
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Number of parallel processing workers (default: 1)'
    )
    
    parser.add_argument(
        '--visual-workers',
        type=int,
        default=1,
        help='Number of visual processing workers (default: 1)'
    )
    
    parser.add_argument(
        '--timeout',
        type=float,
        default=5.0,
        help='Visual processing batch timeout in seconds (default: 5.0)'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory (default: same as input or cli/output/latest)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def main():
    """Process specified file or run test on sample documents."""
    args = parse_arguments()
    
    # Validate input path
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"❌ Path not found: {input_path}")
        return
    
    # Configure processor based on arguments
    # If strategy is 'fast' or --no-visual is set, enable text_only_mode
    text_only = args.text_only or args.strategy == 'fast' or args.no_visual
    
    processor_config = {
        'max_visual_workers': args.visual_workers,
        'visual_batch_timeout': args.timeout,
        'enable_visual_processing': not args.no_visual and args.strategy != 'fast',
        'enable_document_tagging': not args.no_tagging,
        'enable_tables': not args.no_tables,
        'enable_images': not args.no_images,
        'text_only_mode': text_only,
        'force_strategy': args.strategy
    }
    
    # Print configuration summary
    print("🚀 HIGH-PERFORMANCE DOCUMENT PROCESSOR")
    print("=" * 60)
    print(f"📁 Input: {input_path}")
    
    if args.text_only:
        print("⚡ Mode: TEXT-ONLY (fastest)")
    elif args.strategy:
        print(f"⚡ Mode: {args.strategy.upper()} (forced)")
    else:
        print("⚡ Mode: AUTO-DETECT (smart)")
    
    print(f"🎨 Visual processing: {'✅' if processor_config['enable_visual_processing'] else '❌'}")
    print(f"📋 Tables: {'✅' if processor_config['enable_tables'] else '❌'}")
    print(f"🖼️  Images: {'✅' if processor_config['enable_images'] else '❌'}")
    print(f"🏷️  Tagging: {'✅' if processor_config['enable_document_tagging'] else '❌'}")
    print(f"👥 Workers: {args.workers} processing, {args.visual_workers} visual")
    print("=" * 60)
    
    # Initialize processor
    processor = HighPerformancePDFProcessor(**processor_config)
    
    try:
        if input_path.is_file():
            # Process single file
            print(f"\n📄 Processing: {input_path.name}")
            
            # Determine output directory
            output_dir = Path(args.output_dir) if args.output_dir else None
            
            result = processor.process_document(input_path, output_dir)
            
            if result.success:
                print(f"   ✅ Success!")
                print(f"   📊 Strategy: {result.processing_strategy.value}")
                print(f"   📝 Words extracted: {result.extraction_result.word_count:,}")
                print(f"   📄 Pages: {result.extraction_result.page_count}")
                print(f"   ⏱️  Total time: {result.total_processing_time:.3f}s")
                
                # Calculate pages per second
                if result.total_processing_time > 0:
                    pages_per_sec = result.extraction_result.page_count / result.total_processing_time
                    print(f"   ⚡ Speed: {pages_per_sec:.1f} pages/sec")
                
                print(f"   🎨 Visual jobs queued: {result.visual_jobs_queued}")
                
                if result.visual_jobs_completed > 0:
                    print(f"   ✅ Visual jobs completed: {result.visual_jobs_completed}")
            else:
                print(f"   ❌ Failed: {result.error_message}")
            
        elif input_path.is_dir():
            # Process directory
            print(f"\n📁 Processing directory: {input_path}")
            
            # Find all supported files
            file_patterns = ['*.pdf', '*.docx', '*.html', '*.md', '*.txt']
            all_files = []
            
            for pattern in file_patterns:
                files = list(input_path.glob(pattern))
                all_files.extend(files)
                if files:
                    print(f"   Found {len(files)} {pattern} files")
            
            if not all_files:
                print(f"   ❌ No supported files found in {input_path}")
                return
            
            print(f"\n📦 Total files to process: {len(all_files)}")
            print(f"   🔧 Using {args.workers} parallel workers for {len(all_files)} files")
            
            # Determine output directory
            if args.output_dir:
                output_dir = Path(args.output_dir)
            else:
                output_dir = Path('/home/corey/projects/docling/cli/output/latest')
            
            results = processor.process_batch(all_files, output_dir, max_workers=args.workers)
            
            print(f"\n🎯 DIRECTORY PROCESSING COMPLETE")
            print(f"   📁 Output directory: {output_dir}")
        
        else:
            print(f"❌ Invalid input path: {input_path}")
            
    except Exception as e:
        print(f"❌ Processing error: {e}")
    
    finally:
        processor.shutdown()


if __name__ == "__main__":
    main()