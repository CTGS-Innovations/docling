"""
Modular extraction engines for different document processing methodologies.
Each extractor follows naming convention: {Performance}_{OutputFormat}_{InputType}_Extractor

WORKING EXTRACTOR:
- HighSpeed_Markdown_General_Extractor: 2000+ pages/sec for all document types

ARCHITECTURAL STUBS (TODO - examples of future implementations):
- HighAccuracy_Markdown_General_Extractor: Slow but precise extraction
- HighSpeed_JSON_PDF_Extractor: PDF-specific with metadata
- Specialized_Markdown_Legal_Extractor: Domain-specific legal processing
"""

from .base_extractor import BaseExtractor, ExtractionResult
from .highspeed_markdown_general_extractor import HighSpeed_Markdown_General_Extractor

# Import stubs for reference (all return "not implemented" errors)
from .extractor_stubs import (
    HighAccuracy_Markdown_General_Extractor,
    HighSpeed_JSON_PDF_Extractor, 
    Specialized_Markdown_Legal_Extractor
)

__all__ = [
    'BaseExtractor', 
    'ExtractionResult',
    'HighSpeed_Markdown_General_Extractor',
    # Architectural stubs (not implemented)
    'HighAccuracy_Markdown_General_Extractor',
    'HighSpeed_JSON_PDF_Extractor',
    'Specialized_Markdown_Legal_Extractor'
]