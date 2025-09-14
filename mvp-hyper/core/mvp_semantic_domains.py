#!/usr/bin/env python3
"""
MVP Semantic Domain Configuration
==================================
Domain-specific extraction profiles for the semantic extraction layer.
This provides the domain-adaptive tier that enhances core foundational facts
with specialized domain knowledge.

Architecture:
- Core Tier: Universal facts (who, what, when, how much) - always extracted
- Domain Tier: Specialized facts based on document domain - loaded on demand

Performance targets:
- Domain classification: < 10ms per document
- Domain-specific extraction: 1,000-3,000 pages/sec (regex/dictionary based)
"""

import re
from typing import Dict, List, Tuple, Optional, Any, Set, Pattern
from dataclasses import dataclass, field
from enum import Enum
import time


@dataclass
class CoreFact:
    """Universal fact structure - extracted for all documents."""
    subject: str           # Who/What entity
    predicate: str         # Action/relationship
    object: Optional[str]  # Target entity
    value: Optional[Any]   # Numerical value
    unit: Optional[str]    # Unit of measurement
    date: Optional[str]    # Temporal information
    location: Optional[str] # Spatial information
    confidence: float = 0.8
    

@dataclass
class DomainFact:
    """Domain-specific fact with enriched attributes."""
    core: CoreFact                    # Base fact
    domain: str                       # Domain identifier
    fact_type: str                    # Domain-specific type
    domain_attributes: Dict[str, Any] # Additional domain fields
    extraction_pattern: str           # Pattern that matched
    compliance_level: Optional[str] = None  # For regulatory domains
    

@dataclass
class DomainProfile:
    """Domain-specific extraction profile."""
    name: str
    description: str
    confidence_threshold: float = 0.7
    
    # Domain classification signals
    classification_keywords: List[str] = field(default_factory=list)
    classification_patterns: Dict[str, str] = field(default_factory=dict)
    
    # Core entity enhancement patterns
    entity_patterns: Dict[str, str] = field(default_factory=dict)
    
    # Domain-specific fact patterns
    fact_patterns: List[Tuple[str, str, float]] = field(default_factory=list)  # (pattern, type, confidence)
    
    # Value extraction patterns with units
    value_patterns: Dict[str, str] = field(default_factory=dict)
    
    # Gazetteers for fast lookup
    gazetteers: Dict[str, Set[str]] = field(default_factory=dict)
    
    # Relationship patterns
    relationship_patterns: List[Tuple[str, str]] = field(default_factory=list)
    
    # Post-processing rules
    normalization_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Quality indicators
    quality_indicators: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)  # Patterns that indicate wrong domain


@dataclass 
class CompiledDomainProfile:
    """Domain profile with pre-compiled patterns for performance."""
    name: str
    description: str
    confidence_threshold: float
    
    # Pre-compiled patterns (compiled once at startup)
    classification_patterns: Dict[str, Pattern] = field(default_factory=dict)
    entity_patterns: Dict[str, Pattern] = field(default_factory=dict)
    fact_patterns: List[Tuple[Pattern, str, float]] = field(default_factory=list)
    value_patterns: Dict[str, Pattern] = field(default_factory=dict)
    
    # Fast RAM-based lookups
    classification_keywords_set: Set[str] = field(default_factory=set)
    gazetteers: Dict[str, Set[str]] = field(default_factory=dict)
    quality_indicators_set: Set[str] = field(default_factory=set)
    anti_patterns_set: Set[str] = field(default_factory=set)


# ============================================================================
# SAFETY/COMPLIANCE DOMAIN
# ============================================================================

