"""
Intelligent SPO Fact Extractor for Meaningful Knowledge Extraction

This module focuses on extracting meaningful, actionable facts using advanced SPO relationships
rather than fragmented, repetitive information. Emphasizes quality over quantity.

Key Features:
- High-confidence fact filtering (>0.7 threshold)
- Relationship-based extraction instead of isolated entities
- Compound fact assembly for related information
- Actionable requirement extraction with clear subjects/objects
- Anti-repetition algorithms for unique, valuable facts
"""

import re
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass
import logging
from pathlib import Path
from collections import defaultdict, Counter

# Import base extractor
try:
    from .semantic_fact_extractor import SemanticFactExtractor
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent))
    from semantic_fact_extractor import SemanticFactExtractor

# Import FLPC for high-performance pattern matching
try:
    from fusion.flpc_engine import FLPCEngine
except ImportError:
    FLPCEngine = None

@dataclass
class MeaningfulFact:
    """Represents a meaningful, actionable fact with clear relationships"""
    subject: str
    predicate: str
    object: str
    confidence: float
    fact_type: str
    context: str
    span: Tuple[int, int]
    modifiers: List[str] = None
    related_entities: List[str] = None
    actionable: bool = False
    
    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = []
        if self.related_entities is None:
            self.related_entities = []

@dataclass
class CompoundFact:
    """Represents a compound fact that combines related information"""
    primary_fact: MeaningfulFact
    related_facts: List[MeaningfulFact]
    relationship_type: str  # 'measurement_series', 'requirement_chain', etc.
    confidence: float
    
