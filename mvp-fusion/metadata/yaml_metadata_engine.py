#!/usr/bin/env python3
"""
MVP-Fusion YAML Metadata Engine
===============================
Centralized, extensible system for generating YAML frontmatter.

LOCATION: /metadata/yaml_metadata_engine.py
PURPOSE: Single source of truth for all YAML metadata generation
SCHEMA: mvp-fusion-yaml-v1 (schema version 1.0)

Usage:
    from metadata.yaml_metadata_engine import YAMLMetadataEngine
    engine = YAMLMetadataEngine()
    yaml_content = engine.generate_conversion_metadata(file_path, page_count)

Extension Guidelines:
1. Add new metadata sections as separate methods
2. Increment schema_version for breaking changes
3. Maintain backward compatibility with version checks
4. Keep performance-first: only "free" operations
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional


class YAMLMetadataEngine:
    """
    Centralized YAML metadata generation engine.
    
    Design Principles:
    - Single source of truth for YAML structure
    - Performance-first (no expensive operations)
    - Extensible without breaking existing contracts
    - Version-tracked for maintainability
    """
    
    # Engine versioning
    ENGINE_NAME = "mvp-fusion-yaml-v1"
    SCHEMA_VERSION = "1.0"
    
    def __init__(self):
        pass
    
    def generate_conversion_metadata(self, file_path: Path, page_count: int, 
                                   extra_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate YAML frontmatter for document conversion.
        
        Args:
            file_path: Path to source document
            page_count: Number of pages extracted
            extra_metadata: Optional additional metadata to include
            
        Returns:
            Complete YAML frontmatter as string
        """
        try:
            # Core conversion metadata
            conversion_data = self._get_conversion_section(file_path, page_count)
            
            # Start building YAML
            yaml_sections = ["---", "conversion:"]
            
            # Add conversion data
            for key, value in conversion_data.items():
                yaml_sections.append(f'  {key}: {self._format_yaml_value(value)}')
            
            # Add extra metadata if provided
            if extra_metadata:
                for section_name, section_data in extra_metadata.items():
                    yaml_sections.append(f"{section_name}:")
                    for key, value in section_data.items():
                        yaml_sections.append(f'  {key}: {self._format_yaml_value(value)}')
            
            yaml_sections.append("---")
            
            return "\n".join(yaml_sections) + "\n"
            
        except Exception as e:
            # Fallback to minimal metadata
            return self._generate_fallback_yaml(file_path, page_count)
    
    def _get_conversion_section(self, file_path: Path, page_count: int) -> Dict[str, Any]:
        """Get conversion metadata section (all free operations)."""
        # File stats (free from filesystem)
        file_stats = file_path.stat()
        file_size = file_stats.st_size
        
        return {
            "description": "High-Speed Document Conversion & Analysis",
            "yaml_engine": self.ENGINE_NAME,
            "yaml_schema_version": self.SCHEMA_VERSION,
            "conversion_method": "mvp-fusion-highspeed",
            "extractor": "HighSpeed_Markdown_General",
            "source_type": "file",
            "source_path": str(file_path.absolute()),
            "filename": file_path.name,
            "file_extension": file_path.suffix,
            "format": file_path.suffix.upper().lstrip('.') if file_path.suffix else "UNKNOWN",
            "size_bytes": file_size,
            "size_human": self._format_file_size(file_size),
            "conversion_date": time.strftime('%Y-%m-%dT%H:%M:%S'),
            "page_count": page_count
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
    
    def _format_yaml_value(self, value: Any) -> str:
        """Format a value for YAML output."""
        if isinstance(value, str):
            # Quote strings that might need it
            if any(char in value for char in ['"', "'", ":", "\n", "\t"]):
                return f'"{value.replace('"', '\\"')}"'
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        else:
            return str(value)
    
    def _generate_fallback_yaml(self, file_path: Path, page_count: int) -> str:
        """Minimal fallback YAML if main generation fails."""
        return f"""---
conversion:
  description: "High-Speed Document Conversion"
  yaml_engine: "{self.ENGINE_NAME}"
  yaml_schema_version: "{self.SCHEMA_VERSION}"
  filename: "{file_path.name}"
  conversion_date: "{time.strftime('%Y-%m-%dT%H:%M:%S')}"
  page_count: {page_count}
---
"""

    # Extension Methods - Add new metadata sections here
    
    def generate_classification_metadata(self, document_types: list, confidence: float) -> Dict[str, Any]:
        """
        Generate classification metadata section.
        
        Usage: Add to extra_metadata parameter in generate_conversion_metadata()
        """
        return {
            "classification": {
                "description": "Document Classification & Type Detection",
                "classification_date": time.strftime('%Y-%m-%dT%H:%M:%S'),
                "classification_method": "mvp-fusion-enhanced",
                "document_types": str(document_types),
                "confidence": confidence
            }
        }
    
    def generate_enrichment_metadata(self, entities_found: int, domains_processed: list) -> Dict[str, Any]:
        """
        Generate enrichment metadata section.
        
        Usage: Add to extra_metadata parameter in generate_conversion_metadata()
        """
        return {
            "enrichment": {
                "description": "Domain-Specific Enrichment & Entity Extraction",
                "enrichment_date": time.strftime('%Y-%m-%dT%H:%M:%S'),
                "enrichment_method": "mvp-fusion-targeted",
                "total_entities": entities_found,
                "domains_processed": str(domains_processed)
            }
        }


# Convenience function for direct usage
def generate_conversion_yaml(file_path: Path, page_count: int, 
                           extra_metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Convenience function for generating conversion YAML.
    
    Args:
        file_path: Path to source document
        page_count: Number of pages extracted
        extra_metadata: Optional additional metadata sections
        
    Returns:
        Complete YAML frontmatter as string
    """
    engine = YAMLMetadataEngine()
    return engine.generate_conversion_metadata(file_path, page_count, extra_metadata)