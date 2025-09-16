#!/usr/bin/env python3
"""
MVP-Fusion Pipeline Processor
============================
Service-first, stage-based document processing pipeline.

Stages:
1. CONVERT: PDF → Markdown with conversion YAML
2. CLASSIFY: Add classification YAML section  
3. ENRICH: Add enrichment YAML section
4. EXTRACT: Generate semantic rules JSON

Service Architecture:
- Single-file processing optimized
- Progressive YAML building without file re-reading
- Each stage reads previous stage output
"""

import re
import time
from pathlib import Path
from typing import List, Dict, Any, Union
import yaml


class FusionPipeline:
    """
    Service-oriented pipeline processor for MVP-Fusion.
    
    Processes files through progressive stages:
    convert → classify → enrich → extract
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stages_to_run = config.get('pipeline', {}).get('stages_to_run', ['convert'])
        
    def process_files(self, extractor, file_paths: List[Path], output_dir: Path, 
                     max_workers: int = 2) -> tuple[List[Any], float, Dict[str, Any]]:
        """
        Process files through the configured pipeline stages.
        
        Args:
            extractor: Conversion extractor to use
            file_paths: List of input files
            output_dir: Output directory
            max_workers: Number of workers for conversion
            
        Returns:
            Tuple of (results, total_time, resource_summary)
        """
        start_time = time.perf_counter()
        
        print(f"🚀 Pipeline stages: {' → '.join(self.stages_to_run)}")
        
        # Stage 1: CONVERT (if requested)
        if 'convert' in self.stages_to_run:
            print(f"📄 Stage 1: Converting {len(file_paths)} files...")
            stage_start = time.perf_counter()
            
            # Use extractor for conversion
            batch_result = extractor.extract_batch(file_paths, output_dir, max_workers=max_workers)
            if len(batch_result) == 3:
                conversion_results, conversion_time, resource_summary = batch_result
            else:
                conversion_results, conversion_time = batch_result
                resource_summary = None
                
            stage_time = (time.perf_counter() - stage_start) * 1000
            print(f"   ✅ Conversion complete: {stage_time:.0f}ms")
        else:
            # If not converting, assume markdown files already exist
            conversion_results = []
            for file_path in file_paths:
                md_file = output_dir / f"{file_path.stem}.md"
                if md_file.exists():
                    conversion_results.append(type('Result', (), {
                        'success': True, 
                        'file_path': str(file_path),
                        'output_path': str(md_file),
                        'pages': 0
                    })())
            conversion_time = 0
            resource_summary = None
        
        # Stage 2: CLASSIFY (if requested)
        if 'classify' in self.stages_to_run:
            print(f"📋 Stage 2: Classifying documents...")
            print(f"   🔍 DEBUG: {len(conversion_results)} conversion results to classify")
            stage_start = time.perf_counter()
            
            classification_results = self._classify_stage(conversion_results, output_dir)
            
            stage_time = (time.perf_counter() - stage_start) * 1000
            print(f"   ✅ Classification complete: {stage_time:.0f}ms")
        
        # Stage 3: ENRICH (if requested)
        if 'enrich' in self.stages_to_run:
            print(f"🔍 Stage 3: Enriching documents...")
            stage_start = time.perf_counter()
            
            # TODO: Implement enrichment stage
            print(f"   ⚠️  Enrichment not implemented yet")
            
            stage_time = (time.perf_counter() - stage_start) * 1000
            print(f"   ✅ Enrichment complete: {stage_time:.0f}ms")
        
        # Stage 4: EXTRACT (if requested)  
        if 'extract' in self.stages_to_run:
            print(f"📄 Stage 4: Extracting semantic rules...")
            stage_start = time.perf_counter()
            
            # TODO: Implement extraction stage
            print(f"   ⚠️  Extraction not implemented yet")
            
            stage_time = (time.perf_counter() - stage_start) * 1000
            print(f"   ✅ Extraction complete: {stage_time:.0f}ms")
        
        total_time = time.perf_counter() - start_time
        
        return conversion_results, total_time, resource_summary
    
    def _classify_stage(self, conversion_results: List[Any], output_dir: Path) -> List[Any]:
        """
        Add classification YAML section to converted markdown files.
        
        Performance target: <50ms per file
        """
        classification_results = []
        
        for result in conversion_results:
            if not result.success:
                print(f"   ⚠️  Skipping failed result: {getattr(result, 'file_path', 'unknown')}")
                continue
            
            # Debug: Show all attributes of the result object
            print(f"   🔍 DEBUG: Result attributes:")
            for attr in ['file_path', 'output_path', 'success', 'pages']:
                value = getattr(result, attr, 'MISSING')
                print(f"     {attr}: {value}")
                
            try:
                # Derive markdown file path
                if hasattr(result, 'output_path') and result.output_path:
                    md_file = Path(result.output_path)
                    print(f"   📁 Using output_path: {md_file}")
                else:
                    # Fallback: derive from file_path and output_dir
                    file_path_str = getattr(result, 'file_path', '')
                    if not file_path_str:
                        print(f"   ❌ No file_path available, skipping")
                        continue
                    source_file = Path(file_path_str)
                    md_file = output_dir / f"{source_file.stem}.md"
                    print(f"   📁 Derived path: {md_file}")
                
                if not md_file.exists():
                    print(f"   ⚠️  Markdown file not found: {md_file}")
                    continue
                    
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse existing YAML frontmatter and content
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1]
                        markdown_content = parts[2]
                        
                        # Parse existing YAML
                        existing_yaml = yaml.safe_load(yaml_content)
                        
                        # Add classification section
                        classification_data = self._generate_classification_data(markdown_content, md_file)
                        existing_yaml['classification'] = classification_data
                        
                        # Reconstruct file with updated YAML
                        new_yaml = yaml.dump(existing_yaml, default_flow_style=False, sort_keys=False)
                        new_content = f"---\n{new_yaml}---{markdown_content}"
                        
                        # Write updated file
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print(f"   📋 Classified: {md_file.name}")
                        classification_results.append(result)
                
            except Exception as e:
                print(f"   ❌ Classification failed for {result.file_path}: {e}")
        
        return classification_results
    
    def _generate_classification_data(self, content: str, file_path: Path) -> Dict[str, Any]:
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