class IntelligentSPOFactExtractor(SemanticFactExtractor):
    """
    Intelligent SPO fact extractor focused on meaningful knowledge extraction
    
    Replaces fragmented entity extraction with structured, actionable facts that
    capture real relationships and requirements from documents.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize intelligent extractor with quality-focused parameters"""
        super().__init__(*args, **kwargs)
        
        # Quality thresholds
        self.min_confidence = 0.75  # Raised from 0.6 to ensure high-quality facts
        self.min_context_length = 20  # Require meaningful context
        self.max_similar_facts = 3  # Limit repetitive information
        
        # Initialize FLPC for high-performance extraction
        self.flpc_engine = None
        if FLPCEngine:
            try:
                self.flpc_engine = FLPCEngine({})
                self.logger.logger.info("✅ FLPC engine initialized for intelligent extraction")
            except Exception as e:
                self.logger.logger.warning(f"⚠️  FLPC initialization failed: {e}")
        
        # Meaningful relationship patterns (using FLPC when available)
        self.relationship_patterns = self._initialize_relationship_patterns()
        
        # Anti-repetition tracking
        self.extracted_facts = set()
        self.fact_clusters = defaultdict(list)
        
        self.logger.logger.info("🧠 Intelligent SPO Fact Extractor initialized for meaningful knowledge extraction")
    
    def _initialize_relationship_patterns(self) -> Dict[str, List[str]]:
        """Initialize high-value relationship patterns for meaningful fact extraction"""
        return {
            'safety_requirements': [
                r'(?:must|shall|required to|mandatory)\s+(?:wear|use|maintain|comply with|follow)\s+(.*?)(?=\.[\s]*$|!|\?|$)',
                r'(?:employees|workers|personnel|staff)\s+(?:must|shall|are required to)\s+(.*?)(?=\.[\s]*$|!|\?|$)',
                r'(?:minimum|maximum)\s+(?:distance|height|weight|time|temperature)\s+(?:of|is|must be)\s+(.*?)(?=\.[\s]*$|!|\?|$)',
            ],
            'compliance_requirements': [
                r'(?:comply with|adhere to|follow|meet)\s+(OSHA|ISO|ANSI|[A-Z]{2,5})\s+(?:standards?|regulations?|requirements?)',
                r'(?:violation|breach|non-compliance)\s+(?:of|with)\s+([^.;!?]*(?:\([^)]*\))?[^.;!?]*)',
                r'(?:inspection|audit|review)\s+(?:required|mandatory|must be conducted)\s+([^.;!?]*(?:\([^)]*\))?[^.;!?]*)',
            ],
            'measurement_relationships': [
                r'(?:distance|height|weight|length|width|depth|diameter|radius)\s+(?:of|must be|shall be|is)\s+([0-9]+(?:\.[0-9]+)?\s*[a-zA-Z]+(?:\s*\([^)]*\))?)',
                r'(?:limit|threshold|maximum|minimum)\s+(?:of|for\s+\w+\s+is|is|must not exceed)\s+(.*?)(?=\.[\s]*$|!|\?|$)',
                r'(?:temperature|pressure|voltage|current)\s+(?:range|between|from)\s+(.*?)(?=\.[\s]*$|!|\?|$)',
            ],
            'organizational_actions': [
                r'(company|organization|employer|management)\s+(?:must|shall|will|provides?|ensures?)\s+([^.;!?]*(?:\([^)]*\))?[^.;!?]*)',
                r'(employees|workers|staff)\s+(?:receive|provided with|equipped with)\s+([^.;!?]*(?:\([^)]*\))?[^.;!?]*)',
                r'(?:training|education|certification)\s+(?:required|mandatory|provided)\s+([^.;!?]*(?:\([^)]*\))?[^.;!?]*)',
            ],
            'temporal_requirements': [
                r'(?:within|by|before|after|during)\s+([0-9]+\s*(?:days?|hours?|weeks?|months?|years?))',
                r'(?:annually|monthly|weekly|daily|quarterly)\s+([^.;!?]*(?:\([^)]*\))?[^.;!?]*)',
                r'(?:deadline|due date|expiration)\s+(?:is|of)\s+([^.;!?]*(?:\([^)]*\))?)',
            ]
        }
    
    def extract_semantic_facts(self, text: str, cache_spo_components: bool = True) -> Dict[str, Any]:
        """
        Extract meaningful semantic facts focused on actionable information
        
        Args:
            text: Full document text with YAML frontmatter
            cache_spo_components: Whether to use SPO component caching
            
        Returns:
            High-quality semantic facts with meaningful relationships
        """
        import time
        start_time = time.time()
        
        self.logger.logger.info("🧠 Starting intelligent fact extraction (quality-focused)")
        
        # Reset tracking for this extraction
        self.extracted_facts.clear()
        self.fact_clusters.clear()
        
        # Parse document sections
        yaml_content, markdown_content = self._parse_document_sections(text)
        
        # Extract domain context from YAML for focused extraction
        domain_context = self._extract_domain_context(yaml_content)
        
        # Step 1: Extract meaningful facts using relationship patterns
        meaningful_facts = self._extract_meaningful_facts(markdown_content, domain_context)
        
        # Step 2: Assemble compound facts from related information
        compound_facts = self._assemble_compound_facts(meaningful_facts)
        
        # Step 3: Extract actionable requirements with clear SPO structure
        actionable_requirements = self._extract_actionable_requirements(markdown_content, domain_context)
        
        # Step 4: Filter and deduplicate for final high-quality output
        final_facts = self._filter_and_deduplicate_facts(
            meaningful_facts + compound_facts + actionable_requirements
        )
        
        # Step 5: Structure results for semantic analysis output
        structured_results = self._structure_intelligent_results(final_facts, domain_context)
        
        # Performance tracking
        extraction_time = (time.time() - start_time) * 1000
        structured_results['intelligent_extraction'] = {
            'extraction_time_ms': extraction_time,
            'quality_threshold': self.min_confidence,
            'facts_extracted': len(final_facts),
            'domain_context': domain_context,
            'extraction_method': 'Intelligent SPO with relationship focus'
        }
        
        self.logger.logger.info(f"✅ Intelligent extraction complete: {len(final_facts)} meaningful facts in {extraction_time:.1f}ms")
        
        return structured_results
    
    def _parse_document_sections(self, text: str) -> Tuple[str, str]:
        """Parse YAML frontmatter and markdown content"""
        parts = text.split('---')
        if len(parts) >= 3:
            return parts[1], '---'.join(parts[2:])
        return "", text
    
    def _extract_domain_context(self, yaml_content: str) -> Dict[str, Any]:
        """Extract domain context to focus extraction on relevant patterns"""
        domain_context = {
            'primary_domain': 'general',
            'document_types': [],
            'focus_areas': []
        }
        
        # Look for domain classification in YAML
        if 'safety' in yaml_content.lower() or 'osha' in yaml_content.lower():
            domain_context['primary_domain'] = 'safety_compliance'
            domain_context['focus_areas'] = ['safety_requirements', 'compliance_requirements']
        elif 'financial' in yaml_content.lower() or 'audit' in yaml_content.lower():
            domain_context['primary_domain'] = 'financial'
            domain_context['focus_areas'] = ['organizational_actions', 'compliance_requirements']
        elif 'research' in yaml_content.lower() or 'academic' in yaml_content.lower():
            domain_context['primary_domain'] = 'research'
            domain_context['focus_areas'] = ['measurement_relationships', 'organizational_actions']
        else:
            domain_context['focus_areas'] = list(self.relationship_patterns.keys())
        
        return domain_context
    
    def _extract_meaningful_facts(self, text: str, domain_context: Dict) -> List[MeaningfulFact]:
        """Extract meaningful facts using relationship-focused patterns"""
        meaningful_facts = []
        
        # Focus on domain-relevant patterns
        focus_patterns = domain_context.get('focus_areas', list(self.relationship_patterns.keys()))
        
        for pattern_category in focus_patterns:
            if pattern_category in self.relationship_patterns:
                category_facts = self._extract_category_facts(
                    text, pattern_category, self.relationship_patterns[pattern_category]
                )
                meaningful_facts.extend(category_facts)
        
        return meaningful_facts
    
    def _extract_category_facts(self, text: str, category: str, patterns: List[str]) -> List[MeaningfulFact]:
        """Extract facts for a specific category using high-performance patterns"""
        facts = []
        
        for pattern in patterns:
            try:
                if self.flpc_engine:
                    # Use FLPC for high-performance extraction
                    matches = self.flpc_engine.find_all_matches(pattern, text)
                else:
                    # Fallback to Python regex
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))
                
                for match in matches:
                    fact = self._create_meaningful_fact_from_match(
                        match, category, text
                    )
                    if fact and self._is_high_quality_fact(fact):
                        facts.append(fact)
                        
            except Exception as e:
                self.logger.logger.debug(f"Pattern extraction failed for {category}: {e}")
        
        return facts
    
    def _create_meaningful_fact_from_match(self, match, category: str, text: str) -> Optional[MeaningfulFact]:
        """Create meaningful fact from pattern match with SPO structure"""
        try:
            if hasattr(match, 'group'):
                # Python regex match
                matched_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                captured_group = match.group(1) if match.lastindex and match.lastindex >= 1 else matched_text
            else:
                # FLPC match (dict format)
                matched_text = match.get('text', '')
                start_pos = match.get('start', 0)
                end_pos = match.get('end', 0)
                captured_group = matched_text
            
            # Extract meaningful context (200 chars around match)
            context_start = max(0, start_pos - 100)
            context_end = min(len(text), end_pos + 100)
            context = text[context_start:context_end].strip()
            
            # Determine SPO structure based on category
            subject, predicate, obj = self._determine_spo_structure(
                matched_text, captured_group, category, context
            )
            
            # Calculate confidence based on pattern match quality and context
            confidence = self._calculate_fact_confidence(matched_text, context, category)
            
            if confidence >= self.min_confidence:
                return MeaningfulFact(
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    confidence=confidence,
                    fact_type=f"{category}_fact",
                    context=context,
                    span=(start_pos, end_pos),
                    actionable=self._is_actionable_fact(category, predicate)
                )
        
        except Exception as e:
            self.logger.logger.debug(f"Failed to create fact from match: {e}")
        
        return None
    
    def _determine_spo_structure(self, matched_text: str, captured_group: str, 
                                category: str, context: str) -> Tuple[str, str, str]:
        """Determine Subject-Predicate-Object structure for meaningful facts"""
        
        # Category-specific SPO extraction logic
        if category == 'safety_requirements':
            if 'must' in matched_text.lower() or 'required' in matched_text.lower():
                subject = self._extract_subject_from_context(context, ['employees', 'workers', 'personnel', 'staff'])
                predicate = 'MUST_COMPLY_WITH'
                obj = captured_group.strip()
                return subject or 'Personnel', predicate, obj
        
        elif category == 'compliance_requirements':
            if 'comply with' in matched_text.lower():
                subject = self._extract_subject_from_context(context, ['company', 'organization', 'facility'])
                predicate = 'MUST_COMPLY_WITH'
                obj = captured_group.strip()
                return subject or 'Organization', predicate, obj
        
        elif category == 'measurement_relationships':
            if any(word in matched_text.lower() for word in ['distance', 'height', 'limit', 'maximum', 'minimum']):
                subject = self._extract_measurement_subject(context)
                predicate = 'HAS_MEASUREMENT'
                obj = captured_group.strip()
                return subject, predicate, obj
        
        elif category == 'organizational_actions':
            if any(word in matched_text.lower() for word in ['provides', 'ensures', 'requires']):
                subject = self._extract_subject_from_context(context, ['company', 'employer', 'organization'])
                predicate = 'PROVIDES' if 'provides' in matched_text.lower() else 'ENSURES'
                obj = captured_group.strip()
                return subject or 'Organization', predicate, obj
        
        elif category == 'temporal_requirements':
            subject = self._extract_subject_from_context(context, ['deadline', 'requirement', 'task', 'inspection'])
            predicate = 'HAS_TIMEFRAME'
            obj = captured_group.strip()
            return subject or 'Requirement', predicate, obj
        
        # Fallback SPO structure
        return 'Entity', 'RELATES_TO', captured_group.strip()
    
    def _extract_subject_from_context(self, context: str, subject_keywords: List[str]) -> Optional[str]:
        """Extract meaningful subject from context using keyword matching"""
        context_lower = context.lower()
        
        for keyword in subject_keywords:
            # Look for keyword in context
            keyword_pos = context_lower.find(keyword)
            if keyword_pos >= 0:
                # Extract the full subject phrase (up to 50 chars)
                start = max(0, keyword_pos - 10)
                end = min(len(context), keyword_pos + len(keyword) + 30)
                subject_phrase = context[start:end].strip()
                
                # Clean up the subject phrase
                sentences = subject_phrase.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return sentence.strip()
        
        return None
    
    def _extract_measurement_subject(self, context: str) -> str:
        """Extract subject for measurement facts"""
        measurement_subjects = [
            'safety distance', 'height requirement', 'weight limit', 
            'temperature range', 'pressure limit', 'clearance distance',
            'minimum distance', 'maximum height', 'load capacity'
        ]
        
        context_lower = context.lower()
        for subject in measurement_subjects:
            if subject in context_lower:
                return subject.title()
        
        return 'Measurement Requirement'
    
    def _calculate_fact_confidence(self, matched_text: str, context: str, category: str) -> float:
        """Calculate confidence score for extracted fact"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for strong requirement language
        if any(word in matched_text.lower() for word in ['must', 'shall', 'required', 'mandatory']):
            confidence += 0.2
        
        # Boost confidence for specific regulatory references
        if any(word in matched_text.upper() for word in ['OSHA', 'ISO', 'ANSI', 'CFR', 'USC']):
            confidence += 0.15
        
        # Boost confidence for quantitative measurements
        if re.search(r'\\b\\d+(?:\\.\\d+)?\\s*[a-zA-Z]+\\b', matched_text):
            confidence += 0.1
        
        # Boost confidence for meaningful context length
        if len(context.strip()) >= self.min_context_length:
            confidence += 0.1
        
        # Penalty for very short matches
        if len(matched_text.strip()) < 10:
            confidence -= 0.1
        
        return min(1.0, confidence)
    
    def _is_actionable_fact(self, category: str, predicate: str) -> bool:
        """Determine if fact is actionable (requires specific action)"""
        actionable_categories = ['safety_requirements', 'compliance_requirements', 'temporal_requirements']
        actionable_predicates = ['MUST_COMPLY_WITH', 'PROVIDES', 'ENSURES', 'HAS_TIMEFRAME']
        
        return category in actionable_categories or predicate in actionable_predicates
    
    def _is_high_quality_fact(self, fact: MeaningfulFact) -> bool:
        """Filter for high-quality facts to avoid repetitive information"""
        
        # Confidence threshold
        if fact.confidence < self.min_confidence:
            return False
        
        # Context requirement
        if len(fact.context.strip()) < self.min_context_length:
            return False
        
        # Avoid overly short objects
        if len(fact.object.strip()) < 3:
            return False
        
        # Check for repetitive content
        fact_signature = f"{fact.subject}:{fact.predicate}:{fact.object}"
        if fact_signature in self.extracted_facts:
            return False
        
        self.extracted_facts.add(fact_signature)
        return True
    
    def _assemble_compound_facts(self, meaningful_facts: List[MeaningfulFact]) -> List[CompoundFact]:
        """Assemble related facts into compound facts for better information structure"""
        compound_facts = []
        
        # Group facts by similarity
        fact_groups = self._group_related_facts(meaningful_facts)
        
        for group_key, related_facts in fact_groups.items():
            if len(related_facts) >= 2:  # Only create compound facts for 2+ related facts
                primary_fact = max(related_facts, key=lambda f: f.confidence)
                other_facts = [f for f in related_facts if f != primary_fact]
                
                compound_fact = CompoundFact(
                    primary_fact=primary_fact,
                    related_facts=other_facts,
                    relationship_type=self._determine_relationship_type(related_facts),
                    confidence=sum(f.confidence for f in related_facts) / len(related_facts)
                )
                compound_facts.append(compound_fact)
        
        return compound_facts
    
    def _group_related_facts(self, facts: List[MeaningfulFact]) -> Dict[str, List[MeaningfulFact]]:
        """Group related facts by subject similarity and predicate type"""
        groups = defaultdict(list)
        
        for fact in facts:
            # Group by subject + predicate combination for related requirements
            group_key = f"{fact.subject.lower()}:{fact.predicate}"
            groups[group_key].append(fact)
        
        # Also group measurement facts by subject similarity
        measurement_groups = defaultdict(list)
        for fact in facts:
            if 'measurement' in fact.fact_type.lower():
                # Extract measurement type (distance, height, etc.)
                measurement_type = self._extract_measurement_type(fact.object)
                if measurement_type:
                    measurement_groups[measurement_type].append(fact)
        
        groups.update(measurement_groups)
        return groups
    
    def _extract_measurement_type(self, measurement_text: str) -> Optional[str]:
        """Extract measurement type for grouping (distance, height, weight, etc.)"""
        measurement_types = {
            'distance': ['meter', 'foot', 'yard', 'mile', 'km', 'm', 'ft'],
            'height': ['height', 'tall', 'high', 'elevation'],
            'weight': ['pound', 'kilogram', 'ton', 'kg', 'lb', 'weight'],
            'temperature': ['degree', 'celsius', 'fahrenheit', 'kelvin', '°C', '°F'],
            'time': ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']
        }
        
        measurement_lower = measurement_text.lower()
        for measure_type, keywords in measurement_types.items():
            if any(keyword in measurement_lower for keyword in keywords):
                return measure_type
        
        return None
    
    def _determine_relationship_type(self, related_facts: List[MeaningfulFact]) -> str:
        """Determine the type of relationship between related facts"""
        if len(related_facts) < 2:
            return 'single'
        
        # Check if all facts are measurements
        if all('measurement' in fact.fact_type.lower() for fact in related_facts):
            return 'measurement_series'
        
        # Check if all facts are requirements
        if all('requirement' in fact.fact_type.lower() for fact in related_facts):
            return 'requirement_chain'
        
        # Check if facts share the same subject
        subjects = set(fact.subject.lower() for fact in related_facts)
        if len(subjects) == 1:
            return 'subject_cluster'
        
        return 'related_facts'
    
    def _extract_actionable_requirements(self, text: str, domain_context: Dict) -> List[MeaningfulFact]:
        """Extract clear, actionable requirements with SPO structure"""
        actionable_facts = []
        
        # Strong requirement patterns for actionable extraction
        requirement_patterns = [
            r'(?:employees|workers|personnel|staff|individuals)\\s+(?:must|shall|are required to)\\s+([^.]{10,100})',
            r'(?:company|organization|employer|facility)\\s+(?:must|shall|will)\\s+(?:provide|ensure|maintain|implement)\\s+([^.]{10,100})',
            r'(?:all|any)\\s+(?:equipment|devices|systems|procedures)\\s+(?:must|shall)\\s+(?:be|meet|comply with)\\s+([^.]{10,100})',
            r'(?:before|after|within)\\s+([0-9]+\\s*(?:days?|hours?|weeks?|months?))\\s*,?\\s*([^.]{10,100})',
        ]
        
        for pattern in requirement_patterns:
            try:
                if self.flpc_engine:
                    matches = self.flpc_engine.find_all_matches(pattern, text)
                else:
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))
                
                for match in matches:
                    fact = self._create_actionable_requirement_from_match(match, text)
                    if fact and fact.confidence >= self.min_confidence:
                        fact.actionable = True  # Mark as actionable
                        actionable_facts.append(fact)
                        
            except Exception as e:
                self.logger.logger.debug(f"Actionable requirement extraction failed: {e}")
        
        return actionable_facts
    
    def _create_actionable_requirement_from_match(self, match, text: str) -> Optional[MeaningfulFact]:
        """Create actionable requirement fact from pattern match"""
        try:
            if hasattr(match, 'group'):
                matched_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                requirement_text = match.group(1) if match.lastindex and match.lastindex >= 1 else matched_text
            else:
                matched_text = match.get('text', '')
                start_pos = match.get('start', 0)
                end_pos = match.get('end', 0)
                requirement_text = matched_text
            
            # Extract context
            context_start = max(0, start_pos - 100)
            context_end = min(len(text), end_pos + 100)
            context = text[context_start:context_end].strip()
            
            # Determine SPO for actionable requirement
            if 'employees' in matched_text.lower() or 'workers' in matched_text.lower():
                subject = 'Personnel'
                predicate = 'REQUIRED_TO'
            elif 'company' in matched_text.lower() or 'organization' in matched_text.lower():
                subject = 'Organization'
                predicate = 'MUST_PROVIDE'
            elif any(word in matched_text.lower() for word in ['equipment', 'devices', 'systems']):
                subject = 'Equipment/Systems'
                predicate = 'MUST_COMPLY_WITH'
            else:
                subject = 'Entity'
                predicate = 'MUST_COMPLY_WITH'
            
            confidence = 0.8  # High confidence for explicit requirements
            if any(word in matched_text.lower() for word in ['must', 'shall', 'required']):
                confidence += 0.1
            
            return MeaningfulFact(
                subject=subject,
                predicate=predicate,
                object=requirement_text.strip(),
                confidence=min(1.0, confidence),
                fact_type='actionable_requirement',
                context=context,
                span=(start_pos, end_pos),
                actionable=True
            )
        
        except Exception as e:
            self.logger.logger.debug(f"Failed to create actionable requirement: {e}")
        
        return None
    
    def _filter_and_deduplicate_facts(self, all_facts: List) -> List:
        """Filter and deduplicate facts for final high-quality output"""
        # Convert compound facts to meaningful facts for consistent processing
        flattened_facts = []
        for fact in all_facts:
            if isinstance(fact, CompoundFact):
                # Use primary fact from compound fact
                flattened_facts.append(fact.primary_fact)
            elif isinstance(fact, MeaningfulFact):
                flattened_facts.append(fact)
        
        # Sort by confidence (highest first)
        sorted_facts = sorted(flattened_facts, key=lambda f: f.confidence, reverse=True)
        
        # Deduplicate by content similarity
        unique_facts = []
        seen_objects = set()
        
        for fact in sorted_facts:
            # Create similarity signature
            obj_words = set(fact.object.lower().split())
            
            # Check for significant overlap with existing facts
            is_duplicate = False
            for seen_obj in seen_objects:
                seen_words = set(seen_obj.split())
                if len(obj_words & seen_words) / max(len(obj_words), len(seen_words)) > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_facts.append(fact)
                seen_objects.add(fact.object.lower())
                
                # Limit total facts to avoid overwhelming output
                if len(unique_facts) >= 50:
                    break
        
        return unique_facts
    
    def _structure_intelligent_results(self, final_facts: List[MeaningfulFact], 
                                     domain_context: Dict) -> Dict[str, Any]:
        """Structure intelligent extraction results for semantic analysis output"""
        # Group facts by type
        structured_facts = {
            'actionable_requirements': [],
            'compliance_facts': [], 
            'measurement_facts': [],
            'organizational_facts': [],
            'temporal_facts': [],
            'spo_triplets': []
        }
        
        for fact in final_facts:
            # Create structured fact representation
            structured_fact = {
                'subject': fact.subject,
                'predicate': fact.predicate,
                'object': fact.object,
                'confidence': fact.confidence,
                'fact_type': fact.fact_type,
                'context': fact.context[:200] + '...' if len(fact.context) > 200 else fact.context,
                'span': {'start': fact.span[0], 'end': fact.span[1]},
                'actionable': fact.actionable,
                'extraction_layer': 'intelligent_spo_analysis'
            }
            
            # Categorize fact
            if fact.actionable:
                structured_facts['actionable_requirements'].append(structured_fact)
            elif 'compliance' in fact.fact_type.lower():
                structured_facts['compliance_facts'].append(structured_fact)
            elif 'measurement' in fact.fact_type.lower():
                structured_facts['measurement_facts'].append(structured_fact)
            elif 'organizational' in fact.fact_type.lower():
                structured_facts['organizational_facts'].append(structured_fact)
            elif 'temporal' in fact.fact_type.lower():
                structured_facts['temporal_facts'].append(structured_fact)
            
            # Add to SPO triplets
            structured_facts['spo_triplets'].append({
                'subject': fact.subject,
                'predicate': fact.predicate,
                'object': fact.object,
                'confidence': fact.confidence
            })
        
        # Create semantic summary
        total_facts = len(final_facts)
        fact_types = {k: len(v) for k, v in structured_facts.items() if isinstance(v, list) and v}
        
        return {
            'semantic_facts': structured_facts,
            'semantic_summary': {
                'total_facts': total_facts,
                'fact_types': fact_types,
                'extraction_engine': 'Intelligent SPO Hybrid with Relationship Focus',
                'performance_model': 'Quality-over-Quantity Extraction',
                'domain_context': domain_context['primary_domain'],
                'actionable_facts': len(structured_facts['actionable_requirements']),
                'quality_threshold': self.min_confidence
            }
        }

# Factory function for easy integration  
def create_intelligent_spo_extractor(*args, **kwargs) -> IntelligentSPOFactExtractor:
    """Create intelligent SPO fact extractor focused on meaningful knowledge"""
    return IntelligentSPOFactExtractor(*args, **kwargs)