SAFETY_DOMAIN = DomainProfile(
    name="safety_compliance",
    description="Workplace safety, OSHA regulations, hazard management",
    confidence_threshold=0.75,
    
    classification_keywords=[
        'osha', 'safety', 'hazard', 'workplace', 'injury', 'accident', 
        'ppe', 'occupational', 'compliance', 'violation', 'inspection',
        'regulation', 'standard', 'cfr', 'incident', 'emergency'
    ],
    
    classification_patterns={
        'osha_reference': r'\b(?:OSHA|29 CFR|Part 19\d{2})\b',
        'safety_topic': r'\b(?:safety|hazard|risk|protection|injury|accident)\b',
        'compliance': r'\b(?:comply|compliance|violation|citation|penalty)\b'
    },
    
    entity_patterns={
        # Regulatory entities
        'regulation_number': r'\b(?:29 CFR |Part |Section |§)\s*(\d+(?:\.\d+)*)\b',
        'osha_standard': r'\bOSHA\s+(\d+(?:\.\d+)?)\b',
        'citation_id': r'\b(?:Citation|Violation)\s+(\d+[A-Z]?\d*)\b',
        
        # Safety equipment
        'ppe_equipment': r'\b(hard hat|safety glasses|respirator|gloves|harness|vest|boots?|helmet|goggles|mask)\b',
        'safety_device': r'\b(guardrail|barrier|scaffold|ladder|platform|net|shield|lock-?out|tag-?out)\b',
        
        # Hazard types
        'hazard_category': r'\b(fall|electrical|chemical|fire|ergonomic|biological|physical|struck-?by|caught-?in)\s+hazard\b',
        
        # Measurements
        'height_depth': r'(\d+(?:\.\d+)?)\s*(?:feet|ft|meters?|m)\s+(?:high|tall|deep|above|below)',
        'weight_load': r'(\d+(?:\.\d+)?)\s*(?:pounds?|lbs?|kilograms?|kg)\s+(?:capacity|load|weight)',
        'noise_level': r'(\d+)\s*(?:decibels?|dB[A]?)',
        'temperature': r'(\d+)\s*(?:degrees?|°)\s*([CF])',
    },
    
    fact_patterns=[
        # Regulatory requirements - high confidence
        (r'(?:employer|contractor|worker)s?\s+(?:shall|must)\s+([^.;]{15,150})', 'mandatory_requirement', 0.9),
        (r'(?:is|are)\s+required\s+to\s+([^.;]{15,150})', 'requirement', 0.85),
        (r'(?:prohibited|not permitted|shall not)\s+([^.;]{15,150})', 'prohibition', 0.9),
        
        # Safety thresholds
        (r'(?:when|if|where)\s+(?:height|depth|elevation)\s+(?:exceeds?|greater than|above)\s+(\d+)\s*(feet|ft|meters?)', 'threshold_condition', 0.85),
        (r'(?:maximum|minimum|not exceed|at least)\s+(\d+(?:\.\d+)?)\s*(feet|ft|lbs?|kg|degrees?)', 'limit_specification', 0.8),
        
        # Hazard identification
        (r'(?:hazards?\s+include|identified hazards?|potential hazards?)\s*:?\s*([^.;]{20,200})', 'hazard_identification', 0.8),
        (r'(?:to prevent|to protect|to avoid|to minimize)\s+([^.;]{15,150})', 'safety_objective', 0.75),
        
        # Incident/violation patterns
        (r'(?:resulted in|caused|led to)\s+(\d+)\s*(?:injuries?|deaths?|fatalities?|violations?)', 'incident_outcome', 0.85),
        (r'(?:fine|penalty|citation)\s+of\s+\$?([\d,]+)', 'enforcement_action', 0.9),
        
        # Training requirements
        (r'(?:training|certification|qualification)\s+(?:is required|must be|shall be)\s+([^.;]{15,150})', 'training_requirement', 0.85),
        (r'(?:annual|periodic|initial|refresher)\s+training\s+(?:on|for|in)\s+([^.;]{10,100})', 'training_schedule', 0.8),
    ],
    
    value_patterns={
        'depth_measurement': r'(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\s+deep',
        'height_measurement': r'(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\s+(?:high|tall|above)',
        'weight_capacity': r'(\d+(?:\.\d+)?)\s*(pounds?|lbs?|kg)\s+(?:capacity|maximum)',
        'time_duration': r'(\d+)\s*(hours?|minutes?|days?|weeks?|months?|years?)',
        'percentage': r'(\d+(?:\.\d+)?)\s*(?:percent|%)',
        'temperature': r'(\d+)\s*(?:°|degrees?)\s*([CF])',
        'sound_level': r'(\d+)\s*(?:dB[A]?|decibels?)',
    },
    
    gazetteers={
        'safety_agencies': {
            'OSHA', 'NIOSH', 'EPA', 'MSHA', 'DOL', 'CDC',
            'Occupational Safety and Health Administration',
            'National Institute for Occupational Safety and Health',
            'Mine Safety and Health Administration',
        },
        'compliance_terms': {
            'shall', 'must', 'required', 'mandatory', 'prohibited',
            'permitted', 'allowed', 'authorized', 'qualified',
            'competent person', 'designated', 'approved',
        },
        'hazard_types': {
            'fall hazard', 'electrical hazard', 'chemical exposure',
            'confined space', 'excavation', 'trenching', 'scaffolding',
            'ladder safety', 'machine guarding', 'lockout tagout',
            'respiratory protection', 'hearing conservation',
        },
    },
    
    relationship_patterns=[
        (r'(\w+)\s+requires\s+(\w+)', 'requires'),
        (r'(\w+)\s+must be\s+(\w+)', 'must_be'),
        (r'(\w+)\s+protects against\s+(\w+)', 'protects_against'),
        (r'(\w+)\s+prevents\s+(\w+)', 'prevents'),
    ],
    
    quality_indicators=[
        '29 CFR', 'OSHA', 'shall', 'must', 'required',
        'standard', 'regulation', 'compliance', 'safety'
    ],
    
    anti_patterns=[
        'stock price', 'revenue', 'earnings', 'market cap',  # Financial
        'diagnosis', 'treatment', 'patient', 'clinical',     # Medical
        'algorithm', 'software', 'code', 'function',          # Technical
    ]
)


# ============================================================================
# FINANCIAL DOMAIN
# ============================================================================

FINANCIAL_DOMAIN = DomainProfile(
    name="financial",
    description="Financial reports, earnings, market data, accounting",
    confidence_threshold=0.75,
    
    classification_keywords=[
        'revenue', 'profit', 'earnings', 'ebitda', 'margin', 'quarterly',
        'fiscal', 'dividend', 'shares', 'market', 'investment', 'capital',
        'assets', 'liabilities', 'cash flow', 'balance sheet', 'income statement'
    ],
    
    classification_patterns={
        'financial_statement': r'\b(?:income statement|balance sheet|cash flow|10-[KQ]|8-K|annual report)\b',
        'financial_metric': r'\b(?:revenue|profit|EBITDA|EPS|P/E|ROI|ROE|margin)\b',
        'period': r'\b(?:Q[1-4]|FY\d{2,4}|fiscal year|quarter|YTD|YoY)\b'
    },
    
    entity_patterns={
        # Financial amounts
        'currency_amount': r'\$\s?([\d,]+(?:\.\d{2})?)\s*(?:million|billion|thousand|M|B|K)?',
        'percentage_change': r'([+-]?\d+(?:\.\d+)?)\s*(?:percent|%)\s*(?:increase|decrease|growth|decline)?',
        
        # Time periods
        'fiscal_period': r'\b(?:Q[1-4]|H[12]|FY)\s*(\d{2,4})\b',
        'reporting_date': r'(?:quarter|year)\s+ended?\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        
        # Financial metrics
        'eps_value': r'(?:EPS|earnings per share)\s*(?:of\s+)?\$?(\d+\.\d{2})',
        'revenue_metric': r'(?:revenue|sales)\s+of\s+\$?([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?',
        
        # Market data
        'stock_symbol': r'\b([A-Z]{2,5})\s*:\s*(?:NYSE|NASDAQ|AMEX)\b',
        'share_price': r'\$(\d+(?:\.\d{2})?)\s+per\s+share',
    },
    
    fact_patterns=[
        # Financial performance
        (r'(?:reported|posted|announced)\s+(?:revenue|sales)\s+of\s+\$?([\d,]+[MBK]?)', 'revenue_report', 0.9),
        (r'(?:net income|profit)\s+of\s+\$?([\d,]+[MBK]?)', 'profit_report', 0.9),
        (r'(?:increased|decreased|rose|fell)\s+(?:by\s+)?(\d+(?:\.\d+)?%)', 'metric_change', 0.85),
        
        # Guidance and forecasts
        (r'(?:guidance|forecast|outlook)\s+(?:for|of)\s+\$?([\d,]+[MBK]?)', 'financial_guidance', 0.8),
        (r'(?:expects?|projects?|anticipates?)\s+(?:revenue|earnings)\s+(?:of|between)\s+([^.;]{10,100})', 'projection', 0.75),
        
        # Dividends and distributions
        (r'(?:declared?|announced?)\s+(?:a\s+)?dividend\s+of\s+\$?(\d+\.\d{2})\s+per\s+share', 'dividend_declaration', 0.9),
        
        # Market movements
        (r'(?:shares?|stock)\s+(?:rose|fell|gained|lost)\s+(\d+(?:\.\d+)?%)', 'stock_movement', 0.85),
    ],
    
    value_patterns={
        'dollar_amount': r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        'percentage': r'(\d+(?:\.\d+)?)\s*%',
        'multiplier': r'(\d+(?:\.\d+)?)[xX]\s+(?:multiple|times)',
        'ratio': r'(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)',
        'basis_points': r'(\d+)\s+(?:basis points?|bps?|bp)',
    },
    
    gazetteers={
        'financial_terms': {
            'revenue', 'profit', 'loss', 'margin', 'EBITDA', 'EBIT',
            'earnings', 'income', 'expenses', 'costs', 'assets',
            'liabilities', 'equity', 'cash flow', 'working capital',
            'debt', 'dividend', 'shares', 'market cap', 'valuation',
        },
        'accounting_standards': {
            'GAAP', 'IFRS', 'SEC', 'FASB', 'PCAOB',
            'Generally Accepted Accounting Principles',
            'International Financial Reporting Standards',
        },
        'market_indicators': {
            'bull market', 'bear market', 'volatility', 'liquidity',
            'P/E ratio', 'EPS', 'ROI', 'ROE', 'ROA', 'ROIC',
        },
    },
    
    quality_indicators=[
        'revenue', 'earnings', 'GAAP', 'fiscal', 'quarter',
        'financial', 'profit', 'margin', 'cash flow'
    ],
    
    anti_patterns=[
        'patient', 'treatment', 'clinical',      # Medical
        'hazard', 'safety', 'injury', 'OSHA',    # Safety
        'algorithm', 'function', 'code',          # Technical
    ]
)


