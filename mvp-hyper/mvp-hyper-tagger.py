#!/usr/bin/env python3
"""
MVP Hyper Document Tagger
==========================
Sidecar document tagging system for MVP Hyper-Core.
Adds intelligent metadata and classification to processed documents.

This runs alongside MVP Hyper-Core without affecting its performance.
Enable with --enable-tagging flag or ENABLE_TAGGING environment variable.
"""

import re
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
import hashlib
import collections


class DocumentType(Enum):
    """Simplified document type classifications for speed."""
    TECHNICAL = "technical"
    BUSINESS = "business"
    LEGAL = "legal"
    SAFETY = "safety"
    RESEARCH = "research"
    FINANCIAL = "financial"
    GENERAL = "general"
    CODE = "code"
    DATA = "data"


class DocumentDomain(Enum):
    """Document domain classifications."""
    ENGINEERING = "engineering"
    COMPLIANCE = "compliance"
    FINANCE = "finance"
    LEGAL = "legal"
    MEDICAL = "medical"
    IT = "it"
    HR = "hr"
    SAFETY = "safety"
    GENERAL = "general"


@dataclass
class DocumentTags:
    """Document metadata and tags."""
    document_types: List[str]  # Top 3 types with percentages
    domains: List[str]         # Top 3 domains with percentages
    keywords: List[str]
    entities: List[str]
    topics: List[str]
    language: str
    confidence: float
    word_count: int
    unique_terms: int
    technical_score: float
    timestamp: str
    file_hash: str
    processing_time: float
    # Enhanced extraction fields for better fact extraction
    measurements: Optional[Dict[str, List[str]]] = None
    time_references: Optional[Dict[str, List[str]]] = None
    regulatory_framework: Optional[Dict[str, List[str]]] = None
    logical_structures: Optional[Dict[str, List[str]]] = None
    priority_fact_spans: Optional[List[Dict]] = None
    stakeholder_roles: Optional[List[str]] = None
    
    # Universal Business Intelligence Entities for Opportunity Discovery
    universal_entities: Optional[Dict[str, List[str]]] = None
    pain_points: Optional[List[str]] = None
    market_opportunities: Optional[List[str]] = None
    innovation_signals: Optional[List[str]] = None
    competitive_intelligence: Optional[List[str]] = None


