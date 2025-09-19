#!/usr/bin/env python3
"""
MVP-Fusion Service Processor
============================
Clean I/O + CPU worker architecture for edge service deployment.

Architecture:
- 1 I/O Worker: Non-blocking ingestion (downloads, file reads, PDF conversion)
- N CPU Workers: Pure compute (entity extraction, classification, semantic analysis)
- Work Queue: Async queue between I/O and CPU layers with backpressure
"""

import time
try:
    from knowledge.extractors.fast_regex import FastRegexEngine
    import knowledge.extractors.fast_regex as regex_module
    # Use the existing fast_regex wrapper which handles FLPC + fallback
    _regex_engine = FastRegexEngine()
    # Create re-like interface
    re = _regex_engine
    # Get flags from the module
    re.IGNORECASE = regex_module.IGNORECASE
    re.MULTILINE = regex_module.MULTILINE
    re.DOTALL = regex_module.DOTALL
    FLPC_AVAILABLE = True
except ImportError:
    import re
    FLPC_AVAILABLE = False
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty, Full
from pathlib import Path
from typing import List, Dict, Any, Union, Optional, Set
from dataclasses import dataclass

from utils.logging_config import get_fusion_logger
from utils.phase_manager import get_phase_manager, set_current_phase, add_files_processed, add_pages_processed, get_phase_performance_report
from pipeline.in_memory_document import InMemoryDocument
from metadata.yaml_metadata_engine import YAMLMetadataEngine

# Import real extraction functions
try:
    import fitz  # PyMuPDF for PDF processing
except ImportError:
    fitz = None

# Import real entity extraction
try:
    from knowledge.extractors.semantic_fact_extractor import SemanticFactExtractor
    from knowledge.aho_corasick_engine import AhoCorasickKnowledgeEngine
except ImportError:
    SemanticFactExtractor = None
    AhoCorasickKnowledgeEngine = None

# Import conservative person entity extractor for validation
try:
    from utils.person_entity_extractor import PersonEntityExtractor
    CONSERVATIVE_PERSON_AVAILABLE = True
except ImportError:
    CONSERVATIVE_PERSON_AVAILABLE = False

# Import entity normalizer for structured data enhancement
try:
    from knowledge.extractors.entity_normalizer import EntityNormalizer
    ENTITY_NORMALIZER_AVAILABLE = True
except ImportError:
    ENTITY_NORMALIZER_AVAILABLE = False


@dataclass
class WorkItem:
    """Work item passed from I/O worker to CPU workers"""
    document: 'InMemoryDocument'  # Pass the actual document object, not just markdown
    metadata: Dict[str, Any]
    ingestion_time: float


