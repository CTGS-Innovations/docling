"""
YAML Metadata Manager for Pipeline Steps

Provides structured, section-aware YAML frontmatter management to prevent 
duplicate sections and ensure clean step separation.
"""

import yaml
import re
from typing import Dict, Any, Optional


class YAMLMetadataManager:
    """Manages YAML frontmatter with structured section blocks."""
    
    def __init__(self):
        self.STEP_KEYS = {
            'step1': 'conversion',
            'step2': 'classification', 
            'step3': 'enrichment'
        }
    
    def parse_existing_metadata(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse existing YAML frontmatter and return metadata dict + body content."""
        if not content.startswith('---'):
            return {}, content
            
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
            
        try:
            metadata = yaml.safe_load(parts[1]) or {}
            body = parts[2]
            return metadata, body
        except yaml.YAMLError:
            return {}, content
    
    def update_step_metadata(self, content: str, step_key: str, step_data: Dict[str, Any]) -> str:
        """Update specific step metadata while preserving other steps."""
        metadata, body = self.parse_existing_metadata(content)
        
        # Update the specific step block
        section_key = self.STEP_KEYS.get(step_key, step_key)
        metadata[section_key] = step_data
        
        # Serialize back to YAML with no line wrapping
        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False, width=float('inf'))
        
        # Clean up extra blank lines in body
        clean_body = body.lstrip('\n')
        
        return f"---\n{yaml_content}---\n{clean_body}"
    
    def get_step_metadata(self, content: str, step_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific step."""
        metadata, _ = self.parse_existing_metadata(content)
        section_key = self.STEP_KEYS.get(step_key, step_key)
        return metadata.get(section_key)
    
    def has_step(self, content: str, step_key: str) -> bool:
        """Check if a step's metadata exists."""
        return self.get_step_metadata(content, step_key) is not None
    
    def remove_step(self, content: str, step_key: str) -> str:
        """Remove a specific step's metadata."""
        metadata, body = self.parse_existing_metadata(content)
        section_key = self.STEP_KEYS.get(step_key, step_key)
        
        if section_key in metadata:
            del metadata[section_key]
        
        if metadata:
            yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
            return f"---\n{yaml_content}---\n{body}"
        else:
            return body
    
    def get_all_steps(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Get all step metadata."""
        metadata, _ = self.parse_existing_metadata(content)
        steps = {}
        
        for step_key, section_key in self.STEP_KEYS.items():
            if section_key in metadata:
                steps[step_key] = metadata[section_key]
                
        return steps