# ============================================================================
# TECHNICAL/ENGINEERING DOMAIN
# ============================================================================

TECHNICAL_DOMAIN = DomainProfile(
    name="technical",
    description="Technical specifications, engineering, software, hardware",
    confidence_threshold=0.7,
    
    classification_keywords=[
        'specification', 'technical', 'system', 'architecture', 'protocol',
        'algorithm', 'implementation', 'configuration', 'performance',
        'software', 'hardware', 'network', 'database', 'api', 'framework'
    ],
    
    classification_patterns={
        'tech_spec': r'\b(?:specification|spec|requirement|RFC\s*\d+|ISO\s*\d+)\b',
        'programming': r'\b(?:function|method|class|variable|parameter|API|SDK)\b',
        'infrastructure': r'\b(?:server|database|network|cloud|deployment|container)\b'
    },
    
    entity_patterns={
        # Technical specifications
        'version_number': r'\b[vV]?(\d+(?:\.\d+)*(?:-[\w]+)?)\b',
        'standard_reference': r'\b(?:RFC|ISO|IEEE|ANSI)\s*(\d+(?:[-:]\d+)?)\b',
        
        # Performance metrics
        'frequency': r'(\d+(?:\.\d+)?)\s*(Hz|kHz|MHz|GHz)',
        'data_size': r'(\d+(?:\.\d+)?)\s*(bytes?|KB|MB|GB|TB|PB)',
        'data_rate': r'(\d+(?:\.\d+)?)\s*(bps|Kbps|Mbps|Gbps|KB/s|MB/s)',
        'latency': r'(\d+(?:\.\d+)?)\s*(ns|μs|ms|seconds?)',
        
        # Technical components
        'ip_address': r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',
        'port_number': r'\b(?:port)\s*(\d{1,5})\b',
        'error_code': r'\b(?:error|code)\s*(\d{3,5})\b',
    },
    
    fact_patterns=[
        # Technical requirements
        (r'(?:requires?|needs?|depends on)\s+([^.;]{15,150})', 'technical_requirement', 0.8),
        (r'(?:supports?|compatible with|works with)\s+([^.;]{10,100})', 'compatibility', 0.75),
        
        # Performance specifications
        (r'(?:throughput|bandwidth)\s+of\s+(\d+(?:\.\d+)?)\s*([A-Za-z/]+)', 'performance_spec', 0.85),
        (r'(?:maximum|minimum|typical)\s+(\d+(?:\.\d+)?)\s*([A-Za-z/]+)', 'limit_spec', 0.8),
        
        # Configuration and setup
        (r'(?:configure|set|enable|disable)\s+([^.;]{10,100})', 'configuration', 0.75),
        (r'(?:default|recommended|optimal)\s+(?:value|setting)\s+(?:is|of)\s+([^.;]{5,50})', 'default_setting', 0.8),
    ],
    
    value_patterns={
        'version': r'(\d+)\.(\d+)(?:\.(\d+))?',
        'percentage': r'(\d+(?:\.\d+)?)\s*%',
        'range': r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)',
        'hex_value': r'0x([0-9A-Fa-f]+)',
    },
    
    gazetteers={
        'tech_terms': {
            'API', 'SDK', 'framework', 'library', 'module',
            'function', 'method', 'class', 'interface', 'protocol',
            'database', 'server', 'client', 'endpoint', 'service',
        },
        'protocols': {
            'HTTP', 'HTTPS', 'TCP', 'UDP', 'IP', 'DNS', 'FTP',
            'SSH', 'TLS', 'SSL', 'MQTT', 'WebSocket', 'REST', 'GraphQL',
        },
    },
    
    quality_indicators=[
        'specification', 'implementation', 'protocol', 'architecture',
        'performance', 'configuration', 'technical', 'system'
    ],
)


# ============================================================================
# RESEARCH/ACADEMIC DOMAIN
# ============================================================================

