"""
Orchestrated Pipeline - Clean Architecture Implementation
=========================================================

Common pipeline orchestrator that manages sequential execution of 7 isolated stages.
Each stage is completely independent with no cross-stage code.

Pipeline Stages:
1. PDF Conversion Stage
2. Document Processing Stage  
3. Classification Stage
4. Entity Extraction Stage
5. Normalization Stage
6. Semantic Analysis Stage
7. File Writing Stage

Each stage:
- Accepts output from previous stage as input
- Produces output for next stage
- Has isolated timing measurement
- Can be replaced with sidecar implementation
"""

import time
from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path
from abc import ABC, abstractmethod


class StageInterface(ABC):
    """Interface that all pipeline stages must implement."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def process(self, input_data: Any, metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """
        Process stage input and return output.
        
        Args:
            input_data: Output from previous stage (or initial input for stage 1)
            metadata: Processing metadata and context
            
        Returns:
            Tuple of (stage_output, timing_ms)
        """
        pass


class PdfConversionStage(StageInterface):
    """Stage 1: Convert PDFs and documents to processable format."""
    
    def process(self, input_data: List[Path], metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """Convert documents using extractors."""
        start_time = time.perf_counter()
        
        # For Phase 1, we'll use simplified conversion
        # Later this will use actual extractors for PDF conversion
        converted_documents = []
        for file_path in input_data:
            # Simplified document conversion for baseline
            doc_result = {
                'file_path': str(file_path),
                'extractor': 'baseline_converter',
                'content': f"[Converted content from {file_path.name}]",
                'pages': 1,
                'status': 'converted'
            }
            converted_documents.append(doc_result)
        
        timing_ms = (time.perf_counter() - start_time) * 1000
        return converted_documents, timing_ms


class DocumentProcessingStage(StageInterface):
    """Stage 2: Core document processing and transformation."""
    
    def process(self, input_data: List[Dict], metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """Process converted documents."""
        start_time = time.perf_counter()
        
        processed_documents = []
        for doc in input_data:
            # Document processing logic
            processed = {
                **doc,
                'processed': True,
                'processing_timestamp': time.time(),
                'word_count': len(doc.get('content', '').split()),
                'stage': 'document_processing'
            }
            processed_documents.append(processed)
        
        timing_ms = (time.perf_counter() - start_time) * 1000
        return processed_documents, timing_ms


class ClassificationStage(StageInterface):
    """Stage 3: Document type and content classification."""
    
    def process(self, input_data: List[Dict], metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """Classify documents by type and content."""
        start_time = time.perf_counter()
        
        classified_documents = []
        for doc in input_data:
            # Classification logic
            classified = {
                **doc,
                'classification': {
                    'document_type': 'general',
                    'confidence': 0.95,
                    'categories': ['business', 'technical'],
                    'language': 'en'
                },
                'stage': 'classification'
            }
            classified_documents.append(classified)
        
        timing_ms = (time.perf_counter() - start_time) * 1000
        return classified_documents, timing_ms


class EntityExtractionStage(StageInterface):
    """Stage 4: Extract entities (people, organizations, locations, etc.)."""
    
    def process(self, input_data: List[Dict], metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """Extract entities from documents."""
        start_time = time.perf_counter()
        
        documents_with_entities = []
        for doc in input_data:
            # Entity extraction logic
            enriched = {
                **doc,
                'entities': {
                    'people': [],
                    'organizations': [],
                    'locations': [],
                    'dates': [],
                    'money': []
                },
                'entity_count': 0,
                'stage': 'entity_extraction'
            }
            documents_with_entities.append(enriched)
        
        timing_ms = (time.perf_counter() - start_time) * 1000
        return documents_with_entities, timing_ms


class NormalizationStage(StageInterface):
    """Stage 5: Standardize and canonicalize extracted entities."""
    
    def process(self, input_data: List[Dict], metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """Normalize entities to canonical forms."""
        start_time = time.perf_counter()
        
        normalized_documents = []
        for doc in input_data:
            # Normalization logic
            normalized = {
                **doc,
                'normalized_entities': doc.get('entities', {}),
                'normalization_applied': True,
                'stage': 'normalization'
            }
            normalized_documents.append(normalized)
        
        timing_ms = (time.perf_counter() - start_time) * 1000
        return normalized_documents, timing_ms


class SemanticAnalysisStage(StageInterface):
    """Stage 6: Extract facts, rules, and relationships."""
    
    def process(self, input_data: List[Dict], metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """Perform semantic analysis on documents."""
        start_time = time.perf_counter()
        
        semantic_documents = []
        for doc in input_data:
            # Semantic analysis logic
            analyzed = {
                **doc,
                'semantic_data': {
                    'facts': [],
                    'rules': [],
                    'relationships': [],
                    'knowledge_points': []
                },
                'semantic_score': 0.0,
                'stage': 'semantic_analysis'
            }
            semantic_documents.append(analyzed)
        
        timing_ms = (time.perf_counter() - start_time) * 1000
        return semantic_documents, timing_ms


class FileWritingStage(StageInterface):
    """Stage 7: Write processed results to output files."""
    
    def process(self, input_data: List[Dict], metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """Write results to output files."""
        start_time = time.perf_counter()
        
        output_dir = Path(metadata.get('output_dir', '../output/fusion'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        written_files = []
        for doc in input_data:
            # Generate output file paths
            base_name = Path(doc['file_path']).stem
            
            # Write markdown file
            md_path = output_dir / f"{base_name}_enhanced.md"
            with open(md_path, 'w') as f:
                f.write(f"# {base_name}\n\n")
                f.write(f"Processing complete through 7-stage pipeline\n\n")
                f.write(f"- Document Type: {doc.get('classification', {}).get('document_type', 'unknown')}\n")
                f.write(f"- Entities Found: {doc.get('entity_count', 0)}\n")
                f.write(f"- Semantic Score: {doc.get('semantic_score', 0.0)}\n")
            
            # Write JSON metadata file
            json_path = output_dir / f"{base_name}_semantic.json"
            import json
            with open(json_path, 'w') as f:
                json.dump({
                    'file_path': doc['file_path'],
                    'classification': doc.get('classification', {}),
                    'entities': doc.get('normalized_entities', {}),
                    'semantic_data': doc.get('semantic_data', {})
                }, f, indent=2)
            
            written_files.append({
                'markdown': str(md_path),
                'json': str(json_path),
                'source': doc['file_path']
            })
        
        timing_ms = (time.perf_counter() - start_time) * 1000
        return written_files, timing_ms


class OrchestratedPipeline:
    """
    Common pipeline orchestrator that executes stages in sequence.
    
    This is the core pipeline that:
    - Calls stages 1→2→3→4→5→6→7 in order
    - Measures each stage's performance independently
    - Allows any stage to be replaced with a sidecar
    - Maintains clean separation between stages
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stages = []
        self.stage_timings = {}
        
        # Initialize all 7 stages
        self._initialize_stages()
    
    def _initialize_stages(self):
        """Initialize the 7 pipeline stages based on configuration."""
        
        # Stage 1: PDF Conversion
        self.stages.append(self._create_stage(1, 'pdf_conversion', PdfConversionStage))
        
        # Stage 2: Document Processing
        self.stages.append(self._create_stage(2, 'document_processing', DocumentProcessingStage))
        
        # Stage 3: Classification
        self.stages.append(self._create_stage(3, 'classification', ClassificationStage))
        
        # Stage 4: Entity Extraction
        self.stages.append(self._create_stage(4, 'entity_extraction', EntityExtractionStage))
        
        # Stage 5: Normalization
        self.stages.append(self._create_stage(5, 'normalization', NormalizationStage))
        
        # Stage 6: Semantic Analysis
        self.stages.append(self._create_stage(6, 'semantic_analysis', SemanticAnalysisStage))
        
        # Stage 7: File Writing
        self.stages.append(self._create_stage(7, 'file_writing', FileWritingStage))
    
    def _create_stage(self, stage_num: int, stage_name: str, default_class: type) -> StageInterface:
        """
        Create a stage instance, checking for sidecar configuration.
        
        Args:
            stage_num: Stage number (1-7)
            stage_name: Name of the stage in configuration
            default_class: Default implementation class
            
        Returns:
            Stage instance (either default or sidecar)
        """
        # Check if there's a sidecar configured for this stage
        pipeline_config = self.config.get('pipeline', {})
        stage_config = pipeline_config.get(f'stage_{stage_num}_{stage_name}', {})
        
        # For now, use default implementation
        # Later, we'll check for sidecar_test or processor override
        return default_class(self.config)
    
    def process(self, input_files: List[Path], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process files through all 7 stages sequentially.
        
        Args:
            input_files: List of input file paths
            metadata: Processing metadata and context
            
        Returns:
            Dictionary with results and performance metrics
        """
        metadata = metadata or {}
        pipeline_start = time.perf_counter()
        
        # Track data as it flows through stages
        current_data = input_files
        stage_results = []
        
        print(f"🚀 ORCHESTRATED PIPELINE: Processing {len(input_files)} files through 7 stages")
        print("=" * 60)
        
        # Execute each stage in sequence
        for i, stage in enumerate(self.stages, 1):
            stage_name = stage.__class__.__name__
            print(f"\n📊 Stage {i}: {stage_name}")
            
            # Process through stage
            try:
                stage_output, stage_timing = stage.process(current_data, metadata)
                
                # Record timing
                self.stage_timings[f"stage_{i}_{stage_name}"] = stage_timing
                
                # Record result
                stage_results.append({
                    'stage_num': i,
                    'stage_name': stage_name,
                    'timing_ms': stage_timing,
                    'success': True,
                    'output_count': len(stage_output) if hasattr(stage_output, '__len__') else 1
                })
                
                print(f"   ✅ Completed in {stage_timing:.2f}ms")
                
                # Pass output to next stage
                current_data = stage_output
                
            except Exception as e:
                # Record failure
                stage_results.append({
                    'stage_num': i,
                    'stage_name': stage_name,
                    'timing_ms': 0,
                    'success': False,
                    'error': str(e)
                })
                print(f"   ❌ Failed: {e}")
                break
        
        # Calculate total pipeline time
        total_pipeline_time = (time.perf_counter() - pipeline_start) * 1000
        
        # Performance summary
        print(f"\n🎯 PIPELINE PERFORMANCE SUMMARY")
        print("=" * 60)
        
        for result in stage_results:
            if result['success']:
                percentage = (result['timing_ms'] / total_pipeline_time * 100) if total_pipeline_time > 0 else 0
                print(f"Stage {result['stage_num']}: {result['timing_ms']:.2f}ms ({percentage:.1f}%)")
        
        print(f"\nTotal Pipeline Time: {total_pipeline_time:.2f}ms")
        
        # Return comprehensive results compatible with CLI expectations
        # The CLI expects specific metrics for display
        total_pages = len(input_files)  # Simplified for now
        pages_per_sec = (total_pages / (total_pipeline_time / 1000)) if total_pipeline_time > 0 else 0
        
        return {
            'success': all(r['success'] for r in stage_results),
            'final_output': current_data,
            'stage_results': stage_results,
            'stage_timings': self.stage_timings,
            'total_pipeline_ms': total_pipeline_time,
            'files_processed': len(input_files),
            # Additional metrics expected by CLI
            'pages_processed': total_pages,
            'pages_per_sec': pages_per_sec,
            'total_entities': 0,  # Will be populated by actual extraction
            'entity_breakdown': {},  # Will be populated by actual extraction
        }