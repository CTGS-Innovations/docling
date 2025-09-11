#!/usr/bin/env python3
"""
Universal Document Tagging System
=================================

NLP-powered document classification and semantic tagging for all document types.
Creates searchable metadata headers for enterprise document intelligence.

Features:
- Document type classification (research_paper, manual, report, etc.)
- Domain classification (legal, medical, technical, financial)
- Semantic keyword extraction
- Entity recognition
- Topic modeling
- Multi-language support
"""

import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib

# NLP libraries (multiple options for flexibility)
try:
    import spacy
    from spacy.lang.en.stop_words import STOP_WORDS as EN_STOP_WORDS
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    EN_STOP_WORDS = set()

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import yake
    YAKE_AVAILABLE = True
except ImportError:
    YAKE_AVAILABLE = False

# Fallback text processing
import collections
from datetime import datetime, timezone


class DocumentType(Enum):
    """Document type classifications."""
    # Original types
    RESEARCH_PAPER = "research_paper"
    TECHNICAL_MANUAL = "technical_manual"
    BUSINESS_REPORT = "business_report"
    FINANCIAL_DOCUMENT = "financial_document"
    LEGAL_DOCUMENT = "legal_document"
    MEDICAL_DOCUMENT = "medical_document"
    PRESENTATION = "presentation"
    SPREADSHEET = "spreadsheet"
    WEB_CONTENT = "web_content"
    EMAIL = "email"
    SPECIFICATION = "specification"
    TUTORIAL = "tutorial"
    NEWS_ARTICLE = "news_article"
    ACADEMIC_PAPER = "academic_paper"
    CONTRACT = "contract"
    INVOICE = "invoice"
    RESUME = "resume"
    
    # Safety & Compliance
    SAFETY_MANUAL = "safety_manual"
    COMPLIANCE_REPORT = "compliance_report"
    INCIDENT_REPORT = "incident_report"
    AUDIT_REPORT = "audit_report"
    RISK_ASSESSMENT = "risk_assessment"
    INSPECTION_CHECKLIST = "inspection_checklist"
    
    # Government & Legal
    POLICY_DOCUMENT = "policy_document"
    REGULATION = "regulation"
    GOVERNMENT_FORM = "government_form"
    PUBLIC_NOTICE = "public_notice"
    LEGISLATIVE_BILL = "legislative_bill"
    PATENT_APPLICATION = "patent_application"
    LICENSE_AGREEMENT = "license_agreement"
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    
    # Business & Operations
    PROJECT_PLAN = "project_plan"
    MEETING_MINUTES = "meeting_minutes"
    PROPOSAL = "proposal"
    MEMO = "memo"
    WORKFLOW = "workflow"
    SOP = "standard_operating_procedure"
    CHECKLIST = "checklist"
    BUDGET = "budget"
    SCHEDULE = "schedule"
    
    # Technical & Engineering
    API_DOCUMENTATION = "api_documentation"
    DEPLOYMENT_GUIDE = "deployment_guide"
    ARCHITECTURE_DOCUMENT = "architecture_document"
    DESIGN_SPECIFICATION = "design_specification"
    CODE_DOCUMENTATION = "code_documentation"
    USER_GUIDE = "user_guide"
    INSTALLATION_GUIDE = "installation_guide"
    
    # Educational & Training
    SYLLABUS = "syllabus"
    LESSON_PLAN = "lesson_plan"
    ASSIGNMENT = "assignment"
    EXAM = "exam"
    TEXTBOOK = "textbook"
    WORKBOOK = "workbook"
    TRAINING_MATERIAL = "training_material"
    COURSE_OUTLINE = "course_outline"
    
    # Marketing & Sales
    BROCHURE = "brochure"
    DATASHEET = "datasheet"
    WHITEPAPER = "whitepaper"
    CASE_STUDY = "case_study"
    PRESS_RELEASE = "press_release"
    MARKETING_PLAN = "marketing_plan"
    SALES_PROPOSAL = "sales_proposal"
    
    # Personal & Administrative
    CERTIFICATE = "certificate"
    TRANSCRIPT = "transcript"
    RECOMMENDATION_LETTER = "recommendation_letter"
    APPLICATION_FORM = "application_form"
    QUESTIONNAIRE = "questionnaire"
    SURVEY = "survey"
    REPORT_CARD = "report_card"
    
    # Specialized
    MANUAL = "manual"
    HANDBOOK = "handbook"
    FACT_SHEET = "fact_sheet"
    FAQ = "frequently_asked_questions"
    GLOSSARY = "glossary"
    BIBLIOGRAPHY = "bibliography"
    
    UNKNOWN = "unknown"


