#!/usr/bin/env python3
"""
Real Document Detection Test
============================

GOAL: Test throwaway regex methodology on actual ENTITY_EXTRACTION_MD_DOCUMENT.md
REASON: User wants to see range/FLPC detection on real document content
PROBLEM: Validate our methodology works on production data, not just test cases

INPUT: /home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md
OUTPUT: ../output/fusion/real_document_detection_results.md

FOCUS AREAS:
- All range detections (10-15%, -20°F to 120°F, etc.)
- All FLPC entities (DATE, TIME, MONEY, MEASUREMENT)
- Comparison with current pipeline output
- Performance metrics
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import time

@dataclass
class DetectedEntity:
    """Structured entity representation"""
    type: str  # "range", "negative", "positive"
    text: str  # Original text
    value: Optional[float] = None  # For single values
    start: Optional[float] = None  # For ranges
    end: Optional[float] = None    # For ranges
    unit: str = ""
    category: str = ""  # "measurement", "money", "date", "time"
    raw_start: str = ""  # Original start text
    raw_end: str = ""    # Original end text
    position: int = 0    # Character position in document
    line_num: int = 0    # Line number in document

class RealDocumentTester:
    """Test regex methodology on real document content"""
    
    def __init__(self):
        # Use CORRECTED widest-to-narrowest order
        self.patterns = self._build_corrected_patterns()
        
        # Compile patterns
        self.compiled_patterns = []
        for pattern_info in self.patterns:
            try:
                compiled = re.compile(pattern_info['pattern'], re.IGNORECASE)
                self.compiled_patterns.append({
                    **pattern_info,
                    'compiled': compiled
                })
            except Exception as e:
                print(f"⚠️  Failed to compile pattern '{pattern_info['name']}': {e}")
    
    def _build_corrected_patterns(self) -> List[Dict]:
        """Build patterns in CORRECT widest-to-narrowest order"""
        patterns = []
        
        # PRIORITY 1: WIDEST - Complete ranges with full context
        patterns.extend([
            {
                'name': 'measurement_range_context_to',
                'pattern': r'(\w+\s+(?:range|from|between))\s+(-?\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)\s+(?:to|through|thru)\s+(-?\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)',
                'priority': 1,
                'category': 'measurement'
            },
            {
                'name': 'money_range_context_to',
                'pattern': r'(\w+\s+(?:budget|range|from|between))\s+(\$?\d+(?:\.\d+)?(?:[KMB])?)\s+(?:to|through|thru)\s+(\$?\d+(?:\.\d+)?(?:[KMB])?)',
                'priority': 1,
                'category': 'money'
            },
            {
                'name': 'time_range_context',
                'pattern': r'(\w+\s+(?:hours|from|between))\s+(\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?)\s+(?:to|through|thru)\s+(\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?)',
                'priority': 1,
                'category': 'time'
            },
            {
                'name': 'date_range_context',
                'pattern': r'(\w+\s+(?:from|between|period))\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\s+(?:to|through|thru)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
                'priority': 1,
                'category': 'date'
            }
        ])
        
        # PRIORITY 2: WIDE - Simple ranges without context
        patterns.extend([
            {
                'name': 'measurement_range_hyphen',
                'pattern': r'(-?\d+(?:\.\d+)?)\s*[-−–—]\s*(-?\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)',
                'priority': 2,
                'category': 'measurement'
            },
            {
                'name': 'measurement_range_to',
                'pattern': r'(-?\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)\s+(?:to|through|thru)\s+(-?\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)',
                'priority': 2,
                'category': 'measurement'
            },
            {
                'name': 'money_range_hyphen',
                'pattern': r'(\$?\d+(?:\.\d+)?(?:[KMB])?)\s*[-−–—]\s*(\$?\d+(?:\.\d+)?(?:[KMB])?)',
                'priority': 2,
                'category': 'money'
            },
            {
                'name': 'time_range_hyphen',
                'pattern': r'(\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?)\s*[-−–—]\s*(\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?)',
                'priority': 2,
                'category': 'time'
            }
        ])
        
        # PRIORITY 3: MEDIUM - Complete single entities
        patterns.extend([
            {
                'name': 'date_full',
                'pattern': r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}',
                'priority': 3,
                'category': 'date'
            },
            {
                'name': 'time_full',
                'pattern': r'\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)',
                'priority': 3,
                'category': 'time'
            },
            {
                'name': 'money_full',
                'pattern': r'\$\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
                'priority': 3,
                'category': 'money'
            }
        ])
        
        # PRIORITY 4: NARROW - Negative indicators
        patterns.extend([
            {
                'name': 'measurement_negative',
                'pattern': r'(?:below|minus|negative|loss\s+of|decline\s+of|drop\s+of)\s+(-?\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)',
                'priority': 4,
                'category': 'measurement'
            },
            {
                'name': 'measurement_direct_negative',
                'pattern': r'[-−]\s*(\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)',
                'priority': 4,
                'category': 'measurement'
            },
            {
                'name': 'money_negative',
                'pattern': r'(?:loss\s+of|deficit|minus|negative)\s+(\$?\d+(?:\.\d+)?(?:[KMB])?)',
                'priority': 4,
                'category': 'money'
            }
        ])
        
        # PRIORITY 5: NARROWEST - Simple single entities
        patterns.extend([
            {
                'name': 'measurement_simple',
                'pattern': r'(?<!\d)\s*(\d+(?:\.\d+)?)\s*(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm)(?!\d)',
                'priority': 5,
                'category': 'measurement'
            },
            {
                'name': 'money_simple',
                'pattern': r'(?<!\d)\s*(\$?\d+(?:\.\d+)?(?:[KMB])?)(?!\d)',
                'priority': 5,
                'category': 'money'
            }
        ])
        
        # Sort by priority (widest first)
        return sorted(patterns, key=lambda x: x['priority'])
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process real document and extract all entities"""
        print(f"🔍 PROCESSING REAL DOCUMENT: {file_path}")
        print("=" * 70)
        
        start_time = time.time()
        
        # Read document
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'error': f"Failed to read file: {e}"}
        
        lines = content.split('\n')
        total_chars = len(content)
        total_lines = len(lines)
        
        print(f"📄 Document stats: {total_chars:,} chars, {total_lines:,} lines")
        
        # Detect entities with position tracking
        entities = self._detect_with_positions(content, lines)
        
        processing_time = time.time() - start_time
        
        # Analyze results
        results = {
            'document_path': file_path,
            'processing_time_ms': processing_time * 1000,
            'document_stats': {
                'total_characters': total_chars,
                'total_lines': total_lines
            },
            'detection_summary': self._analyze_detections(entities),
            'entities': entities,
            'performance': {
                'chars_per_second': total_chars / processing_time if processing_time > 0 else 0,
                'entities_per_second': len(entities) / processing_time if processing_time > 0 else 0
            }
        }
        
        return results
    
    def _detect_with_positions(self, content: str, lines: List[str]) -> List[DetectedEntity]:
        """Detect entities with line and position tracking"""
        entities = []
        used_spans = set()
        
        # Process patterns in priority order (widest first)
        for pattern_info in self.compiled_patterns:
            matches = pattern_info['compiled'].finditer(content)
            
            for match in matches:
                start, end = match.span()
                
                # Skip if overlaps with higher-priority match
                if any(pos in used_spans for pos in range(start, end)):
                    continue
                
                used_spans.update(range(start, end))
                
                # Find line number
                line_num = content[:start].count('\n') + 1
                
                entity = self._parse_match_with_position(
                    match, pattern_info, content, start, line_num
                )
                if entity:
                    entities.append(entity)
        
        return sorted(entities, key=lambda x: x.position)
    
    def _parse_match_with_position(self, match: re.Match, pattern_info: Dict, 
                                 content: str, position: int, line_num: int) -> Optional[DetectedEntity]:
        """Parse match with position tracking"""
        groups = match.groups()
        matched_text = match.group(0)
        
        try:
            if 'range' in pattern_info['name']:
                # Range patterns
                if len(groups) >= 2:
                    start_val = self._extract_number(groups[0])
                    end_val = self._extract_number(groups[-2])  # Second to last for ranges
                    unit = groups[-1] if groups[-1] else self._extract_unit(matched_text)
                    
                    return DetectedEntity(
                        type="range",
                        text=matched_text,
                        start=start_val,
                        end=end_val,
                        unit=unit,
                        category=pattern_info['category'],
                        raw_start=groups[0],
                        raw_end=groups[-2],
                        position=position,
                        line_num=line_num
                    )
            
            elif 'negative' in pattern_info['name']:
                # Negative patterns
                if groups:
                    # Find the numeric group
                    for group in groups:
                        if group and re.search(r'\d', group):
                            value = -abs(self._extract_number(group))
                            unit = self._extract_unit(matched_text)
                            
                            return DetectedEntity(
                                type="negative",
                                text=matched_text,
                                value=value,
                                unit=unit,
                                category=pattern_info['category'],
                                position=position,
                                line_num=line_num
                            )
            
            else:
                # Positive single values
                if groups:
                    for group in groups:
                        if group and re.search(r'\d', group):
                            value = self._extract_number(group)
                            unit = self._extract_unit(matched_text)
                            
                            return DetectedEntity(
                                type="positive",
                                text=matched_text,
                                value=value,
                                unit=unit,
                                category=pattern_info['category'],
                                position=position,
                                line_num=line_num
                            )
                
        except Exception as e:
            print(f"⚠️  Parse error for '{matched_text}': {e}")
            return None
    
    def _extract_number(self, text: str) -> float:
        """Extract numeric value"""
        if not text:
            return 0.0
        clean_text = text.replace('−', '-').replace('$', '').strip()
        number_match = re.search(r'[-]?\d+(?:\.\d+)?', clean_text)
        return float(number_match.group()) if number_match else 0.0
    
    def _extract_unit(self, text: str) -> str:
        """Extract unit from text"""
        unit_pattern = r'(°[CF]|%|inches?|feet|ft|pounds?|lbs?|kg|minutes?|min|hours?|hr|decibels?|db|meters?|m|cm|mm|\$|[KMB])'
        unit_match = re.search(unit_pattern, text, re.IGNORECASE)
        return unit_match.group() if unit_match else ""
    
    def _analyze_detections(self, entities: List[DetectedEntity]) -> Dict[str, Any]:
        """Analyze detection results"""
        by_type = {'range': 0, 'negative': 0, 'positive': 0}
        by_category = {'measurement': 0, 'money': 0, 'date': 0, 'time': 0}
        
        for entity in entities:
            by_type[entity.type] += 1
            by_category[entity.category] += 1
        
        return {
            'total_entities': len(entities),
            'by_type': by_type,
            'by_category': by_category,
            'range_entities': [e for e in entities if e.type == 'range'],
            'negative_entities': [e for e in entities if e.type == 'negative']
        }
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save detailed results to output folder"""
        print(f"\n💾 SAVING RESULTS TO: {output_path}")
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate detailed markdown report
        report = self._generate_markdown_report(results)
        
        # Save markdown report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save JSON data
        json_path = output_path.replace('.md', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            # Convert entities to serializable format
            serializable_results = dict(results)
            serializable_results['entities'] = [
                {
                    'type': e.type,
                    'text': e.text,
                    'value': e.value,
                    'start': e.start,
                    'end': e.end,
                    'unit': e.unit,
                    'category': e.category,
                    'position': e.position,
                    'line_num': e.line_num
                }
                for e in results['entities']
            ]
            json.dump(serializable_results, f, indent=2)
        
        print(f"✅ Markdown report: {output_path}")
        print(f"✅ JSON data: {json_path}")
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate detailed markdown report"""
        entities = results['entities']
        summary = results['detection_summary']
        
        report = f"""# Real Document Detection Results
## {results['document_path']}

### Processing Summary
- **Processing Time**: {results['processing_time_ms']:.1f}ms
- **Document Size**: {results['document_stats']['total_characters']:,} characters, {results['document_stats']['total_lines']:,} lines
- **Performance**: {results['performance']['chars_per_second']:,.0f} chars/sec, {results['performance']['entities_per_second']:.1f} entities/sec

### Detection Summary
- **Total Entities**: {summary['total_entities']}
- **By Type**: Ranges: {summary['by_type']['range']}, Negatives: {summary['by_type']['negative']}, Positives: {summary['by_type']['positive']}
- **By Category**: Measurements: {summary['by_category']['measurement']}, Money: {summary['by_category']['money']}, Dates: {summary['by_category']['date']}, Times: {summary['by_category']['time']}

## 🎯 RANGE ENTITIES DETECTED
"""
        
        range_entities = [e for e in entities if e.type == 'range']
        if range_entities:
            for i, entity in enumerate(range_entities, 1):
                report += f"\n{i:2d}. **Line {entity.line_num}**: `{entity.text}` → {entity.start} to {entity.end} {entity.unit} [{entity.category}]"
        else:
            report += "\nNo range entities detected."
        
        report += "\n\n## ➖ NEGATIVE ENTITIES DETECTED\n"
        
        negative_entities = [e for e in entities if e.type == 'negative']
        if negative_entities:
            for i, entity in enumerate(negative_entities, 1):
                report += f"\n{i:2d}. **Line {entity.line_num}**: `{entity.text}` → {entity.value} {entity.unit} [{entity.category}]"
        else:
            report += "\nNo negative entities detected."
        
        report += "\n\n## 📊 ALL ENTITIES BY CATEGORY\n"
        
        for category in ['measurement', 'money', 'date', 'time']:
            category_entities = [e for e in entities if e.category == category]
            if category_entities:
                report += f"\n### {category.upper()} ({len(category_entities)} entities)\n"
                for i, entity in enumerate(category_entities, 1):
                    if entity.type == 'range':
                        desc = f"{entity.start} to {entity.end} {entity.unit}"
                    else:
                        desc = f"{entity.value} {entity.unit}" if entity.value is not None else entity.text
                    report += f"\n{i:2d}. **Line {entity.line_num}**: `{entity.text}` → {desc}"
        
        report += f"\n\n## 🔧 METHODOLOGY VALIDATION\n"
        report += f"\nThis test validates the **widest-to-narrowest** order of operations approach:\n"
        report += f"1. ✅ Widest patterns (ranges with context) matched first\n"
        report += f"2. ✅ Simple ranges matched second\n" 
        report += f"3. ✅ Complete single entities matched third\n"
        report += f"4. ✅ Negative indicators matched fourth\n"
        report += f"5. ✅ Narrowest patterns (bare numbers) matched last\n"
        report += f"\nPrevents narrow patterns from 'eating' parts of wider patterns.\n"
        
        return report

