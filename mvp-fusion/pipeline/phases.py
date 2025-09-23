"""
Pipeline Phase Definitions
==========================

Defines the standard phases for MVP-Fusion document processing pipeline.

Each phase represents a distinct step in the document processing workflow:
1. PDF Conversion - Convert documents to markdown
2. Document Processing - Core entity extraction and processing  
3. Classification - Document type and category classification
4. Entity Extraction - Extract and identify entities
5. Normalization - Normalize and canonicalize entities
6. Semantic Analysis - Extract facts, rules, and relationships

The phases are designed to be:
- Independent and testable
- Configurable via config.yaml
- Replaceable with different implementations
- Measurable for performance optimization
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass

class PhaseType(Enum):
    """Standard pipeline phase types."""
    PDF_CONVERSION = "pdf_conversion"
    DOCUMENT_PROCESSING = "document_processing"
    CLASSIFICATION = "classification"
    ENTITY_EXTRACTION = "entity_extraction"
    NORMALIZATION = "normalization"
    SEMANTIC_ANALYSIS = "semantic_analysis"

@dataclass
class PhaseConfig:
    """Configuration for a pipeline phase."""
    name: str
    enabled: bool = True
    processor: str = "default"
    timeout_ms: int = 30000  # 30 second default timeout
    target_time_ms: int = 30  # Performance target
    sidecar_test: str = None  # Optional A/B test processor
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}

class PhaseDefinitions:
    """Standard phase definitions for MVP-Fusion pipeline."""
    
    @staticmethod
    def get_default_phases() -> List[PhaseConfig]:
        """Get the default pipeline phase configuration."""
        return [
            PhaseConfig(
                name=PhaseType.PDF_CONVERSION.value,
                processor="docling_extractor",
                target_time_ms=40,  # PDF conversion target
                config={"preserve_formatting": True, "extract_tables": True}
            ),
            PhaseConfig(
                name=PhaseType.DOCUMENT_PROCESSING.value,
                processor="service_processor",
                target_time_ms=30,  # Main performance target
                config={"max_workers": 8}
            ),
            PhaseConfig(
                name=PhaseType.CLASSIFICATION.value,
                processor="embedded",
                target_time_ms=5,
                config={"confidence_threshold": 0.7}
            ),
            PhaseConfig(
                name=PhaseType.ENTITY_EXTRACTION.value,
                processor="embedded", 
                target_time_ms=10,
                config={"max_entities_per_type": 100}
            ),
            PhaseConfig(
                name=PhaseType.NORMALIZATION.value,
                processor="embedded",
                target_time_ms=8,
                config={"fuzzy_matching_threshold": 0.85}
            ),
            PhaseConfig(
                name=PhaseType.SEMANTIC_ANALYSIS.value,
                processor="embedded",
                target_time_ms=5,
                config={"extract_facts": True, "extract_rules": True}
            )
        ]
    
    @staticmethod
    def from_config(config: Dict[str, Any]) -> List[PhaseConfig]:
        """Create phase configurations from config dictionary."""
        phases = []
        pipeline_config = config.get('pipeline', {})
        
        for phase_type in PhaseType:
            phase_name = phase_type.value
            phase_config = pipeline_config.get(phase_name, {})
            
            phases.append(PhaseConfig(
                name=phase_name,
                enabled=phase_config.get('enabled', True),
                processor=phase_config.get('processor', 'default'),
                timeout_ms=phase_config.get('timeout_ms', 30000),
                target_time_ms=phase_config.get('target_time_ms', 30),
                sidecar_test=phase_config.get('sidecar_test'),
                config=phase_config.get('config', {})
            ))
        
        return phases