class Domain(Enum):
    """Domain classifications."""
    # Original domains
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    LEGAL = "legal"
    MEDICAL = "medical"
    SCIENCE = "science"
    BUSINESS = "business"
    EDUCATION = "education"
    GOVERNMENT = "government"
    MANUFACTURING = "manufacturing"
    MARKETING = "marketing"
    HR = "human_resources"
    ENGINEERING = "engineering"
    RESEARCH = "research"
    
    # Industry & Infrastructure
    AEROSPACE = "aerospace"
    AUTOMOTIVE = "automotive"
    CONSTRUCTION = "construction"
    ENERGY = "energy"
    UTILITIES = "utilities"
    TRANSPORTATION = "transportation"
    TELECOMMUNICATIONS = "telecommunications"
    MINING = "mining"
    AGRICULTURE = "agriculture"
    FORESTRY = "forestry"
    
    # Professional Services
    CONSULTING = "consulting"
    REAL_ESTATE = "real_estate"
    INSURANCE = "insurance"
    MEDIA = "media"
    PUBLISHING = "publishing"
    ADVERTISING = "advertising"
    ARCHITECTURE = "architecture"
    LAW_ENFORCEMENT = "law_enforcement"
    EMERGENCY_SERVICES = "emergency_services"
    
    # Academic & Scientific
    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    PSYCHOLOGY = "psychology"
    SOCIOLOGY = "sociology"
    ECONOMICS = "economics"
    LINGUISTICS = "linguistics"
    PHILOSOPHY = "philosophy"
    HISTORY = "history"
    
    # Health & Safety
    PUBLIC_HEALTH = "public_health"
    ENVIRONMENTAL = "environmental"
    OCCUPATIONAL_SAFETY = "occupational_safety"
    HEALTHCARE = "healthcare"
    PHARMACEUTICALS = "pharmaceuticals"
    BIOTECHNOLOGY = "biotechnology"
    
    # Creative & Design
    DESIGN = "design"
    ARTS = "arts"
    ENTERTAINMENT = "entertainment"
    GAMING = "gaming"
    FASHION = "fashion"
    PHOTOGRAPHY = "photography"
    
    # Service Industries
    HOSPITALITY = "hospitality"
    RETAIL = "retail"
    FOOD_SERVICE = "food_service"
    LOGISTICS = "logistics"
    SUPPLY_CHAIN = "supply_chain"
    SHIPPING = "shipping"
    WAREHOUSE = "warehouse"
    
    # Technology Specializations
    SOFTWARE = "software"
    HARDWARE = "hardware"
    CYBERSECURITY = "cybersecurity"
    DATA_SCIENCE = "data_science"
    ARTIFICIAL_INTELLIGENCE = "artificial_intelligence"
    ROBOTICS = "robotics"
    
    # Non-Profit & Social
    NON_PROFIT = "non_profit"
    SOCIAL_SERVICES = "social_services"
    COMMUNITY = "community"
    RELIGIOUS = "religious"
    POLITICAL = "political"
    
    GENERAL = "general"


@dataclass
class DocumentTags:
    """Complete document tagging result."""
    document_types: List[Tuple[DocumentType, float]]  # Top 3 types with confidence scores
    domains: List[Tuple[Domain, float]]              # Top 3 domains with confidence scores
    overall_confidence: float                        # Average confidence across classifications
    keywords: List[str]                             # High-quality keywords (up to 25)
    entities: List[Dict[str, str]]
    topics: List[str]
    language: str
    sentiment: Optional[str]
    reading_level: Optional[str]
    word_count: int
    unique_words: int
    processing_time: float
    
    # Format-specific metadata
    format_metadata: Dict[str, Any]
    
    # NLP method used
    nlp_method: str
    
    # Legacy properties for backward compatibility
    @property
    def document_type(self) -> DocumentType:
        """Get the top document type for backward compatibility."""
        return self.document_types[0][0] if self.document_types else DocumentType.UNKNOWN
    
    @property
    def domain(self) -> Domain:
        """Get the top domain for backward compatibility."""
        return self.domains[0][0] if self.domains else Domain.GENERAL
    
    @property
    def confidence(self) -> float:
        """Get overall confidence for backward compatibility."""
        return self.overall_confidence


