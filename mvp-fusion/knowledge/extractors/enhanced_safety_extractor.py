"""
Enhanced Safety Knowledge Extractor for Scout MVP-Fusion
Production-ready knowledge extraction using Rust regex (FLPC)
Optimized for OSHA and safety compliance documents
"""

try:
    from . import fast_regex as re  # MVP-Fusion standard: FLPC Rust regex
except ImportError:
    # Fallback for standalone execution
    import fast_regex as re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class ComplianceRequirement:
    """Detailed compliance requirement with full context"""
    requirement_text: str
    measurement: Optional[str] = None
    condition: Optional[str] = None
    target: str = ""
    regulation_ref: str = ""
    page_ref: int = 0
    confidence: float = 0.0
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class SafetyHazard:
    """Identified safety hazard with risk assessment"""
    hazard_type: str
    description: str
    severity: str  # low, medium, high, critical
    affected_parties: List[str]
    mitigation: Optional[str] = None
    statistics: Optional[str] = None
    
@dataclass
class EquipmentSpecification:
    """Detailed equipment specification"""
    equipment_name: str
    category: str  # access, protection, safety, monitoring
    specifications: Dict[str, Any]
    required: bool
    conditions: List[str]
    standards: List[str]

@dataclass
class MVPOpportunity:
    """Business opportunity for Scout's MVP development"""
    opportunity_type: str  # compliance_automation, safety_monitoring, training, etc.
    pain_point: str
    market_size: str
    solution_description: str
    technical_requirements: List[str]
    regulatory_drivers: List[str]
    confidence: float