RESEARCH_DOMAIN = DomainProfile(
    name="research",
    description="Academic research papers, AI/ML, scientific publications, experimental studies",
    confidence_threshold=0.65,  # Lower threshold for academic language
    
    classification_keywords=[
        'abstract', 'introduction', 'methodology', 'results', 'conclusion',
        'experiment', 'evaluation', 'baseline', 'dataset', 'training',
        'model', 'algorithm', 'neural', 'learning', 'network', 'deep',
        'machine learning', 'artificial intelligence', 'research', 'paper',
        'study', 'analysis', 'approach', 'method', 'technique', 'framework',
        'diffusion', 'transformer', 'attention', 'convolution', 'optimization'
    ],
    
    classification_patterns={
        'academic_sections': r'\b(?:Abstract|Introduction|Related Work|Methodology|Method|Results|Discussion|Conclusion|References|Appendix)\b',
        'ml_ai_terms': r'\b(?:neural network|deep learning|machine learning|AI|ML|CNN|RNN|LSTM|GAN|VAE|BERT|GPT|transformer)\b',
        'research_format': r'\b(?:et al\.|Figure \d+|Table \d+|Section \d+|Equation \d+|\[\d+\])',
        'metrics': r'\b(?:accuracy|precision|recall|F1|AUC|BLEU|ROUGE|FID|IS|LPIPS|loss)\b',
        'citations': r'\[\d+(?:,\s*\d+)*\]|\(\d{4}[a-z]?\)',
        'academic_verbs': r'\b(?:propose|introduce|present|demonstrate|evaluate|compare|analyze|investigate)\b',
    },
    
    entity_patterns={
        # Authors and researchers
        'author_citation': r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s+et al\.?\s*\(?(\d{4}[a-z]?)?\)?',
        'researcher_email': r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.edu)\b',
        
        # Research artifacts - optimized patterns
        'model_architecture': r'\b([A-Z][a-zA-Z0-9-]{2,20})\s+(?:model|architecture|network|framework)',
        'dataset': r'\b([A-Z][A-Za-z0-9-]{2,20})\s+dataset',
        'benchmark': r'\b([A-Z][a-zA-Z-]{2,30})\s+benchmark',
        
        # Academic references
        'figure_ref': r'\b(?:Figure|Fig\.?)\s+(\d+[a-z]?)',
        'table_ref': r'\b(?:Table|Tab\.?)\s+(\d+)',
        'section_ref': r'\b(?:Section|Sec\.?)\s+(\d+(?:\.\d+)*)',
        'equation_ref': r'\b(?:Equation|Eq\.?)\s+(\d+)',
        
        # Performance metrics
        'metric_value': r'\b(accuracy|precision|recall|F1|BLEU|ROUGE|FID|IS)\s*[:=]\s*([\d.]+)%?',
        'loss_value': r'\b(loss|error|MSE|MAE)\s*[:=]\s*([\d.e-]+)',
        
        # Technical specs
        'hyperparameter': r'\b(learning rate|batch size|epochs?|iterations?|layers?|hidden units?)\s*[:=]\s*([\d.e-]+)',
        'model_params': r'\b(parameters?|params?)\s*[:=]?\s*([\d.]+)[MBK]?',
    },
    
    fact_patterns=[
        # Research contributions - optimized capture groups
        (r'(?:We propose|We introduce|We present|This paper (?:proposes?|introduces?|presents?))\s+([^.;]{10,80})', 'research_contribution', 0.9),
        (r'(?:Our (?:method|approach|model|framework)|The proposed (?:method|approach|model))\s+([^.;]{10,60})', 'methodology_description', 0.85),
        (r'(?:The main contribution|Our contribution|Key contribution)\s+(?:is|of this work is)\s+([^.;]{10,80})', 'main_contribution', 0.9),
        
        # Experimental results - optimized capture groups
        (r'(?:achieves?|obtains?|reaches?|attains?)\s+(?:an?\s+)?([^.;]*(?:accuracy|performance|score|F1|BLEU|FID)[^.;]{0,40})', 'performance_result', 0.9),
        (r'(?:outperforms?|surpasses?|exceeds?|beats?)\s+([^.;]{10,60})', 'comparison_result', 0.85),
        (r'(?:improves?|increases?|reduces?|decreases?)\s+([^.;]*(?:by|from|to)[^.;]{5,50})', 'improvement_claim', 0.8),
        
        # Experimental setup - optimized capture groups
        (r'(?:trained on|trained using|trained with|fine-tuned on)\s+([^.;]{5,60})', 'training_setup', 0.85),
        (r'(?:evaluated on|tested on|benchmarked on)\s+([^.;]{5,50})', 'evaluation_setup', 0.85),
        (r'(?:implemented in|built using|developed with|using)\s+([^.;]{5,40})', 'implementation_detail', 0.75),
        
        # Research findings - optimized capture groups
        (r'(?:We find that|We observe that|Results show that|Our findings suggest that)\s+([^.;]{10,80})', 'research_finding', 0.85),
        (r'(?:In contrast|However|Nevertheless|Surprisingly),?\s+([^.;]{10,70})', 'contrasting_finding', 0.75),
        
        # Limitations and future work - optimized capture groups
        (r'(?:limitation|challenge|drawback|issue)\s+(?:of|is|with)\s+([^.;]{5,60})', 'limitation', 0.8),
        (r'(?:future work|future research|next steps?)\s+(?:will|could|might|should|include)\s+([^.;]{5,60})', 'future_work', 0.75),
        
        # Dataset and model details - optimized capture groups
        (r'(?:dataset contains|dataset consists of|dataset includes)\s+([^.;]{5,60})', 'dataset_description', 0.8),
        (r'(?:model has|model contains|architecture includes)\s+([^.;]{5,60})', 'model_description', 0.8),
    ],
    
    value_patterns={
        # Performance metrics
        'accuracy_percentage': r'(?:accuracy|acc\.?)\s*[:=]\s*([\d.]+)%',
        'f1_score': r'(?:F1|F-1)\s*(?:score)?\s*[:=]\s*([\d.]+)',
        'bleu_score': r'(?:BLEU|BLEU-?\d+)\s*[:=]\s*([\d.]+)',
        'loss_number': r'(?:loss|error)\s*[:=]\s*([\d.e-]+)',
        
        # Training parameters
        'learning_rate_val': r'(?:learning rate|lr)\s*[:=]\s*([\d.e-]+)',
        'batch_size_val': r'(?:batch size|bs)\s*[:=]\s*(\d+)',
        'epoch_count': r'(?:epochs?|training epochs?)\s*[:=]\s*(\d+)',
        'parameter_count': r'(?:parameters?|params?)\s*[:=]?\s*([\d.]+)\s*([MBK])?',
        
        # Dataset statistics
        'sample_count': r'(?:samples?|examples?|instances?|images?)\s*[:=]?\s*([\d,]+)',
        'dataset_size': r'(?:dataset|training set|test set)(?:\s+of|\s+with|\s+contains)\s*([\d,]+)',
        'resolution': r'(?:resolution|image size)\s*[:=]?\s*(\d+)\s*[×x]\s*(\d+)',
    },
    
    gazetteers={
        'ml_models': {
            'ResNet', 'VGG', 'AlexNet', 'BERT', 'GPT', 'T5', 'CLIP', 'DALL-E',
            'Transformer', 'LSTM', 'GRU', 'CNN', 'RNN', 'GAN', 'VAE', 'U-Net',
            'DDPM', 'DDIM', 'Stable Diffusion', 'Diffusion Models', 'Autoencoder'
        },
        'datasets': {
            'ImageNet', 'MNIST', 'CIFAR-10', 'CIFAR-100', 'COCO', 'OpenImages',
            'Places365', 'CelebA', 'FFHQ', 'LSUN', 'WikiText', 'Common Crawl',
            'OpenWebText', 'BookCorpus', 'MS COCO', 'Pascal VOC'
        },
        'frameworks_libraries': {
            'TensorFlow', 'PyTorch', 'Keras', 'JAX', 'Flax', 'scikit-learn',
            'Hugging Face', 'Transformers', 'OpenAI', 'Weights & Biases',
            'wandb', 'MLflow', 'TensorBoard'
        },
        'metrics': {
            'accuracy', 'precision', 'recall', 'F1', 'F-score', 'AUC', 'ROC',
            'BLEU', 'ROUGE', 'METEOR', 'CIDEr', 'SPICE', 'FID', 'IS', 'LPIPS',
            'PSNR', 'SSIM', 'MSE', 'MAE', 'RMSE', 'perplexity'
        },
        'research_venues': {
            'NeurIPS', 'NIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI', 'ACL', 'EMNLP',
            'NAACL', 'CVPR', 'ICCV', 'ECCV', 'WACV', 'BMVC', 'ICLR', 'ICASSP'
        },
        'research_institutions': {
            'OpenAI', 'DeepMind', 'Google Research', 'Google AI', 'Facebook Research',
            'Microsoft Research', 'IBM Research', 'NVIDIA Research', 'Anthropic',
            'Stanford', 'MIT', 'CMU', 'Berkeley', 'Toronto', 'Oxford', 'Cambridge'
        }
    },
    
    relationship_patterns=[
        (r'([A-Z][a-zA-Z\s-]+?)\s+(?:builds on|extends|improves upon|is based on)\s+([A-Z][a-zA-Z\s-]+)', 'builds_on'),
        (r'([A-Z][a-zA-Z\s-]+?)\s+(?:compared (?:to|with)|vs\.?|versus)\s+([A-Z][a-zA-Z\s-]+)', 'compared_to'),
        (r'([A-Z][a-zA-Z\s-]+?)\s+(?:trained on|evaluated on|tested on)\s+([A-Z][a-zA-Z\s-]+)', 'evaluated_on'),
        (r'([A-Z][a-zA-Z\s-]+?)\s+(?:inspired by|motivated by|influenced by)\s+([A-Z][a-zA-Z\s-]+)', 'inspired_by'),
    ],
    
    quality_indicators=[
        'research', 'experiment', 'evaluation', 'baseline', 'state-of-the-art',
        'novel', 'approach', 'method', 'algorithm', 'model', 'architecture',
        'training', 'learning', 'optimization', 'performance', 'results',
        'contribution', 'findings', 'analysis', 'empirical', 'theoretical'
    ],
    
    anti_patterns=[
        'patient', 'treatment', 'diagnosis', 'clinical', 'medical',     # Medical domain
        'OSHA', 'safety', 'hazard', 'injury', 'accident', 'workplace', # Safety domain  
        'revenue', 'profit', 'earnings', 'financial', 'fiscal',        # Financial domain
        'server', 'database', 'network', 'deployment', 'infrastructure' # Technical/engineering domain
    ]
)