class UniversalDocumentTagger:
    """Universal document classification and tagging system."""
    
    def __init__(self):
        # Load models if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
        
        # Document type indicators
        self.doc_type_indicators = {
            DocumentType.RESEARCH_PAPER: [
                "abstract", "introduction", "methodology", "results", "conclusion",
                "references", "citation", "doi", "journal", "proceedings",
                "hypothesis", "experiment", "analysis", "findings", "literature review"
            ],
            DocumentType.TECHNICAL_MANUAL: [
                "installation", "configuration", "setup", "requirements", "troubleshooting",
                "api", "documentation", "guide", "manual", "instructions",
                "parameters", "options", "examples", "usage"
            ],
            DocumentType.BUSINESS_REPORT: [
                "executive summary", "quarterly", "annual", "performance", "metrics",
                "revenue", "profit", "loss", "growth", "market share",
                "kpi", "dashboard", "analytics", "forecast"
            ],
            DocumentType.FINANCIAL_DOCUMENT: [
                "balance sheet", "income statement", "cash flow", "assets", "liabilities",
                "equity", "revenue", "expenses", "profit", "loss", "budget",
                "financial", "accounting", "audit", "investment"
            ],
            DocumentType.LEGAL_DOCUMENT: [
                "contract", "agreement", "terms", "conditions", "clause", "liability",
                "copyright", "patent", "trademark", "compliance", "regulation",
                "whereas", "therefore", "party", "jurisdiction"
            ],
            DocumentType.MEDICAL_DOCUMENT: [
                "patient", "diagnosis", "treatment", "symptoms", "medication", "dosage",
                "clinical", "medical", "health", "disease", "condition",
                "therapy", "procedure", "surgery", "prescription"
            ],
            DocumentType.PRESENTATION: [
                "slide", "agenda", "overview", "objectives", "summary", "next steps",
                "action items", "timeline", "milestones", "deliverables"
            ],
            DocumentType.SPECIFICATION: [
                "specification", "requirements", "architecture", "design", "protocol",
                "interface", "standard", "compliance", "implementation", "version"
            ]
        }
        
        # Domain indicators
        self.domain_indicators = {
            Domain.TECHNOLOGY: [
                "software", "hardware", "algorithm", "database", "api", "framework",
                "programming", "code", "development", "system", "network", "security",
                "cloud", "ai", "machine learning", "data science"
            ],
            Domain.FINANCE: [
                "financial", "banking", "investment", "portfolio", "trading", "market",
                "economy", "fiscal", "monetary", "capital", "currency", "stocks"
            ],
            Domain.LEGAL: [
                "legal", "law", "court", "judge", "attorney", "lawsuit", "litigation",
                "statute", "regulation", "compliance", "contract", "intellectual property"
            ],
            Domain.MEDICAL: [
                "medical", "health", "clinical", "patient", "diagnosis", "treatment",
                "pharmaceutical", "healthcare", "medicine", "therapy", "surgery"
            ],
            Domain.SCIENCE: [
                "research", "study", "experiment", "hypothesis", "theory", "analysis",
                "scientific", "laboratory", "data", "methodology", "peer review"
            ],
            Domain.ENGINEERING: [
                "engineering", "design", "manufacturing", "construction", "mechanical",
                "electrical", "civil", "chemical", "structural", "materials"
            ]
        }
    
    def tag_document(self, text_content: str, file_path: Path, 
                    format_metadata: Optional[Dict] = None) -> DocumentTags:
        """
        Perform complete document tagging and classification.
        
        Args:
            text_content: Extracted text content
            file_path: Original file path for context
            format_metadata: Format-specific metadata
        
        Returns:
            Complete document tags
        """
        start_time = time.time()
        
        if not text_content or len(text_content.strip()) < 50:
            # Handle empty or very short documents
            return self._create_minimal_tags(text_content, file_path, format_metadata, start_time)
        
        # Dual-text processing: keep raw text for entity extraction, cleaned for classification
        raw_text = text_content  # Preserve original for entity/topic extraction
        clean_text = self._preprocess_text(text_content)  # Normalized for classification
        
        # Classify document type and domain (get top 3 for each) - use cleaned text
        document_types = self._classify_document_type(clean_text, file_path)
        domains = self._classify_domain(clean_text, file_path)
        
        # Extract keywords - use cleaned text for better NLP processing
        keywords = self._extract_keywords(clean_text)
        
        # Extract entities - use raw text to preserve emails, URLs, etc.
        entities = self._extract_entities(raw_text)
        
        # Extract topics - use raw text to preserve capitalization patterns
        topics = self._extract_topics(raw_text)
        
        # Language detection (basic)
        language = self._detect_language(clean_text)
        
        # Calculate text statistics
        words = clean_text.split()
        word_count = len(words)
        unique_words = len(set(word.lower() for word in words))
        
        # Determine NLP method used
        nlp_method = "spacy" if self.nlp else "heuristic"
        
        # Calculate overall confidence from top classifications
        top_type_confidence = document_types[0][1] if document_types else 0.3
        top_domain_confidence = domains[0][1] if domains else 0.3
        overall_confidence = (top_type_confidence + top_domain_confidence) / 2.0
        
        processing_time = time.time() - start_time
        
        return DocumentTags(
            document_types=document_types,
            domains=domains,
            overall_confidence=overall_confidence,
            keywords=keywords,
            entities=entities,
            topics=topics,
            language=language,
            sentiment=None,  # Could add sentiment analysis
            reading_level=None,  # Could add reading level analysis
            word_count=word_count,
            unique_words=unique_words,
            processing_time=processing_time,
            format_metadata=format_metadata or {},
            nlp_method=nlp_method
        )
    
    def _score_indicators(self, text: str, indicators: List[str]) -> int:
        """Score indicators using proper tokenization to avoid false substring matches."""
        import re
        import collections
        
        # Tokenize with word boundaries, keeping hyphenated terms
        tokens = re.findall(r"\b\w[\w\-]*\b", text.lower())
        freq = collections.Counter(tokens)
        
        # Count actual token matches, not substring matches
        score = 0
        for indicator in indicators:
            indicator_lower = indicator.lower()
            # Handle multi-word indicators
            if ' ' in indicator_lower:
                # For phrases, check if all words are present (simple approach)
                indicator_words = indicator_lower.split()
                if all(word in freq for word in indicator_words):
                    score += min(freq[word] for word in indicator_words)
            else:
                # Single word indicator
                score += freq.get(indicator_lower, 0)
        
        return score
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-]', ' ', text)
        
        # Convert to lowercase for analysis
        return text.lower().strip()
    
    def _classify_document_type(self, text: str, file_path: Path) -> List[Tuple[DocumentType, float]]:
        """Classify document type using keyword matching and heuristics. Returns top 3 results."""
        
        # Check file extension hints
        suffix = file_path.suffix.lower()
        extension_hints = {
            '.pptx': DocumentType.PRESENTATION,
            '.ppt': DocumentType.PRESENTATION,
            '.xlsx': DocumentType.SPREADSHEET,
            '.xls': DocumentType.SPREADSHEET,
            '.csv': DocumentType.SPREADSHEET,
        }
        
        if suffix in extension_hints:
            # Return file extension hint as top result, plus two generic possibilities
            return [
                (extension_hints[suffix], 0.8),
                (DocumentType.TECHNICAL_MANUAL, 0.2),
                (DocumentType.BUSINESS_REPORT, 0.1)
            ]
        
        # Keyword-based classification using token-aware scoring
        scores = {}
        
        for doc_type, indicators in self.doc_type_indicators.items():
            # Use token-based scoring instead of substring counting
            score = self._score_indicators(text, indicators)
            
            # Normalize by text length (in tokens)
            tokens = text.split()
            scores[doc_type] = score / len(tokens) if tokens else 0
        
        if not scores or max(scores.values()) == 0:
            return [
                (DocumentType.UNKNOWN, 0.3),
                (DocumentType.BUSINESS_REPORT, 0.2),
                (DocumentType.TECHNICAL_MANUAL, 0.1)
            ]
        
        # Sort by score and get top 3
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Proper confidence calculation using normalized scores
        results = []
        
        # Calculate total score for normalization
        total_score = sum(score for _, score in sorted_types if score > 0)
        
        if total_score > 0:
            # Use softmax-like normalization for better confidence calibration
            for i, (doc_type, score) in enumerate(sorted_types[:3]):
                if score > 0:
                    # Normalize to probability distribution
                    normalized_confidence = score / total_score
                    # Apply slight decay for ranking effect
                    confidence = normalized_confidence * (0.9 ** i)
                    # Ensure minimum confidence floor
                    confidence = max(0.1, min(0.95, confidence))
                    results.append((doc_type, confidence))
        else:
            # Fallback for no matches
            results = [(sorted_types[0][0], 0.3)]
        
        # Ensure we always return 3 results
        while len(results) < 3:
            fallback_types = [DocumentType.BUSINESS_REPORT, DocumentType.TECHNICAL_MANUAL, DocumentType.UNKNOWN]
            for fallback in fallback_types:
                if not any(result[0] == fallback for result in results):
                    results.append((fallback, 0.1))
                    break
        
        return results[:3]
    
    def _classify_domain(self, text: str, file_path: Path) -> List[Tuple[Domain, float]]:
        """Classify document domain using keyword matching. Returns top 3 results."""
        
        scores = {}
        
        for domain, indicators in self.domain_indicators.items():
            # Use token-based scoring instead of substring counting
            score = self._score_indicators(text, indicators)
            
            # Normalize by text length (in tokens)
            tokens = text.split()
            scores[domain] = score / len(tokens) if tokens else 0
        
        if not scores or max(scores.values()) == 0:
            return [
                (Domain.GENERAL, 0.3),
                (Domain.BUSINESS, 0.2),
                (Domain.TECHNOLOGY, 0.1)
            ]
        
        # Sort by score and get top 3
        sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Proper confidence calculation using normalized scores
        results = []
        
        # Calculate total score for normalization
        total_score = sum(score for _, score in sorted_domains if score > 0)
        
        if total_score > 0:
            # Use softmax-like normalization for better confidence calibration
            for i, (domain, score) in enumerate(sorted_domains[:3]):
                if score > 0:
                    # Normalize to probability distribution
                    normalized_confidence = score / total_score
                    # Apply slight decay for ranking effect
                    confidence = normalized_confidence * (0.9 ** i)
                    # Ensure minimum confidence floor
                    confidence = max(0.1, min(0.95, confidence))
                    results.append((domain, confidence))
        else:
            # Fallback for no matches
            results = [(sorted_domains[0][0], 0.3)]
        
        # Ensure we always return 3 results
        while len(results) < 3:
            fallback_domains = [Domain.GENERAL, Domain.BUSINESS, Domain.TECHNOLOGY]
            for fallback in fallback_domains:
                if not any(result[0] == fallback for result in results):
                    results.append((fallback, 0.1))
                    break
        
        return results[:3]
    
    def _extract_keywords(self, text: str, max_keywords: int = 25) -> List[str]:
        """Extract high-quality key terms and phrases from text with advanced filtering."""
        
        # Comprehensive common words blacklist (much more aggressive)
        common_words = {
            # Basic function words
            'the', 'it', 'is', 'with', 'such', 'shall', 'this', 'that', 'and', 'or', 'but', 
            'for', 'in', 'on', 'at', 'to', 'from', 'by', 'as', 'an', 'a', 'be', 'are', 'was', 
            'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
            'should', 'may', 'might', 'can', 'must', 'should', 'shall', 'if', 'then', 'else', 
            'when', 'where', 'what', 'who', 'why', 'how', 'which', 'these', 'those', 'they', 
            'them', 'their', 'there', 'here', 'now', 'then', 'than', 'more', 'most', 'less', 
            'least', 'some', 'any', 'all', 'each', 'every', 'other', 'another', 'same', 'different',
            
            # Directional and positional
            'first', 'last', 'next', 'previous', 'new', 'old', 'good', 'bad', 'big', 'small',
            'high', 'low', 'long', 'short', 'right', 'left', 'up', 'down', 'out', 'over', 'under',
            'above', 'below', 'between', 'through', 'during', 'before', 'after', 'while', 'until',
            
            # Conjunctions and transitions
            'since', 'because', 'although', 'though', 'however', 'therefore', 'thus', 'hence',
            'also', 'too', 'very', 'quite', 'rather', 'just', 'only', 'even', 'still', 'yet',
            'already', 'again', 'once', 'twice', 'always', 'never', 'sometimes', 'often', 'usually',
            'about', 'around', 'against', 'among', 'within', 'without', 'including', 'excluding',
            'regarding', 'concerning', 'according', 'following', 'resulting', 'leading', 'making',
            'getting', 'taking', 'giving', 'coming', 'going', 'being', 'having', 'doing', 'saying',
            'looking', 'working', 'using', 'based', 'related', 'associated', 'connected', 'linked',
            
            # Personal pronouns and common references
            'he', 'she', 'his', 'her', 'him', 'its', 'us', 'we', 'our', 'you', 'your', 'yours',
            'mine', 'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves', 'yourselves',
            'themselves', 'one', 'ones', 'both', 'either', 'neither', 'none', 'everyone', 'someone',
            'anyone', 'everyone', 'no', 'not', 'nor', 'yes', 'yeah', 'ok', 'okay',
            
            # Document structure words (very common in legal/gov docs)
            'section', 'subsection', 'clause', 'paragraph', 'part', 'chapter', 'title', 'article',
            'item', 'point', 'number', 'page', 'line', 'column', 'row', 'table', 'figure', 'chart',
            'appendix', 'exhibit', 'attachment', 'reference', 'note', 'footnote', 'endnote',
            'see', 'above', 'below', 'herein', 'thereof', 'whereby', 'wherein', 'whereas',
            
            # Legal/administrative common words
            'order', 'pursuant', 'accordance', 'compliance', 'provision', 'requirement', 'condition',
            'term', 'terms', 'conditions', 'means', 'include', 'includes', 'including', 'such',
            'other', 'any', 'each', 'every', 'all', 'applicable', 'appropriate', 'necessary',
            'required', 'prescribed', 'specified', 'designated', 'authorized', 'approved',
            'effective', 'date', 'time', 'period', 'day', 'days', 'year', 'years', 'month', 'months',
            
            # Geographic/governmental (too generic)
            'state', 'states', 'federal', 'national', 'local', 'government', 'governmental',
            'public', 'private', 'individual', 'person', 'persons', 'people', 'human', 'individual',
            'citizen', 'residents', 'population', 'community', 'society', 'nation', 'country',
            'united', 'america', 'american',
            
            # Publication/citation words
            'pub', 'publication', 'published', 'vol', 'volume', 'ed', 'edition', 'revised',
            'amended', 'update', 'updated', 'version', 'draft', 'final', 'preliminary',
            'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
            'september', 'october', 'november', 'december', 'jan', 'feb', 'mar', 'apr',
            'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
            
            # Administrative terms (too generic)
            'office', 'department', 'agency', 'bureau', 'division', 'unit', 'organization',
            'administration', 'management', 'director', 'manager', 'officer', 'official',
            'secretary', 'assistant', 'deputy', 'chief', 'head', 'supervisor', 'coordinator',
            'representative', 'agent', 'staff', 'personnel', 'employee', 'employees',
            
            # Generic business/process words
            'process', 'procedure', 'method', 'system', 'program', 'plan', 'policy', 'practice',
            'operation', 'operations', 'activity', 'activities', 'function', 'functions',
            'service', 'services', 'product', 'products', 'result', 'results', 'outcome',
            'effect', 'effects', 'impact', 'impacts', 'benefit', 'benefits', 'cost', 'costs',
            'value', 'amount', 'level', 'degree', 'extent', 'scope', 'range', 'limit', 'limits',
            
            # Common verbs (too generic as keywords)
            'make', 'makes', 'made', 'take', 'takes', 'taken', 'took', 'get', 'gets', 'got', 'gotten',
            'give', 'gives', 'given', 'gave', 'put', 'puts', 'set', 'sets', 'find', 'finds', 'found',
            'use', 'uses', 'used', 'keep', 'keeps', 'kept', 'hold', 'holds', 'held', 'run', 'runs', 'ran',
            'move', 'moves', 'moved', 'turn', 'turns', 'turned', 'show', 'shows', 'showed', 'shown',
            'tell', 'tells', 'told', 'ask', 'asks', 'asked', 'try', 'tries', 'tried', 'seem', 'seems',
            'seemed', 'become', 'becomes', 'became', 'leave', 'leaves', 'left', 'feel', 'feels', 'felt',
            'fact', 'facts', 'way', 'ways', 'case', 'cases', 'thing', 'things', 'work', 'works', 'worked'
        }
        
        def is_high_quality_keyword(word: str, text: str) -> bool:
            """Check if a word/phrase meets quality criteria."""
            word_clean = word.strip().lower()
            
            # Remove punctuation for checking
            word_no_punct = ''.join(c for c in word_clean if c.isalnum() or c.isspace()).strip()
            if not word_no_punct:
                return False
            
            # Filter out common words (check both original and cleaned versions)
            if word_clean in common_words or word_no_punct in common_words:
                return False
            
            # Filter individual words in phrases
            words_in_phrase = word_no_punct.split()
            if len(words_in_phrase) == 1 and words_in_phrase[0] in common_words:
                return False
            
            # Minimum length filter (more strict)
            if len(word_no_punct) < 4:  # Increased from 3 to 4
                return False
            
            # Filter out numeric-only or mostly numeric
            if word_no_punct.replace(' ', '').isdigit():
                return False
            
            # Filter out dates and years
            if word_no_punct.isdigit() and 1900 <= int(word_no_punct) <= 2100:
                return False
            
            # Filter out single letters with punctuation (like "a.", "b)", etc.)
            if len(word_no_punct) == 1:
                return False
            
            # Filter out very common abbreviations
            common_abbreviations = {'usc', 'cfr', 'etc', 'inc', 'ltd', 'llc', 'corp', 'co', 'vs', 'ie', 'eg'}
            if word_no_punct in common_abbreviations:
                return False
            
            # Frequency-based filtering: skip words appearing too frequently (>8% of document)
            word_count = text.lower().count(word_clean)
            total_words = len(text.split())
            if total_words > 0 and (word_count / total_words) > 0.08:  # More strict: 8% instead of 10%
                return False
            
            # Filter out words that are mostly punctuation
            alpha_chars = sum(1 for c in word_clean if c.isalpha())
            if alpha_chars < len(word_clean) * 0.8:  # More strict: 80% instead of 70%
                return False
            
            # Filter out words with trailing punctuation that creates duplicates (like "act,")
            if word_clean.endswith((',', '.', ';', ':', '!', '?', ')', ']', '}')):
                # Check if the word without punctuation is already common
                base_word = word_clean.rstrip(',.;:!?)]')
                if base_word in common_words or len(base_word) < 4:
                    return False
            
            # Prioritize domain-specific terms over generic ones
            # Give higher weight to technical/specialized terms
            technical_indicators = ['occupational', 'safety', 'health', 'hazard', 'workplace', 'compliance', 
                                  'regulation', 'standard', 'inspection', 'protection', 'equipment', 
                                  'training', 'emergency', 'prevention', 'assessment', 'monitoring']
            
            # Allow shorter technical terms if they're domain-specific
            if any(indicator in word_no_punct for indicator in technical_indicators):
                return True
            
            return True
        
        # Try YAKE first (most effective)
        if YAKE_AVAILABLE:
            try:
                kw_extractor = yake.KeywordExtractor(
                    lan="en",
                    n=3,  # Extract up to trigrams
                    dedupLim=0.7,
                    top=max_keywords * 2  # Get more candidates for filtering
                )
                yake_keywords = kw_extractor.extract_keywords(text)
                filtered_keywords = []
                
                # YAKE returns (keyword, score) tuples, not (score, keyword)
                for keyword, score in yake_keywords:
                    if is_high_quality_keyword(keyword, text):
                        filtered_keywords.append(keyword.lower())
                        if len(filtered_keywords) >= max_keywords:
                            break
                
                if len(filtered_keywords) >= max_keywords // 2:  # If we got good results
                    return filtered_keywords[:max_keywords]
            except:
                pass
        
        # Try spaCy if available
        if self.nlp:
            try:
                doc = self.nlp(text[:100000])  # Limit text length for performance
                
                # Extract noun phrases and named entities
                keywords = set()
                
                # Prioritize named entities (higher quality) - use real spaCy labels
                ENT_KEEP = {'ORG', 'PRODUCT', 'GPE', 'LOC', 'PERSON', 'WORK_OF_ART', 'EVENT', 'LAW', 'NORP'}
                for ent in doc.ents:
                    if ent.label_ in ENT_KEEP:
                        if is_high_quality_keyword(ent.text, text):
                            keywords.add(ent.text.lower())
                
                # Add technical noun chunks
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) <= 3:
                        if is_high_quality_keyword(chunk.text, text):
                            keywords.add(chunk.text.lower())
                
                # Add important individual nouns if we need more keywords
                if len(keywords) < max_keywords:
                    for token in doc:
                        if (token.pos_ in ['NOUN', 'PROPN'] and 
                            not token.is_stop and 
                            is_high_quality_keyword(token.text, text)):
                            keywords.add(token.text.lower())
                
                keyword_list = list(keywords)[:max_keywords]
                if len(keyword_list) >= max_keywords // 2:  # If we got reasonable results
                    return keyword_list
                
            except:
                pass
        
        # Enhanced fallback: TF-IDF approach with quality filtering
        if SKLEARN_AVAILABLE:
            try:
                # Enhanced TF-IDF keyword extraction
                vectorizer = TfidfVectorizer(
                    max_features=max_keywords * 3,  # Get more candidates
                    stop_words='english',
                    ngram_range=(1, 3),  # Include trigrams
                    min_df=1,
                    max_df=0.9  # Filter very common terms
                )
                tfidf_matrix = vectorizer.fit_transform([text])
                feature_names = vectorizer.get_feature_names_out()
                scores = tfidf_matrix.toarray()[0]
                
                # Get top keywords with quality filtering
                keyword_scores = list(zip(feature_names, scores))
                keyword_scores.sort(key=lambda x: x[1], reverse=True)
                
                filtered_keywords = []
                for keyword, score in keyword_scores:
                    if is_high_quality_keyword(keyword, text):
                        filtered_keywords.append(keyword)
                        if len(filtered_keywords) >= max_keywords:
                            break
                
                if len(filtered_keywords) >= max_keywords // 3:  # If we got some good results
                    return filtered_keywords[:max_keywords]
            except:
                pass
        
        # Final fallback: enhanced frequency analysis
        words = text.lower().split()
        word_freq = collections.Counter(words)
        
        # Filter and prioritize words
        filtered_words = []
        for word, freq in word_freq.most_common(max_keywords * 5):
            if is_high_quality_keyword(word, text):
                filtered_words.append(word)
                if len(filtered_words) >= max_keywords:
                    break
        
        # If still not enough, add some longer words that passed basic filtering
        if len(filtered_words) < max_keywords // 2:
            for word, freq in word_freq.most_common():
                if (len(word) >= 4 and 
                    word not in common_words and 
                    word.isalpha() and 
                    word not in filtered_words):
                    filtered_words.append(word)
                    if len(filtered_words) >= max_keywords:
                        break
        
        return filtered_words[:max_keywords]
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities from text."""
        
        entities = []
        
        if self.nlp:
            try:
                doc = self.nlp(text[:50000])  # Limit for performance
                
                for ent in doc.ents:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "description": spacy.explain(ent.label_) or ent.label_
                    })
                
                return entities[:20]  # Limit number of entities
                
            except:
                pass
        
        # Fallback: regex-based entity extraction
        entities = []
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append({
                "text": match.group(),
                "label": "EMAIL",
                "description": "Email address"
            })
        
        # URLs
        url_pattern = r'https?://[^\s]+'
        for match in re.finditer(url_pattern, text):
            entities.append({
                "text": match.group(),
                "label": "URL", 
                "description": "Web URL"
            })
        
        # Phone numbers (basic pattern)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        for match in re.finditer(phone_pattern, text):
            entities.append({
                "text": match.group(),
                "label": "PHONE",
                "description": "Phone number"
            })
        
        return entities[:20]
    
    def _extract_topics(self, text: str, max_topics: int = 5) -> List[str]:
        """Extract main topics from text."""
        
        # Simple topic extraction based on frequent noun phrases
        topics = []
        
        if self.nlp:
            try:
                doc = self.nlp(text[:50000])
                
                # Count noun phrases
                phrase_freq = collections.Counter()
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) >= 2:  # Multi-word phrases
                        phrase_freq[chunk.text.lower()] += 1
                
                topics = [phrase for phrase, freq in phrase_freq.most_common(max_topics)]
                
            except:
                pass
        
        if not topics:
            # Fallback: extract capitalized phrases
            capitalized_phrases = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
            phrase_freq = collections.Counter(capitalized_phrases)
            topics = [phrase for phrase, freq in phrase_freq.most_common(max_topics)]
        
        return topics
    
    def _detect_language(self, text: str) -> str:
        """Basic language detection."""
        
        # Very simple heuristic - could be improved with proper language detection
        sample = text[:1000].lower()
        
        # Check for common English words
        english_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']
        english_score = sum(1 for word in english_indicators if word in sample)
        
        if english_score >= 3:
            return "en"
        
        # Could add more language detection here
        return "unknown"
    
    def _create_minimal_tags(self, text: str, file_path: Path, 
                           format_metadata: Dict, start_time: float) -> DocumentTags:
        """Create minimal tags for empty or very short documents."""
        
        # Infer type from file extension
        suffix = file_path.suffix.lower()
        doc_type = DocumentType.UNKNOWN
        
        if suffix in ['.pptx', '.ppt']:
            doc_type = DocumentType.PRESENTATION
        elif suffix in ['.xlsx', '.xls', '.csv']:
            doc_type = DocumentType.SPREADSHEET
        elif suffix in ['.html', '.htm']:
            doc_type = DocumentType.WEB_CONTENT
        
        processing_time = time.time() - start_time
        
        return DocumentTags(
            document_types=[(doc_type, 0.3), (DocumentType.BUSINESS_REPORT, 0.2), (DocumentType.UNKNOWN, 0.1)],
            domains=[(Domain.GENERAL, 0.3), (Domain.BUSINESS, 0.2), (Domain.TECHNOLOGY, 0.1)],
            overall_confidence=0.3,
            keywords=[],
            entities=[],
            topics=[],
            language="unknown",
            sentiment=None,
            reading_level=None,
            word_count=len(text.split()) if text else 0,
            unique_words=0,
            processing_time=processing_time,
            format_metadata=format_metadata,
            nlp_method="minimal"
        )
    
    def generate_metadata_header(self, tags: DocumentTags, file_path: Path) -> str:
        """Generate enhanced YAML frontmatter with top 3 document types and domains."""
        
        # Format top 3 document types with confidence scores
        document_types_list = []
        for i, (doc_type, confidence) in enumerate(tags.document_types[:3]):
            document_types_list.append({
                "type": doc_type.value.replace('_', ' ').title(),
                "confidence": round(confidence, 3),
                "rank": i + 1
            })
        
        # Format top 3 domains with confidence scores  
        domains_list = []
        for i, (domain, confidence) in enumerate(tags.domains[:3]):
            domains_list.append({
                "domain": domain.value.replace('_', ' ').title(),
                "confidence": round(confidence, 3),
                "rank": i + 1
            })
        
        metadata = {
            "docling_meta": {
                # Enhanced classification with top 3 results
                "document_types": document_types_list,
                "domains": domains_list,
                "overall_confidence": round(tags.overall_confidence, 3),
                
                # Legacy fields for backward compatibility
                "document_type": tags.document_type.value,
                "domain": tags.domain.value,
                "confidence": round(tags.confidence, 3),
                
                # Processing information
                "processing_time": round(tags.processing_time, 3),
                "nlp_method": tags.nlp_method,
                "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                
                # File information
                "file_info": {
                    "name": file_path.name,
                    "size": file_path.stat().st_size if file_path.exists() else 0,
                    "format": file_path.suffix.lower()
                },
                
                # Content traceability (add content hash for traceability)
                "content_hash": hashlib.sha1(str(tags.word_count).encode("utf-8")).hexdigest(),  # Simple hash based on content stats
                
                # Content statistics
                "content_stats": {
                    "word_count": tags.word_count,
                    "unique_words": tags.unique_words,
                    "language": tags.language
                }
            }
        }
        
        # Add enhanced keywords (now up to 25 high-quality keywords)
        if tags.keywords:
            metadata["docling_meta"]["keywords"] = tags.keywords  # Show all keywords
        
        # Add entities if available
        if tags.entities:
            metadata["docling_meta"]["entities"] = [
                {"text": ent["text"], "type": ent["label"]} 
                for ent in tags.entities[:10]  # More entities
            ]
        
        # Add topics if available
        if tags.topics:
            metadata["docling_meta"]["topics"] = tags.topics
        
        # Add format-specific metadata
        if tags.format_metadata:
            metadata["docling_meta"]["format_metadata"] = tags.format_metadata
        
        # Convert to YAML-like format (simple implementation)
        yaml_lines = ["---"]
        yaml_lines.extend(self._dict_to_yaml(metadata, indent=0))
        yaml_lines.append("---")
        yaml_lines.append("")
        
        return "\n".join(yaml_lines)
    
    def _dict_to_yaml(self, data: Any, indent: int = 0) -> List[str]:
        """Simple YAML serialization."""
        lines = []
        spaces = "  " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{spaces}{key}:")
                    lines.extend(self._dict_to_yaml(value, indent + 1))
                else:
                    lines.append(f"{spaces}{key}: {self._yaml_value(value)}")
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(f"{spaces}- ")
                    lines.extend(self._dict_to_yaml(item, indent + 1))
                else:
                    lines.append(f"{spaces}- {self._yaml_value(item)}")
        
        return lines
    
    def _yaml_value(self, value: Any) -> str:
        """Format value for YAML output."""
        if isinstance(value, str):
            # Quote strings that need it
            if any(char in value for char in ['"', "'", ':', '#', '\n']):
                return f'"{value.replace('"', '\\"')}"'
            return value
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif value is None:
            return "null"
        else:
            return str(value)


def main():
    """Tag specified file or run test with sample documents."""
    import sys
    
    tagger = UniversalDocumentTagger()
    
    # Check if specific file was provided
    if len(sys.argv) > 1:
        # Process specific file
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return
        
        print("🏷️  UNIVERSAL DOCUMENT TAGGING")
        print("=" * 50)
        print(f"\n📄 Tagging: {file_path.name}")
        
        # Extract text first (simplified version)
        try:
            if file_path.suffix.lower() == '.pdf':
                from fast_text_extractor import FastTextExtractor
                extractor = FastTextExtractor()
                result = extractor.extract(file_path)
                if result.success:
                    text_content = result.text_content[:5000]  # First 5000 chars for tagging
                else:
                    print(f"❌ Failed to extract text: {result.error_message}")
                    return
            else:
                # Simple text file reading
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()[:5000]
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
        
        # Tag the document
        tags = tagger.tag_document(text_content, file_path)
        
        print(f"   🏷️  Document Type: {tags.document_type}")
        print(f"   🌐 Domain: {tags.domain}")
        print(f"   🎯 Confidence: {tags.confidence:.2f}")
        print(f"   🔤 Language: {tags.language}")
        print(f"   📊 Processing time: {tags.processing_time:.3f}s")
        print(f"   🔗 Keywords: {', '.join(tags.keywords[:10])}")  # Show first 10 keywords
        
        return
    
    # Default: Test with sample text
    sample_texts = [
        ("This document presents a comprehensive analysis of machine learning algorithms for natural language processing. The research methodology includes experimental validation using deep neural networks.", "research_paper.pdf"),
        ("Installation Guide: This manual provides step-by-step instructions for configuring the API server. Prerequisites include Python 3.8+ and database connectivity.", "manual.pdf"),
        ("Q4 Financial Report: Revenue increased by 15% compared to previous quarter. Net profit margins improved significantly due to cost optimization initiatives.", "report.xlsx"),
    ]
    
    print("🏷️  UNIVERSAL DOCUMENT TAGGING TEST")
    print("=" * 50)
    
    for i, (text, filename) in enumerate(sample_texts, 1):
        print(f"\n📄 Test {i}: {filename}")
        
        file_path = Path(filename)
        tags = tagger.tag_document(text, file_path)
        
        print(f"   📋 Type: {tags.document_type.value} (confidence: {tags.confidence:.2f})")
        print(f"   🏢 Domain: {tags.domain.value}")
        print(f"   🔑 Keywords: {', '.join(tags.keywords[:5])}")
        print(f"   🎯 Topics: {', '.join(tags.topics)}")
        print(f"   👥 Entities: {len(tags.entities)}")
        print(f"   📊 Words: {tags.word_count}")
        print(f"   ⏱️  Time: {tags.processing_time:.3f}s")
        
        # Show metadata header
        header = tagger.generate_metadata_header(tags, file_path)
        print(f"\n   📝 Metadata header:")
        for line in header.split('\n')[:15]:  # Show first 15 lines
            print(f"      {line}")
        if len(header.split('\n')) > 15:
            print("      ...")


if __name__ == "__main__":
    main()