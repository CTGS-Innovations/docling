#!/usr/bin/env python3
"""
MVP-Fusion In-Memory Pipeline Processor
=======================================
Edge-optimized, service-first document processing with zero I/O between stages.

Stages:
1. CONVERT: PDF → In-memory markdown + YAML
2. CLASSIFY: Add classification data to in-memory YAML
3. ENRICH: Add enrichment data to in-memory YAML  
4. EXTRACT: Generate semantic JSON in memory

Edge Architecture:
- 1GB RAM limit compliance
- Zero file I/O between stages  
- Single final write operation
- CloudFlare Workers ready
"""

import re
import time
from pathlib import Path
from typing import List, Dict, Any, Union
import yaml
from .in_memory_document import InMemoryDocument, MemoryOverflowError


class FusionPipeline:
    """
    Edge-optimized in-memory pipeline processor for MVP-Fusion.
    
    Processes files through progressive stages with zero I/O:
    convert → classify → enrich → extract
    
    Memory-first architecture for CloudFlare Workers deployment.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stages_to_run = config.get('pipeline', {}).get('stages_to_run', ['convert'])
        self.memory_limit_mb = config.get('pipeline', {}).get('memory_limit_mb', 100)
        self.service_memory_limit_mb = config.get('pipeline', {}).get('service_memory_limit_mb', 1024)
        
    def process_files(self, extractor, file_paths: List[Path], output_dir: Path, 
                     max_workers: int = 2) -> tuple[List[InMemoryDocument], float, Dict[str, Any]]:
        """
        Process files through in-memory pipeline stages with zero I/O between stages.
        
        Edge-optimized architecture:
        - Convert PDF → in-memory markdown + YAML
        - Progressive YAML building in memory
        - Single final write operation per file
        
        Args:
            extractor: Conversion extractor to use
            file_paths: List of input files
            output_dir: Output directory
            max_workers: Number of workers for conversion
            
        Returns:
            Tuple of (in_memory_documents, total_time, resource_summary)
        """
        start_time = time.perf_counter()
        
        print(f"🚀 In-Memory Pipeline: {' → '.join(self.stages_to_run)}")
        print(f"💾 Memory limit: {self.memory_limit_mb}MB per file, {self.service_memory_limit_mb}MB service total")
        
        # Initialize in-memory documents
        in_memory_docs = []
        total_service_memory = 0
        
        # Stage 1: CONVERT (if requested)
        if 'convert' in self.stages_to_run:
            print(f"📄 Stage 1: Converting {len(file_paths)} files to in-memory documents...")
            stage_start = time.perf_counter()
            
            # Use extractor for conversion but process results into InMemoryDocument objects
            batch_result = extractor.extract_batch(file_paths, output_dir, max_workers=max_workers)
            if len(batch_result) == 3:
                conversion_results, conversion_time, resource_summary = batch_result
            else:
                conversion_results, conversion_time = batch_result
                resource_summary = None
            
            # Convert extraction results to InMemoryDocument objects
            for result in conversion_results:
                if result.success and hasattr(result, 'output_path') and result.output_path:
                    try:
                        # Read the markdown file that was just created
                        with open(result.output_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Parse YAML frontmatter and markdown content
                        if content.startswith('---'):
                            parts = content.split('---', 2)
                            if len(parts) >= 3:
                                yaml_content = parts[1]
                                markdown_content = parts[2]
                                yaml_metadata = yaml.safe_load(yaml_content) or {}
                            else:
                                yaml_metadata = {}
                                markdown_content = content
                        else:
                            yaml_metadata = {}
                            markdown_content = content
                        
                        # Create in-memory document
                        doc = InMemoryDocument(result.file_path, self.memory_limit_mb)
                        doc.set_conversion_data(markdown_content, yaml_metadata, result.pages)
                        doc.record_stage_timing('convert', (time.perf_counter() - stage_start) * 1000)
                        
                        # Check service memory limit
                        doc_memory = doc.get_memory_footprint() / 1024 / 1024
                        if total_service_memory + doc_memory > self.service_memory_limit_mb:
                            doc.mark_failed(f"Service memory limit exceeded: {total_service_memory + doc_memory:.1f}MB > {self.service_memory_limit_mb}MB")
                        else:
                            total_service_memory += doc_memory
                        
                        in_memory_docs.append(doc)
                        
                        # Delete the temporary file (we have it in memory now)
                        Path(result.output_path).unlink()
                        
                    except Exception as e:
                        doc = InMemoryDocument(result.file_path, self.memory_limit_mb)
                        doc.mark_failed(f"Failed to load conversion result: {e}")
                        in_memory_docs.append(doc)
                else:
                    doc = InMemoryDocument(getattr(result, 'file_path', 'unknown'), self.memory_limit_mb)
                    doc.mark_failed(f"Conversion failed: {getattr(result, 'error', 'Unknown error')}")
                    in_memory_docs.append(doc)
                
            stage_time = (time.perf_counter() - stage_start) * 1000
            successful_docs = [doc for doc in in_memory_docs if doc.success]
            print(f"   ✅ Conversion complete: {stage_time:.0f}ms ({len(successful_docs)}/{len(in_memory_docs)} successful)")
            print(f"   💾 Total service memory: {total_service_memory:.1f}MB")
        else:
            resource_summary = None
        
        # Stage 2: CLASSIFY (if requested)
        if 'classify' in self.stages_to_run:
            print(f"📋 Stage 2: Classifying documents in memory...")
            stage_start = time.perf_counter()
            
            successful_classifications = 0
            for doc in in_memory_docs:
                if doc.success:
                    try:
                        classification_data = self._generate_classification_data(doc.markdown_content, doc.source_filename)
                        doc.add_classification_data(classification_data)
                        doc.record_stage_timing('classify', (time.perf_counter() - stage_start) * 1000)
                        successful_classifications += 1
                    except MemoryOverflowError as e:
                        doc.mark_failed(str(e))
                    except Exception as e:
                        doc.mark_failed(f"Classification failed: {e}")
            
            stage_time = (time.perf_counter() - stage_start) * 1000
            print(f"   ✅ Classification complete: {stage_time:.0f}ms ({successful_classifications}/{len(in_memory_docs)} successful)")
        
        # Stage 3: ENRICH (if requested)
        if 'enrich' in self.stages_to_run:
            print(f"🔍 Stage 3: Enriching documents in memory...")
            stage_start = time.perf_counter()
            
            successful_enrichments = 0
            for doc in in_memory_docs:
                if doc.success:
                    try:
                        # TODO: Implement domain-specific enrichment
                        enrichment_data = {
                            'description': 'Domain-Specific Enrichment & Entity Extraction',
                            'enrichment_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                            'enrichment_method': 'mvp-fusion-basic',
                            'domains_processed': '["general"]',
                            'total_entities': 0,
                            'enhanced_mode': False
                        }
                        doc.add_enrichment_data(enrichment_data)
                        doc.record_stage_timing('enrich', (time.perf_counter() - stage_start) * 1000)
                        successful_enrichments += 1
                    except MemoryOverflowError as e:
                        doc.mark_failed(str(e))
                    except Exception as e:
                        doc.mark_failed(f"Enrichment failed: {e}")
            
            stage_time = (time.perf_counter() - stage_start) * 1000
            print(f"   ✅ Enrichment complete: {stage_time:.0f}ms ({successful_enrichments}/{len(in_memory_docs)} successful)")
        
        # Stage 4: EXTRACT (if requested)  
        if 'extract' in self.stages_to_run:
            print(f"📄 Stage 4: Extracting semantic rules in memory...")
            stage_start = time.perf_counter()
            
            successful_extractions = 0
            for doc in in_memory_docs:
                if doc.success:
                    try:
                        # TODO: Implement semantic rule extraction
                        semantic_data = {
                            'extraction_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                            'extraction_method': 'mvp-fusion-basic',
                            'rules_extracted': 0,
                            'knowledge_points': []
                        }
                        doc.set_semantic_data(semantic_data)
                        doc.record_stage_timing('extract', (time.perf_counter() - stage_start) * 1000)
                        successful_extractions += 1
                    except MemoryOverflowError as e:
                        doc.mark_failed(str(e))
                    except Exception as e:
                        doc.mark_failed(f"Extraction failed: {e}")
            
            stage_time = (time.perf_counter() - stage_start) * 1000
            print(f"   ✅ Extraction complete: {stage_time:.0f}ms ({successful_extractions}/{len(in_memory_docs)} successful)")
        
        # Final Stage: WRITE (always performed)
        print(f"💾 Final Stage: Writing processed documents to disk...")
        write_start = time.perf_counter()
        
        successful_writes = 0
        for doc in in_memory_docs:
            if doc.success:
                try:
                    # Write final markdown file
                    final_markdown = doc.generate_final_markdown()
                    output_file = output_dir / f"{doc.source_stem}.md"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(final_markdown)
                    
                    # Write semantic JSON if available
                    if doc.semantic_json:
                        json_file = output_dir / f"{doc.source_stem}.semantic.json"
                        import json
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(doc.semantic_json, f, indent=2)
                    
                    successful_writes += 1
                    
                except Exception as e:
                    doc.mark_failed(f"Write failed: {e}")
        
        write_time = (time.perf_counter() - write_start) * 1000
        print(f"   ✅ Write complete: {write_time:.0f}ms ({successful_writes}/{len(in_memory_docs)} successful)")
        
        total_time = time.perf_counter() - start_time
        
        return in_memory_docs, total_time, resource_summary
    
    def _generate_classification_data(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Generate classification metadata for document content.
        
        Performance target: <50ms per file
        Basic implementation - will be enhanced with Aho-Corasick later
        """
        start_time = time.perf_counter()
        
        # Basic entity extraction using regex (placeholder for Aho-Corasick)
        entities = {
            'money': self._extract_money(content),
            'phone': self._extract_phone(content), 
            'regulation': self._extract_regulation(content),
            'date': self._extract_dates(content),
            'url': self._extract_urls(content),
            'measurement': self._extract_measurements(content)
        }
        
        # Count total entities found
        total_entities = sum(len(v) for v in entities.values() if isinstance(v, list))
        
        # Determine document type based on content analysis
        document_types = self._classify_document_type(content)
        primary_domain = document_types[0] if document_types else "general"
        
        # Calculate processing time
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        classification_data = {
            'description': 'Document Classification & Type Detection',
            'classification_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'classification_method': 'mvp-fusion-basic',
            'document_types': str(document_types),
            'primary_domain': primary_domain,
            'confidence': 0.8,  # Basic implementation confidence
            'universal_entities_found': total_entities,
            'processing_time_ms': round(processing_time_ms, 2),
            'enhanced_mode': False  # Will be True when Aho-Corasick implemented
        }
        
        # Add entity lists if found
        for entity_type, entity_list in entities.items():
            if entity_list:
                classification_data[entity_type] = str(entity_list)
                
        # Add flags for important entity types
        classification_data['has_financial_data'] = bool(entities['money'])
        classification_data['has_regulations'] = bool(entities['regulation'])
        classification_data['has_contact_info'] = bool(entities['phone'])
        
        return classification_data
    
    def _extract_money(self, content: str) -> List[str]:
        """Extract monetary amounts from content"""
        pattern = r'\$[\d,]+(?:\.\d{2})?|\$\d+'
        return list(set(re.findall(pattern, content)))[:10]  # Limit to 10 items
    
    def _extract_phone(self, content: str) -> List[str]:
        """Extract phone numbers from content"""
        pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        return list(set(re.findall(pattern, content)))[:10]
    
    def _extract_regulation(self, content: str) -> List[str]:
        """Extract regulation references from content"""
        pattern = r'\d+\s*CFR\s*\d+(?:\.\d+)*'
        return list(set(re.findall(pattern, content)))[:10]
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates from content"""
        patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}\b'
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(dates))[:10]
    
    def _extract_urls(self, content: str) -> List[str]:
        """Extract URLs from content"""
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return list(set(re.findall(pattern, content)))[:5]
    
    def _extract_measurements(self, content: str) -> List[str]:
        """Extract measurements from content"""
        pattern = r'\d+(?:\.\d+)?\s*(?:inches?|feet?|meters?|cm|mm|kg|lbs?|pounds?)\b'
        return list(set(re.findall(pattern, content, re.IGNORECASE)))[:10]
    
    def _classify_document_type(self, content: str) -> List[str]:
        """Classify document type based on content analysis"""
        content_lower = content.lower()
        
        # Basic keyword-based classification
        if any(word in content_lower for word in ['osha', 'safety', 'hazard', 'injury']):
            return ['safety', 'compliance']
        elif any(word in content_lower for word in ['regulation', 'cfr', 'compliance']):
            return ['compliance', 'regulatory']
        elif any(word in content_lower for word in ['legal', 'contract', 'agreement']):
            return ['legal']
        else:
            return ['general']