class EnhancedSafetyKnowledgeExtractor:
    """
    Production-ready safety knowledge extraction for Scout
    Uses FLPC Rust regex for maximum performance
    """
    
    def __init__(self):
        # Compile all patterns once for performance
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Pre-compile all regex patterns using FLPC for performance"""
        
        # Measurement patterns - expanded for more formats
        self.measurement_patterns = {
            'imperial_metric': re.compile(r'(\d+(?:\.\d+)?)\s*(inches?|feet?|yards?)\s*\((\d+(?:\.\d+)?)\s*(cm|m|mm)\)'),
            'metric_only': re.compile(r'(\d+(?:\.\d+)?)\s*(cm|m|mm|km)\b'),
            'imperial_only': re.compile(r'(\d+(?:\.\d+)?)\s*(inches?|feet?|yards?|miles?)\b'),
            'degrees': re.compile(r'(\d+(?:\.\d+)?)\s*degrees?\b'),
            'percentage': re.compile(r'(\d+(?:\.\d+)?)\s*%'),
            'ratio': re.compile(r'(\d+):(\d+)\s*ratio'),
        }
        
        # Regulatory patterns - comprehensive coverage
        self.regulatory_patterns = {
            'osha': re.compile(r'OSHA\s+(\d+[-\w]*(?:\.\d+)?)'),
            'cfr': re.compile(r'(\d+)\s+CFR\s+([\d.]+)'),
            'section': re.compile(r'[Ss]ection\s+([\d.]+(?:\([a-z]\))?)'),
            'standard': re.compile(r'[Ss]tandard\s+(\d+[-\w]+)'),
            'ansi': re.compile(r'ANSI\s+([A-Z]\d+\.?\d*[-\w]*)'),
            'iso': re.compile(r'ISO\s+(\d+(?:[-:]\d+)?)'),
        }
        
        # Requirement patterns - action-oriented
        self.requirement_patterns = {
            'must_provide': re.compile(r'(employers?\s+)?must\s+provide\s+([^.]+)'),
            'shall_ensure': re.compile(r'shall\s+ensure\s+([^.]+)'),
            'required_to': re.compile(r'(is|are)\s+required\s+to\s+([^.]+)'),
            'prohibited': re.compile(r'(is|are)\s+prohibited\s+from\s+([^.]+)'),
            'mandatory': re.compile(r'mandatory\s+([^.]+)'),
        }
        
        # Equipment patterns with specifications
        self.equipment_patterns = {
            'access': re.compile(r'\b(stairway|ladder|ramp|runway|scaffold|platform)s?\b', re.IGNORECASE),
            'protection': re.compile(r'\b(guardrail|handrail|safety net|harness|barrier|fence)s?\b', re.IGNORECASE),
            'ppe': re.compile(r'\b(hard hat|safety glasses|gloves|respirator|safety shoes)s?\b', re.IGNORECASE),
            'systems': re.compile(r'\b(fall protection system|warning system|ventilation system)s?\b', re.IGNORECASE),
        }
        
        # Hazard indicators
        self.hazard_patterns = {
            'injury_types': re.compile(r'\b(injuries|fatalities|accidents|incidents|falls|struck by)\b', re.IGNORECASE),
            'risk_levels': re.compile(r'\b(hazardous|dangerous|unsafe|risk|exposure|threat)\b', re.IGNORECASE),
            'statistics': re.compile(r'(\d+(?:,\d+)?)\s*(?:injuries|fatalities|accidents)\s*(?:per|annually|yearly)'),
        }
        
        # Business/MVP opportunity patterns
        self.opportunity_patterns = {
            'compliance_gap': re.compile(r'\b(difficult|complex|time-consuming|costly|manual)\s+(?:to\s+)?(?:comply|implement|maintain)\b'),
            'training_need': re.compile(r'\b(training|education|certification|qualified)\s+(?:is\s+)?(?:required|needed|mandatory)\b'),
            'monitoring_gap': re.compile(r'\b(inspection|monitoring|tracking|reporting)\s+(?:is\s+)?(?:required|needed)\b'),
        }
    
    def extract_compliance_requirements(self, text: str) -> List[ComplianceRequirement]:
        """Extract detailed compliance requirements with full context"""
        requirements = []
        
        # Split into sentences for context (FLPC doesn't support lookbehind)
        sentences = re.split(r'[.!?]+', text)
        
        for i, sentence in enumerate(sentences):
            # Check for requirement triggers
            for req_type, pattern in self.requirement_patterns.items():
                matches = re.findall(pattern, sentence)
                if matches:
                    # Look for associated measurements
                    measurement = None
                    for meas_pattern in self.measurement_patterns.values():
                        meas_match = meas_pattern.search(sentence)
                        if meas_match:
                            measurement = meas_match.group(0)
                            break
                    
                    # Look for regulation references
                    reg_ref = ""
                    for reg_pattern in self.regulatory_patterns.values():
                        reg_match = reg_pattern.search(sentence)
                        if reg_match:
                            reg_ref = reg_match.group(0)
                            break
                    
                    # Extract condition (when/where/if clauses)
                    condition = self._extract_condition(sentence)
                    
                    req = ComplianceRequirement(
                        requirement_text=sentence.strip(),
                        measurement=measurement,
                        condition=condition,
                        target=req_type,
                        regulation_ref=reg_ref,
                        confidence=0.9 if reg_ref else 0.7
                    )
                    requirements.append(req)
        
        return requirements
    
    def extract_safety_hazards(self, text: str) -> List[SafetyHazard]:
        """Extract safety hazards with risk assessment"""
        hazards = []
        seen_hazards = set()  # Avoid duplicates
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Check for hazard indicators
            for hazard_type, pattern in self.hazard_patterns.items():
                if pattern.search(sentence):
                    # Determine severity
                    severity = self._assess_severity(sentence)
                    
                    # Extract affected parties
                    affected = self._extract_affected_parties(sentence)
                    
                    # Look for statistics
                    stats_match = self.hazard_patterns['statistics'].search(sentence)
                    statistics = stats_match.group(0) if stats_match else None
                    
                    hazard_key = f"{hazard_type}:{sentence[:50]}"
                    if hazard_key not in seen_hazards:
                        seen_hazards.add(hazard_key)
                        hazard = SafetyHazard(
                            hazard_type=hazard_type,
                            description=sentence.strip(),
                            severity=severity,
                            affected_parties=affected,
                            statistics=statistics
                        )
                        hazards.append(hazard)
        
        return hazards
    
    def extract_equipment_specifications(self, text: str) -> List[EquipmentSpecification]:
        """Extract detailed equipment specifications"""
        equipment_list = []
        
        for category, pattern in self.equipment_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                equipment_name = match.group(0)
                
                # Get context around equipment mention
                start = max(0, match.start(0) - 100)
                end = min(len(text), match.end(0) + 100)
                context = text[start:end]
                
                # Extract specifications
                specs = self._extract_specifications(context)
                
                # Check if required
                required = any(word in context.lower() for word in ['must', 'shall', 'required'])
                
                # Extract conditions
                conditions = self._extract_conditions_list(context)
                
                # Extract standards
                standards = []
                for reg_pattern in self.regulatory_patterns.values():
                    reg_matches = reg_pattern.findall(context)
                    standards.extend([match if isinstance(match, str) else match[0] for match in reg_matches])
                
                equipment = EquipmentSpecification(
                    equipment_name=equipment_name,
                    category=category,
                    specifications=specs,
                    required=required,
                    conditions=conditions,
                    standards=standards
                )
                equipment_list.append(equipment)
        
        return equipment_list
    
    def extract_mvp_opportunities(self, text: str) -> List[MVPOpportunity]:
        """Extract MVP opportunities for Scout's development"""
        opportunities = []
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            for opp_type, pattern in self.opportunity_patterns.items():
                if pattern.search(sentence):
                    # Identify pain point
                    pain_point = self._identify_pain_point(sentence)
                    
                    # Generate solution description
                    solution = self._generate_solution(opp_type, pain_point)
                    
                    # Extract regulatory drivers
                    reg_drivers = []
                    for reg_pattern in self.regulatory_patterns.values():
                        reg_matches = reg_pattern.findall(sentence)
                        reg_drivers.extend([m if isinstance(m, str) else m[0] for m in reg_matches])
                    
                    opportunity = MVPOpportunity(
                        opportunity_type=opp_type,
                        pain_point=pain_point,
                        market_size="Construction Safety Market",
                        solution_description=solution,
                        technical_requirements=self._get_tech_requirements(opp_type),
                        regulatory_drivers=reg_drivers,
                        confidence=0.8 if reg_drivers else 0.6
                    )
                    opportunities.append(opportunity)
        
        return opportunities
    
    def extract_all_knowledge(self, text: str) -> Dict[str, Any]:
        """
        High-performance batch extraction using Rust regex
        Returns comprehensive knowledge graph for Scout
        """
        return {
            'compliance_requirements': self.extract_compliance_requirements(text),
            'safety_hazards': self.extract_safety_hazards(text),
            'equipment_specifications': self.extract_equipment_specifications(text),
            'mvp_opportunities': self.extract_mvp_opportunities(text),
            'metadata': {
                'extraction_timestamp': datetime.now().isoformat(),
                'engine': 'FLPC Rust Regex',
                'version': '2.0',
                'document_type': 'safety_compliance'
            }
        }
    
    # Helper methods
    def _extract_condition(self, text: str) -> str:
        """Extract conditional context"""
        condition_patterns = [
            re.compile(r'[Ww]hen\s+([^,]+)'),
            re.compile(r'[Ii]f\s+([^,]+)'),
            re.compile(r'[Ww]here\s+([^,]+)'),
        ]
        for pattern in condition_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""
    
    def _assess_severity(self, text: str) -> str:
        """Assess hazard severity based on keywords"""
        if any(word in text.lower() for word in ['fatal', 'death', 'killed']):
            return 'critical'
        elif any(word in text.lower() for word in ['serious', 'severe', 'major']):
            return 'high'
        elif any(word in text.lower() for word in ['injury', 'accident']):
            return 'medium'
        return 'low'
    
    def _extract_affected_parties(self, text: str) -> List[str]:
        """Extract who is affected by hazards"""
        parties = []
        party_pattern = re.compile(r'\b(workers?|employees?|contractors?|employers?|supervisors?|inspectors?)\b', re.IGNORECASE)
        matches = party_pattern.findall(text)
        return list(set(matches))
    
    def _extract_specifications(self, text: str) -> Dict[str, Any]:
        """Extract technical specifications from context"""
        specs = {}
        
        # Look for measurements
        for name, pattern in self.measurement_patterns.items():
            matches = pattern.findall(text)
            if matches:
                specs[name] = matches
        
        # Look for materials
        material_pattern = re.compile(r'\b(wood|metal|steel|aluminum|fiberglass)\b', re.IGNORECASE)
        materials = material_pattern.findall(text)
        if materials:
            specs['materials'] = list(set(materials))
        
        return specs
    
    def _extract_conditions_list(self, text: str) -> List[str]:
        """Extract multiple conditions"""
        conditions = []
        condition_words = ['when', 'if', 'where', 'unless', 'during', 'after', 'before']
        for word in condition_words:
            pattern = re.compile(rf'\b{word}\s+([^,]+)', re.IGNORECASE)
            matches = pattern.findall(text)
            conditions.extend(matches)
        return conditions
    
    def _identify_pain_point(self, text: str) -> str:
        """Identify specific pain point from text"""
        pain_indicators = {
            'time': 'time-consuming compliance processes',
            'cost': 'expensive compliance implementation',
            'complex': 'complex regulatory requirements',
            'manual': 'manual tracking and reporting',
            'difficult': 'difficult to maintain compliance'
        }
        for indicator, description in pain_indicators.items():
            if indicator in text.lower():
                return description
        return 'compliance challenge'
    
    def _generate_solution(self, opp_type: str, pain_point: str) -> str:
        """Generate solution description based on opportunity type"""
        solutions = {
            'compliance_gap': f'Automated compliance management platform to address {pain_point}',
            'training_need': f'Digital training and certification system for {pain_point}',
            'monitoring_gap': f'Real-time monitoring and reporting dashboard for {pain_point}'
        }
        return solutions.get(opp_type, f'Digital solution for {pain_point}')
    
    def _get_tech_requirements(self, opp_type: str) -> List[str]:
        """Get technical requirements for opportunity type"""
        tech_reqs = {
            'compliance_gap': ['Document parsing', 'Rules engine', 'Compliance tracking', 'Reporting'],
            'training_need': ['LMS integration', 'Video content', 'Quiz engine', 'Certificate generation'],
            'monitoring_gap': ['IoT sensors', 'Real-time data', 'Alert system', 'Analytics dashboard']
        }
        return tech_reqs.get(opp_type, ['Web platform', 'Mobile app', 'Cloud storage'])

