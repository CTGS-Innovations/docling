"""
Safety Knowledge Extractor
Demonstrates knowledge extraction patterns for OSHA and safety documents
Uses FLPC Rust Regex for 14.9x performance improvement
"""

try:
    from . import fast_regex as re  # MVP-Fusion standard: FLPC Rust regex
except ImportError:
    # Fallback for standalone execution
    import fast_regex as re
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class SafetyRequirement:
    measurement: str
    condition: str
    requirement: str
    regulation_ref: str = ""

@dataclass
class SafetyEquipment:
    name: str
    category: str
    context: str
    required: bool = False

@dataclass
class BusinessImpact:
    impact_type: str
    severity: str
    target_group: str
    description: str

class SafetyKnowledgeExtractor:
    
    def __init__(self):
        # Measurement patterns
        self.measurement_patterns = [
            r'(\d+)\s*inches?\s*\((\d+)\s*cm\)',  # "19 inches (48 cm)"
            r'(\d+)\s*feet?\s*\((\d+\.?\d*)\s*m\)',  # "6 feet (1.8 m)"
            r'(\d+)\s*degrees?',  # "30 degrees"
        ]
        
        # Regulation reference patterns
        self.regulation_patterns = [
            r'OSHA\s+(\d+[-\w]*)',  # "OSHA 3124-12R"
            r'(\d+)\s+CFR\s+(\d+\.?\d*)',  # "29 CFR 1926"
            r'Section\s+(\d+\.?\d*)',  # "Section 1926.1051"
        ]
        
        # Requirement trigger words
        self.requirement_triggers = [
            "must provide", "shall provide", "required to", "employers must",
            "shall be", "must be", "required", "shall", "must"
        ]
        
        # Safety equipment terms
        self.equipment_terms = [
            "stairway", "ladder", "ramp", "runway", "embankment", 
            "personnel hoist", "guardrail", "handrail", "hard hat",
            "safety harness", "fall protection", "safety net"
        ]
        
        # Business impact indicators
        self.impact_indicators = [
            "injuries", "fatalities", "time off", "workers compensation",
            "accidents", "incidents", "hazardous", "dangerous", "risk"
        ]

    def extract_regulatory_requirements(self, text: str) -> List[SafetyRequirement]:
        """Extract specific regulatory requirements with measurements"""
        requirements = []
        
        # Find measurement-based requirements
        for pattern in self.measurement_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get surrounding context (FLPC match objects need index)
                start = max(0, match.start(0) - 100)
                end = min(len(text), match.end(0) + 100)
                context = text[start:end]
                
                # Look for requirement triggers in context
                for trigger in self.requirement_triggers:
                    if trigger.lower() in context.lower():
                        req = SafetyRequirement(
                            measurement=match.group(0),
                            condition=self._extract_condition(context),
                            requirement=self._extract_requirement(context),
                            regulation_ref=self._find_regulation_ref(context)
                        )
                        requirements.append(req)
                        break
        
        return requirements
    
    def extract_safety_equipment(self, text: str) -> List[SafetyEquipment]:
        """Extract mentioned safety equipment and context"""
        equipment_list = []
        
        for equipment in self.equipment_terms:
            pattern = rf'\b{re.escape(equipment)}s?\b'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Get surrounding context (FLPC match objects need index)
                start = max(0, match.start(0) - 50)
                end = min(len(text), match.end(0) + 50)
                context = text[start:end]
                
                # Determine if required
                is_required = any(trigger in context.lower() 
                                for trigger in self.requirement_triggers)
                
                eq = SafetyEquipment(
                    name=match.group(0),
                    category=self._categorize_equipment(equipment),
                    context=context.strip(),
                    required=is_required
                )
                equipment_list.append(eq)
        
        return equipment_list
    
    def extract_business_impact(self, text: str) -> List[BusinessImpact]:
        """Extract business impact statements"""
        impacts = []
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Check if sentence contains impact indicators
            for indicator in self.impact_indicators:
                if indicator.lower() in sentence.lower():
                    impact = BusinessImpact(
                        impact_type=indicator,
                        severity=self._determine_severity(sentence),
                        target_group=self._extract_target_group(sentence),
                        description=sentence.strip()
                    )
                    impacts.append(impact)
                    break
        
        return impacts
    
    def extract_all_entities_fast(self, text: str) -> Dict[str, Any]:
        """
        High-performance batch entity extraction using FLPC
        Processes all entity types in one pass - MVP-Fusion optimized
        """
        # Define all entity patterns for batch processing
        entity_patterns = {
            'measurements': r'(\d+)\s*(?:inches?|feet?|cm|degrees?)',
            'regulations': r'OSHA\s+(\d+[-\w]*)|(\d+)\s+CFR\s+(\d+\.?\d*)',
            'equipment': r'\b(?:stairway|ladder|ramp|runway|guardrail|handrail|harness)s?\b',
            'requirements': r'(?:must|shall|required)\s+(?:provide|be|have)',
            'measurements_with_units': r'(\d+)\s*inches?\s*\((\d+)\s*cm\)',
            'impact_indicators': r'\b(?:injuries|fatalities|accidents|hazardous|dangerous)\b',
            'target_groups': r'\b(?:construction workers|workers|employees|contractors)\b'
        }
        
        # Batch process all patterns with FLPC
        batch_results = re.extract_entities(entity_patterns, text)
        
        # Structure results for Scout's intelligence pipeline
        structured_results = {
            'regulatory_requirements': [],
            'safety_equipment': [],
            'business_impacts': [],
            'mvp_opportunities': [],
            'performance_stats': re.get_performance_info()
        }
        
        # Process measurements into requirements
        measurements = batch_results.get('measurements', [])
        for measurement in measurements:
            structured_results['regulatory_requirements'].append({
                'type': 'measurement_requirement',
                'value': measurement['text'],
                'confidence': measurement['confidence'],
                'extraction_method': 'flpc_batch'
            })
        
        # Process equipment mentions
        equipment = batch_results.get('equipment', [])
        for eq in equipment:
            structured_results['safety_equipment'].append({
                'name': eq['text'],
                'category': self._categorize_equipment(eq['text']),
                'confidence': eq['confidence'],
                'extraction_method': 'flpc_batch'
            })
        
        # Process impact indicators
        impacts = batch_results.get('impact_indicators', [])
        for impact in impacts:
            structured_results['business_impacts'].append({
                'impact_type': impact['text'],
                'severity': self._determine_severity_from_text(impact['text']),
                'confidence': impact['confidence'],
                'extraction_method': 'flpc_batch'
            })
        
        return structured_results
    
    def _determine_severity_from_text(self, impact_text: str) -> str:
        """Determine severity from impact text"""
        if impact_text.lower() in ['fatalities', 'death']:
            return 'critical'
        elif impact_text.lower() in ['injuries', 'accidents']:
            return 'high'
        else:
            return 'medium'

    def extract_mvp_opportunities(self, text: str) -> List[Dict[str, Any]]:
        """Identify potential MVP opportunities from compliance gaps"""
        opportunities = []
        
        # Look for compliance challenges
        challenge_indicators = [
            "difficult", "complex", "challenging", "time-consuming",
            "expensive", "costly", "manual", "paperwork", "inspection"
        ]
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            for indicator in challenge_indicators:
                if indicator.lower() in sentence.lower():
                    opportunity = {
                        "type": "compliance_automation",
                        "description": sentence.strip(),
                        "pain_point": indicator,
                        "market": "construction_safety",
                        "potential_solution": self._suggest_solution(sentence, indicator)
                    }
                    opportunities.append(opportunity)
                    break
        
        return opportunities
    
    def _extract_condition(self, context: str) -> str:
        """Extract the condition that triggers a requirement"""
        # Look for "when" clauses
        when_match = re.search(r'when\s+([^,]+)', context, re.IGNORECASE)
        if when_match:
            return when_match.group(1).strip()
        
        # Look for "if" clauses
        if_match = re.search(r'if\s+([^,]+)', context, re.IGNORECASE)
        if if_match:
            return if_match.group(1).strip()
        
        return "unspecified condition"
    
    def _extract_requirement(self, context: str) -> str:
        """Extract what is required"""
        for trigger in self.requirement_triggers:
            if trigger.lower() in context.lower():
                parts = context.lower().split(trigger.lower())
                if len(parts) > 1:
                    requirement = parts[1].split('.')[0].strip()
                    return requirement[:100]  # Limit length
        return "unspecified requirement"
    
    def _find_regulation_ref(self, context: str) -> str:
        """Find regulation references in context"""
        for pattern in self.regulation_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(0)
        return ""
    
    def _categorize_equipment(self, equipment: str) -> str:
        """Categorize equipment type"""
        access_equipment = ["stairway", "ladder", "ramp", "runway"]
        protection_equipment = ["guardrail", "handrail", "harness", "net"]
        
        if equipment.lower() in access_equipment:
            return "access"
        elif equipment.lower() in protection_equipment:
            return "protection"
        else:
            return "general"
    
    def _determine_severity(self, sentence: str) -> str:
        """Determine severity of impact"""
        high_severity = ["fatalities", "death", "serious", "major"]
        medium_severity = ["injuries", "time off", "accidents"]
        
        sentence_lower = sentence.lower()
        
        if any(term in sentence_lower for term in high_severity):
            return "high"
        elif any(term in sentence_lower for term in medium_severity):
            return "medium"
        else:
            return "low"
    
    def _extract_target_group(self, sentence: str) -> str:
        """Extract who is affected"""
        target_groups = [
            "construction workers", "workers", "employees", "employers",
            "contractors", "inspectors", "supervisors"
        ]
        
        for group in target_groups:
            if group.lower() in sentence.lower():
                return group
        
        return "general workforce"
    
    def _suggest_solution(self, sentence: str, pain_point: str) -> str:
        """Suggest potential tech solution for identified pain point"""
        solutions = {
            "manual": "automation software",
            "paperwork": "digital compliance platform",
            "inspection": "mobile inspection app",
            "complex": "simplified compliance tool",
            "time-consuming": "automated reporting system",
            "expensive": "cost-effective SaaS solution"
        }
        
        return solutions.get(pain_point.lower(), "digital solution")

