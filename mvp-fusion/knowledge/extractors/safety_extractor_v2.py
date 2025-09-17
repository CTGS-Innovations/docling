"""
Enhanced Safety Knowledge Extractor V2 for Scout MVP-Fusion
Production-ready knowledge extraction using Rust regex (FLPC)
Properly handles FLPC's module-function architecture
"""

try:
    from . import fast_regex as re  # MVP-Fusion standard: FLPC Rust regex
except ImportError:
    import sys
    sys.path.insert(0, '.')
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
    regulation_ref: str = ""
    confidence: float = 0.0

@dataclass
class SafetyHazard:
    """Identified safety hazard with risk assessment"""
    hazard_type: str
    description: str
    severity: str
    affected_parties: List[str]

@dataclass  
class EquipmentSpecification:
    """Equipment with requirements"""
    equipment_name: str
    category: str
    required: bool
    standards: List[str]

@dataclass
class MVPOpportunity:
    """Business opportunity for Scout"""
    opportunity_type: str
    pain_point: str
    solution: str
    confidence: float

class SafetyKnowledgeExtractorV2:
    """
    Production-ready safety knowledge extraction
    Properly uses FLPC module functions (no pre-compilation)
    """
    
    def __init__(self):
        # Define pattern strings (not compiled)
        self.measurement_pattern = r'(\d+(?:\.\d+)?)\s*(inches?|feet?|cm|m)\s*(?:\(([^)]+)\))?'
        self.osha_pattern = r'OSHA\s+(\d+[-\w]*)'
        self.cfr_pattern = r'(\d+)\s+CFR\s+([\d.]+)'
        self.requirement_triggers = ['must provide', 'shall', 'required', 'employers must']
        
    def extract_compliance_requirements(self, text: str) -> List[ComplianceRequirement]:
        """Extract compliance requirements using FLPC"""
        requirements = []
        
        # Split into sentences (simple split for FLPC compatibility)
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Check for requirement triggers
            for trigger in self.requirement_triggers:
                if trigger.lower() in sentence.lower():
                    # Extract measurements
                    measurement = None
                    meas_matches = re.findall(self.measurement_pattern, sentence)
                    if meas_matches:
                        measurement = ' '.join(meas_matches[0])
                    
                    # Extract regulation references
                    reg_ref = ""
                    osha_matches = re.findall(self.osha_pattern, sentence)
                    if osha_matches:
                        reg_ref = f"OSHA {osha_matches[0]}"
                    else:
                        cfr_matches = re.findall(self.cfr_pattern, sentence)
                        if cfr_matches:
                            reg_ref = f"{cfr_matches[0][0]} CFR {cfr_matches[0][1]}"
                    
                    # Extract condition
                    condition = ""
                    if "when" in sentence.lower():
                        when_pattern = r'[Ww]hen\s+([^,]+)'
                        when_matches = re.findall(when_pattern, sentence)
                        if when_matches:
                            condition = when_matches[0]
                    
                    req = ComplianceRequirement(
                        requirement_text=sentence.strip(),
                        measurement=measurement,
                        condition=condition,
                        regulation_ref=reg_ref,
                        confidence=0.9 if reg_ref else 0.7
                    )
                    requirements.append(req)
                    break  # Only add once per sentence
        
        return requirements
    
    def extract_safety_hazards(self, text: str) -> List[SafetyHazard]:
        """Extract safety hazards with risk assessment"""
        hazards = []
        
        # Hazard patterns
        hazard_pattern = r'\b(injuries|fatalities|accidents|hazardous|dangerous)\b'
        worker_pattern = r'\b(workers?|employees?|contractors?)\b'
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            hazard_matches = re.findall(hazard_pattern, sentence, re.IGNORECASE)
            if hazard_matches:
                # Assess severity
                severity = 'high' if 'fatal' in sentence.lower() else 'medium'
                
                # Find affected parties
                affected = re.findall(worker_pattern, sentence, re.IGNORECASE)
                
                hazard = SafetyHazard(
                    hazard_type=hazard_matches[0],
                    description=sentence.strip(),
                    severity=severity,
                    affected_parties=list(set(affected)) if affected else ['workers']
                )
                hazards.append(hazard)
        
        return hazards
    
    def extract_equipment(self, text: str) -> List[EquipmentSpecification]:
        """Extract equipment specifications"""
        equipment_list = []
        
        # Equipment patterns
        access_pattern = r'\b(stairway|ladder|ramp|runway|scaffold)s?\b'
        protection_pattern = r'\b(guardrail|handrail|harness|barrier)s?\b'
        
        # Find access equipment
        access_matches = re.finditer(access_pattern, text, re.IGNORECASE)
        for match in access_matches:
            # Get context
            start = max(0, match.start(0) - 50)
            end = min(len(text), match.end(0) + 50)
            context = text[start:end]
            
            # Check if required
            required = any(word in context.lower() for word in ['must', 'shall', 'required'])
            
            # Find standards
            standards = []
            osha_refs = re.findall(self.osha_pattern, context)
            standards.extend([f"OSHA {ref}" for ref in osha_refs])
            
            equipment = EquipmentSpecification(
                equipment_name=match.group(0),
                category='access',
                required=required,
                standards=standards
            )
            equipment_list.append(equipment)
        
        # Find protection equipment
        protection_matches = re.finditer(protection_pattern, text, re.IGNORECASE)
        for match in protection_matches:
            start = max(0, match.start(0) - 50)
            end = min(len(text), match.end(0) + 50)
            context = text[start:end]
            
            required = any(word in context.lower() for word in ['must', 'shall', 'required'])
            
            standards = []
            osha_refs = re.findall(self.osha_pattern, context)
            standards.extend([f"OSHA {ref}" for ref in osha_refs])
            
            equipment = EquipmentSpecification(
                equipment_name=match.group(0),
                category='protection',
                required=required,
                standards=standards
            )
            equipment_list.append(equipment)
        
        return equipment_list
    
    def extract_mvp_opportunities(self, text: str) -> List[MVPOpportunity]:
        """Extract MVP opportunities for Scout"""
        opportunities = []
        
        # Opportunity patterns
        pain_pattern = r'\b(time off|costly|complex|difficult|manual)\b'
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            pain_matches = re.findall(pain_pattern, sentence, re.IGNORECASE)
            if pain_matches:
                pain_point = pain_matches[0]
                
                # Determine opportunity type
                if 'time off' in sentence.lower() or 'injuries' in sentence.lower():
                    opp_type = 'safety_monitoring'
                    solution = 'Real-time safety monitoring system to prevent injuries'
                elif 'costly' in sentence.lower() or 'expensive' in sentence.lower():
                    opp_type = 'cost_reduction'
                    solution = 'Automated compliance system to reduce costs'
                else:
                    opp_type = 'compliance_automation'
                    solution = 'Digital compliance management platform'
                
                opportunity = MVPOpportunity(
                    opportunity_type=opp_type,
                    pain_point=f"{pain_point} mentioned in safety context",
                    solution=solution,
                    confidence=0.7
                )
                opportunities.append(opportunity)
        
        return opportunities
    
    def extract_all_knowledge(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive knowledge using FLPC Rust regex"""
        return {
            'compliance_requirements': [
                {
                    'text': req.requirement_text,
                    'measurement': req.measurement,
                    'condition': req.condition,
                    'regulation': req.regulation_ref,
                    'confidence': req.confidence
                }
                for req in self.extract_compliance_requirements(text)
            ],
            'safety_hazards': [
                {
                    'type': hazard.hazard_type,
                    'description': hazard.description,
                    'severity': hazard.severity,
                    'affected': hazard.affected_parties
                }
                for hazard in self.extract_safety_hazards(text)
            ],
            'equipment': [
                {
                    'name': eq.equipment_name,
                    'category': eq.category,
                    'required': eq.required,
                    'standards': eq.standards
                }
                for eq in self.extract_equipment(text)
            ],
            'mvp_opportunities': [
                {
                    'type': opp.opportunity_type,
                    'pain_point': opp.pain_point,
                    'solution': opp.solution,
                    'confidence': opp.confidence
                }
                for opp in self.extract_mvp_opportunities(text)
            ],
            'metadata': {
                'engine': 'FLPC Rust Regex',
                'extraction_time': datetime.now().isoformat()
            }
        }

if __name__ == "__main__":
    # Test with real OSHA text
    osha_text = """
    Working on and around stairways and ladders is hazardous. Stairways and ladders are major
    sources of injuries and fatalities among construction workers for example, and many of the 
    injuries are serious enough to require time off the job. OSHA rules apply to all stairways 
    and ladders used in construction, alteration, repair, painting, decorating and demolition.
    When there is a break in elevation of 19 inches (48 cm) or more and no ramp, runway,
    embankment or personnel hoist is available, employers must provide a stairway or ladder
    at all worker points of access. OSHA 3124-12R 2003 Stairways and Ladders.
    """
    
    extractor = SafetyKnowledgeExtractorV2()
    knowledge = extractor.extract_all_knowledge(osha_text)
    
    print("=== KNOWLEDGE EXTRACTION RESULTS ===")
    print(json.dumps(knowledge, indent=2))
    print(f"\n✅ Extracted {len(knowledge['compliance_requirements'])} requirements")
    print(f"✅ Extracted {len(knowledge['safety_hazards'])} hazards")
    print(f"✅ Extracted {len(knowledge['equipment'])} equipment items")
    print(f"✅ Extracted {len(knowledge['mvp_opportunities'])} MVP opportunities")