# ============================================================================
# HEALTHCARE/MEDICAL DOMAIN
# ============================================================================

MEDICAL_DOMAIN = DomainProfile(
    name="medical",
    description="Healthcare, clinical, pharmaceutical, medical devices",
    confidence_threshold=0.8,
    
    classification_keywords=[
        'patient', 'clinical', 'medical', 'treatment', 'diagnosis',
        'drug', 'medication', 'therapy', 'disease', 'symptom',
        'trial', 'FDA', 'healthcare', 'hospital', 'physician'
    ],
    
    classification_patterns={
        'clinical_term': r'\b(?:diagnosis|prognosis|treatment|therapy|clinical)\b',
        'medical_entity': r'\b(?:FDA|CDC|NIH|WHO|hospital|clinic)\b',
        'pharma': r'\b(?:drug|medication|dose|dosage|mg|ml|tablet|capsule)\b'
    },
    
    entity_patterns={
        # Dosage and measurements
        'dosage': r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|L|IU|units?)',
        'frequency': r'\b(once|twice|three times|QD|BID|TID|QID|PRN)\s+(?:daily|per day)',
        
        # Clinical measurements
        'blood_pressure': r'(\d{2,3})/(\d{2,3})\s*(?:mmHg)?',
        'heart_rate': r'(\d{2,3})\s*(?:bpm|beats per minute)',
        'temperature': r'(\d{2,3}(?:\.\d)?)\s*°[CF]',
        
        # Trial phases
        'trial_phase': r'\b(?:Phase|phase)\s*(I{1,3}|[1-4][ab]?)\b',
        'efficacy_rate': r'(\d+(?:\.\d+)?)\s*%\s*(?:efficacy|effectiveness|response rate)',
    },
    
    fact_patterns=[
        # Clinical findings
        (r'(?:diagnosed with|presents with|history of)\s+([^.;]{10,150})', 'clinical_diagnosis', 0.85),
        (r'(?:treatment with|treated with|prescribed)\s+([^.;]{10,100})', 'treatment_plan', 0.8),
        
        # Drug information
        (r'(?:approved for|indicated for|used to treat)\s+([^.;]{10,150})', 'drug_indication', 0.85),
        (r'(?:adverse events?|side effects?)\s+(?:include|such as)\s+([^.;]{10,200})', 'adverse_events', 0.8),
        
        # Clinical outcomes
        (r'(?:resulted in|showed|demonstrated)\s+(\d+(?:\.\d+)?%)\s+(?:improvement|reduction|increase)', 'clinical_outcome', 0.85),
    ],
    
    gazetteers={
        'medical_terms': {
            'diagnosis', 'treatment', 'therapy', 'medication',
            'surgery', 'procedure', 'examination', 'test',
            'symptom', 'syndrome', 'disease', 'disorder',
        },
        'clinical_entities': {
            'FDA', 'CDC', 'NIH', 'WHO', 'CMS',
            'Food and Drug Administration',
            'Centers for Disease Control',
            'World Health Organization',
        },
    },
    
    quality_indicators=[
        'clinical', 'patient', 'treatment', 'FDA', 'medical',
        'diagnosis', 'therapy', 'drug', 'trial'
    ],
)


