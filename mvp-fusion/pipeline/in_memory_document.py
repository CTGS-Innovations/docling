#!/usr/bin/env python3
"""
In-Memory Document Processing for Edge-Optimized Services
========================================================
Designed for CloudFlare Workers / Edge deployment with 1GB RAM limit.
Zero I/O between processing stages - everything stays in memory.
"""

import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class MemoryOverflowError(Exception):
    """Raised when document processing would exceed memory limits"""
    pass


class InMemoryDocument:
    """
    Edge-optimized document container for single-file service processing.
    
    Architecture:
    - PDF → markdown content (in memory)
    - Progressive YAML frontmatter building
    - Semantic JSON generation
    - Single final write operation
    
    Memory Budget: <100MB per document, <1GB total service limit
    """
    
    def __init__(self, source_file_path: str, memory_limit_mb: int = 100, source_url: Optional[str] = None):
        self.source_file_path = source_file_path
        self.source_filename = Path(source_file_path).name
        self.source_stem = Path(source_file_path).stem
        self.source_url = source_url  # Track original URL if this is URL-based processing
        
        # Content containers
        self.markdown_content = ""
        self.yaml_frontmatter = {}
        self.semantic_json = {}
        
        # Memory management
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.processing_start_time = time.perf_counter()
        
        # Processing metadata
        self.pages_processed = 0
        self.stage_timings = {}
        self.success = True
        self.error_message = None
        
    def set_conversion_data(self, markdown_content: str, yaml_metadata: Dict[str, Any], pages: int):
        """Set the initial conversion results"""
        self.markdown_content = markdown_content
        self.yaml_frontmatter = yaml_metadata.copy()
        self.pages_processed = pages
        self._check_memory_limit("after conversion")
        
    def add_classification_data(self, classification_data: Dict[str, Any]):
        """Add classification section to YAML frontmatter"""
        self.yaml_frontmatter['classification'] = classification_data
        
        # Check for semantic facts and store them for JSON generation
        if '_semantic_facts_for_json' in classification_data:
            self.semantic_json = classification_data['_semantic_facts_for_json']
            # Remove the temporary key to keep classification data clean
            del classification_data['_semantic_facts_for_json']
        
        self._check_memory_limit("after classification")
        
    def add_enrichment_data(self, enrichment_data: Dict[str, Any]):
        """Add enrichment section to YAML frontmatter"""
        self.yaml_frontmatter['enrichment'] = enrichment_data
        self._check_memory_limit("after enrichment")
        
    def add_normalization_data(self, normalization_data: Dict[str, Any]):
        """Add normalization section to YAML frontmatter"""
        self.yaml_frontmatter['normalization'] = normalization_data
        self._check_memory_limit("after normalization")
        
    def set_semantic_data(self, semantic_json: Dict[str, Any]):
        """Set the semantic extraction JSON"""
        self.semantic_json = semantic_json
        self._check_memory_limit("after extraction")
        
    def record_stage_timing(self, stage_name: str, time_ms: float):
        """Record timing for a processing stage"""
        self.stage_timings[stage_name] = time_ms
        
    def get_memory_footprint(self) -> int:
        """Calculate current memory usage in bytes"""
        markdown_bytes = len(self.markdown_content.encode('utf-8'))
        yaml_bytes = len(str(self.yaml_frontmatter).encode('utf-8'))
        json_bytes = len(str(self.semantic_json).encode('utf-8'))
        
        return markdown_bytes + yaml_bytes + json_bytes
        
    def _check_memory_limit(self, stage: str):
        """Check if memory usage exceeds limits"""
        current_memory = self.get_memory_footprint()
        if current_memory > self.memory_limit_bytes:
            memory_mb = current_memory / 1024 / 1024
            limit_mb = self.memory_limit_bytes / 1024 / 1024
            raise MemoryOverflowError(
                f"Memory limit exceeded {stage}: {memory_mb:.1f}MB > {limit_mb:.1f}MB limit"
            )
    
    def generate_final_markdown(self) -> str:
        """Generate the final markdown file with clean YAML frontmatter (no semantic duplication)"""
        if not self.yaml_frontmatter:
            return self.markdown_content
            
        # Create clean YAML without semantic_facts (goes to JSON only)
        clean_yaml = {}
        for key, value in self.yaml_frontmatter.items():
            if key == 'classification' and isinstance(value, dict):
                # Clean classification section - remove semantic data
                clean_classification = {}
                for sub_key, sub_value in value.items():
                    if sub_key not in ['semantic_facts', 'normalized_entities', 'semantic_summary']:
                        clean_classification[sub_key] = sub_value
                clean_yaml[key] = clean_classification
            else:
                clean_yaml[key] = value
            
        # Serialize clean YAML frontmatter with no line wrapping
        yaml_content = yaml.dump(
            clean_yaml, 
            default_flow_style=False, 
            sort_keys=False,
            width=float('inf'),  # Prevent line wrapping
            allow_unicode=True   # Properly handle unicode characters
        )
        
        # Combine YAML frontmatter with markdown content
        if self.markdown_content.startswith('---'):
            # Replace existing frontmatter
            parts = self.markdown_content.split('---', 2)
            if len(parts) >= 3:
                markdown_body = parts[2]
            else:
                markdown_body = self.markdown_content
        else:
            # Add frontmatter to content without frontmatter
            markdown_body = self.markdown_content
            
        return f"---\n{yaml_content}---{markdown_body}"
    
    def generate_knowledge_json(self) -> Dict[str, Any]:
        """Generate knowledge JSON file with semantic facts (matches temp file format)"""
        # Get semantic facts from YAML frontmatter (where they actually live)
        classification = self.yaml_frontmatter.get('classification', {})
        semantic_facts = classification.get('semantic_facts', {})
        semantic_summary = classification.get('semantic_summary', {})
        
        # If no semantic facts in YAML, try the semantic_json fallback
        if not semantic_facts and self.semantic_json:
            semantic_facts = self.semantic_json.get('semantic_facts', {})
            semantic_summary = self.semantic_json.get('semantic_summary', {})
        
        # If still no semantic facts, return empty
        if not semantic_facts:
            return {}
        
        # Calculate entity counts from classification data
        entities_section = classification.get('entities', {})
        global_entities = entities_section.get('global_entities', {})
        domain_entities = entities_section.get('domain_entities', {})
        
        # Count entities
        global_count = 0
        for entity_type, entities in global_entities.items():
            if isinstance(entities, list):
                global_count += len(entities)
        
        domain_count = 0  
        for entity_type, entities in domain_entities.items():
            if isinstance(entities, list):
                domain_count += len(entities)
        
        # Build knowledge data structure (matches temp file format)
        # Use URL as source if available, otherwise use file path
        source_reference = self.source_url if self.source_url else self.source_file_path
        source_type = 'url' if self.source_url else 'file'
        
        knowledge_data = {
            'source_info': {
                'source_file': source_reference,
                'source_type': source_type,
                'extraction_timestamp': semantic_summary.get('timestamp', ''),
                'extraction_engine': semantic_summary.get('extraction_engine', ''),
                'processing_method': 'mvp-fusion-pipeline'
            },
            'entity_summary': {
                'global_entities_count': global_count,
                'domain_entities_count': domain_count,
                'total_entities': global_count + domain_count
            },
            'semantic_facts': semantic_facts,
            'normalized_entities': classification.get('normalized_entities', {}),
            'semantic_summary': semantic_summary
        }
        
        return knowledge_data
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get comprehensive processing summary"""
        total_time_ms = (time.perf_counter() - self.processing_start_time) * 1000
        memory_mb = self.get_memory_footprint() / 1024 / 1024
        
        return {
            'source_file': self.source_filename,
            'success': self.success,
            'error': self.error_message,
            'pages_processed': self.pages_processed,
            'memory_used_mb': round(memory_mb, 2),
            'total_time_ms': round(total_time_ms, 1),
            'stage_timings': self.stage_timings.copy(),
            'has_classification': 'classification' in self.yaml_frontmatter,
            'has_enrichment': 'enrichment' in self.yaml_frontmatter,
            'has_semantic_json': bool(self.semantic_json)
        }
    
    def mark_failed(self, error_message: str):
        """Mark document processing as failed"""
        self.success = False
        self.error_message = error_message
        
    def __str__(self):
        return f"InMemoryDocument({self.source_filename}, {self.get_memory_footprint()/1024/1024:.1f}MB)"
    
    def __repr__(self):
        return self.__str__()