class ServiceProcessor:
    """
    Clean I/O + CPU service processor for edge deployment.
    
    Separates I/O-bound ingestion from CPU-bound processing with async queue.
    """
    
    def __init__(self, config: Dict[str, Any], max_workers: int = None):
        self.config = config
        self.logger = get_fusion_logger(__name__)
        self.yaml_engine = YAMLMetadataEngine()  # Initialize YAML metadata engine
        
        # Phase-specific loggers for clearer identification
        self.pdf_converter = get_fusion_logger("pdf_converter")
        self.document_classifier = get_fusion_logger("document_classifier") 
        self.core8_extractor = get_fusion_logger("core8_extractor")
        self.entity_extraction = get_fusion_logger("entity_extraction")
        self.semantic_analyzer = get_fusion_logger("semantic_analyzer")
        
        # Service coordination loggers
        self.service_coordinator = get_fusion_logger("service_coordinator")
        self.document_processor = get_fusion_logger("document_processor")
        self.file_writer = get_fusion_logger("file_writer")
        self.memory_manager = get_fusion_logger("memory_manager")
        self.queue_manager = get_fusion_logger("queue_manager")
        
        # Initialize phase manager
        self.phase_manager = get_phase_manager()
        
        # Worker configuration - use CLI override if provided, otherwise config
        if max_workers is not None:
            self.cpu_workers = max_workers  # Use CLI override
        else:
            # Fallback to config file
            from utils.deployment_manager import DeploymentManager
            deployment_manager = DeploymentManager(config)
            self.cpu_workers = deployment_manager.get_max_workers()
        self.queue_size = config.get('pipeline', {}).get('queue_size', 100)
        self.memory_limit_mb = config.get('pipeline', {}).get('memory_limit_mb', 100)
        
        # Work queue between I/O and CPU layers
        self.work_queue = Queue(maxsize=self.queue_size)
        
        # Processing state
        self.active = False
        self.io_worker = None
        self.cpu_executor = None
        
        # Initialize real extractors (shared across CPU workers)
        self.aho_corasick_engine = None
        self.semantic_extractor = None
        self.person_extractor = None
        self._initialize_extractors()
        
        self.service_coordinator.staging(f"Service Processor initialized: 1 I/O + {self.cpu_workers} CPU workers")
        set_current_phase('initialization')
        self.phase_manager.log('memory_manager', f"📋 Queue size: {self.queue_size}, Memory limit: {self.memory_limit_mb}MB")
    
    def _initialize_extractors(self):
        """Initialize real entity extractors for CPU workers"""
        if AhoCorasickKnowledgeEngine and SemanticFactExtractor:
            try:
                # Initialize Aho-Corasick engine for pattern matching (needs knowledge dir path)
                self.aho_corasick_engine = AhoCorasickKnowledgeEngine("knowledge")
                
                # Initialize semantic fact extractor
                self.semantic_extractor = SemanticFactExtractor()
                
                # Initialize conservative person entity extractor for validation
                if CONSERVATIVE_PERSON_AVAILABLE:
                    # Point to the actual corpus files with hundreds of thousands of names
                    corpus_dir = Path("knowledge/corpus/foundation_data")
                    self.person_extractor = PersonEntityExtractor(
                        first_names_path=corpus_dir / "first_names_2025_09_18.txt",
                        last_names_path=corpus_dir / "last_names_2025_09_18.txt", 
                        organizations_path=corpus_dir / "organizations_2025_09_18.txt",
                        min_confidence=0.7
                    )
                    set_current_phase('initialization')
                    self.phase_manager.log('core8_extractor', "✅ Conservative person extractor initialized with 429K first names, 99K last names, 139K orgs")
                
                # Load GPE corpus for geopolitical entity recognition
                self.gpe_corpus = self._load_gpe_corpus()
                
                # Initialize entity normalizer for structured data enhancement
                if ENTITY_NORMALIZER_AVAILABLE:
                    self.entity_normalizer = EntityNormalizer()
                    set_current_phase('initialization')
                    self.phase_manager.log('core8_extractor', "✅ Entity normalizer initialized for structured data enhancement")
                else:
                    self.entity_normalizer = None
                
                set_current_phase('initialization')
                self.phase_manager.log('core8_extractor', "✅ Real extractors initialized")
            except Exception as e:
                self.logger.logger.warning(f"⚠️  Failed to initialize extractors: {e}")
                self.aho_corasick_engine = None
                self.semantic_extractor = None
                self.person_extractor = None
                self.entity_normalizer = None
        else:
            self.logger.logger.warning("⚠️  Real extractors not available - using mock processing")
            self.entity_normalizer = None
    
    def start_service(self):
        """Start the I/O + CPU worker service"""
        if self.active:
            self.logger.logger.warning("⚠️  Service already running")
            return
        
        self.active = True
        self.service_coordinator.staging("Starting I/O + CPU service...")
        
        # Start CPU worker pool
        self.cpu_executor = ThreadPoolExecutor(
            max_workers=self.cpu_workers, 
            thread_name_prefix="CPUWorker"
        )
        
        self.service_coordinator.staging(f"Service started: 1 I/O worker + {self.cpu_workers} CPU workers")
    
    def stop_service(self):
        """Stop the I/O + CPU worker service"""
        if not self.active:
            return
        
        self.service_coordinator.staging("Stopping I/O + CPU service...")
        self.active = False
        
        # Stop CPU workers
        if self.cpu_executor:
            self.cpu_executor.shutdown(wait=True)
            self.cpu_executor = None
        
        self.service_coordinator.staging("Service stopped")
    
    def _extract_universal_entities(self, content: str) -> Dict[str, List]:
        """
        Extract Core 8 Universal Entities with span information and clean text.
        Core 8: PERSON, ORG, LOC, GPE, DATE, TIME, MONEY, PERCENT
        Additional: phone, email, url, regulations, measurements
        """
        entities = {}
        
        # PERSON - Standard NLP flow: Use original working logic from comprehensive_entity_extractor
        # Stage 1: Conservative PersonEntityExtractor with Aho-Corasick validation (this was working)
        if self.person_extractor:
            try:
                conservative_persons = self.person_extractor.extract_persons(content)
                set_current_phase('entity_extraction')
                self.phase_manager.log('core8_extractor', f"🎯 Conservative person extractor found {len(conservative_persons)} validated persons")
                
                entities['person'] = []
                for person in conservative_persons:
                    # Standard NER format with validation confidence (from Aho-Corasick corpus matching)
                    entity = {
                        'value': person.get('text', person.get('name', '')),
                        'text': person.get('text', person.get('name', '')),
                        'type': 'PERSON',
                        'span': {
                            'start': person.get('position', 0),
                            'end': person.get('position', 0) + len(person.get('text', person.get('name', '')))
                        },
                        'confidence': person.get('confidence', 0.0)  # Validation confidence from corpus matching
                    }
                    entities['person'].append(entity)
                
                # Limit to 20 persons
                entities['person'] = entities['person'][:20]
                
            except Exception as e:
                self.logger.logger.warning(f"Conservative person extraction failed: {e}")
                # Fallback to basic regex
                person_patterns = [
                    r'\b(?:Dr|Prof|Mr|Mrs|Ms|Rev|Sr|Jr)\.\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b',
                    r'\b[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+\b',
                    r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?\b'
                ]
                person_candidates = []
                for pattern in person_patterns:
                    person_candidates.extend(self._extract_entities_with_spans(content, pattern, 'PERSON'))
                entities['person'] = person_candidates[:20]
        else:
            self.logger.logger.warning("PersonEntityExtractor not available, using basic regex")
            # Basic regex fallback
            person_pattern = r'\b(?:Dr|Prof|Mr|Mrs|Ms|Rev|Sr|Jr)\.\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b'
            entities['person'] = self._extract_entities_with_spans(content, person_pattern, 'PERSON')[:20]
        
        # ORGANIZATION - Multiple patterns
        org_patterns = [
            r'\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:Inc|Corp|LLC|Ltd|Company|Organization|Institute|University|College|Department|Agency|Administration|Commission|Bureau|Office)\b',
            r'\b(?:OSHA|FDA|EPA|NASA|FBI|CIA|DOD|DOJ|USDA|CDC|NIH|NSF|NIST|NOAA|FAA|FCC|SEC|IRS|ATF|DEA|DHS|TSA|FEMA)\b'
        ]
        org_entities = []
        for pattern in org_patterns:
            org_entities.extend(self._extract_entities_with_spans(content, pattern, 'ORG'))
        # Deduplicate by value while preserving span info
        entities['org'] = self._deduplicate_entities(org_entities)[:20]
        
        # LOCATION
        loc_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b|\b\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Plaza|Place|Pl)\b'
        entities['location'] = self._extract_entities_with_spans(content, loc_pattern, 'LOCATION')[:20]
        
        # GPE (Geo-political entities) - Use comprehensive corpus
        gpe_entities = []
        if hasattr(self, 'gpe_corpus') and self.gpe_corpus:
            # Use corpus-based matching for high accuracy
            for gpe_name in self.gpe_corpus:
                if len(gpe_name) > 2:  # Skip very short entries
                    # Use word boundary matching for precise detection
                    gpe_pattern = r'\b' + re.escape(gpe_name) + r'\b'
                    matches = list(re.finditer(gpe_pattern, content, re.IGNORECASE))
                    for match in matches:
                        clean_text = self._clean_entity_text(match.group(0))
                        if self._is_valid_entity_text(clean_text):
                            # Handle FLPC vs Python re API differences
                            try:
                                start = match.start(0)
                                end = match.end(0)
                            except TypeError:
                                start = match.start()
                                end = match.end()
                                
                            entity = {
                                'value': clean_text,
                                'text': clean_text,
                                'type': 'GPE',
                                'span': {
                                    'start': start,
                                    'end': end
                                }
                            }
                            gpe_entities.append(entity)
        else:
            # Fallback to basic patterns
            gpe_pattern = r'\b(?:United States|USA|US|Canada|Mexico|China|Japan|Germany|France|UK|United Kingdom)\b'
            gpe_entities = self._extract_entities_with_spans(content, gpe_pattern, 'GPE', re.IGNORECASE)
        
        entities['gpe'] = self._deduplicate_entities(gpe_entities)[:20]
        
        # DATE - Multiple patterns
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s*\d{4}\b'
        ]
        date_entities = []
        for pattern in date_patterns:
            date_entities.extend(self._extract_entities_with_spans(content, pattern, 'DATE', re.IGNORECASE))
        entities['date'] = self._deduplicate_entities(date_entities)[:20]
        
        # TIME
        time_pattern = r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?\b'
        entities['time'] = self._extract_entities_with_spans(content, time_pattern, 'TIME', re.IGNORECASE)[:10]
        
        # MONEY - Handle amounts with M/K suffixes (FLPC compatible - no lookahead)
        money_pattern = r'\$[\d,]+(?:\.\d+)?(?:[MKB]|(?:\s*(?:billion|million|thousand|hundred|USD|dollars?)))?\b'
        entities['money'] = self._extract_entities_with_spans(content, money_pattern, 'MONEY', re.IGNORECASE)[:20]
        
        # PERCENT
        percent_pattern = r'\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?\s+percent\b'
        entities['percent'] = self._extract_entities_with_spans(content, percent_pattern, 'PERCENT', re.IGNORECASE)[:20]
        
        # PHONE
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        entities['phone'] = self._extract_entities_with_spans(content, phone_pattern, 'PHONE')[:10]
        
        # EMAIL
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['email'] = self._extract_entities_with_spans(content, email_pattern, 'EMAIL')[:10]
        
        # URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        entities['url'] = self._extract_entities_with_spans(content, url_pattern, 'URL')[:10]
        
        # REGULATIONS (CFR, USC, etc.)
        reg_pattern = r'\b\d+\s+(?:CFR|USC|U\.S\.C\.|C\.F\.R\.)\s+§?\s*\d+(?:\.\d+)?(?:\([a-z]\))?|\b(?:Section|Sec\.)\s+\d+(?:\.\d+)?'
        entities['regulation'] = self._extract_entities_with_spans(content, reg_pattern, 'REGULATION', re.IGNORECASE)[:20]
        
        # MEASUREMENTS - Handle potential newlines between number and unit
        measurement_pattern = r'\b\d+(?:\.\d+)?(?:\s|\n)*(?:feet|ft|inches|in|meters|m|kilometers|km|miles|mi|pounds|lbs|kilograms|kg|gallons|gal|liters|L|degrees|°|FLOPS|flops|parameters|params|MHz|GHz|KB|MB|GB|TB)\b'
        entities['measurement'] = self._extract_entities_with_spans(content, measurement_pattern, 'MEASUREMENT', re.IGNORECASE | re.MULTILINE)[:20]
        
        return entities
    
    def _extract_entities_with_spans(self, content: str, pattern: str, entity_type: str, flags: int = 0) -> List[Dict]:
        """Extract entities with span information and clean text."""
        entities = []
        seen = set()
        
        try:
            # Use FLPC regex engine with fallback to Python re for compatibility
            for match in re.finditer(pattern, content, flags):
                # Clean the matched text (remove newlines, normalize whitespace)
                raw_text = match.group(0)
                clean_text = self._clean_entity_text(raw_text)
                
                # Skip if already seen or invalid
                if clean_text in seen or not self._is_valid_entity_text(clean_text):
                    continue
                seen.add(clean_text)
                
                # FLPC Match objects require index parameter (0 for full match)
                try:
                    # Try FLPC API first (requires index)
                    start = match.start(0)
                    end = match.end(0)
                except TypeError:
                    # Fallback to Python re API (no index)
                    start = match.start()
                    end = match.end()
                
                entity = {
                    'value': clean_text,
                    'text': clean_text, 
                    'type': entity_type,
                    'span': {
                        'start': start,
                        'end': end
                    }
                }
                entities.append(entity)
        except Exception as e:
            # Fallback to Python re if FLPC fails
            import re as python_re
            for match in python_re.finditer(pattern, content, flags):
                raw_text = match.group(0)
                clean_text = self._clean_entity_text(raw_text)
                
                if clean_text in seen or not self._is_valid_entity_text(clean_text):
                    continue
                seen.add(clean_text)
                
                # Handle FLPC vs Python re API differences
                try:
                    start = match.start(0)
                    end = match.end(0)
                except TypeError:
                    start = match.start()
                    end = match.end()
                    
                entity = {
                    'value': clean_text,
                    'text': clean_text, 
                    'type': entity_type,
                    'span': {
                        'start': start,
                        'end': end
                    }
                }
                entities.append(entity)
        
        return entities
    
    def _clean_entity_text(self, text: str) -> str:
        """Clean entity text by normalizing whitespace and removing line breaks."""
        if not text:
            return ""
        
        # Replace all whitespace (including newlines) with single spaces
        cleaned = ' '.join(text.split()).strip()
        
        # Handle common unicode issues
        cleaned = cleaned.replace('\\u2014', '—')  # em-dash
        cleaned = cleaned.replace('\\u2013', '–')  # en-dash
        cleaned = cleaned.replace('\\u2019', "'")  # right single quote
        cleaned = cleaned.replace('\\u201c', '"')  # left double quote
        cleaned = cleaned.replace('\\u201d', '"')  # right double quote
        
        return cleaned
    
    def _is_valid_entity_text(self, text: str) -> bool:
        """Validate entity text to filter out malformed entries."""
        if not text or len(text.strip()) < 2:
            return False
        
        # Filter out entities that are mostly punctuation or whitespace
        alpha_chars = sum(1 for c in text if c.isalnum())
        if alpha_chars < len(text) * 0.3:  # At least 30% alphanumeric
            return False
            
        return True
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities while preserving the first occurrence."""
        seen = set()
        deduplicated = []
        
        for entity in entities:
            value = entity.get('value', '')
            if value not in seen:
                seen.add(value)
                deduplicated.append(entity)
        
        return deduplicated
    
    def _extract_role_from_context(self, context: str) -> Optional[str]:
        """Extract person's role from context (from original comprehensive extractor)"""
        if not context:
            return None
            
        context_lower = context.lower()
        
        # Universal role patterns with transitional connectors
        role_patterns = [
            r'(?:chief|senior|executive|deputy|assistant|associate|junior)\s+\w+(?:\s+\w+){0,2}',
            r'(?:president|ceo|cto|cfo|coo|cmo|ciso|chairman|chairwoman|chairperson)',
            r'(?:director|manager|supervisor|head|lead|coordinator|administrator)(?:\s+of\s+\w+(?:\s+\w+){0,2})?',
            r'(?:vice\s+president|vp|evp|svp)(?:\s+of\s+\w+(?:\s+\w+){0,2})?',
        ]
        
        for pattern in role_patterns:
            match = re.search(pattern, context_lower)
            if match:
                return match.group(0).strip()
        
        # Simple role words
        simple_roles = ['director', 'manager', 'supervisor', 'inspector', 'worker', 'contractor', 'president', 'ceo']
        for role in simple_roles:
            if role in context_lower:
                return role
                
        return None
    
    def _load_gpe_corpus(self) -> Set[str]:
        """Load geopolitical entities corpus for GPE recognition."""
        gpe_file = Path("knowledge/corpus/foundation_data/geopolitical_entities_2025_09_18.txt")
        gpe_entities = set()
        
        try:
            if gpe_file.exists():
                with open(gpe_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith('#'):
                            gpe_entities.add(line)
                set_current_phase('entity_extraction')
                self.phase_manager.log('entity_extraction', f"✅ Loaded {len(gpe_entities)} GPE entities from corpus")
            else:
                self.logger.logger.warning(f"⚠️  GPE corpus file not found: {gpe_file}")
        except Exception as e:
            self.logger.logger.warning(f"⚠️  Failed to load GPE corpus: {e}")
        
        return gpe_entities
    
    def _quick_content_scan(self, content: str) -> Dict[str, bool]:
        """
        Quick pre-screening scan for content types (tables, images, formulas, etc.)
        Fast yes/no flags to inform classification downstream.
        """
        content_lower = content.lower()
        
        # Quick pattern-based detection
        return {
            'has_tables': bool(re.search(r'\|.*\|.*\|', content)) or 'table' in content_lower,
            'has_images': bool(re.search(r'!\[.*\]\(.*\)', content)) or any(x in content_lower for x in ['image', 'figure', 'diagram']),
            'has_formulas': bool(re.search(r'[\$`]{1,2}.*?[\$`]{1,2}', content)) or any(x in content_lower for x in ['equation', 'formula', '∑', '∫', 'α', 'β']),
            'has_code': bool(re.search(r'```.*?```', content, re.DOTALL)) or 'import ' in content,
            'has_links': bool(re.search(r'https?://', content)) or bool(re.search(r'\[.*?\]\(.*?\)', content)),
            'has_lists': bool(re.search(r'^\s*[-*+•]\s', content, re.MULTILINE)) or bool(re.search(r'^\s*\d+\.', content, re.MULTILINE)),
            'has_headers': bool(re.search(r'^#+\s', content, re.MULTILINE)),
            'has_footnotes': bool(re.search(r'\[\d+\]', content)) or 'footnote' in content_lower,
            'has_citations': bool(re.search(r'\(\d{4}\)', content)) or 'et al' in content_lower,
            'has_structured_data': 'json' in content_lower or 'xml' in content_lower or 'yaml' in content_lower
        }
    
    def _convert_pdf_to_markdown(self, pdf_path: Path) -> str:
        """Convert PDF to markdown using PyMuPDF (real conversion)"""
        if not fitz:
            return f"# {pdf_path.name}\n\nPyMuPDF not available - mock content"
        
        try:
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            
            # Skip files that are too large
            if page_count > 100:
                doc.close()
                return f"# {pdf_path.name}\n\nSkipped: {page_count} pages (>100 limit)"
            
            # Extract text from all pages
            markdown_content = [f"# {pdf_path.stem}\n"]
            
            for page_num in range(page_count):
                page = doc[page_num]
                
                # Use blocks method for fastest extraction
                blocks = page.get_text("blocks")
                if blocks:
                    markdown_content.append(f"\n## Page {page_num + 1}\n")
                    for block in blocks:
                        if block[4]:  # Check if block contains text
                            text = block[4].strip()
                            if text:
                                markdown_content.append(text + "\n")
            
            doc.close()
            return '\n'.join(markdown_content)
            
        except Exception as e:
            return f"# {pdf_path.name}\n\nPDF conversion error: {str(e)}"
    
    def _io_worker_ingestion(self, file_paths: List[Path]) -> None:
        """
        I/O Worker: Handle all I/O-bound operations.
        
        Responsibilities:
        - File reading and validation
        - PDF to markdown conversion  
        - URL downloading
        - Feed work items to CPU queue
        """
        # Set thread name for worker tagging
        threading.current_thread().name = "IOWorker-1"
        
        self.queue_manager.staging(f"I/O worker starting ingestion of {len(file_paths)} files")
        
        for i, file_path in enumerate(file_paths):
            if not self.active:
                break
            
            ingestion_start = time.perf_counter()
            
            try:
                self.logger.conversion(f"Reading file: {file_path.name}")
                
                # Real file processing (I/O bound)
                if file_path.suffix.lower() == '.pdf':
                    self.pdf_converter.conversion(f"Converting PDF to markdown: {file_path.name}")
                    markdown_content = self._convert_pdf_to_markdown(file_path)
                else:
                    # Read text files directly
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        markdown_content = f.read()
                
                # Create InMemoryDocument with basic YAML metadata (I/O worker responsibility)
                doc = InMemoryDocument(
                    source_file_path=str(file_path),
                    memory_limit_mb=self.memory_limit_mb
                )
                doc.markdown_content = markdown_content
                
                # Quick content pre-screening (fast yes/no flags)
                content_flags = self._quick_content_scan(markdown_content)
                
                # Calculate page count for PDFs
                page_count = 0
                if file_path.suffix.lower() == '.pdf' and fitz:
                    try:
                        pdf_doc = fitz.open(str(file_path))
                        page_count = len(pdf_doc)
                        pdf_doc.close()
                    except:
                        page_count = 0
                
                # Use YAMLMetadataEngine to generate comprehensive metadata
                conversion_time = time.perf_counter() - ingestion_start
                yaml_content = self.yaml_engine.generate_conversion_metadata(
                    file_path=file_path,
                    page_count=page_count,
                    extra_metadata={
                        'content_detection': content_flags,  # Add pre-screening flags
                        'processing_info': {
                            'conversion_time_ms': conversion_time * 1000,
                            'content_length': len(markdown_content),
                            'stage': 'converted'
                        }
                    }
                )
                
                # Parse YAML string back to dict for frontmatter
                import yaml
                doc.yaml_frontmatter = yaml.safe_load(yaml_content.replace('---\n', '').replace('\n---', ''))
                
                set_current_phase('document_processing')
                add_files_processed(1)
                add_pages_processed(page_count)
                self.phase_manager.log('document_processor', f"📄 Created InMemoryDocument with basic YAML: {file_path.name}")
                
                # Create work item for CPU workers (now passes the document)
                work_item = WorkItem(
                    document=doc,
                    metadata={'conversion_time': conversion_time},
                    ingestion_time=time.perf_counter()
                )
                
                # Add to queue with backpressure handling
                try:
                    self.work_queue.put(work_item, timeout=5.0)
                    queue_size = self.work_queue.qsize()
                    self.logger.queue(f"Queued InMemoryDocument: {file_path.name}", 
                                    queue_size=queue_size, queue_max=self.queue_size)
                except Full:
                    self.logger.logger.warning(f"⚠️  Queue full, dropping: {file_path.name}")
                    
            except Exception as e:
                self.logger.logger.error(f"❌ I/O error processing {file_path.name}: {e}")
        
        # Signal completion to CPU workers
        for _ in range(self.cpu_workers):
            self.work_queue.put(None)  # Sentinel value
        
        self.queue_manager.staging(f"I/O worker completed ingestion of {len(file_paths)} files")
    
    def _cpu_worker_processing(self, worker_id: int) -> List[InMemoryDocument]:
        """
        CPU Worker: Handle all CPU-bound operations.
        
        Responsibilities:
        - Entity extraction
        - Document classification
        - Semantic analysis
        - JSON generation
        """
        # Set thread name for worker tagging
        threading.current_thread().name = f"CPUWorker-{worker_id}"
        
        results = []
        set_current_phase('service_coordination')
        self.phase_manager.log('service_coordinator', f"🧠 CPU worker {worker_id} started")
        
        while self.active:
            try:
                # Get work from I/O queue
                work_item = self.work_queue.get(timeout=1.0)
                
                # Check for completion signal
                if work_item is None:
                    break
                
                # Process work item (CPU bound)
                processing_start = time.perf_counter()
                
                # Get the InMemoryDocument from I/O worker (shared memory handoff)
                doc = work_item.document
                
                self.entity_extraction.semantics(f"Processing entities: {doc.source_filename}")
                set_current_phase('document_processing')
                self.phase_manager.log('document_processor', f"📄 Received InMemoryDocument with YAML: {doc.source_filename}")
                
                # Real entity extraction and classification (enrich existing document)
                try:
                    if self.aho_corasick_engine and self.semantic_extractor:
                        # Real classification with Aho-Corasick
                        self.document_classifier.classification(f"Classifying document: {doc.source_filename}")
                        
                        # Get domain and document type classifications
                        domain_results = self.aho_corasick_engine.classify_domains(doc.markdown_content)
                        doctype_results = self.aho_corasick_engine.classify_document_types(doc.markdown_content)
                        
                        # Determine primary domain and confidence
                        primary_domain = max(domain_results.keys(), key=lambda k: domain_results[k]) if domain_results else 'general'
                        primary_domain_confidence = domain_results.get(primary_domain, 0)
                        
                        # Determine primary document type and confidence
                        primary_document_type = max(doctype_results.keys(), key=lambda k: doctype_results[k]) if doctype_results else 'document'
                        primary_doctype_confidence = doctype_results.get(primary_document_type, 0)
                        
                        # Domain-based routing decisions
                        routing_decisions = {
                            'skip_entity_extraction': primary_domain_confidence < 5.0,
                            'enable_deep_domain_extraction': primary_domain_confidence >= 60.0,
                            'domain_specialization_route': primary_domain if primary_domain_confidence >= 40.0 else 'general'
                        }
                        
                        # Combine results with primary fields
                        classification_result = {
                            'domains': domain_results,
                            'document_types': doctype_results,
                            'primary_domain': primary_domain,
                            'primary_domain_confidence': primary_domain_confidence,
                            'primary_document_type': primary_document_type,
                            'primary_doctype_confidence': primary_doctype_confidence,
                            'domain_routing': routing_decisions
                        }
                        
                        if classification_result:
                            # Enrich existing YAML frontmatter
                            doc.yaml_frontmatter['classification'] = classification_result
                            # Safely update processing stage
                            if 'processing' not in doc.yaml_frontmatter:
                                doc.yaml_frontmatter['processing'] = {}
                            doc.yaml_frontmatter['processing']['stage'] = 'classified'
                            
                            set_current_phase('classification')
                            # Get page count from document metadata
                            doc_page_count = doc.yaml_frontmatter.get('page_count', 0)
                            add_pages_processed(doc_page_count)
                            self.phase_manager.log('document_classifier', f"📋 Added classification to YAML: {doc.source_filename}")
                            
                            # Extract Core 8 Universal Entities
                            self.core8_extractor.enrichment(f"Extracting entities: {doc.source_filename}")
                            entities = self._extract_universal_entities(doc.markdown_content)
                            
                            # Normalize entities for structured data enhancement
                            if self.entity_normalizer:
                                normalized_entities = {}
                                normalization_count = 0
                                
                                for entity_type, entity_list in entities.items():
                                    normalized_list = []
                                    for entity in entity_list:
                                        # Normalize entity while preserving original structure
                                        normalized_entity = self.entity_normalizer.normalize_entity(entity)
                                        normalized_list.append(normalized_entity)
                                        
                                        # Count successful normalizations
                                        if 'normalized' in normalized_entity and 'error' not in normalized_entity['normalized']:
                                            normalization_count += 1
                                    
                                    normalized_entities[entity_type] = normalized_list
                                
                                # Use normalized entities
                                entities = normalized_entities
                                
                                # Log normalization success
                                if normalization_count > 0:
                                    self.core8_extractor.enrichment(f"🔧 Normalized {normalization_count} entities with structured data")
                            
                            # Add entity extraction to YAML
                            doc.yaml_frontmatter['entities'] = entities
                            doc.yaml_frontmatter['entity_insights'] = {
                                'has_financial_data': len(entities.get('money', [])) > 0,
                                'has_contact_info': len(entities.get('phone', [])) > 0 or len(entities.get('email', [])) > 0,
                                'has_temporal_data': len(entities.get('date', [])) > 0,
                                'has_external_references': len(entities.get('url', [])) > 0,
                                'total_entities_found': sum(len(v) for v in entities.values())
                            }
                            
                            # Log Core 8 entities using Rule #11 structured format
                            core8_counts = []
                            for entity_type in ['person', 'org', 'location', 'gpe', 'date', 'time', 'money', 'percent']:
                                count = len(entities.get(entity_type, []))
                                if count > 0:
                                    core8_counts.append(f"{entity_type}:{count}")
                            
                            if core8_counts:
                                self.core8_extractor.semantics(f"📊 Global entities: {', '.join(core8_counts)}")
                            
                            set_current_phase('entity_extraction')
                            # Get page count from document metadata
                            doc_page_count = doc.yaml_frontmatter.get('page_count', 0)
                            add_pages_processed(doc_page_count)
                            self.phase_manager.log('entity_extraction', f"🔍 Extracted {doc.yaml_frontmatter['entity_insights']['total_entities_found']} total entities")
                            
                            # Real semantic extraction
                            self.semantic_analyzer.semantics(f"Extracting semantic facts: {doc.source_filename}")
                            semantic_facts = self.semantic_extractor.extract_semantic_facts_from_classification(
                                classification_result, 
                                doc.markdown_content
                            )
                            
                            if semantic_facts:
                                # Store semantic data in document
                                doc.semantic_json = semantic_facts
                                # Safely update processing stage
                                if 'processing' not in doc.yaml_frontmatter:
                                    doc.yaml_frontmatter['processing'] = {}
                                doc.yaml_frontmatter['processing']['stage'] = 'extracted'
                                
                                set_current_phase('semantic_analysis')
                                # Get page count from document metadata
                                doc_page_count = doc.yaml_frontmatter.get('page_count', 0)
                                add_pages_processed(doc_page_count)
                                self.phase_manager.log('semantic_analyzer', f"🔍 Added semantic JSON to document: {doc.source_filename}")
                                
                                # Log entity counts (following Rule #11 format)
                                global_facts = semantic_facts.get('global_entities', {})
                                domain_facts = semantic_facts.get('domain_entities', {})
                                
                                if global_facts:
                                    global_counts = [f"{k}:{len(v)}" for k, v in global_facts.items() if v]
                                    if global_counts:
                                        self.semantic_analyzer.semantics(f"Global entities: {', '.join(global_counts)}")
                                
                                if domain_facts:
                                    domain_counts = [f"{k}:{len(v)}" for k, v in domain_facts.items() if v]
                                    if domain_counts:
                                        self.semantic_analyzer.semantics(f"Domain entities: {', '.join(domain_counts)}")
                        
                        doc.success = True
                    else:
                        # Fallback to mock processing
                        doc.success = True
                        doc.yaml_frontmatter['processing']['stage'] = 'mock_processed'
                        set_current_phase('document_processing')
                        self.phase_manager.log('document_processor', f"⚠️  Using mock processing for {doc.source_filename}")
                        
                except Exception as e:
                    self.logger.logger.error(f"❌ Entity extraction failed for {doc.source_filename}: {e}")
                    doc.success = False
                    doc.mark_failed(f"Entity extraction error: {e}")
                
                processing_time = time.perf_counter() - processing_start
                
                # Return the enriched document
                results.append(doc)
                set_current_phase('document_processing')
                self.phase_manager.log('document_processor', f"✅ Completed processing: {doc.source_filename}")
                
            except Empty:
                # Normal timeout, continue checking
                continue
            except Exception as e:
                self.logger.logger.error(f"❌ CPU worker {worker_id} error: {e}")
        
        self.document_processor.logger.debug(f"🏁 CPU worker {worker_id} finished: {len(results)} items processed")
        return results
    
    def process_files_service(self, file_paths: List[Path], output_dir: Path = None) -> tuple[List[InMemoryDocument], float]:
        """
        Process files using clean I/O + CPU service architecture.
        
        Returns:
            Tuple of (in_memory_documents_list, total_processing_time)
        """
        if not self.active:
            self.start_service()
        
        total_start = time.perf_counter()
        
        self.service_coordinator.staging(f"Processing {len(file_paths)} files with I/O + CPU service")
        
        # Start I/O worker thread
        io_thread = threading.Thread(
            target=self._io_worker_ingestion,
            args=(file_paths,),
            name="IOWorker-1"
        )
        io_thread.start()
        
        # Start CPU worker futures
        cpu_futures = []
        for worker_id in range(1, self.cpu_workers + 1):
            future = self.cpu_executor.submit(self._cpu_worker_processing, worker_id)
            cpu_futures.append(future)
        
        # Wait for I/O completion
        io_thread.join()
        self.queue_manager.staging("I/O ingestion completed")
        
        # Collect CPU results
        all_results = []
        for i, future in enumerate(cpu_futures):
            worker_results = future.result()
            all_results.extend(worker_results)
            self.document_processor.logger.debug(f"📊 CPU worker {i+1} returned {len(worker_results)} results")
        
        total_time = time.perf_counter() - total_start
        
        self.service_coordinator.staging(f"Service processing complete: {len(all_results)} results in {total_time:.2f}s")
        
        # Write files to disk (WRITER-IO phase)
        if all_results:
            self._write_results_to_disk(all_results, output_dir or Path.cwd())
        
        return all_results, total_time
    
    def _write_results_to_disk(self, results: List[InMemoryDocument], output_dir: Path):
        """WRITER-IO phase: Write processed documents to disk"""
        # Set thread name for I/O worker attribution 
        original_name = threading.current_thread().name
        threading.current_thread().name = "IOWorker-1"
        
        try:
            successful_writes = 0
            
            for doc in results:
                if doc.success and doc.markdown_content:
                    try:
                        # Debug what we have in the document
                        yaml_size = len(str(doc.yaml_frontmatter)) if doc.yaml_frontmatter else 0
                        json_size = len(str(doc.semantic_json)) if doc.semantic_json else 0
                        
                        self.memory_manager.logger.debug(f"📄 Document state: {doc.source_filename} - YAML: {yaml_size}B, JSON: {json_size}B")
                        
                        # Write markdown file (with YAML frontmatter)
                        md_filename = f"{doc.source_stem}.md"
                        md_path = output_dir / md_filename
                        
                        # Construct full markdown with YAML frontmatter (in correct order)
                        full_content = doc.markdown_content
                        if doc.yaml_frontmatter:
                            import yaml
                            from collections import OrderedDict
                            
                            # Create ordered YAML with proper section ordering
                            ordered_yaml = OrderedDict()
                            
                            # 1. Conversion info FIRST
                            if 'conversion' in doc.yaml_frontmatter:
                                ordered_yaml['conversion'] = doc.yaml_frontmatter['conversion']
                            
                            # 2. Content analysis (pre-screening flags)
                            if 'content_detection' in doc.yaml_frontmatter:
                                import copy
                                ordered_yaml['content_analysis'] = copy.deepcopy(doc.yaml_frontmatter['content_detection'])
                            
                            # 3. Processing info (merge processing and processing_info)
                            processing = {}
                            if 'processing' in doc.yaml_frontmatter:
                                processing.update(doc.yaml_frontmatter['processing'])
                            if 'processing_info' in doc.yaml_frontmatter:
                                processing.update(doc.yaml_frontmatter['processing_info'])
                            if processing:
                                ordered_yaml['processing'] = processing
                            
                            # 4. Domain Classification (enhanced structure)
                            if 'classification' in doc.yaml_frontmatter:
                                import copy
                                classification_data = copy.deepcopy(doc.yaml_frontmatter['classification'])
                                if 'source_file' in classification_data:
                                    del classification_data['source_file']
                                
                                # Build enhanced domain_classification structure
                                domain_classification = {}
                                
                                # Routing decisions FIRST (drives classification)
                                if 'domain_routing' in classification_data:
                                    domain_classification['routing'] = copy.deepcopy(classification_data['domain_routing'])
                                
                                # Top domains and document types (configurable top 5)
                                domains = classification_data.get('domains', {})
                                document_types = classification_data.get('document_types', {})
                                
                                # Get top 5 domains with scores > 0.5
                                top_domains = [(k, v) for k, v in sorted(domains.items(), key=lambda x: x[1], reverse=True) 
                                             if v > 0.5][:5]
                                top_doc_types = [(k, v) for k, v in sorted(document_types.items(), key=lambda x: x[1], reverse=True) 
                                               if v > 0.5][:5]
                                
                                if top_domains:
                                    domain_classification['top_domains'] = [k for k, v in top_domains]
                                if top_doc_types:
                                    domain_classification['top_document_types'] = [k for k, v in top_doc_types]
                                
                                # Full detailed breakdowns (only scores > 0.5)
                                filtered_domains = {k: v for k, v in domains.items() if v > 0.5}
                                filtered_doc_types = {k: v for k, v in document_types.items() if v > 0.5}
                                
                                if filtered_domains:
                                    domain_classification['domains'] = filtered_domains
                                if filtered_doc_types:
                                    domain_classification['document_types'] = filtered_doc_types
                                
                                ordered_yaml['domain_classification'] = domain_classification
                            
                            # 5. Source info
                            if 'source' in doc.yaml_frontmatter:
                                ordered_yaml['source'] = doc.yaml_frontmatter['source']
                            
                            # Add any other sections not explicitly ordered
                            for key, value in doc.yaml_frontmatter.items():
                                if key not in ordered_yaml and key not in ['processing_info', 'classification', 'content_detection']:
                                    ordered_yaml[key] = value
                            
                            yaml_header = yaml.dump(dict(ordered_yaml), default_flow_style=False, sort_keys=False)
                            full_content = f"---\n{yaml_header}---\n\n{doc.markdown_content}"
                            
                        set_current_phase('file_writing')
                        # Get page count from document metadata
                        doc_page_count = doc.yaml_frontmatter.get('page_count', 0)
                        add_pages_processed(doc_page_count)
                        self.phase_manager.log('file_writer', f"Writing markdown with YAML: {md_filename}")
                        with open(md_path, 'w', encoding='utf-8') as f:
                            f.write(full_content)
                        
                        # Write JSON knowledge file if we have semantic data
                        if doc.semantic_json:
                            json_filename = f"{doc.source_stem}.json"
                            json_path = output_dir / json_filename
                            
                            set_current_phase('file_writing')
                            self.phase_manager.log('file_writer', f"Writing JSON knowledge: {json_filename}")
                            import json
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(doc.semantic_json, f, indent=2)
                        else:
                            set_current_phase('file_writing')
                            self.phase_manager.log('file_writer', f"⚠️  No semantic JSON to write for {doc.source_filename}")
                        
                        successful_writes += 1
                        
                    except Exception as e:
                        self.logger.logger.error(f"❌ Failed to write {doc.source_filename}: {e}")
            
            set_current_phase('file_writing')
            self.phase_manager.log('file_writer', f"Saved {successful_writes} files to {output_dir}")
            
        finally:
            # Restore original thread name
            threading.current_thread().name = original_name


if __name__ == "__main__":
    # Test the service processor
    from utils.logging_config import setup_logging
    
    setup_logging(verbosity=3, log_file=None, use_colors=False)
    
    config = {'pipeline': {'queue_size': 10, 'memory_limit_mb': 100}}
    processor = ServiceProcessor(config)
    
    # Test with sample files
    test_files = [
        Path('/tmp/test1.txt'),
        Path('/tmp/test2.txt')
    ]
    
    # Create test files
    for f in test_files:
        f.write_text(f"Sample content for {f.name}")
    
    try:
        results, timing = processor.process_files_service(test_files)
        print(f"\n✅ Test completed: {len(results)} results in {timing:.2f}s")
        
        for result in results:
            print(f"  - {result['source_filename']}: worker {result['worker_id']}, "
                  f"processing {result['processing_time']:.3f}s")
    finally:
        processor.stop_service()
        # Clean up test files
        for f in test_files:
            f.unlink(missing_ok=True)