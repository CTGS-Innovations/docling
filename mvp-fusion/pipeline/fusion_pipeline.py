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
from datetime import datetime
from .in_memory_document import InMemoryDocument, MemoryOverflowError

# Import Aho-Corasick engine for high-performance pattern matching
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from knowledge.extractors.semantic_fact_extractor import SemanticFactExtractor
    from knowledge.aho_corasick_engine import AhoCorasickLayeredClassifier
    AHOCORASICK_AVAILABLE = True
except ImportError:
    AHOCORASICK_AVAILABLE = False
    print("⚠️  Aho-Corasick engine not available, falling back to regex patterns")


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
        
        # Initialize Aho-Corasick engine for high-performance classification
        self.ac_classifier = None
        if AHOCORASICK_AVAILABLE:
            try:
                self.ac_classifier = AhoCorasickLayeredClassifier()
                self.semantic_extractor = SemanticFactExtractor()
            except ImportError:
                self.semantic_extractor = None
                print("✅ Aho-Corasick engine initialized for government/regulatory + AI domains")
            except Exception as e:
                print(f"⚠️  Aho-Corasick initialization failed: {e}, using regex fallback")
                self.ac_classifier = None
        
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
                    
                    # Write semantic facts JSON knowledge file if available
                    print(f"🔍 Debug: Checking JSON generation for {doc.source_stem}")
                    print(f"   - Has semantic_json attr: {hasattr(doc, 'semantic_json')}")
                    print(f"   - semantic_json exists: {bool(doc.semantic_json)}")
                    print(f"   - semantic_json type: {type(doc.semantic_json)}")
                    
                    if doc.semantic_json:
                        json_file = output_dir / f"{doc.source_stem}.json"
                        import json
                        
                        print(f"📝 Generating JSON knowledge file: {json_file}")
                        
                        # Use the standardized knowledge JSON format (matches temp file)
                        knowledge_data = doc.generate_knowledge_json()
                        
                        if knowledge_data:  # Only write if we have semantic data
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
                            
                            total_facts = knowledge_data.get('semantic_summary', {}).get('total_facts', 0)
                            print(f"📄 Generated knowledge file: {json_file.name} ({total_facts} facts)")
                        else:
                            print(f"⚠️  No semantic facts to write for {doc.source_filename}")
                    
                    # Fallback: Legacy semantic JSON support  
                    elif hasattr(doc, 'semantic_json') and doc.semantic_json:
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
        Layered Classification Architecture - Progressive Intelligence Building
        
        Architecture:
        - Layer 1: File Metadata (free)
        - Layer 2: Document Structure (free from regex)  
        - Layer 3: Domain Classification (<15ms target)
        - Layer 4: Entity Extraction (<20ms target)
        - Layer 5: Deep Domain Entities - conditional based on confidence
        
        Performance target: <50ms total with early termination
        """
        start_time = time.perf_counter()
        layer_timings = {}
        
        # Initialize clean layered structure (no redundancy)
        classification_data = {}
        
        # LAYER 1: FILE METADATA (Free - already available)
        layer1_start = time.perf_counter()
        file_metadata = self._layer1_file_metadata(filename, content)
        classification_data['file_metadata'] = file_metadata['file_metadata']
        layer_timings['layer1_file_metadata'] = (time.perf_counter() - layer1_start) * 1000
        
        # LAYER 2: DOCUMENT STRUCTURE (Free from existing regex patterns)
        layer2_start = time.perf_counter()
        structure_data = self._layer2_document_structure(content)
        classification_data['document_structure'] = structure_data['document_structure']
        classification_data['structural_complexity_score'] = structure_data['structural_complexity_score']
        classification_data['structure_based_routing'] = structure_data['structure_based_routing']
        layer_timings['layer2_document_structure'] = (time.perf_counter() - layer2_start) * 1000
        
        # LAYER 3: DOMAIN CLASSIFICATION (<15ms target) - Aho-Corasick or Regex
        layer3_start = time.perf_counter()
        if self.ac_classifier:
            # Use high-performance Aho-Corasick classification
            domain_data = self.ac_classifier.layer3_domain_classification_ac(content)
        else:
            # Fallback to regex classification
            domain_data = self._layer3_domain_classification(content)
        
        # Clean domain and document type structure
        classification_data['domains'] = domain_data['domains']
        classification_data['primary_domain'] = domain_data['primary_domain']
        classification_data['primary_domain_confidence'] = domain_data['primary_domain_confidence']
        
        # Add document types if available (from Aho-Corasick)
        if 'document_types' in domain_data:
            classification_data['document_types'] = domain_data['document_types']
            classification_data['primary_document_type'] = domain_data['primary_document_type']
            classification_data['primary_doctype_confidence'] = domain_data['primary_doctype_confidence']
        
        classification_data['domain_routing'] = domain_data['domain_routing']
        classification_data['classification_method'] = domain_data.get('classification_method', 'regex')
        layer_timings['layer3_domain_classification'] = (time.perf_counter() - layer3_start) * 1000
        
        # Early termination check - if domain confidence is low, skip heavy layers
        primary_domain_confidence = max(domain_data['domains'].values()) if domain_data['domains'] else 0
        layers_processed = ['layer1_file_metadata', 'layer2_document_structure', 'layer3_domain_classification']
        
        if primary_domain_confidence < 5.0:  # Low confidence threshold (matching entity extraction threshold)
            classification_data['early_termination'] = True
            classification_data['termination_reason'] = f'Low domain confidence: {primary_domain_confidence}%'
        else:
            # LAYER 4: ENTITY EXTRACTION (<20ms target)
            layer4_start = time.perf_counter()
            entity_data = self._layer4_entity_extraction(content)
            
            # Clean entity structure
            classification_data['entities'] = entity_data['universal_entities']
            classification_data['entity_insights'] = {
                'has_financial_data': entity_data['has_financial_data'],
                'has_regulations': entity_data['has_regulations'],
                'has_contact_info': entity_data['has_contact_info'],
                'has_temporal_data': entity_data['has_temporal_data'],
                'has_external_references': entity_data['has_external_references'],
                'has_technical_measurements': entity_data['has_technical_measurements'],
                'total_entities_found': entity_data['total_entities_found'],
                'entity_density': entity_data['entity_density']
            }
            layers_processed.append('layer4_entity_extraction')
            layer_timings['layer4_entity_extraction'] = (time.perf_counter() - layer4_start) * 1000
            
            # LAYER 5: DEEP DOMAIN ENTITIES (Conditional - only for high-confidence domains)
            if primary_domain_confidence >= 60.0:  # High confidence threshold
                layer5_start = time.perf_counter()
                if self.ac_classifier:
                    # Use high-performance Aho-Corasick entity extraction
                    deep_entity_data = self.ac_classifier.layer5_deep_domain_entities_ac(content, domain_data['domains'])
                else:
                    # Fallback to regex entity extraction
                    deep_entity_data = self._layer5_deep_domain_entities(content, domain_data['domains'])
                
                # Clean deep entity structure
                if deep_entity_data.get('deep_domain_entities'):
                    classification_data['deep_domain_entities'] = deep_entity_data['deep_domain_entities']
                    classification_data['deep_domain_specialization'] = deep_entity_data['deep_domain_specialization']
                    classification_data['deep_entities_found'] = deep_entity_data['deep_entities_found']
                
                layers_processed.append('layer5_deep_domain_entities')
                layer_timings['layer5_deep_domain_entities'] = (time.perf_counter() - layer5_start) * 1000
        
        # LAYER 6: SEMANTIC FACT EXTRACTION (Conditional - only if semantic extractor available)
        if hasattr(self, 'semantic_extractor') and self.semantic_extractor and not classification_data.get('early_termination', False):
            layer6_start = time.perf_counter()
            
            try:
                # Pass both classification data (for entities) and content (for context) - parallel processing
                semantic_facts = self.semantic_extractor.extract_semantic_facts_from_classification(
                    classification_data=classification_data,
                    markdown_content=content
                )
                
                # Add semantic facts to classification data
                classification_data['semantic_facts'] = semantic_facts.get('semantic_facts', {})
                classification_data['normalized_entities'] = semantic_facts.get('normalized_entities', {})
                classification_data['semantic_summary'] = semantic_facts.get('semantic_summary', {})
                
                # Store semantic facts for JSON knowledge file generation (fix: return for doc storage)
                classification_data['_semantic_facts_for_json'] = semantic_facts
                
                layers_processed.append('layer6_semantic_facts')
                layer_timings['layer6_semantic_facts'] = (time.perf_counter() - layer6_start) * 1000
                
                print(f"🧠 Layer 6: Semantic facts extracted - {semantic_facts.get('semantic_summary', {}).get('total_facts', 0)} facts found")
                
            except Exception as e:
                print(f"⚠️  Layer 6 semantic extraction failed: {e}")
                layer_timings['layer6_semantic_facts'] = (time.perf_counter() - layer6_start) * 1000
        
        # Final performance summary (clean structure)
        total_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Add performance section at the end
        classification_data['performance'] = {
            'processing_time_ms': round(total_time_ms, 2),
            'layers_processed': layers_processed,
            'layer_timings_ms': {k: round(v, 2) for k, v in layer_timings.items()},
            'early_termination': classification_data.get('early_termination', False)
        }
        
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
        matches = re.findall(pattern, content)
        # Clean up whitespace and newlines
        cleaned = [' '.join(match.split()) for match in matches]
        return list(set(cleaned))[:10]
    
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
        matches = re.findall(pattern, content, re.IGNORECASE)
        # Clean up whitespace and newlines
        cleaned = [' '.join(match.split()) for match in matches]
        return list(set(cleaned))[:10]
    
    # Core 8 Entity Extraction Methods
    def _extract_person(self, content: str) -> List[str]:
        """Extract person names (Core 8)"""
        # Simple pattern for common name formats
        patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # First Last
            r'\b(?:Dr|Mr|Ms|Mrs|Prof)\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',  # Title Name
        ]
        persons = []
        for pattern in patterns:
            persons.extend(re.findall(pattern, content))
        return list(set(persons))[:10]
    
    def _extract_org(self, content: str) -> List[str]:
        """Extract organization names (Core 8)"""
        patterns = [
            r'\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:Inc|Corp|LLC|Ltd|Company|Organization|Institute|University|College)\b',
            r'\b(?:OSHA|FDA|EPA|NASA|FBI|CIA|DOD|USDA)\b',  # Common acronyms
        ]
        orgs = []
        for pattern in patterns:
            orgs.extend(re.findall(pattern, content))
        return list(set(orgs))[:10]
    
    def _extract_location(self, content: str) -> List[str]:
        """Extract location names (Core 8)"""
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b',  # City, ST
            r'\b(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr)\b',  # Street types
        ]
        locations = []
        for pattern in patterns:
            locations.extend(re.findall(pattern, content))
        return list(set(locations))[:10]
    
    def _extract_gpe(self, content: str) -> List[str]:
        """Extract geo-political entities (Core 8)"""
        patterns = [
            r'\b(?:United States|USA|US|Canada|Mexico|California|Texas|Florida|New York)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:County|State|Province|Territory)\b',
        ]
        gpes = []
        for pattern in patterns:
            gpes.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(gpes))[:10]
    
    def _extract_time(self, content: str) -> List[str]:
        """Extract time expressions (Core 8)"""
        patterns = [
            r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',  # 12:30 PM
            r'\b(?:morning|afternoon|evening|night|noon|midnight)\b',  # Time periods
        ]
        times = []
        for pattern in patterns:
            times.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(times))[:10]
    
    def _extract_percent(self, content: str) -> List[str]:
        """Extract percentages (Core 8)"""
        patterns = [
            r'\b\d+(?:\.\d+)?%\b',  # 50%, 25.5%
            r'\b\d+(?:\.\d+)?\s*percent\b',  # 50 percent
        ]
        percentages = []
        for pattern in patterns:
            percentages.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(percentages))[:10]
    
    def _classify_domains_with_scores(self, content: str) -> Dict[str, float]:
        """
        Classify document into domains with percentage scores.
        TODO: Replace with Aho-Corasick for 25+ domains
        """
        content_lower = content.lower()
        
        # Domain keyword patterns (will be Aho-Corasick patterns)
        domain_keywords = {
            'safety': ['osha', 'safety', 'hazard', 'injury', 'accident', 'ppe', 'protective'],
            'compliance': ['compliance', 'regulation', 'cfr', 'requirement', 'standard'],
            'regulatory': ['regulatory', 'regulation', 'rule', 'mandate', 'directive'],
            'legal': ['legal', 'contract', 'agreement', 'liability', 'lawsuit'],
            'medical': ['medical', 'health', 'diagnosis', 'treatment', 'patient'],
            'financial': ['financial', 'revenue', 'profit', 'investment', 'budget'],
            'technical': ['technical', 'engineering', 'specification', 'design', 'system'],
            'construction': ['construction', 'building', 'contractor', 'scaffold', 'ladder'],
            'environmental': ['environmental', 'epa', 'pollution', 'emission', 'waste']
        }
        
        # Count keyword hits per domain
        domain_hits = {}
        total_hits = 0
        
        for domain, keywords in domain_keywords.items():
            hits = sum(1 for keyword in keywords if keyword in content_lower)
            if hits > 0:
                domain_hits[domain] = hits
                total_hits += hits
        
        # Convert to percentages
        domain_scores = {}
        if total_hits > 0:
            for domain, hits in domain_hits.items():
                percentage = (hits / total_hits) * 100
                domain_scores[domain] = round(percentage, 1)
        else:
            domain_scores['general'] = 100.0
            
        # Sort by percentage (highest first) - free since dict creation
        domain_scores = dict(sorted(domain_scores.items(), key=lambda x: x[1], reverse=True))
        
        return domain_scores
    
    def _classify_document_types_with_scores(self, content: str) -> Dict[str, float]:
        """
        Classify document types with percentage scores.
        TODO: Replace with Aho-Corasick for document types
        """
        content_lower = content.lower()
        
        # Document type patterns
        doctype_keywords = {
            'regulation': ['29 cfr', '40 cfr', 'regulation', 'regulatory', 'compliance'],
            'guide': ['guide', 'guidance', 'how to', 'instructions', 'manual'],
            'standard': ['standard', 'specification', 'requirement', 'shall', 'must'],
            'report': ['report', 'analysis', 'findings', 'results', 'conclusion'],
            'policy': ['policy', 'procedure', 'protocol', 'guidelines'],
            'training': ['training', 'education', 'learning', 'course', 'certification'],
            'reference': ['reference', 'appendix', 'glossary', 'definition', 'terminology']
        }
        
        # Count keyword hits per document type
        type_hits = {}
        total_hits = 0
        
        for doctype, keywords in doctype_keywords.items():
            hits = sum(1 for keyword in keywords if keyword in content_lower)
            if hits > 0:
                type_hits[doctype] = hits
                total_hits += hits
        
        # Convert to percentages
        type_scores = {}
        if total_hits > 0:
            for doctype, hits in type_hits.items():
                percentage = (hits / total_hits) * 100
                type_scores[doctype] = round(percentage, 1)
        else:
            type_scores['document'] = 100.0
            
        # Sort by percentage (highest first)
        type_scores = dict(sorted(type_scores.items(), key=lambda x: x[1], reverse=True))
        
        return type_scores

    # ========================================
    # LAYERED CLASSIFICATION IMPLEMENTATION
    # ========================================
    
    def _layer1_file_metadata(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Layer 1: File Metadata (Free - already available during conversion)
        
        Extract basic file properties and statistics that guide later layers.
        This replaces the separate conversion metadata section.
        Performance: ~0.1ms (essentially free)
        """
        from pathlib import Path
        
        file_path = Path(filename)
        content_length = len(content)
        
        return {
            'file_metadata': {
                'filename': file_path.name,
                'file_stem': file_path.stem,
                'file_extension': file_path.suffix.lower(),
                'content_length_chars': content_length,
                'estimated_pages': max(1, content_length // 3000),  # Rough estimate
                'processing_priority': 'high' if content_length < 50000 else 'normal',
                'conversion_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'processing_method': 'mvp-fusion-layered-classification'
            }
        }
    
    def _layer2_document_structure(self, content: str) -> Dict[str, Any]:
        """
        Layer 2: Document Structure (Free from existing regex patterns)
        
        Extract structural elements that help classify document type and domain.
        Performance: ~1-2ms (regex patterns already running)
        """
        content_lower = content.lower()
        
        # Structural indicators (very fast checks)
        structure_indicators = {
            'has_table_of_contents': 'table of contents' in content_lower or 'contents' in content_lower[:1000],
            'has_sections': bool(re.search(r'(?:section|chapter)\s+\d+', content_lower)),
            'has_numbered_lists': bool(re.search(r'^\s*\d+\.', content, re.MULTILINE)),
            'has_bullet_points': bool(re.search(r'^\s*[•\-\*]', content, re.MULTILINE)),
            'has_headers': bool(re.search(r'^#+\s', content, re.MULTILINE)),
            'has_footnotes': 'footnote' in content_lower or bool(re.search(r'\[\d+\]', content)),
            'has_citations': bool(re.search(r'\(\d{4}\)', content)) or 'et al' in content_lower,
            'document_language': 'english'  # TODO: Add simple language detection
        }
        
        # Document complexity scoring (helps route to appropriate layers)
        complexity_score = sum([
            int(structure_indicators['has_table_of_contents']) * 2,
            int(structure_indicators['has_sections']) * 2,
            int(structure_indicators['has_numbered_lists']),
            int(structure_indicators['has_headers']),
            int(structure_indicators['has_footnotes']),
            int(structure_indicators['has_citations'])
        ])
        
        return {
            'document_structure': structure_indicators,
            'structural_complexity_score': complexity_score,
            'structure_based_routing': {
                'route_to_deep_analysis': complexity_score >= 4,
                'priority_processing': complexity_score <= 2
            }
        }
    
    def _layer3_domain_classification(self, content: str) -> Dict[str, Any]:
        """
        Layer 3: Domain Classification (<15ms target)
        
        Fast domain classification using Aho-Corasick patterns (currently regex).
        This determines processing route for subsequent layers.
        """
        # Use existing domain classification logic
        domain_scores = self._classify_domains_with_scores(content)
        doctype_scores = self._classify_document_types_with_scores(content)
        
        # Determine primary domain and confidence
        primary_domain = max(domain_scores.keys(), key=lambda k: domain_scores[k]) if domain_scores else 'general'
        primary_domain_confidence = domain_scores.get(primary_domain, 0)
        
        # Domain-based routing decisions
        routing_decisions = {
            'skip_entity_extraction': primary_domain_confidence < 5.0,  # Lower threshold for early testing
            'enable_deep_domain_extraction': primary_domain_confidence >= 60.0,
            'domain_specialization_route': primary_domain if primary_domain_confidence >= 40.0 else 'general'
        }
        
        return {
            'domains': domain_scores,  # Native dict for semantic extraction
            'document_types': doctype_scores,  # Native dict for semantic extraction
            'primary_domain': primary_domain,
            'primary_domain_confidence': primary_domain_confidence,
            'domain_routing': routing_decisions
        }
    
    def _layer4_entity_extraction(self, content: str) -> Dict[str, Any]:
        """
        Layer 4: Global + Domain Entity Extraction
        
        Global entities: Core 8 (PERSON, ORG, LOC, GPE, DATE, TIME, MONEY, PERCENT) + reliable patterns (phone, URLs, measurements, regulations)
        Domain entities: comprehensive FLPC extraction (organizations, people, locations, percentages, statistics)
        """
        # Global entity extraction using FLPC (Core 8 + proven patterns)
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'knowledge', 'extractors'))
            from fast_regex import FastRegexEngine
            
            flpc = FastRegexEngine()
            
            # Core 8 entities using FLPC
            global_entities = {
                'person': self._extract_core8_person_flpc(content, flpc),
                'org': self._extract_core8_org_flpc(content, flpc),
                'loc': self._extract_core8_location_flpc(content, flpc),
                'gpe': self._extract_core8_gpe_flpc(content, flpc),
                'date': self._extract_core8_date_flpc(content, flpc),
                'time': self._extract_core8_time_flpc(content, flpc),
                'money': self._extract_core8_money_flpc(content, flpc),
                'percent': self._extract_core8_percent_flpc(content, flpc),
                # Additional reliable patterns with FLPC
                'phone': self._extract_core8_phone_flpc(content, flpc),
                'regulation': self._extract_core8_regulation_flpc(content, flpc),
                'url': self._extract_core8_url_flpc(content, flpc),
                'measurement': self._extract_core8_measurement_flpc(content, flpc)
            }
        except Exception:
            # Fallback to Python regex if FLPC fails
            global_entities = {
                'person': self._extract_person(content),
                'org': self._extract_org(content),
                'loc': self._extract_location(content),
                'gpe': self._extract_gpe(content),
                'date': self._extract_dates(content),
                'time': self._extract_time(content),
                'money': self._extract_money(content),
                'percent': self._extract_percent(content),
                'phone': self._extract_phone(content), 
                'regulation': self._extract_regulation(content),
                'url': self._extract_urls(content),
                'measurement': self._extract_measurements(content)
            }
        
        # Domain entity extraction using FLPC
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'knowledge', 'extractors'))
            from comprehensive_entity_extractor import ComprehensiveEntityExtractor
            
            extractor = ComprehensiveEntityExtractor()
            domain_results = extractor.extract_all_entities(content)
            domain_entities = domain_results['entities']
        except Exception:
            # Fallback if domain extraction fails
            domain_entities = {
                'financial': [],
                'percentages': [],
                'organizations': [],
                'people': [],
                'locations': [],
                'regulations': [],
                'statistics': []
            }
        
        # Structure entities by type
        structured_entities = {
            'global_entities': global_entities,
            'domain_entities': {
                'financial': domain_entities.get('financial', []),
                'percentages': domain_entities.get('percentages', []),
                'organizations': domain_entities.get('organizations', []),
                'people': domain_entities.get('people', []),
                'locations': domain_entities.get('locations', []),
                'regulations': domain_entities.get('regulations', []),
                'statistics': domain_entities.get('statistics', [])
            }
        }
        
        # Count total entities from both sources
        global_count = sum(len(v) for v in global_entities.values() if isinstance(v, list))
        domain_count = sum(len(v) for v in domain_entities.values() if isinstance(v, list))
        total_entities = global_count + domain_count
        
        # Entity-based insights for semantic extraction
        entity_insights = {
            'has_financial_data': bool(global_entities['money']) or bool(domain_entities.get('financial', [])),
            'has_regulations': bool(global_entities['regulation']) or bool(domain_entities.get('regulations', [])),
            'has_contact_info': bool(global_entities['phone']) or bool(domain_entities.get('people', [])),
            'has_temporal_data': bool(global_entities['date']),
            'has_external_references': bool(global_entities['url']) or bool(domain_entities.get('organizations', [])),
            'has_technical_measurements': bool(global_entities['measurement']) or bool(domain_entities.get('measurements', [])),
            'total_entities_found': total_entities,
            'entity_density': total_entities / max(1, len(content) // 1000)  # Entities per KB
        }
        
        # Return structured results
        result = {'universal_entities': structured_entities}
        result.update(entity_insights)
        
        return result
    
    def _layer5_deep_domain_entities(self, content: str, domain_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Layer 5: Deep Domain Entities (Conditional - only for high-confidence domains)
        
        Domain-specific entity extraction for specialized vocabularies.
        Only runs when primary domain confidence >= 60%.
        Performance: <15ms target
        """
        primary_domain = max(domain_scores.keys(), key=lambda k: domain_scores[k])
        
        deep_entities = {}
        
        # Safety domain specialization
        if primary_domain == 'safety':
            deep_entities['safety_equipment'] = self._extract_safety_equipment(content)
            deep_entities['hazard_types'] = self._extract_hazard_types(content)
            deep_entities['injury_types'] = self._extract_injury_types(content)
        
        # Compliance domain specialization  
        elif primary_domain == 'compliance' or primary_domain == 'regulatory':
            deep_entities['compliance_standards'] = self._extract_compliance_standards(content)
            deep_entities['regulatory_agencies'] = self._extract_regulatory_agencies(content)
            deep_entities['penalty_amounts'] = self._extract_penalty_amounts(content)
        
        # Construction domain specialization
        elif primary_domain == 'construction':
            deep_entities['construction_equipment'] = self._extract_construction_equipment(content)
            deep_entities['building_materials'] = self._extract_building_materials(content)
            deep_entities['construction_phases'] = self._extract_construction_phases(content)
        
        # Medical domain specialization
        elif primary_domain == 'medical':
            deep_entities['medical_conditions'] = self._extract_medical_conditions(content)
            deep_entities['medical_procedures'] = self._extract_medical_procedures(content)
            deep_entities['medications'] = self._extract_medications(content)
        
        total_deep_entities = sum(len(v) for v in deep_entities.values() if isinstance(v, list))
        
        return {
            'deep_domain_entities': deep_entities,
            'deep_domain_specialization': primary_domain,
            'deep_entities_found': total_deep_entities,
            'domain_expertise_applied': True
        }
    
    # ========================================
    # DEEP DOMAIN ENTITY EXTRACTORS
    # ========================================
    
    def _extract_safety_equipment(self, content: str) -> List[str]:
        """Extract safety equipment mentions"""
        pattern = r'\b(?:helmet|harness|goggles|gloves|respirator|hard hat|ppe|protective equipment)\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return list(set([match.lower() for match in matches]))[:10]
    
    def _extract_hazard_types(self, content: str) -> List[str]:
        """Extract hazard type mentions"""
        pattern = r'\b(?:fall|slip|trip|electrical|chemical|biological|radiation|noise)\s+hazard\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        cleaned = [' '.join(match.split()) for match in matches]
        return list(set([match.lower() for match in cleaned]))[:10]
    
    def _extract_injury_types(self, content: str) -> List[str]:
        """Extract injury type mentions"""
        pattern = r'\b(?:fracture|sprain|cut|burn|bruise|laceration|contusion)\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return list(set([match.lower() for match in matches]))[:10]
    
    def _extract_compliance_standards(self, content: str) -> List[str]:
        """Extract compliance standards"""
        pattern = r'\b(?:ISO|ANSI|ASTM|OSHA|EPA|NFPA)\s*[-\s]*\d+(?:[-\.]\d+)*\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        cleaned = [' '.join(match.split()).upper() for match in matches]
        return list(set(cleaned))[:10]
    
    def _extract_regulatory_agencies(self, content: str) -> List[str]:
        """Extract regulatory agency mentions"""
        pattern = r'\b(?:OSHA|EPA|FDA|CPSC|NHTSA|FAA|FCC|SEC)\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return list(set([match.upper() for match in matches]))[:10]
    
    def _extract_penalty_amounts(self, content: str) -> List[str]:
        """Extract penalty/fine amounts"""
        pattern = r'(?:fine|penalty|citation)\s*[:\-]?\s*\$[\d,]+(?:\.\d{2})?'
        matches = re.findall(pattern, content, re.IGNORECASE)
        cleaned = [' '.join(match.split()) for match in matches]
        return list(set(cleaned))[:10]
    
    def _extract_construction_equipment(self, content: str) -> List[str]:
        """Extract construction equipment mentions"""
        pattern = r'\b(?:crane|excavator|bulldozer|loader|scaffold|ladder|forklift)\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return list(set([match.lower() for match in matches]))[:10]
    
    def _extract_building_materials(self, content: str) -> List[str]:
        """Extract building materials"""
        pattern = r'\b(?:concrete|steel|lumber|drywall|insulation|rebar|plywood)\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return list(set([match.lower() for match in matches]))[:10]
    
    def _extract_construction_phases(self, content: str) -> List[str]:
        """Extract construction phases"""
        pattern = r'\b(?:foundation|framing|roofing|plumbing|electrical|finishing)\s*(?:phase|stage|work)?\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        cleaned = [' '.join(match.split()) for match in matches]
        return list(set([match.lower() for match in cleaned]))[:10]
    
    def _extract_medical_conditions(self, content: str) -> List[str]:
        """Extract medical conditions"""
        pattern = r'\b(?:diabetes|hypertension|asthma|pneumonia|infection|syndrome)\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return list(set([match.lower() for match in matches]))[:10]
    
    def _extract_medical_procedures(self, content: str) -> List[str]:
        """Extract medical procedures"""
        pattern = r'\b(?:surgery|biopsy|examination|treatment|therapy|procedure)\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return list(set([match.lower() for match in matches]))[:10]
    
    def _extract_medications(self, content: str) -> List[str]:
        """Extract medication mentions"""
        pattern = r'\b(?:aspirin|ibuprofen|acetaminophen|medication|drug|prescription)\b'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return list(set([match.lower() for match in matches]))[:10]

    # FLPC Core 8 Entity Extraction Methods (14.9x faster with spans)
    
    def _extract_entities_with_spans(self, patterns: List[str], content: str, flpc, entity_type: str) -> List[Dict]:
        """Helper to extract entities with spans using FLPC"""
        entities = []
        for pattern in patterns:
            try:
                for match in flpc.finditer(pattern, content):
                    raw_text = match.group(0)
                    # Clean text: normalize whitespace, remove line breaks, strip
                    cleaned_text = ' '.join(raw_text.split()).strip()
                    
                    # Skip if cleaning resulted in empty/invalid text
                    if not cleaned_text or len(cleaned_text) < 2:
                        continue
                        
                    entity = {
                        "value": cleaned_text,
                        "span": {"start": match.start(0), "end": match.end(0)},
                        "text": cleaned_text,
                        "type": entity_type
                    }
                    entities.append(entity)
            except:
                continue
        # Remove duplicates by value and limit
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity["value"] not in seen:
                seen.add(entity["value"])
                unique_entities.append(entity)
        return unique_entities[:10]
    
    def _extract_core8_person_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract person names with spans using FLPC (Core 8)"""
        patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # First Last
            r'\b(?:Dr|Mr|Ms|Mrs|Prof)\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',  # Title Name
        ]
        return self._extract_entities_with_spans(patterns, content, flpc, "PERSON")
    
    def _extract_core8_org_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract organization names with spans using FLPC (Core 8)"""
        patterns = [
            r'\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:Inc|Corp|LLC|Ltd|Company|Organization|Institute|University|College)\b',
            r'\b(?:OSHA|FDA|EPA|NASA|FBI|CIA|DOD|USDA)\b',
        ]
        return self._extract_entities_with_spans(patterns, content, flpc, "ORG")
    
    def _extract_core8_location_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract location names with spans using FLPC (Core 8)"""
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b',  # City, ST
            r'\b(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr)\b',
        ]
        return self._extract_entities_with_spans(patterns, content, flpc, "LOC")
    
    def _extract_core8_gpe_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract geo-political entities with spans using FLPC (Core 8)"""
        patterns = [
            r'\b(?:United States|USA|US|Canada|Mexico|California|Texas|Florida|New York)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:County|State|Province|Territory)\b',
        ]
        return self._extract_entities_with_spans(patterns, content, flpc, "GPE")
    
    def _extract_core8_date_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract dates with spans using FLPC (Core 8)"""
        patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}\b'
        ]
        return self._extract_entities_with_spans(patterns, content, flpc, "DATE")
    
    def _extract_core8_time_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract time expressions with spans using FLPC (Core 8)"""
        patterns = [
            r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',
            r'\b(?:morning|afternoon|evening|night|noon|midnight)\b',
        ]
        return self._extract_entities_with_spans(patterns, content, flpc, "TIME")
    
    def _extract_core8_money_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract monetary amounts with spans using FLPC (Core 8)"""
        patterns = [r'\$[\d,]+(?:\.\d{2})?|\$\d+']
        return self._extract_entities_with_spans(patterns, content, flpc, "MONEY")
    
    def _extract_core8_percent_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract percentages with spans using FLPC (Core 8)"""
        patterns = [
            r'\b\d+(?:\.\d+)?%\b',
            r'\b\d+(?:\.\d+)?\s*percent\b',
        ]
        return self._extract_entities_with_spans(patterns, content, flpc, "PERCENT")
    
    def _extract_core8_phone_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract phone numbers with spans using FLPC"""
        patterns = [r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}']
        return self._extract_entities_with_spans(patterns, content, flpc, "PHONE")
    
    def _extract_core8_regulation_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract regulation references with spans using FLPC"""
        patterns = [r'\d+\s*CFR\s*\d+(?:\.\d+)*']
        return self._extract_entities_with_spans(patterns, content, flpc, "REGULATION")
    
    def _extract_core8_url_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract URLs with spans using FLPC"""
        patterns = [r'https?://[^\s<>"{}|\\^`\[\]]+']
        return self._extract_entities_with_spans(patterns, content, flpc, "URL")[:5]
    
    def _extract_core8_measurement_flpc(self, content: str, flpc) -> List[Dict]:
        """Extract measurements with spans using FLPC"""
        patterns = [r'\d+(?:\.\d+)?\s*(?:inches?|feet?|meters?|cm|mm|kg|lbs?|pounds?)\b']
        return self._extract_entities_with_spans(patterns, content, flpc, "MEASUREMENT")