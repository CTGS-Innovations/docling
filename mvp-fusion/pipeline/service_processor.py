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
import yaml
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
from pipeline.in_memory_document import InMemoryDocument, NoAliasDumper, force_flow_style_spans
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
        
        # PERFORMANCE FIX: Initialize Aho-Corasick systems ONCE, not per document
        self._hybrid_system = None
        
        # Phase-specific loggers for clearer identification
        self.pdf_converter = get_fusion_logger("pdf_converter")
        self.document_classifier = get_fusion_logger("document_classifier") 
        self.core8_extractor = get_fusion_logger("core8_extractor")
        self.entity_extraction = get_fusion_logger("entity_extraction")
        self.entity_normalizer_logger = get_fusion_logger("entity_normalizer")
        self.semantic_analyzer = get_fusion_logger("semantic_analyzer")
        
        # Service coordination loggers
        self.service_coordinator = get_fusion_logger("service_coordinator")
        self.document_processor = get_fusion_logger("document_processor")
        self.file_writer = get_fusion_logger("file_writer")
        self.memory_manager = get_fusion_logger("memory_manager")
        self.queue_manager = get_fusion_logger("queue_manager")
        
        # Initialize phase manager
        self.phase_manager = get_phase_manager()
        
        # PERFORMANCE FIX: Initialize FLPC engine ONCE for high-speed pattern matching
        self.flpc_engine = None
        
        # PERFORMANCE OPTIMIZATION: Pre-build YAML template structure (avoid per-document overhead)
        self.yaml_template = {
            'conversion': {
                'engine': 'mvp-fusion-highspeed',
                'page_count': 0,  # Will be updated per document
                'conversion_time_ms': 0,  # Will be updated per document
                'source_file': '',  # Will be updated per document
                'format': ''  # Will be updated per document
            },
            'content_detection': {},  # Will be updated per document
            'processing': {
                'stage': 'converted',
                'content_length': 0  # Will be updated per document
            }
        }
        
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
        self.pos_gap_discovery = None
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
                
                # PERFORMANCE FIX: Initialize optimized system ONCE, not per document
                try:
                    from high_performance_entity_metadata import HighPerformanceEntityMetadata
                    self._hybrid_system = HighPerformanceEntityMetadata()
                    self.logger.logger.info("🟢 High-performance Aho-Corasick entity system initialized")
                except Exception as e:
                    self.logger.logger.warning(f"⚠️ High-performance extraction system failed: {e}")
                    self._hybrid_system = None
                
                # CORE-8 ENTITY CORPUS INITIALIZATION
                try:
                    from utils.core8_corpus_loader import Core8CorpusLoader
                    # Initialize in non-verbose mode (only shows summary)
                    corpus_loader = Core8CorpusLoader(verbose=False)
                    # Store the automatons for use in entity extraction
                    self.core8_automatons = corpus_loader.automatons
                    self.core8_corpus_data = corpus_loader.corpus_data
                    self.core8_corpus_loader = corpus_loader  # Store for subcategory lookup
                except Exception as e:
                    self.logger.logger.warning(f"⚠️ Core-8 corpus loader failed: {e}")
                    self.core8_automatons = {}
                    self.core8_corpus_data = {}
                
                # WORLD-SCALE PERSON EXTRACTOR: Initialize with comprehensive corpus
                try:
                    from utils.world_scale_person_extractor import WorldScalePersonExtractor
                    # Use actual corpus paths
                    corpus_dir = Path("knowledge/corpus/foundation_data")
                    first_names_path = corpus_dir / "first_names_2025_09_18.txt"
                    last_names_path = corpus_dir / "last_names_2025_09_18.txt"
                    organizations_path = corpus_dir / "organizations_2025_09_18.txt"  # Fixed: use correct filename
                    
                    self.world_scale_person_extractor = WorldScalePersonExtractor(
                        first_names_path=first_names_path,
                        last_names_path=last_names_path, 
                        organizations_path=organizations_path if organizations_path.exists() else None,
                        min_confidence=0.7
                    )
                    self.logger.logger.info("🟢 World-scale person extractor initialized (AC + FLPC strategy)")
                except Exception as e:
                    self.logger.logger.warning(f"⚠️ World-scale person extractor failed: {e}")
                    self.world_scale_person_extractor = None
                
                # PERFORMANCE FIX: Initialize FLPC engine ONCE (14.9x faster than Python regex)
                try:
                    from fusion.flpc_engine import FLPCEngine
                    self.flpc_engine = FLPCEngine(self.config)
                    self.logger.logger.info("🟢 FLPC Rust engine initialized (69M+ chars/sec)")
                except Exception as e:
                    self.logger.logger.warning(f"⚠️ FLPC engine failed to initialize: {e}")
                    self.flpc_engine = None
                
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
                    self.entity_normalizer = EntityNormalizer(self.config)
                    set_current_phase('initialization')
                    self.phase_manager.log('core8_extractor', "✅ Entity normalizer initialized for structured data enhancement and normalization phase")
                else:
                    self.entity_normalizer = None
                
                # Initialize POS gap discovery (optional feature)
                try:
                    from knowledge.extractors.pos_gap_discovery import POSGapDiscovery
                    self.pos_gap_discovery = POSGapDiscovery(self.config)
                    if self.pos_gap_discovery.is_enabled():
                        self.phase_manager.log('core8_extractor', "✅ POS Gap Discovery initialized and enabled")
                    else:
                        self.phase_manager.log('core8_extractor', "ℹ️  POS Gap Discovery disabled in configuration")
                except Exception as e:
                    self.logger.logger.warning(f"⚠️ POS Gap Discovery initialization failed: {e}")
                    self.pos_gap_discovery = None
                
                # Initialize tentative corpus manager for auto-learning
                try:
                    from knowledge.corpus.tentative_corpus_manager import TentativeCorpusManager
                    self.tentative_corpus_manager = TentativeCorpusManager(
                        corpus_dir=Path("knowledge/corpus/foundation_data"),
                        config=self.config
                    )
                    if self.tentative_corpus_manager.is_enabled():
                        self.phase_manager.log('core8_extractor', "✅ Tentative corpus auto-learning initialized")
                    else:
                        self.phase_manager.log('core8_extractor', "ℹ️  Tentative corpus auto-learning disabled")
                except Exception as e:
                    self.logger.logger.warning(f"⚠️ Tentative corpus manager initialization failed: {e}")
                    self.tentative_corpus_manager = None
                
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
    
    def _extract_enhanced_gpe_loc(self, content: str) -> Dict[str, List]:
        """High-performance GPE/LOC extraction using single-pass Aho-Corasick - USES PRE-INITIALIZED SYSTEM"""
        try:
            # PERFORMANCE FIX: Use pre-initialized optimized system
            if not self._hybrid_system:
                self.logger.logger.warning("⚠️ High-performance system not initialized, falling back to basic extraction")
                return {'gpe': [], 'location': []}
            
            # Single-pass Aho-Corasick extraction (1,656x faster than O(n²) loops)
            result = self._hybrid_system.extract_entities_fast(content)
            
            # Results are already in the correct format
            return {
                'gpe': result.get('gpe', []),
                'location': result.get('location', [])
            }
            
        except Exception as e:
            self.logger.logger.warning(f"High-performance GPE/LOC extraction failed: {e}")
            return {'gpe': [], 'location': []}
    
    def _convert_flpc_entities(self, flpc_matches: list, entity_type: str) -> list:
        """Convert FLPC match results to service processor entity format"""
        entities = []
        for match in flpc_matches:
            if isinstance(match, dict):
                # FLPC returns structured match data
                entity = {
                    'value': match.get('text', ''),
                    'text': match.get('text', ''),
                    'type': entity_type,
                    'span': {
                        'start': match.get('start', 0),
                        'end': match.get('end', 0)
                    }
                }
                entities.append(entity)
            elif isinstance(match, str):
                # Simple string match
                entity = {
                    'value': match,
                    'text': match,
                    'type': entity_type,
                    'span': {'start': 0, 'end': len(match)}
                }
                entities.append(entity)
        return entities
    
    def _extract_universal_entities(self, content: str) -> Dict[str, List]:
        """
        Extract Core 8 Universal Entities with span information and clean text.
        Core 8: PERSON, ORG, LOC, GPE, DATE, TIME, MONEY, PERCENT
        Additional: phone, email, url, regulations, measurements
        """
        import time
        entities = {}
        timing_breakdown = {}
        
        # PERSON - World-scale AC + FLPC strategy (NO Python regex)
        person_start = time.perf_counter()
        if self.world_scale_person_extractor:
            try:
                world_scale_persons = self.world_scale_person_extractor.extract_persons(content)
                set_current_phase('entity_extraction')
                self.phase_manager.log('core8_extractor', f"🎯 World-scale person extractor found {len(world_scale_persons)} validated persons")
                
                entities['person'] = []
                for person in world_scale_persons:
                    # Standard NER format with clean, consistent structure
                    entity = {
                        'value': person.get('text', person.get('name', '')),
                        'text': person.get('text', person.get('name', '')),
                        'type': 'PERSON',
                        'span': {
                            'start': person.get('position', 0),
                            'end': person.get('position', 0) + len(person.get('text', person.get('name', '')))
                        }
                    }
                    entities['person'].append(entity)
                
                # Limit to 30 persons (increased to capture key people)
                entities['person'] = entities['person'][:30]
                
            except Exception as e:
                self.logger.logger.warning(f"World-scale person extraction failed: {e}")
                # Fallback to old conservative extractor if available
                if self.person_extractor:
                    try:
                        conservative_persons = self.person_extractor.extract_persons(content)
                        entities['person'] = []
                        for person in conservative_persons:
                            entity = {
                                'value': person.get('text', person.get('name', '')),
                                'text': person.get('text', person.get('name', '')),
                                'type': 'PERSON',
                                'span': {
                                    'start': person.get('position', 0),
                                    'end': person.get('position', 0) + len(person.get('text', person.get('name', '')))
                                }
                            }
                            entities['person'].append(entity)
                        entities['person'] = entities['person'][:30]
                        self.logger.logger.info(f"🟡 Using fallback conservative extractor: {len(entities['person'])} persons")
                    except Exception as e2:
                        self.logger.logger.warning(f"Conservative fallback also failed: {e2}")
                        entities['person'] = []
                else:
                    entities['person'] = []
        else:
            self.logger.logger.warning("World-scale PersonEntityExtractor not available")
            entities['person'] = []
        
        timing_breakdown['person'] = (time.perf_counter() - person_start) * 1000
        
        # ORGANIZATION - Using sentence-based processing with Core-8 Aho-Corasick automaton
        org_start = time.perf_counter()
        entities['org'] = []
        if hasattr(self, 'core8_automatons') and 'ORG' in self.core8_automatons:
            try:
                entities['org'] = self._extract_entities_sentence_based(content, 'ORG')
                self.logger.logger.info(f"🏢 ORG extraction (sentence-based): {len(entities['org'])} entities found")
            except Exception as e:
                self.logger.logger.warning(f"ORG extraction error: {e}")
                entities['org'] = []
        else:
            # Fallback to pattern-based extraction if automaton not available
            org_patterns = [
                r'\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:Inc|Corp|LLC|Ltd|Company|Organization|Institute|University|College|Department|Agency|Administration|Commission|Bureau|Office)\b',
                r'\b(?:OSHA|FDA|EPA|NASA|FBI|CIA|DOD|DOJ|USDA|CDC|NIH|NSF|NIST|NOAA|FAA|FCC|SEC|IRS|ATF|DEA|DHS|TSA|FEMA)\b'
            ]
            org_entities = []
            for pattern in org_patterns:
                org_entities.extend(self._extract_entities_with_spans(content, pattern, 'ORG'))
            entities['org'] = self._deduplicate_entities(org_entities)[:50]
        timing_breakdown['org'] = (time.perf_counter() - org_start) * 1000
        
        # ENHANCED LOCATION & GPE EXTRACTION with subcategory metadata - TEMPORARILY DISABLED FOR PERFORMANCE TESTING
        # try:
        #     if self._hybrid_system:
        #         self.logger.logger.info("🔧 Using enhanced GPE/LOC extraction...")
        #         enhanced_entities = self._extract_enhanced_gpe_loc(content)
        #         entities['location'] = enhanced_entities.get('location', [])
        #         entities['gpe'] = enhanced_entities.get('gpe', [])
        #         
        #         # Log enhancement success
        #         loc_count = len(entities['location'])
        #         gpe_count = len(entities['gpe'])
        #         self.logger.logger.info(f"🟢 Enhanced extraction SUCCESS: GPE={gpe_count}, LOC={loc_count}")
        #         
        #         # Debug: Show first few entities with subcategories
        #         if entities['gpe']:
        #             sample_gpe = entities['gpe'][0]
        #             subcategory = sample_gpe.get('subcategory', 'NO_SUBCATEGORY')
        #             self.logger.logger.info(f"🔍 GPE sample: {sample_gpe['value']} [{subcategory}]")
        #     else:
        #         # No enhanced system - use empty entities
        #         entities['location'] = []
        #         entities['gpe'] = []
        # except Exception as e:
        #     self.logger.logger.warning(f"❌ Enhanced extraction failed, using fallback: {e}")
        #     import traceback
        #     self.logger.logger.warning(f"❌ Traceback: {traceback.format_exc()}")
        #     
        #     # FALLBACK: Use empty entities instead of slow regex
        #     entities['location'] = []
        #     entities['gpe'] = []
        
        # GPE & LOCATION - Using Core-8 Aho-Corasick automatons
        loc_gpe_start = time.perf_counter()
        
        # Extract GPE entities using Core-8 automaton
        entities['gpe'] = []
        if hasattr(self, 'core8_automatons') and 'GPE' in self.core8_automatons:
            try:
                gpe_automaton = self.core8_automatons['GPE']
                for end_pos, (entity_type, canonical) in gpe_automaton.iter(content.lower()):
                    start_pos = end_pos - len(canonical) + 1
                    # Get original text from content
                    original_text = content[start_pos:end_pos + 1]
                    
                    # Only add if it's a reasonable match (not single letters, etc.)
                    if len(original_text) > 2:
                        # Get subcategory metadata
                        subcategory = None
                        if hasattr(self, 'core8_corpus_loader'):
                            subcategory = self.core8_corpus_loader.get_subcategory('GPE', original_text)
                        
                        entity = {
                            'value': original_text,
                            'text': original_text,
                            'type': 'GPE',
                            'span': {
                                'start': start_pos,
                                'end': end_pos + 1
                            }
                        }
                        
                        # Add subcategory metadata if available
                        if subcategory:
                            entity['metadata'] = {'subcategory': subcategory}
                        
                        entities['gpe'].append(entity)
                
                # Deduplicate and limit (increased from 20 to 50 to capture basic geography)
                entities['gpe'] = self._deduplicate_entities(entities['gpe'])[:50]
                self.logger.logger.info(f"🌍 GPE extraction: {len(entities['gpe'])} entities found")
            except Exception as e:
                self.logger.logger.warning(f"GPE extraction error: {e}")
                entities['gpe'] = []
        else:
            entities['gpe'] = []
        
        # Extract LOC entities using Core-8 automaton
        entities['location'] = []
        if hasattr(self, 'core8_automatons') and 'LOC' in self.core8_automatons:
            try:
                loc_automaton = self.core8_automatons['LOC']
                for end_pos, (entity_type, canonical) in loc_automaton.iter(content.lower()):
                    start_pos = end_pos - len(canonical) + 1
                    # Get original text from content
                    original_text = content[start_pos:end_pos + 1]
                    
                    # Only add if it's a reasonable match (not single letters, etc.)
                    if len(original_text) > 2:
                        # Get subcategory metadata
                        subcategory = None
                        if hasattr(self, 'core8_corpus_loader'):
                            subcategory = self.core8_corpus_loader.get_subcategory('LOC', original_text)
                        
                        entity = {
                            'value': original_text,
                            'text': original_text,
                            'type': 'LOC',
                            'span': {
                                'start': start_pos,
                                'end': end_pos + 1
                            }
                        }
                        
                        # Add subcategory metadata if available
                        if subcategory:
                            entity['metadata'] = {'subcategory': subcategory}
                        
                        entities['location'].append(entity)
                
                # Deduplicate and limit (increased from 20 to 50 to capture basic geography)  
                entities['location'] = self._deduplicate_entities(entities['location'])[:50]
                self.logger.logger.info(f"📍 LOC extraction: {len(entities['location'])} entities found")
            except Exception as e:
                self.logger.logger.warning(f"LOC extraction error: {e}")
                entities['location'] = []
        else:
            entities['location'] = []
        
        timing_breakdown['loc_gpe'] = (time.perf_counter() - loc_gpe_start) * 1000
        
        # PERFORMANCE FIX: Replace Python regex violations with FLPC (14.9x faster)
        flpc_start = time.perf_counter()
        flpc_entities = {}
        if self.flpc_engine:
            try:
                # Single FLPC pass for all universal entities (dates, money, time, measurements)
                flpc_results = self.flpc_engine.extract_entities(content)
                flpc_entities = flpc_results.get('entities', {})
                
                # Convert FLPC results to service processor format (FLPC uses UPPERCASE keys)
                entities['date'] = self._convert_flpc_entities(flpc_entities.get('DATE', []), 'DATE')[:30]
                entities['time'] = self._convert_flpc_entities(flpc_entities.get('TIME', []), 'TIME')[:10]
                entities['money'] = self._convert_flpc_entities(flpc_entities.get('MONEY', []), 'MONEY')[:40]
                
                self.logger.logger.info(f"🟢 FLPC extraction: DATE={len(entities['date'])}, MONEY={len(entities['money'])}, TIME={len(entities['time'])}")
            except Exception as e:
                self.logger.logger.warning(f"❌ FLPC extraction failed: {e}")
                # Fallback to empty entities rather than slow Python regex
                entities['date'] = []
                entities['time'] = []
                entities['money'] = []
                flpc_entities = {}
        else:
            # No FLPC available - use empty entities (better than slow Python regex)
            entities['date'] = []
            entities['time'] = []
            entities['money'] = []
        
        # PERCENT - Use FLPC for percentages if available (FLPC uses UPPERCASE keys)
        if flpc_entities:
            percent_entities = self._convert_flpc_entities(flpc_entities.get('PERCENT', []), 'MEASUREMENT')[:30]
        else:
            percent_entities = []
        # Keep clean structure - no extra metadata fields
        
        # Additional FLPC entities (phone, email, url, measurements) - FLPC uses UPPERCASE keys
        if flpc_entities:
            entities['phone'] = self._convert_flpc_entities(flpc_entities.get('PHONE', []), 'PHONE')[:10]
            entities['email'] = self._convert_flpc_entities(flpc_entities.get('EMAIL', []), 'EMAIL')[:10]
            entities['url'] = self._convert_flpc_entities(flpc_entities.get('URL', []), 'URL')[:10]
            measurement_entities = self._convert_flpc_entities(flpc_entities.get('MEASUREMENT', []), 'MEASUREMENT')[:30]
        else:
            # No FLPC - use empty entities (eliminating slow Python regex)
            entities['phone'] = []
            entities['email'] = []
            entities['url'] = []
            measurement_entities = []
        
        # REGULATIONS - Keep minimal regex for specialized patterns not in FLPC
        # This is acceptable as it's domain-specific and infrequent
        if content and 'CFR' in content or 'USC' in content:
            reg_pattern = r'\b\d+\s+(?:CFR|USC|U\.S\.C\.|C\.F\.R\.)\s+§?\s*\d+(?:\.\d+)?(?:\([a-z]\))?|\b(?:Section|Sec\.)\s+\d+(?:\.\d+)?'
            entities['regulation'] = self._extract_entities_with_spans(content, reg_pattern, 'REGULATION', re.IGNORECASE)[:30]
        else:
            entities['regulation'] = []
        
        # Combine measurements and percent entities under single 'measurement' key
        entities['measurement'] = measurement_entities + percent_entities
        timing_breakdown['flpc'] = (time.perf_counter() - flpc_start) * 1000
        
        # POS GAP DISCOVERY: Smart discovery for sentences with no entity hits
        pos_start = time.perf_counter()
        pos_discoveries = 0
        pos_learning_candidates = 0
        
        if self.pos_gap_discovery and self.pos_gap_discovery.is_enabled():
            try:
                # Collect all existing entities for gap analysis
                all_existing_entities = []
                for entity_type, entity_list in entities.items():
                    all_existing_entities.extend(entity_list)
                
                # Discover entities in coverage gaps
                discoveries = self.pos_gap_discovery.discover_entities_in_gaps(content, all_existing_entities)
                pos_discoveries = len(discoveries)
                
                # Convert POS discoveries to standard entity format and add to results
                for discovery in discoveries:
                    entity = {
                        'value': discovery.text,
                        'text': discovery.text,
                        'type': discovery.entity_type,
                        'span': {
                            'start': discovery.start,
                            'end': discovery.end
                        },
                        'metadata': {
                            'source': 'pos_gap_discovery',
                            'confidence': discovery.confidence,
                            'pos_pattern': discovery.pos_pattern
                        }
                    }
                    
                    # Add to appropriate entity type list
                    entity_key = discovery.entity_type.lower()
                    if entity_key == 'org':
                        entity_key = 'org'
                    elif entity_key == 'person':
                        entity_key = 'person'
                    elif entity_key == 'location':
                        entity_key = 'location'
                    
                    if entity_key in entities:
                        entities[entity_key].append(entity)
                    else:
                        entities[entity_key] = [entity]
                
                # Get learning candidates for AC corpus enhancement
                learning_candidates = self.pos_gap_discovery.get_learning_candidates(discoveries)
                pos_learning_candidates = len(learning_candidates)
                
                # TENTATIVE CORPUS AUTO-LEARNING: Feed high-confidence discoveries to tentative corpus
                if self.tentative_corpus_manager and self.tentative_corpus_manager.is_enabled():
                    from knowledge.corpus.tentative_corpus_manager import create_learning_candidate_from_pos_discovery
                    
                    learned_count = 0
                    for pos_discovery in learning_candidates:
                        # Convert POS discovery to learning candidate
                        learning_candidate = create_learning_candidate_from_pos_discovery(
                            pos_discovery, 
                            context=f"Document processing - gap discovery"
                        )
                        
                        # Add to tentative corpus (live automaton updates disabled to prevent breaking AC)
                        success = self.tentative_corpus_manager.add_learning_candidate(
                            learning_candidate,
                            live_automatons=None  # Disabled: requires corpus reload for AC updates
                        )
                        
                        if success:
                            learned_count += 1
                    
                    if learned_count > 0:
                        self.logger.logger.info(f"🧠 Tentative Learning: Added {learned_count}/{pos_learning_candidates} discoveries to tentative corpus")
                
                if pos_discoveries > 0:
                    self.logger.logger.info(f"🔍 POS Gap Discovery: Found {pos_discoveries} new entities ({pos_learning_candidates} learning candidates)")
                
            except Exception as e:
                self.logger.logger.warning(f"⚠️ POS Gap Discovery failed: {e}")
        
        timing_breakdown['pos_gap_discovery'] = (time.perf_counter() - pos_start) * 1000
        
        # Log detailed timing breakdown
        total_timing = sum(timing_breakdown.values())
        self.logger.logger.info(f"🕐 Core 8 Entity Timing Breakdown ({total_timing:.1f}ms total):")
        for entity_type, timing_ms in timing_breakdown.items():
            percentage = (timing_ms / total_timing * 100) if total_timing > 0 else 0
            self.logger.logger.info(f"   {entity_type}: {timing_ms:.1f}ms ({percentage:.1f}%)")
        
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
        """Remove duplicate and overlapping entities, preferring longer matches."""
        if not entities:
            return []
        
        # Sort by length FIRST (longer first), then by position for ties
        sorted_entities = sorted(entities, key=lambda e: (
            -(e.get('span', {}).get('end', 0) - e.get('span', {}).get('start', 0)),  # Length FIRST (longer first)
            e.get('span', {}).get('start', 0)  # Position SECOND (earlier first for ties)
        ))
        
        deduplicated = []
        seen_values = set()
        accepted_spans = []  # Track all accepted spans for overlap checking
        
        for entity in sorted_entities:
            value = entity.get('value', '')
            span = entity.get('span', {})
            start = span.get('start', 0)
            end = span.get('end', 0)
            
            # Skip if we've seen this exact value
            if value in seen_values:
                continue
                
            # Check if this entity overlaps with ANY previously accepted entity
            overlaps = False
            for accepted_start, accepted_end in accepted_spans:
                # True overlap: ranges intersect
                if start < accepted_end and end > accepted_start:
                    overlaps = True
                    break
            
            if overlaps:
                continue
            
            seen_values.add(value)
            deduplicated.append(entity)
            accepted_spans.append((start, end))
        
        return deduplicated
    
    def _extract_entities_sentence_based(self, content: str, entity_type: str) -> List[Dict]:
        """
        Extract entities using sentence-based processing (fast sentence splitting).
        
        This follows the standard NLP approach:
        1. Detect sentence boundaries using simple patterns
        2. Process each sentence independently 
        3. Apply longest-match-first within each sentence
        4. No cross-sentence overlaps possible
        
        Args:
            content: Full document text
            entity_type: Type to extract ('ORG', 'GPE', 'LOC', etc.)
            
        Returns:
            List of entities with proper span information
        """
        all_entities = []
        
        # Step 1: Fast sentence detection using simple patterns (no spaCy needed)
        # Split on sentence boundaries: periods, exclamation marks, question marks
        # Keep track of character positions for span calculation
        sentences = self._fast_sentence_split(content)
        
        # Step 2: Process each sentence independently 
        automaton = self.core8_automatons[entity_type]
        
        for sentence_text, sentence_start in sentences:
            sentence_entities = []
            
            # Extract entities from this sentence
            for end_pos, (ent_type, canonical) in automaton.iter(sentence_text.lower()):
                start_pos = end_pos - len(canonical) + 1
                original_text = sentence_text[start_pos:end_pos + 1]
                
                # Only add reasonable matches
                if len(original_text) > 2:
                    entity = {
                        'value': original_text,
                        'text': original_text,
                        'type': entity_type,
                        'span': {
                            'start': sentence_start + start_pos,  # Adjust to document coordinates
                            'end': sentence_start + end_pos + 1
                        }
                    }
                    sentence_entities.append(entity)
            
            # Step 3: Apply longest-match-first deduplication within sentence
            # This works perfectly because no cross-sentence overlaps are possible
            sentence_entities = self._deduplicate_entities(sentence_entities)
            all_entities.extend(sentence_entities)
        
        return all_entities
    
    def _fast_sentence_split(self, content: str) -> List[tuple]:
        """
        Fast sentence splitting without spaCy dependency.
        
        Returns:
            List of (sentence_text, sentence_start_position) tuples
        """
        sentences = []
        current_start = 0
        
        # Simple sentence boundary patterns (much faster than spaCy)
        # Look for periods, exclamation marks, question marks followed by whitespace/newlines
        i = 0
        while i < len(content):
            char = content[i]
            
            # Check for sentence boundary markers
            if char in '.!?':
                # Look ahead to see if this is likely a sentence boundary
                next_pos = i + 1
                
                # Skip if at end of content
                if next_pos >= len(content):
                    # Add final sentence
                    sentence_text = content[current_start:].strip()
                    if sentence_text:
                        sentences.append((sentence_text, current_start))
                    break
                
                # Check if followed by whitespace (strong sentence boundary indicator)
                next_char = content[next_pos]
                if next_char.isspace():
                    # Extract sentence from current_start to i+1
                    sentence_text = content[current_start:i+1].strip()
                    if sentence_text and len(sentence_text) > 5:  # Skip very short "sentences"
                        sentences.append((sentence_text, current_start))
                    
                    # Move to start of next sentence (skip whitespace)
                    while next_pos < len(content) and content[next_pos].isspace():
                        next_pos += 1
                    current_start = next_pos
                    i = next_pos - 1  # Will be incremented by loop
            
            i += 1
        
        # Add any remaining content as final sentence
        if current_start < len(content):
            sentence_text = content[current_start:].strip()
            if sentence_text and len(sentence_text) > 5:
                sentences.append((sentence_text, current_start))
        
        # If no sentences found, treat entire content as one sentence
        if not sentences and content.strip():
            sentences.append((content.strip(), 0))
        
        return sentences
    
    def _extract_entities_document_level(self, content: str, entity_type: str) -> List[Dict]:
        """Fallback document-level extraction (legacy approach)."""
        entities = []
        automaton = self.core8_automatons[entity_type]
        
        for end_pos, (ent_type, canonical) in automaton.iter(content.lower()):
            start_pos = end_pos - len(canonical) + 1
            original_text = content[start_pos:end_pos + 1]
            
            if len(original_text) > 2:
                entity = {
                    'value': original_text,
                    'text': original_text,
                    'type': entity_type,
                    'span': {
                        'start': start_pos,
                        'end': end_pos + 1
                    }
                }
                entities.append(entity)
        
        return self._deduplicate_entities(entities)[:200]
    
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
        PERFORMANCE: Optimized for minimal string operations and single-pass scanning
        """
        content_lower = content.lower()
        
        # OPTIMIZED: Single split for line-based detection
        lines = None
        if '\n' in content:
            lines = content.split('\n')
        
        # Fast single-pass detection
        has_lists = False
        has_headers = False
        if lines:
            for line in lines:
                stripped = line.strip()
                if not has_lists and stripped and (stripped.startswith(('-', '*', '+', '•')) or 
                                                  (stripped[0].isdigit() and '.' in stripped[:10])):
                    has_lists = True
                if not has_headers and stripped.startswith('#'):
                    has_headers = True
                if has_lists and has_headers:
                    break
        
        return {
            'has_tables': '|' in content and content.count('|') >= 3,
            'has_images': '![' in content or 'image' in content_lower,
            'has_formulas': '$' in content or '`' in content,
            'has_code': '```' in content or 'import ' in content,
            'has_links': 'http' in content_lower,
            'has_lists': has_lists,
            'has_headers': has_headers,
            'has_footnotes': '[' in content and ']' in content,
            'has_citations': 'et al' in content_lower or '(202' in content,
            'has_structured_data': 'json' in content_lower or 'xml' in content_lower
        }
    
    def _convert_pdf_to_markdown(self, pdf_path: Path) -> tuple[str, int]:
        """Convert PDF to markdown using PyMuPDF (real conversion) - returns (content, page_count)"""
        if not fitz:
            return f"# {pdf_path.name}\n\nPyMuPDF not available - mock content", 0
        
        try:
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            
            # Skip files that are too large
            if page_count > 100:
                doc.close()
                return f"# {pdf_path.name}\n\nSkipped: {page_count} pages (>100 limit)", page_count
            
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
            return '\n'.join(markdown_content), page_count
            
        except Exception as e:
            return f"# {pdf_path.name}\n\nPDF conversion error: {str(e)}", 0
    
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
                # PERFORMANCE TEST: Disable hot path logging
                # self.logger.conversion(f"Reading file: {file_path.name}")
                
                # Real file processing (I/O bound) - FIXED: No double PDF opening
                page_count = 0
                if file_path.suffix.lower() == '.pdf':
                    # TIMING FIX: Measure only PDF conversion time
                    set_current_phase('pdf_conversion')
                    add_pages_processed(0)  # Will update after we know page count
                    pdf_start = time.perf_counter()
                    markdown_content, page_count = self._convert_pdf_to_markdown(file_path)
                    # Update page count after PDF processing
                    add_pages_processed(page_count)
                else:
                    # Read text files directly
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        markdown_content = f.read()
                    page_count = 0  # Non-PDF files don't have page count
                
                # TIMING FIX: Measure document object creation and metadata generation
                set_current_phase('document_processing') 
                add_files_processed(1)
                if page_count == 0:  # For non-PDF files, add them here
                    add_pages_processed(1)  # Treat text files as 1 page equivalent
                
                # Create InMemoryDocument with basic YAML metadata (I/O worker responsibility)
                doc = InMemoryDocument(
                    source_file_path=str(file_path),
                    memory_limit_mb=self.memory_limit_mb
                )
                doc.markdown_content = markdown_content
                
                # Quick content pre-screening (fast yes/no flags) - FIXED: No regex violations
                content_flags = self._quick_content_scan(markdown_content)
                
                # PERFORMANCE OPTIMIZED: Use pre-built template with minimal updates
                conversion_time = time.perf_counter() - ingestion_start
                
                # Copy template and update only necessary fields (faster than dict creation)
                doc.yaml_frontmatter = self.yaml_template.copy()
                doc.yaml_frontmatter['conversion'] = self.yaml_template['conversion'].copy()
                doc.yaml_frontmatter['processing'] = self.yaml_template['processing'].copy()
                
                # Update only the dynamic values
                doc.yaml_frontmatter['conversion']['page_count'] = page_count
                doc.yaml_frontmatter['conversion']['conversion_time_ms'] = conversion_time * 1000
                doc.yaml_frontmatter['conversion']['source_file'] = file_path.name
                doc.yaml_frontmatter['conversion']['format'] = file_path.suffix.upper().replace('.', '') if file_path.suffix else 'TXT'
                doc.yaml_frontmatter['content_detection'] = content_flags
                doc.yaml_frontmatter['processing']['content_length'] = len(markdown_content)
                # self.phase_manager.log('document_processor', f"📄 Created InMemoryDocument with basic YAML: {file_path.name}")
                
                # Create work item for CPU workers (now passes the document)
                work_item = WorkItem(
                    document=doc,
                    metadata={'conversion_time': conversion_time},
                    ingestion_time=time.perf_counter()
                )
                
                # Add to queue with backpressure handling
                try:
                    self.work_queue.put(work_item, timeout=5.0)
                    # queue_size = self.work_queue.qsize()
                    # self.logger.queue(f"Queued InMemoryDocument: {file_path.name}", 
                    #                 queue_size=queue_size, queue_max=self.queue_size)
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
                
                # Real entity extraction and classification (enrich existing document)
                try:
                    if self.aho_corasick_engine and self.semantic_extractor:
                        # TIMING FIX: Start classification phase  
                        set_current_phase('classification')
                        doc_page_count = doc.yaml_frontmatter.get('conversion', {}).get('page_count', 0)
                        add_pages_processed(doc_page_count)
                        
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
                            
                            # No page counting here - already done above
                            self.phase_manager.log('document_classifier', f"📋 Added classification to YAML: {doc.source_filename}")
                            
                            # TIMING FIX: Start entity extraction phase
                            set_current_phase('entity_extraction')
                            # Pages already counted in classification phase
                            
                            # Extract Core 8 Universal Entities
                            self.core8_extractor.enrichment(f"Extracting entities: {doc.source_filename}")
                            entities = self._extract_universal_entities(doc.markdown_content)
                            
                            # NOTE: Individual entity normalization removed - now handled by normalization phase below
                            
                            # Add entity extraction to YAML
                            doc.yaml_frontmatter['raw_entities'] = entities
                            doc.yaml_frontmatter['entity_insights'] = {
                                'has_financial_data': len(entities.get('money', [])) > 0,
                                'has_contact_info': len(entities.get('phone', [])) > 0 or len(entities.get('email', [])) > 0,
                                'has_temporal_data': len(entities.get('date', [])) > 0,
                                'has_external_references': len(entities.get('url', [])) > 0,
                                'total_entities_found': sum(len(v) for v in entities.values())
                            }
                            
                            # Log Core 8 entities using Rule #11 structured format
                            core8_counts = []
                            for entity_type in ['person', 'org', 'location', 'gpe', 'date', 'time', 'money', 'measurement']:
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
                            
                            # NEW: Entity Normalization Phase
                            if self.entity_normalizer:
                                normalization_start = time.perf_counter()
                                set_current_phase('normalization')
                                self.entity_normalizer_logger.normalization(f"🔄 Normalization Phase: Processing entities for canonicalization: {doc.source_filename}")
                                
                                # Perform entity canonicalization and global text replacement
                                normalization_result = self.entity_normalizer.normalize_entities_phase(
                                    entities, doc.markdown_content
                                )
                                
                                # Log normalized entity counts using structured format
                                normalized_counts = []
                                original_count = sum(len(entity_list) for entity_list in entities.values())
                                canonical_count = len(normalization_result.normalized_entities)
                                
                                for entity_type in ['person', 'org', 'location', 'gpe', 'date', 'time', 'money', 'measurement']:
                                    type_entities = [e for e in normalization_result.normalized_entities if e.type.lower() == entity_type.lower()]
                                    if type_entities:
                                        normalized_counts.append(f"{entity_type}:{len(type_entities)}")
                                
                                if normalized_counts:
                                    reduction_percent = ((original_count - canonical_count) / original_count * 100) if original_count > 0 else 0
                                    self.entity_normalizer_logger.normalization(f"📊 Normalized entities: {', '.join(normalized_counts)} ({original_count}→{canonical_count} entities, {reduction_percent:.0f}% reduction): {doc.source_filename}")
                                
                                # Apply global text replacement
                                self.entity_normalizer_logger.normalization(f"🔄 Global text replacement: Applying ||canonical||id|| format to document: {doc.source_filename}")
                                doc.markdown_content = normalization_result.normalized_text
                                
                                # Add normalization data to YAML
                                doc.yaml_frontmatter['normalization'] = {
                                    'normalization_method': 'mvp-fusion-canonicalization',
                                    'processing_time_ms': normalization_result.processing_time_ms,
                                    'statistics': normalization_result.statistics,
                                    'canonical_entities': [
                                        {
                                            'id': entity.id,
                                            'type': entity.type,
                                            'normalized': entity.normalized,
                                            'aliases': entity.aliases,
                                            'count': entity.count,
                                            'mentions': entity.mentions,
                                            'metadata': entity.metadata
                                        }
                                        for entity in normalization_result.normalized_entities
                                    ],
                                    'entity_reduction_percent': normalization_result.statistics.get('entity_reduction_percent', 0),
                                    'performance': {
                                        'entities_per_ms': normalization_result.statistics.get('performance_metrics', {}).get('entities_per_ms', 0),
                                        'edge_compatible': normalization_result.statistics.get('performance_metrics', {}).get('edge_compatible', False)
                                    }
                                }
                                
                                normalization_time = (time.perf_counter() - normalization_start) * 1000
                                # Pages already counted in classification phase
                                self.phase_manager.log('normalization', f"🔄 Normalized {canonical_count} canonical entities from {original_count} raw entities")
                                self.entity_normalizer_logger.normalization(f"✅ Normalization complete: {normalization_time:.1f}ms (enhanced text ready for semantic analysis): {doc.source_filename}")
                            
                            # TIMING FIX: Start semantic analysis phase
                            set_current_phase('semantic_analysis')
                            # Pages already counted in classification phase
                            
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
                                
                                # Pages already counted in classification phase
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
                            
                            yaml_header = yaml.dump(
                                dict(ordered_yaml), 
                                Dumper=NoAliasDumper,
                                default_flow_style=None,  # Let custom representers decide
                                sort_keys=False,
                                width=200,
                                allow_unicode=True
                            )
                            # Apply regex post-processing to guarantee flow style spans
                            yaml_header = force_flow_style_spans(yaml_header)
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