# Example usage function
def demonstrate_extraction(osha_text: str):
    """Demonstrate knowledge extraction on OSHA document"""
    
    extractor = SafetyKnowledgeExtractor()
    
    print("=" * 60)
    print("SAFETY KNOWLEDGE EXTRACTION DEMONSTRATION")
    print("=" * 60)
    
    # Extract regulatory requirements
    requirements = extractor.extract_regulatory_requirements(osha_text)
    print(f"\n📋 REGULATORY REQUIREMENTS FOUND: {len(requirements)}")
    for req in requirements[:3]:  # Show first 3
        print(f"  • Measurement: {req.measurement}")
        print(f"    Condition: {req.condition}")
        print(f"    Requirement: {req.requirement}")
        print(f"    Regulation: {req.regulation_ref}")
        print()
    
    # Extract safety equipment
    equipment = extractor.extract_safety_equipment(osha_text)
    print(f"🛡️ SAFETY EQUIPMENT FOUND: {len(equipment)}")
    for eq in equipment[:5]:  # Show first 5
        print(f"  • {eq.name} ({eq.category}) - Required: {eq.required}")
        print(f"    Context: {eq.context[:80]}...")
        print()
    
    # Extract business impact
    impacts = extractor.extract_business_impact(osha_text)
    print(f"💼 BUSINESS IMPACTS FOUND: {len(impacts)}")
    for impact in impacts[:3]:  # Show first 3
        print(f"  • Type: {impact.impact_type} (Severity: {impact.severity})")
        print(f"    Target: {impact.target_group}")
        print(f"    Description: {impact.description[:100]}...")
        print()
    
    # Extract MVP opportunities
    opportunities = extractor.extract_mvp_opportunities(osha_text)
    print(f"🚀 MVP OPPORTUNITIES FOUND: {len(opportunities)}")
    for opp in opportunities[:2]:  # Show first 2
        print(f"  • Type: {opp['type']}")
        print(f"    Pain Point: {opp['pain_point']}")
        print(f"    Market: {opp['market']}")
        print(f"    Suggested Solution: {opp['potential_solution']}")
        print(f"    Description: {opp['description'][:100]}...")
        print()
    
    return {
        "requirements": requirements,
        "equipment": equipment,
        "impacts": impacts,
        "opportunities": opportunities
    }

if __name__ == "__main__":
    # Sample OSHA text for testing
    sample_text = """
    Working on and around stairways and ladders is hazardous. Stairways and ladders are major
    sources of injuries and fatalities among construction workers for example, and many of the 
    injuries are serious enough to require time off the job. OSHA rules apply to all stairways 
    and ladders used in construction. When there is a break in elevation of 19 inches (48 cm) 
    or more and no ramp, runway, embankment or personnel hoist is available, employers must 
    provide a stairway or ladder at all worker points of access.
    """
    
    demonstrate_extraction(sample_text)