def main():
    """Main function to test real document"""
    print("# GOAL: Test throwaway regex methodology on real document")
    print("# REASON: User wants to see range/FLPC detection on production data")
    print("# PROBLEM: Validate methodology works on real content")
    print()
    
    # File paths
    input_file = "/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md"
    output_file = "../output/fusion/real_document_detection_results.md"
    
    # Create tester
    tester = RealDocumentTester()
    
    # Process document
    print(f"📄 Input: {input_file}")
    print(f"💾 Output: {output_file}")
    print()
    
    results = tester.process_document(input_file)
    
    if 'error' in results:
        print(f"❌ ERROR: {results['error']}")
        return
    
    # Display summary
    summary = results['detection_summary']
    print(f"\n📊 DETECTION SUMMARY:")
    print(f"   Total entities: {summary['total_entities']}")
    print(f"   Ranges: {summary['by_type']['range']}")
    print(f"   Negatives: {summary['by_type']['negative']}")
    print(f"   By category: M:{summary['by_category']['measurement']} Mo:{summary['by_category']['money']} D:{summary['by_category']['date']} T:{summary['by_category']['time']}")
    
    # Save results
    tester.save_results(results, output_file)
    
    print(f"\n🎯 VALIDATION COMPLETE")
    print(f"📄 Check {output_file} for detailed results")
    print(f"🔍 Monitor output folder for user review")

if __name__ == "__main__":
    main()