# ============================================================================
# GOVERNMENT/LEGISLATIVE DOMAIN  
# ============================================================================

GOVERNMENT_DOMAIN = DomainProfile(
    name="government",
    description="Government documents, legislation, policy, appropriations",
    confidence_threshold=0.75,
    
    classification_keywords=[
        'congress', 'senate', 'house', 'bill', 'law', 'appropriation',
        'committee', 'secretary', 'department', 'federal', 'state',
        'regulation', 'policy', 'executive order', 'vote'
    ],
    
    classification_patterns={
        'legislation': r'\b(?:H\.?R\.?\s*\d+|S\.?\s*\d+|Public Law|USC)\b',
        'government_body': r'\b(?:Congress|Senate|House|Committee|Department of)\b',
        'appropriation': r'\b(?:appropriat\w+|allocat\w+|authoriz\w+)\s+\$',
    },
    
    entity_patterns={
        # Legislative identifiers
        'bill_number': r'\b([HS])\.?\s*(?:R\.?|J\.?\s*RES\.?|CON\.?\s*RES\.?)?\s*(\d+)\b',
        'public_law': r'\bPublic Law\s+(\d+)-(\d+)\b',
        'usc_reference': r'\b(\d+)\s+U\.?S\.?C\.?\s+§?\s*(\d+)',
        
        # Government entities
        'committee': r'\b(?:Committee on|Subcommittee on)\s+([A-Z][^.;,]{5,50})',
        'department': r'\b(?:Department of|Secretary of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        
        # Appropriations
        'appropriation_amount': r'appropriat\w+\s+\$?([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?',
        'fiscal_year': r'\b(?:FY|fiscal year)\s*(\d{4})\b',
    },
    
    fact_patterns=[
        # Legislative actions
        (r'(?:introduced|sponsored)\s+by\s+([^.;,]{5,100})', 'bill_sponsor', 0.85),
        (r'(?:passed|approved)\s+(?:by\s+)?(?:the\s+)?(House|Senate)', 'legislative_passage', 0.9),
        (r'appropriates?\s+\$?([\d,]+[MBK]?)\s+(?:to|for)\s+([^.;]{5,100})', 'appropriation', 0.9),
        
        # Policy directives
        (r'(?:directs?|requires?|authorizes?)\s+(?:the\s+)?([^.;]{10,150})', 'policy_directive', 0.8),
        (r'(?:establishes?|creates?)\s+([^.;]{10,150})', 'establishment', 0.8),
        
        # Voting records
        (r'(?:vote|voted|voting)\s+(\d+)\s*-\s*(\d+)', 'vote_count', 0.9),
    ],
    
    gazetteers={
        'government_bodies': {
            'Congress', 'Senate', 'House', 'White House',
            'Supreme Court', 'Cabinet', 'Federal Reserve',
        },
        'departments': {
            'DOD', 'DOE', 'DOJ', 'DOS', 'DOT', 'DOI', 'USDA',
            'Department of Defense', 'Department of Energy',
            'Department of Justice', 'State Department',
        },
    },
    
    quality_indicators=[
        'Congress', 'appropriates', 'bill', 'law', 'vote',
        'committee', 'secretary', 'federal', 'legislation'
    ],
)


# ============================================================================
# PATTERN COMPILATION AND CACHING
# ============================================================================

def compile_domain_profile(profile: DomainProfile) -> CompiledDomainProfile:
    """Compile a domain profile for high-performance extraction."""
    
    compiled = CompiledDomainProfile(
        name=profile.name,
        description=profile.description, 
        confidence_threshold=profile.confidence_threshold
    )
    
    # Pre-compile classification patterns
    for name, pattern_str in profile.classification_patterns.items():
        try:
            compiled.classification_patterns[name] = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            print(f"Warning: Failed to compile classification pattern '{name}' for {profile.name}: {e}")
    
    # Pre-compile entity patterns
    for name, pattern_str in profile.entity_patterns.items():
        try:
            compiled.entity_patterns[name] = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            print(f"Warning: Failed to compile entity pattern '{name}' for {profile.name}: {e}")
    
    # Pre-compile fact patterns
    for pattern_str, fact_type, confidence in profile.fact_patterns:
        try:
            compiled_pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
            compiled.fact_patterns.append((compiled_pattern, fact_type, confidence))
        except re.error as e:
            print(f"Warning: Failed to compile fact pattern for {profile.name}: {e}")
    
    # Pre-compile value patterns
    for name, pattern_str in profile.value_patterns.items():
        try:
            compiled.value_patterns[name] = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            print(f"Warning: Failed to compile value pattern '{name}' for {profile.name}: {e}")
    
    # Convert lists to fast sets for O(1) lookup
    compiled.classification_keywords_set = set(keyword.lower() for keyword in profile.classification_keywords)
    compiled.quality_indicators_set = set(indicator.lower() for indicator in profile.quality_indicators)  
    compiled.anti_patterns_set = set(pattern.lower() for pattern in profile.anti_patterns)
    
    # Copy gazetteers as-is (already sets)
    compiled.gazetteers = profile.gazetteers.copy()
    
    return compiled