def process_osha_document(text: str) -> Dict[str, Any]:
    """
    Process OSHA document and extract all knowledge
    Ready for Scout's MVP intelligence pipeline
    """
    extractor = EnhancedSafetyKnowledgeExtractor()
    knowledge = extractor.extract_all_knowledge(text)
    
    # Add summary statistics
    knowledge['summary'] = {
        'total_requirements': len(knowledge['compliance_requirements']),
        'total_hazards': len(knowledge['safety_hazards']),
        'total_equipment': len(knowledge['equipment_specifications']),
        'total_opportunities': len(knowledge['mvp_opportunities']),
        'high_confidence_items': sum(1 for req in knowledge['compliance_requirements'] if req.confidence >= 0.8)
    }
    
    return knowledge

if __name__ == "__main__":
    # Test with sample OSHA text
    sample_text = """
    Working on and around stairways and ladders is hazardous. Stairways and ladders are major
    sources of injuries and fatalities among construction workers for example, and many of the 
    injuries are serious enough to require time off the job. OSHA rules apply to all stairways 
    and ladders used in construction. When there is a break in elevation of 19 inches (48 cm) 
    or more and no ramp, runway, embankment or personnel hoist is available, employers must 
    provide a stairway or ladder at all worker points of access. OSHA 3124-12R 2003.
    """
    
    result = process_osha_document(sample_text)
    print(json.dumps(result, default=str, indent=2))