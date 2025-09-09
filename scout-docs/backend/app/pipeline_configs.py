"""
Pipeline configuration definitions for different performance optimization levels.
Each pipeline is optimized for specific use cases with clear trade-offs.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from docling.datamodel.pipeline_options import PdfPipelineOptions, PdfBackend
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice

# Import backend classes
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend


class PipelineProfile(str, Enum):
    """Available pipeline performance profiles."""
    
    # Standard pipelines
    STANDARD = "standard"
    VLM = "vlm"
    
    # Performance-optimized pipelines
    FAST_TEXT = "fast_text"           # Fastest text-only extraction
    BALANCED = "balanced"             # Good balance of features vs speed
    FULL_EXTRACTION = "full_extraction"  # All features enabled (slowest)
    
    # Specialized pipelines
    OCR_ONLY = "ocr_only"            # For scanned documents
    TABLE_FOCUSED = "table_focused"   # Optimized for table extraction


class PipelineConfig(BaseModel):
    """Configuration for a specific pipeline profile."""
    
    name: str
    description: str
    use_case: str
    features: List[str]
    performance: str  # "Fastest", "Fast", "Medium", "Slow"
    compute_preference: str  # "CPU", "GPU", "Either"
    
    # Docling configuration
    pdf_backend: PdfBackend
    backend_class: Any  # The actual backend class to use
    do_ocr: bool
    do_table_structure: bool
    do_picture_classification: bool
    do_picture_description: bool
    generate_page_images: bool
    generate_picture_images: bool
    generate_table_images: bool
    generate_parsed_pages: bool
    
    # Additional options
    force_backend_text: bool = False
    images_scale: float = 1.0
    
    class Config:
        arbitrary_types_allowed = True


class PipelineRegistry:
    """Registry of all available pipeline configurations."""
    
    # Define all pipeline configurations
    CONFIGS: Dict[PipelineProfile, PipelineConfig] = {
        
        PipelineProfile.FAST_TEXT: PipelineConfig(
            name="Fast Text",
            description="Fastest text-only extraction using pypdfium2 backend",
            use_case="Born-digital PDFs, text-only content, bulk processing",
            features=["Text extraction"],
            performance="Fastest",
            compute_preference="CPU",
            
            pdf_backend=PdfBackend.PYPDFIUM2,
            backend_class=PyPdfiumDocumentBackend,
            do_ocr=False,
            do_table_structure=False,
            do_picture_classification=False,
            do_picture_description=False,
            generate_page_images=False,
            generate_picture_images=False,
            generate_table_images=False,
            generate_parsed_pages=False,
            force_backend_text=True
        ),
        
        PipelineProfile.BALANCED: PipelineConfig(
            name="Balanced",
            description="Good balance of features and speed with table extraction",
            use_case="Most documents with mixed content, moderate processing volumes",
            features=["Text extraction", "Table structure", "Basic layout"],
            performance="Fast",
            compute_preference="Either",
            
            pdf_backend=PdfBackend.PYPDFIUM2,
            backend_class=PyPdfiumDocumentBackend,
            do_ocr=False,
            do_table_structure=True,
            do_picture_classification=False,
            do_picture_description=False,
            generate_page_images=False,
            generate_picture_images=False,
            generate_table_images=False,
            generate_parsed_pages=False
        ),
        
        PipelineProfile.OCR_ONLY: PipelineConfig(
            name="OCR Focused",
            description="Optimized for scanned documents with OCR processing",
            use_case="Scanned PDFs, image-based documents, handwritten content",
            features=["OCR text extraction", "Basic layout", "Image processing"],
            performance="Medium",
            compute_preference="GPU",
            
            pdf_backend=PdfBackend.DLPARSE_V2,
            backend_class=DoclingParseV2DocumentBackend,
            do_ocr=True,
            do_table_structure=False,
            do_picture_classification=True,
            do_picture_description=False,
            generate_page_images=False,
            generate_picture_images=False,
            generate_table_images=False,
            generate_parsed_pages=False
        ),
        
        PipelineProfile.TABLE_FOCUSED: PipelineConfig(
            name="Table Focused",
            description="Optimized for documents with complex table structures",
            use_case="Financial reports, data sheets, structured documents",
            features=["Text extraction", "Advanced table structure", "Cell matching"],
            performance="Medium",
            compute_preference="GPU",
            
            pdf_backend=PdfBackend.DLPARSE_V2,
            backend_class=DoclingParseV2DocumentBackend,
            do_ocr=False,
            do_table_structure=True,
            do_picture_classification=False,
            do_picture_description=False,
            generate_page_images=False,
            generate_picture_images=False,
            generate_table_images=True,  # Generate table images for debugging
            generate_parsed_pages=False
        ),
        
        PipelineProfile.FULL_EXTRACTION: PipelineConfig(
            name="Full Extraction",
            description="Complete feature extraction with all processing enabled",
            use_case="Research documents, complex layouts, maximum accuracy needed",
            features=["Text extraction", "OCR", "Table structure", "Image classification", "Image description", "All outputs"],
            performance="Slow",
            compute_preference="GPU",
            
            pdf_backend=PdfBackend.DLPARSE_V4,
            backend_class=DoclingParseV4DocumentBackend,
            do_ocr=True,
            do_table_structure=True,
            do_picture_classification=True,
            do_picture_description=True,
            generate_page_images=True,
            generate_picture_images=True,
            generate_table_images=True,
            generate_parsed_pages=True,
            images_scale=2.0
        ),
        
        # Keep existing pipelines for compatibility
        PipelineProfile.STANDARD: PipelineConfig(
            name="Standard",
            description="Standard processing pipeline with OCR and table structure",
            use_case="General purpose document processing",
            features=["Text extraction", "OCR", "Table structure", "Basic layout"],
            performance="Medium",
            compute_preference="Either",
            
            pdf_backend=PdfBackend.DLPARSE_V2,
            backend_class=DoclingParseV2DocumentBackend,
            do_ocr=True,
            do_table_structure=True,
            do_picture_classification=False,
            do_picture_description=False,
            generate_page_images=False,
            generate_picture_images=False,
            generate_table_images=False,
            generate_parsed_pages=False
        ),
        
        PipelineProfile.VLM: PipelineConfig(
            name="Vision Language Model",
            description="AI-powered document understanding with vision capabilities",
            use_case="Complex documents requiring AI interpretation",
            features=["AI vision processing", "Intelligent layout understanding", "Content description"],
            performance="Slow",
            compute_preference="GPU",
            
            pdf_backend=PdfBackend.DLPARSE_V2,
            backend_class=DoclingParseV2DocumentBackend,
            do_ocr=False,  # VLM handles this
            do_table_structure=False,  # VLM handles this
            do_picture_classification=False,
            do_picture_description=False,
            generate_page_images=True,  # VLM needs page images
            generate_picture_images=False,
            generate_table_images=False,
            generate_parsed_pages=False
        )
    }
    
    @classmethod
    def get_config(cls, profile: PipelineProfile) -> PipelineConfig:
        """Get configuration for a specific pipeline profile."""
        return cls.CONFIGS[profile]
    
    @classmethod
    def list_profiles(cls) -> List[Dict[str, Any]]:
        """List all available pipeline profiles for UI consumption."""
        profiles = []
        for profile, config in cls.CONFIGS.items():
            profiles.append({
                "id": profile.value,
                "name": config.name,
                "description": config.description,
                "use_case": config.use_case,
                "features": config.features,
                "performance": config.performance,
                "compute_preference": config.compute_preference
            })
        return profiles
    
    @classmethod
    def create_pipeline_options(
        cls, 
        profile: PipelineProfile, 
        compute_mode: str = "auto"
    ) -> tuple:
        """Create Docling pipeline options and backend class from a profile configuration."""
        config = cls.get_config(profile)
        
        # Configure accelerator based on compute mode and pipeline preference
        if compute_mode.lower() == "gpu" or (compute_mode == "auto" and config.compute_preference == "GPU"):
            accelerator_options = AcceleratorOptions(
                device=AcceleratorDevice.CUDA,
                num_threads=4
            )
        else:
            accelerator_options = AcceleratorOptions(
                device=AcceleratorDevice.CPU,
                num_threads=8
            )
        
        # Create pipeline options
        options = PdfPipelineOptions()
        options.accelerator_options = accelerator_options
        options.do_ocr = config.do_ocr
        options.do_table_structure = config.do_table_structure
        options.do_picture_classification = config.do_picture_classification
        options.do_picture_description = config.do_picture_description
        options.generate_page_images = config.generate_page_images
        options.generate_picture_images = config.generate_picture_images
        options.generate_table_images = config.generate_table_images
        options.generate_parsed_pages = config.generate_parsed_pages
        options.force_backend_text = config.force_backend_text
        options.images_scale = config.images_scale
        
        # Configure table structure options if enabled
        if config.do_table_structure:
            if hasattr(options, 'table_structure_options') and options.table_structure_options:
                options.table_structure_options.do_cell_matching = True
        
        return options, config.backend_class
    
    @classmethod
    def get_recommended_compute_mode(cls, profile: PipelineProfile) -> str:
        """Get recommended compute mode for a pipeline profile."""
        config = cls.get_config(profile)
        return config.compute_preference.lower()