# Global compiled pattern cache
COMPILED_DOMAIN_CACHE: Dict[str, CompiledDomainProfile] = {}


def get_compiled_domain_profile(domain_name: str) -> Optional[CompiledDomainProfile]:
    """Get compiled domain profile from cache, compiling if needed."""
    
    domain_name_lower = domain_name.lower()
    
    # Check cache first
    if domain_name_lower in COMPILED_DOMAIN_CACHE:
        return COMPILED_DOMAIN_CACHE[domain_name_lower]
    
    # Get base profile
    base_profile = DOMAIN_REGISTRY.get(domain_name_lower)
    if not base_profile:
        return None
    
    # Compile and cache
    print(f"Compiling patterns for {domain_name} domain...")
    start_time = time.time()
    compiled = compile_domain_profile(base_profile)
    compile_time = time.time() - start_time
    print(f"Compiled {len(compiled.fact_patterns)} fact patterns + {len(compiled.entity_patterns)} entity patterns in {compile_time:.3f}s")
    
    COMPILED_DOMAIN_CACHE[domain_name_lower] = compiled
    return compiled


# ============================================================================
# DOMAIN REGISTRY
# ============================================================================

DOMAIN_REGISTRY = {
    'safety': SAFETY_DOMAIN,
    'safety_compliance': SAFETY_DOMAIN,
    'financial': FINANCIAL_DOMAIN,
    'finance': FINANCIAL_DOMAIN,
    'technical': TECHNICAL_DOMAIN,
    'engineering': TECHNICAL_DOMAIN,
    'research': RESEARCH_DOMAIN,
    'academic': RESEARCH_DOMAIN,
    'ml': RESEARCH_DOMAIN,
    'ai': RESEARCH_DOMAIN,
    'medical': MEDICAL_DOMAIN,
    'healthcare': MEDICAL_DOMAIN,
    'government': GOVERNMENT_DOMAIN,
    'legislative': GOVERNMENT_DOMAIN,
    'policy': GOVERNMENT_DOMAIN,
}


# ============================================================================
# DOMAIN CLASSIFICATION
# ============================================================================

def classify_document_domain(content: str, existing_tags: Optional[Dict] = None) -> Tuple[str, float]:
    """
    Classify document into a domain based on content and existing tags.
    Returns (domain_name, confidence).
    """
    
    # If we have high-confidence existing tags, use them
    if existing_tags:
        if 'domains' in existing_tags and existing_tags['domains']:
            # Parse domain from tags like "safety: 70%"
            primary_domain = existing_tags['domains'][0].split(':')[0].strip().lower()
            
            # Map to our domain registry
            if primary_domain in DOMAIN_REGISTRY:
                return primary_domain, 0.9  # High confidence from tagger
            
        if 'document_types' in existing_tags and existing_tags['document_types']:
            primary_type = existing_tags['document_types'][0].split(':')[0].strip().lower()
            
            # Map document type to domain
            type_to_domain = {
                'safety': 'safety',
                'financial': 'financial',
                'technical': 'technical',
                'research': 'research',
                'academic': 'research',
                'legal': 'government',
                'business': 'financial',
            }
            
            if primary_type in type_to_domain:
                return type_to_domain[primary_type], 0.85
    
    # Fallback to content-based classification using compiled patterns
    content_lower = content.lower()
    content_sample = content[:5000]  # First 5000 chars for pattern matching
    domain_scores = {}
    
    for domain_name, profile in DOMAIN_REGISTRY.items():
        score = 0.0
        
        # Get compiled profile (will compile and cache if needed)
        compiled_profile = get_compiled_domain_profile(domain_name)
        if not compiled_profile:
            continue
        
        # Check classification keywords (fast set lookup)
        for keyword in profile.classification_keywords:
            if keyword in content_lower:
                score += 1.0
        
        # Check classification patterns (pre-compiled)
        for pattern_name, compiled_pattern in compiled_profile.classification_patterns.items():
            matches = len(compiled_pattern.findall(content_sample))
            score += matches * 2.0  # Patterns worth more than keywords
        
        # Check for anti-patterns (fast set lookup)
        for anti_pattern in compiled_profile.anti_patterns_set:
            if anti_pattern in content_lower:
                score -= 0.5
        
        domain_scores[domain_name] = score
    
    # Get the highest scoring domain
    if domain_scores:
        best_domain = max(domain_scores.items(), key=lambda x: x[1])
        if best_domain[1] > 0:
            # Calculate confidence based on score
            confidence = min(0.95, 0.5 + (best_domain[1] / 50.0))
            return best_domain[0], confidence
    
    return 'general', 0.5  # Default fallback


# ============================================================================
# DOMAIN-SPECIFIC EXTRACTION
# ============================================================================

def extract_domain_facts(content: str, domain_profile: DomainProfile) -> List[DomainFact]:
    """
    Extract domain-specific facts using pre-compiled patterns for performance.
    """
    facts = []
    
    # Get compiled profile for fast pattern matching
    compiled_profile = get_compiled_domain_profile(domain_profile.name)
    if not compiled_profile:
        return facts
    
    # Extract facts using pre-compiled patterns
    for compiled_pattern, fact_type, base_confidence in compiled_profile.fact_patterns:
        
        for match in compiled_pattern.finditer(content):
            # Build core fact
            core_fact = CoreFact(
                subject=domain_profile.name,
                predicate=fact_type,
                object=None,
                value=match.group(1) if match.lastindex >= 1 else None,
                unit=match.group(2) if match.lastindex >= 2 else None,
                date=None,
                location=None,
                confidence=base_confidence
            )
            
            # Get surrounding context
            context_start = max(0, match.start() - 100)
            context_end = min(len(content), match.end() + 100)
            context = content[context_start:context_end]
            context_lower = context.lower()
            
            # Check for quality indicators in context (fast set lookup)
            quality_boost = 0.0
            for indicator in compiled_profile.quality_indicators_set:
                if indicator in context_lower:
                    quality_boost += 0.02
            
            core_fact.confidence = min(0.95, core_fact.confidence + quality_boost)
            
            # Only keep high-confidence facts
            if core_fact.confidence >= compiled_profile.confidence_threshold:
                domain_fact = DomainFact(
                    core=core_fact,
                    domain=domain_profile.name,
                    fact_type=fact_type,
                    domain_attributes={
                        'match_text': match.group(0),
                        'context': context.strip(),
                        'span': (match.start(), match.end()),
                    },
                    extraction_pattern=f"compiled_{fact_type}"
                )
                facts.append(domain_fact)
    
    return facts