class MVPHyperTagger:
    """Ultra-fast document tagger optimized for MVP Hyper-Core."""
    
    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self.tag_cache = {}
        
        # Pre-compiled patterns for speed (original classification patterns)
        self.patterns = {
            'technical': re.compile(r'\b(algorithm|function|method|system|process|implementation|architecture|framework|protocol|specification|requirement|design|analysis|optimization|performance|configuration|parameter|variable|interface|component|module|class|object|structure|database|network|security|encryption|authentication)\b', re.I),
            'legal': re.compile(r'\b(shall|whereas|hereby|agreement|contract|terms|conditions|liability|indemnify|warranty|copyright|patent|trademark|confidential|proprietary|jurisdiction|governing law|dispute|arbitration|clause|provision|party|parties|obligation|breach|remedy|damages)\b', re.I),
            'safety': re.compile(r'\b(safety|hazard|risk|danger|warning|caution|emergency|accident|injury|protection|ppe|personal protective equipment|osha|compliance|regulation|standard|procedure|inspection|audit|incident|report|training|certification|violation|penalty)\b', re.I),
            'financial': re.compile(r'\b(revenue|profit|loss|asset|liability|equity|balance sheet|income statement|cash flow|budget|forecast|investment|return|roi|expense|cost|price|tax|audit|compliance|gaap|ifrs|depreciation|amortization|dividend|earnings)\b', re.I),
            'research': re.compile(r'\b(study|research|hypothesis|methodology|results|conclusion|abstract|introduction|literature review|discussion|findings|analysis|data|sample|population|statistical|significant|correlation|experiment|observation|theory|model|framework)\b', re.I),
            'code': re.compile(r'\b(def |class |function|import |from |return|if |else|for |while|try|except|async|await|const |let |var |public |private |static|void|int |string|bool|package|module|namespace)\b', re.I),
        }
        
        # Enhanced extraction patterns for fact-focused tagging
        self.enhanced_patterns = {
            # Quantitative measurements
            'measurements': {
                'heights': re.compile(r'(\d+(?:\.\d+)?)\s*(?:feet|ft|foot|meters?|m)\s+(?:high|tall|above|in height)', re.I),
                'depths': re.compile(r'(\d+(?:\.\d+)?)\s*(?:feet|ft|foot|meters?|m)\s+(?:deep|below|in depth)', re.I),
                'weights': re.compile(r'(\d+(?:\.\d+)?)\s*(?:pounds?|lbs?|kilograms?|kg|tons?)\s*(?:capacity|maximum|limit|weight)?', re.I),
                'distances': re.compile(r'(\d+(?:\.\d+)?)\s*(?:feet|ft|inches|in|meters?|m|yards?|yd)\s+(?:apart|away|from|between)', re.I),
                'money': re.compile(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|thousand|M|B|K)?\s*(?:fine|penalty|cost|fee|charge)?', re.I),
                'percentages': re.compile(r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s*(?:increase|decrease|change|of|or|more|less)?', re.I),
                'counts': re.compile(r'(\d+)\s+(?:or\s+)?(?:more|less)\s+(?:employees?|workers?|people|persons?|individuals?)', re.I)
            },
            
            # Temporal references
            'time_references': {
                'dates': re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', re.I),
                'frequencies': re.compile(r'\b(?:daily|weekly|monthly|quarterly|annually|every\s+\d+\s+(?:days?|weeks?|months?|years?))\b', re.I),
                'durations': re.compile(r'\b(?:within|for|during|lasting|over)\s+(\d+)\s*(?:minutes?|hours?|days?|weeks?|months?|years?)\b', re.I),
                'deadlines': re.compile(r'\b(?:by|before|no later than|immediately|as soon as|within)\s+([^,;.]{5,30})', re.I)
            },
            
            # Regulatory framework
            'regulatory': {
                'citations': re.compile(r'\b(?:29\s+CFR|CFR)\s*\d{3,4}(?:\.\d+)*[a-z]?\b', re.I),
                'standards': re.compile(r'\b(?:OSHA|ANSI|NFPA|ASTM|ISO)\s*\d{2,5}(?:[-.]?\d+)*\b', re.I),
                'parts': re.compile(r'\b(?:Part|Subpart|Section)\s+\d{3,4}(?:\.\d+)*[A-Z]?\b', re.I),
                'compliance_terms': re.compile(r'\b(shall|must|required|mandatory|prohibited|not permitted|may not|forbidden)\b', re.I),
                'enforcement': re.compile(r'\b(violation|citation|penalty|fine|warning|notice|compliance|inspection)\b', re.I)
            },
            
            # Logical structures  
            'logical': {
                'conditions': re.compile(r'\b(when|if|where|unless|except|provided that|in cases where)\s+([^,;.]{10,80})', re.I),
                'exceptions': re.compile(r'\b(except for|excluding|does not apply to|not applicable to|other than)\s+([^,;.]{5,50})', re.I),
                'requirements': re.compile(r'\b(employer|employee|worker|person|contractor)s?\s+(?:shall|must|are required to)\s+([^,;.]{10,100})', re.I),
                'scope': re.compile(r'\b(applicable to|applies to|covers|includes|extends to|limited to)\s+([^,;.]{5,60})', re.I)
            },
            
            # Stakeholder roles
            'stakeholders': re.compile(r'\b(employer|employee|worker|contractor|subcontractor|competent person|qualified person|authorized person|safety officer|supervisor|foreman|manager|inspector|auditor)\b', re.I),
            
            # Universal Business Intelligence Entity Patterns for Opportunity Discovery
            'business_intelligence': {
                # Universal entity types for structured classification
                'persons': re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s+(?:said|stated|reported|announced|founded|CEO|CTO|president|director|manager|researcher|scientist|professor|Dr\.|Ph\.D\.)', re.I),
                'organizations': re.compile(r'\b([A-Z][A-Za-z&\s]+(?:Inc\.|LLC|Corp\.|Company|Corporation|Ltd\.|University|Institute|Foundation|Agency|Department|Bureau|Commission))\b', re.I),
                'emails': re.compile(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'),
                'urls': re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?', re.I),
                'locations': re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*),?\s+(?:[A-Z]{2}|California|Texas|New York|Florida|Washington|Oregon|Illinois|Pennsylvania|Ohio|Michigan|Georgia|North Carolina)\b', re.I),
                'phone_numbers': re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
                
                # Pain points and market gaps
                'pain_points': re.compile(r'\b(?:struggle(?:s|d)?|difficult(?:y|ies)?|challenge(?:s|d)?|problem(?:s)?|issue(?:s)?|bottleneck(?:s)?|barrier(?:s)?|obstacle(?:s)?|limitation(?:s)?|constraint(?:s)?|frustrat(?:e|ed|ing)|inefficient|expensive|time-consuming|costly|manual|labor-intensive)\s+(?:with|in|to|for|at|when|while|during)\s+([^,.;]{10,80})', re.I),
                
                # Market opportunities and sizing
                'market_opportunities': re.compile(r'\b(?:market|opportunity|demand|need|gap|potential|growth|expansion|emerging|trend|opportunity|untapped|underserved)\s+(?:for|in|to|worth|valued|estimated|projected|expected)\s+([^,.;]{10,80})', re.I),
                'market_sizing': re.compile(r'\b(?:\$\d+(?:\.\d+)?\s*(?:million|billion|trillion|M|B|T)|market\s+size|addressable\s+market|tam|sam|som)\s+(?:market|opportunity|industry|sector|segment)?', re.I),
                
                # Innovation signals and technology advancement
                'innovation_signals': re.compile(r'\b(?:breakthrough|innovation|advance(?:d|ment)?|novel|new|emerging|cutting-edge|state-of-the-art|revolutionary|disruptive|patent(?:ed)?|proprietary|technology|solution|approach|method|technique)\s+(?:in|for|to|that|which|using)\s+([^,.;]{10,80})', re.I),
                'funding_signals': re.compile(r'\b(?:raised|funding|investment|venture|capital|series|round|IPO|acquisition|merger|valuation)\s+(?:of\s+)?\$\d+(?:\.\d+)?\s*(?:million|billion|M|B)', re.I),
                
                # Competitive intelligence
                'competitive_intel': re.compile(r'\b(?:competitor(?:s)?|rival(?:s)?|alternative(?:s)?|compared\s+to|versus|vs\.?|market\s+leader(?:s)?|dominant\s+player(?:s)?|key\s+player(?:s)?)\s+([^,.;]{10,80})', re.I),
                'partnerships': re.compile(r'\b(?:partner(?:ship)?|collaborat(?:e|ion)|alliance|joint\s+venture|strategic|agreement)\s+(?:with|between)\s+([A-Z][A-Za-z\s&]+(?:Inc\.|LLC|Corp\.|Company|Corporation|Ltd\.)?)', re.I)
            }
        }
        
        # Common stop words for keyword extraction
        self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                               'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were',
                               'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                               'will', 'would', 'could', 'should', 'may', 'might', 'must',
                               'can', 'shall', 'this', 'that', 'these', 'those', 'i', 'you',
                               'he', 'she', 'it', 'we', 'they', 'them', 'their', 'what',
                               'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
                               'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
                               'no', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'])
    
    def tag_document(self, file_path: Path, content: str, metadata: Optional[Dict] = None) -> DocumentTags:
        """Tag a document with metadata and classifications."""
        
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(file_path, content)
        if self.cache_enabled and cache_key in self.tag_cache:
            cached = self.tag_cache[cache_key]
            cached.processing_time = 0.0  # Cached result
            return cached
        
        # Basic text analysis
        words = content.lower().split()
        word_count = len(words)
        unique_terms = len(set(words))
        
        # Document type classification
        doc_types, confidence = self._classify_document_type(content, file_path)
        
        # Domain classification
        domains = self._classify_domain(content)
        
        # Keyword extraction (fast method)
        keywords = self._extract_keywords_fast(content, max_keywords=15)
        
        # Entity extraction (simple pattern matching)
        entities = self._extract_entities_simple(content)
        
        # Topic extraction - use the primary document type
        primary_type_name = doc_types[0].split(':')[0] if doc_types else 'general'
        primary_type = getattr(DocumentType, primary_type_name.upper(), DocumentType.GENERAL)
        topics = self._extract_topics(content, primary_type)
        
        # Technical score
        technical_score = self._calculate_technical_score(content)
        
        # Enhanced extraction for better fact targeting
        enhanced_data = self._extract_enhanced_metadata(content)
        
        # Create tags
        tags = DocumentTags(
            document_types=doc_types,
            domains=domains,
            keywords=keywords,
            entities=entities,
            topics=topics,
            language='en',  # Simplified - assume English
            confidence=confidence,
            word_count=word_count,
            unique_terms=unique_terms,
            technical_score=technical_score,
            timestamp=datetime.now(timezone.utc).isoformat(),
            file_hash=cache_key[:16],  # First 16 chars of hash
            processing_time=time.time() - start_time,
            # Enhanced fields
            measurements=enhanced_data.get('measurements'),
            time_references=enhanced_data.get('time_references'),
            regulatory_framework=enhanced_data.get('regulatory_framework'),
            logical_structures=enhanced_data.get('logical_structures'),
            priority_fact_spans=enhanced_data.get('priority_fact_spans'),
            stakeholder_roles=enhanced_data.get('stakeholder_roles'),
            # Universal Business Intelligence fields
            universal_entities=enhanced_data.get('universal_entities'),
            pain_points=enhanced_data.get('pain_points'),
            market_opportunities=enhanced_data.get('market_opportunities'),
            innovation_signals=enhanced_data.get('innovation_signals'),
            competitive_intelligence=enhanced_data.get('competitive_intelligence')
        )
        
        # Cache result
        if self.cache_enabled:
            self.tag_cache[cache_key] = tags
        
        return tags
    
    def _generate_cache_key(self, file_path: Path, content: str) -> str:
        """Generate cache key for document."""
        key_string = f"{file_path.name}:{len(content)}:{content[:1000]}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _classify_document_type(self, content: str, file_path: Path) -> Tuple[List[str], float]:
        """Classify document type based on content and patterns - returns top 3 matches with percentages."""
        
        scores = {}
        content_lower = content.lower()
        
        # Check file extension hints for strong matches
        ext = file_path.suffix.lower()
        if ext in ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs']:
            return [f"{DocumentType.CODE.value}: 95%"], 0.95
        elif ext in ['.csv', '.json', '.xml', '.sql']:
            return [f"{DocumentType.DATA.value}: 95%"], 0.95
        
        # Pattern matching for classification
        for doc_type, pattern in [
            (DocumentType.TECHNICAL, self.patterns['technical']),
            (DocumentType.LEGAL, self.patterns['legal']),
            (DocumentType.SAFETY, self.patterns['safety']),
            (DocumentType.FINANCIAL, self.patterns['financial']),
            (DocumentType.RESEARCH, self.patterns['research']),
        ]:
            matches = len(pattern.findall(content))
            scores[doc_type] = matches
        
        # Business indicators
        business_terms = ['business', 'company', 'corporate', 'strategy', 'market', 'customer', 'product', 'service']
        business_score = sum(1 for term in business_terms if term in content_lower)
        scores[DocumentType.BUSINESS] = business_score * 5
        
        # Always include GENERAL as a baseline
        scores[DocumentType.GENERAL] = 1
        
        # Calculate percentages and get top 3
        total_score = sum(scores.values())
        if total_score > 0:
            # Sort by score and get top 3
            sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Convert to percentage strings
            type_percentages = []
            for doc_type, score in sorted_types:
                percentage = (score / total_score) * 100
                type_percentages.append(f"{doc_type.value}: {percentage:.0f}%")
            
            # Calculate overall confidence based on score distribution
            max_score = sorted_types[0][1]
            confidence = max_score / total_score if total_score > 0 else 0.5
            
            if max_score > 10:
                confidence = min(confidence + 0.3, 0.95)
            elif max_score > 5:
                confidence = min(confidence + 0.2, 0.85)
            
            return type_percentages, confidence
        
        return [f"{DocumentType.GENERAL.value}: 100%"], 0.5
    
    def _classify_domain(self, content: str) -> List[str]:
        """Classify document domain - returns top 3 matches with percentages."""
        
        content_lower = content.lower()
        scores = {}
        
        # Domain indicators with scoring
        domain_keywords = {
            DocumentDomain.SAFETY: ['osha', 'safety', 'hazard', 'ppe', 'accident', 'incident', 'emergency', 'protection', 'risk'],
            DocumentDomain.COMPLIANCE: ['compliance', 'regulation', 'audit', 'violation', 'standard', 'requirement', 'policy'],
            DocumentDomain.FINANCE: ['financial', 'accounting', 'revenue', 'budget', 'profit', 'cost', 'expense', 'investment'],
            DocumentDomain.LEGAL: ['legal', 'law', 'contract', 'agreement', 'liability', 'jurisdiction', 'clause'],
            DocumentDomain.MEDICAL: ['medical', 'health', 'patient', 'clinical', 'diagnosis', 'treatment', 'healthcare'],
            DocumentDomain.IT: ['software', 'code', 'programming', 'database', 'network', 'system', 'technology'],
            DocumentDomain.ENGINEERING: ['engineering', 'design', 'specification', 'technical', 'construction', 'architecture'],
            DocumentDomain.HR: ['employee', 'hr', 'human resources', 'recruitment', 'benefits', 'personnel', 'workforce']
        }
        
        # Score each domain based on keyword matches
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            scores[domain] = score
        
        # Always include GENERAL as a baseline
        scores[DocumentDomain.GENERAL] = 1
        
        # Calculate percentages and get top 3
        total_score = sum(scores.values())
        if total_score > 0:
            # Sort by score and get top 3
            sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Convert to percentage strings
            domain_percentages = []
            for domain, score in sorted_domains:
                percentage = (score / total_score) * 100
                domain_percentages.append(f"{domain.value}: {percentage:.0f}%")
            
            return domain_percentages
        
        return [f"{DocumentDomain.GENERAL.value}: 100%"]
    
    def _extract_keywords_fast(self, content: str, max_keywords: int = 15) -> List[str]:
        """Extract keywords using fast frequency-based method."""
        
        # Tokenize and clean
        words = re.findall(r'\b[a-z]+\b', content.lower())
        
        # Filter stop words and short words
        meaningful_words = [w for w in words if w not in self.stop_words and len(w) > 3]
        
        # Count frequencies
        word_freq = collections.Counter(meaningful_words)
        
        # Get top keywords
        keywords = []
        for word, freq in word_freq.most_common(max_keywords):
            if freq > 2:  # Word appears at least 3 times
                keywords.append(word)
        
        return keywords
    
    def _extract_entities_simple(self, content: str) -> List[str]:
        """Extract entities using simple pattern matching."""
        
        entities = []
        
        # Extract potential organization names (capitalized multi-word sequences)
        org_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
        orgs = org_pattern.findall(content)
        entities.extend(orgs[:5])  # Top 5 organizations
        
        # Extract potential acronyms
        acronym_pattern = re.compile(r'\b([A-Z]{2,})\b')
        acronyms = acronym_pattern.findall(content)
        entities.extend(acronyms[:5])  # Top 5 acronyms
        
        # Extract emails
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        emails = email_pattern.findall(content)
        entities.extend(emails[:3])  # Top 3 emails
        
        # Extract potential dates
        date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
        dates = date_pattern.findall(content)
        entities.extend(dates[:3])  # Top 3 dates
        
        return list(set(entities))  # Remove duplicates
    
    def _extract_topics(self, content: str, doc_type: DocumentType) -> List[str]:
        """Extract document topics based on type."""
        
        topics = []
        content_lower = content.lower()
        
        # Type-specific topics
        if doc_type == DocumentType.SAFETY:
            safety_topics = ['workplace safety', 'hazard control', 'ppe requirements', 'emergency procedures',
                           'incident reporting', 'safety training', 'risk assessment', 'compliance']
            topics = [t for t in safety_topics if any(word in content_lower for word in t.split())]
        
        elif doc_type == DocumentType.TECHNICAL:
            tech_topics = ['system architecture', 'implementation', 'requirements', 'specifications',
                          'performance', 'security', 'testing', 'deployment']
            topics = [t for t in tech_topics if any(word in content_lower for word in t.split())]
        
        elif doc_type == DocumentType.FINANCIAL:
            fin_topics = ['financial analysis', 'budgeting', 'revenue', 'cost analysis',
                         'investment', 'accounting', 'audit', 'compliance']
            topics = [t for t in fin_topics if any(word in content_lower for word in t.split())]
        
        # General topics if none found
        if not topics:
            if 'training' in content_lower:
                topics.append('training')
            if 'compliance' in content_lower:
                topics.append('compliance')
            if 'report' in content_lower:
                topics.append('reporting')
            if 'analysis' in content_lower:
                topics.append('analysis')
        
        return topics[:5]  # Max 5 topics
    
    def _calculate_technical_score(self, content: str) -> float:
        """Calculate technical complexity score (0-1)."""
        
        technical_matches = len(self.patterns['technical'].findall(content))
        code_matches = len(self.patterns['code'].findall(content))
        
        # Count numbers and special characters (technical indicators)
        numbers = len(re.findall(r'\b\d+\b', content))
        special_chars = len(re.findall(r'[(){}[\]<>=/\\|@#$%^&*]', content))
        
        # Calculate score
        word_count = len(content.split())
        if word_count == 0:
            return 0.0
        
        tech_density = (technical_matches + code_matches * 2) / word_count
        number_density = numbers / word_count
        special_density = special_chars / word_count
        
        score = min(1.0, tech_density * 10 + number_density * 5 + special_density * 2)
        return round(score, 2)
    
    def _extract_enhanced_metadata(self, content: str) -> Dict[str, Any]:
        """Extract enhanced metadata for better fact targeting."""
        enhanced_data = {
            'measurements': {},
            'time_references': {},
            'regulatory_framework': {},
            'logical_structures': {},
            'priority_fact_spans': [],
            'stakeholder_roles': [],
            # Universal Business Intelligence fields
            'universal_entities': {},
            'pain_points': [],
            'market_opportunities': [],
            'innovation_signals': [],
            'competitive_intelligence': []
        }
        
        # Extract measurements
        measurements = {}
        for measure_type, pattern in self.enhanced_patterns['measurements'].items():
            matches = []
            for match in pattern.finditer(content):
                if measure_type in ['money', 'percentages']:
                    matches.append(match.group(0))
                else:
                    matches.append(f"{match.group(1)} {measure_type[:-1]}")  # Remove 's' from type
            if matches:
                measurements[measure_type] = matches[:5]  # Limit to top 5
        enhanced_data['measurements'] = measurements if measurements else None
        
        # Extract time references
        time_refs = {}
        for time_type, pattern in self.enhanced_patterns['time_references'].items():
            matches = [match.group(0) for match in pattern.finditer(content)]
            if matches:
                time_refs[time_type] = matches[:5]
        enhanced_data['time_references'] = time_refs if time_refs else None
        
        # Extract regulatory framework
        regulatory = {}
        for reg_type, pattern in self.enhanced_patterns['regulatory'].items():
            matches = [match.group(0) for match in pattern.finditer(content)]
            if matches:
                regulatory[reg_type] = list(set(matches))[:5]  # Unique matches
        enhanced_data['regulatory_framework'] = regulatory if regulatory else None
        
        # Extract logical structures
        logical = {}
        for logic_type, pattern in self.enhanced_patterns['logical'].items():
            matches = []
            for match in pattern.finditer(content):
                if match.lastindex >= 2:
                    matches.append(f"{match.group(1)} {match.group(2)}")
                else:
                    matches.append(match.group(0))
            if matches:
                logical[logic_type] = matches[:5]
        enhanced_data['logical_structures'] = logical if logical else None
        
        # Extract stakeholder roles
        stakeholders = []
        for match in self.enhanced_patterns['stakeholders'].finditer(content):
            stakeholders.append(match.group(1))
        if stakeholders:
            # Get unique stakeholders
            unique_stakeholders = list(set([s.lower() for s in stakeholders]))
            enhanced_data['stakeholder_roles'] = unique_stakeholders[:10]
        else:
            enhanced_data['stakeholder_roles'] = None
        
        # Identify priority fact spans (high-value locations for fact extraction)
        priority_spans = self._identify_priority_fact_spans(content)
        enhanced_data['priority_fact_spans'] = priority_spans if priority_spans else None
        
        # Extract Universal Business Intelligence entities for opportunity discovery
        bi_patterns = self.enhanced_patterns['business_intelligence']
        
        # Universal entities (structured entity classification)
        universal_entities = {}
        for entity_type, pattern in bi_patterns.items():
            if entity_type in ['persons', 'organizations', 'emails', 'urls', 'locations', 'phone_numbers']:
                matches = []
                for match in pattern.finditer(content):
                    if match.lastindex and match.lastindex >= 1:
                        matches.append(match.group(1))
                    else:
                        matches.append(match.group(0))
                if matches:
                    # Remove duplicates and limit results
                    unique_matches = list(set(matches))[:10]
                    universal_entities[entity_type] = unique_matches
        enhanced_data['universal_entities'] = universal_entities if universal_entities else None
        
        # Pain points extraction
        pain_points = []
        for match in bi_patterns['pain_points'].finditer(content):
            if match.lastindex >= 1:
                pain_points.append(match.group(1).strip())
        enhanced_data['pain_points'] = list(set(pain_points))[:10] if pain_points else None
        
        # Market opportunities extraction
        market_opps = []
        for match in bi_patterns['market_opportunities'].finditer(content):
            if match.lastindex >= 1:
                market_opps.append(match.group(1).strip())
        # Also capture market sizing opportunities
        for match in bi_patterns['market_sizing'].finditer(content):
            market_opps.append(match.group(0))
        enhanced_data['market_opportunities'] = list(set(market_opps))[:10] if market_opps else None
        
        # Innovation signals extraction
        innovation_signals = []
        for match in bi_patterns['innovation_signals'].finditer(content):
            if match.lastindex >= 1:
                innovation_signals.append(match.group(1).strip())
        # Also capture funding signals as innovation indicators
        for match in bi_patterns['funding_signals'].finditer(content):
            innovation_signals.append(match.group(0))
        enhanced_data['innovation_signals'] = list(set(innovation_signals))[:10] if innovation_signals else None
        
        # Competitive intelligence extraction
        competitive_intel = []
        for match in bi_patterns['competitive_intel'].finditer(content):
            if match.lastindex >= 1:
                competitive_intel.append(match.group(1).strip())
        # Also capture partnerships as competitive indicators
        for match in bi_patterns['partnerships'].finditer(content):
            if match.lastindex >= 1:
                competitive_intel.append(f"Partnership: {match.group(1)}")
        enhanced_data['competitive_intelligence'] = list(set(competitive_intel))[:10] if competitive_intel else None
        
        return enhanced_data
    
    def _identify_priority_fact_spans(self, content: str) -> List[Dict]:
        """Identify high-value spans likely to contain important facts."""
        priority_spans = []
        
        # Look for requirement patterns with measurements
        requirement_pattern = re.compile(r'\b(employer|employee|worker)s?\s+(?:shall|must)\s+([^.;]{20,150})', re.I)
        for match in requirement_pattern.finditer(content):
            # Check if this span contains measurements or regulations
            span_text = match.group(0)
            has_measurement = any(pattern.search(span_text) 
                                for pattern in self.enhanced_patterns['measurements'].values())
            has_regulation = any(pattern.search(span_text)
                               for pattern in self.enhanced_patterns['regulatory'].values())
            
            if has_measurement or has_regulation:
                priority_spans.append({
                    'type': 'high_value_requirement',
                    'span': [match.start(), match.end()],
                    'preview': span_text[:80] + '...' if len(span_text) > 80 else span_text,
                    'contains_measurement': has_measurement,
                    'contains_regulation': has_regulation
                })
        
        # Look for regulation + measurement combinations
        regulation_measure_pattern = re.compile(r'(?:OSHA|CFR|Part\s+\d+)[^.;]{0,50}(\d+(?:\.\d+)?)\s*(?:feet|pounds|percent|employees)', re.I)
        for match in regulation_measure_pattern.finditer(content):
            priority_spans.append({
                'type': 'regulation_with_measurement',
                'span': [match.start(), match.end()],
                'preview': match.group(0)
            })
        
        return priority_spans[:10]  # Limit to top 10 priority spans
    
    def format_tags_as_markdown(self, tags: DocumentTags) -> str:
        """Format tags as markdown header."""
        
        header = "---\n"
        header += f"document_types: [{', '.join(tags.document_types)}]\n"
        header += f"domains: [{', '.join(tags.domains)}]\n"
        header += f"keywords: {', '.join(tags.keywords[:10])}\n"
        
        if tags.entities:
            header += f"entities: {', '.join(tags.entities[:5])}\n"
        
        if tags.topics:
            header += f"topics: {', '.join(tags.topics)}\n"
        
        # Enhanced metadata fields
        if tags.measurements:
            header += "measurements:\n"
            for measure_type, values in tags.measurements.items():
                header += f"  {measure_type}: [{', '.join(values)}]\n"
        
        if tags.time_references:
            header += "time_references:\n"
            for time_type, values in tags.time_references.items():
                header += f"  {time_type}: [{', '.join(values)}]\n"
        
        if tags.regulatory_framework:
            header += "regulatory_framework:\n"
            for reg_type, values in tags.regulatory_framework.items():
                header += f"  {reg_type}: [{', '.join(values)}]\n"
        
        if tags.logical_structures:
            header += "logical_structures:\n"
            for logic_type, values in tags.logical_structures.items():
                header += f"  {logic_type}: [{', '.join(values[:3])}]\n"  # Limit display to 3 items
        
        if tags.stakeholder_roles:
            header += f"stakeholder_roles: [{', '.join(tags.stakeholder_roles)}]\n"
        
        if tags.priority_fact_spans:
            header += f"priority_fact_spans: {len(tags.priority_fact_spans)} high-value spans identified\n"
        
        header += f"technical_score: {tags.technical_score}\n"
        header += f"confidence: {tags.confidence:.2f}\n"
        header += f"word_count: {tags.word_count}\n"
        header += f"unique_terms: {tags.unique_terms}\n"
        header += f"language: {tags.language}\n"
        header += f"timestamp: {tags.timestamp}\n"
        header += f"file_hash: {tags.file_hash}\n"
        header += f"tagging_time: {tags.processing_time:.3f}s\n"
        header += "---\n\n"
        
        return header
    
    def add_tags_to_markdown(self, markdown_path: Path, tags: DocumentTags, overwrite: bool = False):
        """Add tags to existing markdown file."""
        
        if not markdown_path.exists():
            return False
        
        content = markdown_path.read_text(encoding='utf-8')
        
        # Check if already has tags
        if content.startswith('---\n') and not overwrite:
            return False
        
        # Remove existing front matter if present
        if content.startswith('---\n'):
            try:
                end_index = content.index('---\n', 4) + 4
                content = content[end_index:]
            except ValueError:
                pass
        
        # Add new tags
        tagged_content = self.format_tags_as_markdown(tags) + content
        markdown_path.write_text(tagged_content, encoding='utf-8')
        
        return True


def tag_output_directory(input_dir: Path, output_dir: Path = None, 
                         file_pattern: str = "*.md", overwrite: bool = True):
    """Tag all markdown files in a directory."""
    
    if output_dir is None:
        output_dir = input_dir
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tagger = MVPHyperTagger(cache_enabled=True)
    
    files = list(input_dir.glob(file_pattern))
    total_files = len(files)
    
    print(f"🏷️  Tagging {total_files} files...")
    
    success_count = 0
    total_time = 0
    total_pages_tagged = 0
    
    for i, file_path in enumerate(files, 1):
        try:
            # Read content
            content = file_path.read_text(encoding='utf-8')
            
            # Tag document
            tags = tagger.tag_document(file_path, content)
            total_time += tags.processing_time
            total_pages_tagged += tags.word_count // 250 or 1  # Estimate pages (250 words/page)
            
            # Output path
            if output_dir != input_dir:
                output_path = output_dir / file_path.name
                # Copy file first
                output_path.write_text(content, encoding='utf-8')
            else:
                output_path = file_path
            
            # Add tags
            if tagger.add_tags_to_markdown(output_path, tags, overwrite):
                success_count += 1
            
            # Progress
            if i % 50 == 0:
                print(f"  [{i}/{total_files}] Tagged {file_path.name}")
        
        except Exception as e:
            print(f"  ❌ Error tagging {file_path.name}: {e}")
    
    # Calculate tagging throughput
    tagging_pages_per_sec = total_pages_tagged / total_time if total_time > 0 else 0
    
    print(f"\n✅ Tagged {success_count}/{total_files} files in {total_time:.2f}s")
    print(f"⚡ Average: {total_time/total_files*1000:.1f}ms per file") 
    print(f"📊 Tagging: {tagging_pages_per_sec:.1f} pages/sec")
    
    return success_count


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mvp-hyper-tagger.py <input_dir> [output_dir]")
        print("Example: python mvp-hyper-tagger.py output/ tagged_output/")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        sys.exit(1)
    
    tag_output_directory(input_dir, output_dir)