def extract_domain_entities(content: str, domain_profile: DomainProfile) -> Dict[str, List[Tuple[str, int, int]]]:
    """
    Extract domain-specific entities using pre-compiled patterns for performance.
    Returns dict of entity_type -> [(text, start, end), ...]
    """
    entities = {}
    
    # Get compiled profile for fast pattern matching
    compiled_profile = get_compiled_domain_profile(domain_profile.name)
    if not compiled_profile:
        return entities
    
    for entity_type, compiled_pattern in compiled_profile.entity_patterns.items():
        matches = []
        
        for match in compiled_pattern.finditer(content):
            matches.append((
                match.group(0),
                match.start(),
                match.end()
            ))
        
        if matches:
            entities[entity_type] = matches
    
    return entities


def extract_domain_values(content: str, domain_profile: DomainProfile) -> List[Dict[str, Any]]:
    """
    Extract numerical values with units using pre-compiled patterns for performance.
    """
    values = []
    
    # Get compiled profile for fast pattern matching
    compiled_profile = get_compiled_domain_profile(domain_profile.name)
    if not compiled_profile:
        return values
    
    for value_type, compiled_pattern in compiled_profile.value_patterns.items():
        
        for match in compiled_pattern.finditer(content):
            value_dict = {
                'type': value_type,
                'value': match.group(1),
                'unit': match.group(2) if match.lastindex >= 2 else None,
                'text': match.group(0),
                'span': (match.start(), match.end())
            }
            values.append(value_dict)
    
    return values


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def get_domain_profile(domain_name: str) -> Optional[DomainProfile]:
    """Get domain profile by name."""
    return DOMAIN_REGISTRY.get(domain_name.lower())


def enhance_facts_with_domain(core_facts: List[Dict], domain_name: str) -> List[DomainFact]:
    """
    Enhance core foundational facts with domain-specific attributes.
    """
    profile = get_domain_profile(domain_name)
    if not profile:
        return []
    
    enhanced_facts = []
    
    for core_fact_dict in core_facts:
        # Convert dict to CoreFact
        core_fact = CoreFact(
            subject=core_fact_dict.get('subject', ''),
            predicate=core_fact_dict.get('predicate', ''),
            object=core_fact_dict.get('object'),
            value=core_fact_dict.get('value'),
            unit=core_fact_dict.get('unit'),
            date=core_fact_dict.get('date'),
            location=core_fact_dict.get('location'),
            confidence=core_fact_dict.get('confidence', 0.7)
        )
        
        # Check if fact matches domain patterns
        domain_attributes = {}
        
        # Check against gazetteers
        for gazetteer_name, terms in profile.gazetteers.items():
            if core_fact.subject in terms or core_fact.object in terms:
                domain_attributes['gazetteer_match'] = gazetteer_name
                core_fact.confidence = min(0.95, core_fact.confidence + 0.1)
        
        # Create enhanced domain fact
        domain_fact = DomainFact(
            core=core_fact,
            domain=domain_name,
            fact_type=core_fact.predicate,
            domain_attributes=domain_attributes,
            extraction_pattern='core_enhancement'
        )
        
        enhanced_facts.append(domain_fact)
    
    return enhanced_facts


# ============================================================================
# FACT QUALITY SCORING
# ============================================================================

def score_fact_quality(fact: DomainFact, domain_profile: DomainProfile) -> float:
    """
    Score the quality of an extracted fact based on domain indicators.
    Returns score between 0.0 and 1.0.
    """
    score = fact.core.confidence
    
    # Check for quality indicators
    context = fact.domain_attributes.get('context', '')
    if context:
        context_lower = context.lower()
        
        # Boost for quality indicators
        for indicator in domain_profile.quality_indicators:
            if indicator.lower() in context_lower:
                score = min(1.0, score + 0.05)
        
        # Penalty for anti-patterns
        for anti_pattern in domain_profile.anti_patterns:
            if anti_pattern.lower() in context_lower:
                score = max(0.0, score - 0.1)
    
    # Boost for complete information
    if fact.core.subject and fact.core.object and fact.core.value:
        score = min(1.0, score + 0.1)
    
    # Boost for temporal information
    if fact.core.date:
        score = min(1.0, score + 0.05)
    
    return score


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def facts_to_json(facts: List[DomainFact]) -> List[Dict]:
    """Convert domain facts to JSON-serializable format."""
    json_facts = []
    
    for fact in facts:
        json_fact = {
            'domain': fact.domain,
            'type': fact.fact_type,
            'subject': fact.core.subject,
            'predicate': fact.core.predicate,
            'object': fact.core.object,
            'value': fact.core.value,
            'unit': fact.core.unit,
            'date': fact.core.date,
            'location': fact.core.location,
            'confidence': fact.core.confidence,
            'attributes': fact.domain_attributes,
            'pattern': fact.extraction_pattern,
        }
        
        # Add compliance level if present
        if fact.compliance_level:
            json_fact['compliance_level'] = fact.compliance_level
        
        json_facts.append(json_fact)
    
    return json_facts


if __name__ == "__main__":
    # Example usage
    sample_text = """
    OSHA requires employers to provide fall protection at elevations of 4 feet 
    in general industry workplaces. Guardrails must be 42 inches high and capable 
    of withstanding 200 pounds of force. Workers must be trained annually on 
    fall hazard recognition. Violations can result in penalties of up to $13,653 
    per violation.
    """
    
    # Classify domain
    domain, confidence = classify_document_domain(sample_text)
    print(f"Domain: {domain} (confidence: {confidence:.2f})")
    
    # Get domain profile
    profile = get_domain_profile(domain)
    if profile:
        # Extract domain facts
        facts = extract_domain_facts(sample_text, profile)
        print(f"\nExtracted {len(facts)} domain facts:")
        
        for fact in facts:
            print(f"  - {fact.fact_type}: {fact.core.value}")
            if fact.core.unit:
                print(f"    Unit: {fact.core.unit}")
            print(f"    Confidence: {fact.core.confidence:.2f}")