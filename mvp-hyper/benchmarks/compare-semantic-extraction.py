#!/usr/bin/env python3
"""
Semantic Extraction Comparison Tool
====================================
Compares semantic extraction results between old and new versions,
focusing on the two-tier extraction system (Core + Domain facts).

This tool analyzes:
- Core facts quality and coverage
- Domain-specific fact extraction
- Entity detection improvements  
- Overall extraction performance metrics
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import statistics
from collections import defaultdict, Counter


@dataclass
class ExtractionStats:
    """Statistics for semantic extraction analysis."""
    file_count: int = 0
    
    # Legacy extraction stats
    legacy_facts: int = 0
    legacy_entities: int = 0
    
    # Two-tier extraction stats
    core_facts: int = 0
    domain_facts: int = 0
    
    # Quality metrics
    avg_core_confidence: float = 0.0
    avg_domain_confidence: float = 0.0
    
    # Domain distribution
    domain_distribution: Dict[str, int] = None
    
    # Fact type distribution
    core_fact_types: Dict[str, int] = None
    domain_fact_types: Dict[str, int] = None
    
    # Performance metrics
    total_processing_time: float = 0.0
    avg_processing_time_per_doc: float = 0.0
    
    # Entity coverage
    entity_types_found: Dict[str, int] = None
    
    def __post_init__(self):
        if self.domain_distribution is None:
            self.domain_distribution = {}
        if self.core_fact_types is None:
            self.core_fact_types = {}
        if self.domain_fact_types is None:
            self.domain_fact_types = {}
        if self.entity_types_found is None:
            self.entity_types_found = {}


def load_metadata_file(file_path: Path) -> Optional[Dict]:
    """Load semantic metadata JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        print(f"⚠️  Warning: Could not load {file_path.name}: {e}")
        return None


def analyze_extraction_directory(dir_path: Path) -> ExtractionStats:
    """Analyze all metadata files in a directory."""
    stats = ExtractionStats()
    
    if not dir_path.exists():
        print(f"❌ Directory not found: {dir_path}")
        return stats
    
    metadata_files = list(dir_path.glob("*.metadata.json"))
    stats.file_count = len(metadata_files)
    
    if stats.file_count == 0:
        print(f"⚠️  No metadata files found in {dir_path}")
        return stats
    
    core_confidences = []
    domain_confidences = []
    processing_times = []
    
    for metadata_file in metadata_files:
        data = load_metadata_file(metadata_file)
        if not data:
            continue
        
        # Legacy extraction stats
        if 'facts' in data and data['facts']:
            stats.legacy_facts += len(data['facts'])
            
        if 'entities' in data and data['entities']:
            stats.legacy_entities += len(data['entities'])
            
            # Count entity types
            for entity in data['entities']:
                entity_type = entity.get('entity_type', 'unknown')
                stats.entity_types_found[entity_type] = stats.entity_types_found.get(entity_type, 0) + 1
        
        # Two-tier extraction stats
        if 'core_facts' in data and data['core_facts']:
            facts = data['core_facts']
            stats.core_facts += len(facts)
            
            # Collect confidence scores
            for fact in facts:
                if 'confidence' in fact:
                    core_confidences.append(fact['confidence'])\n                \n                # Count fact types\n                fact_type = fact.get('type', 'unknown')\n                stats.core_fact_types[fact_type] = stats.core_fact_types.get(fact_type, 0) + 1\n        \n        if 'domain_facts' in data and data['domain_facts']:\n            facts = data['domain_facts']\n            stats.domain_facts += len(facts)\n            \n            # Collect domain confidence scores\n            for fact in facts:\n                if 'confidence' in fact:\n                    domain_confidences.append(fact['confidence'])\n                    \n                # Count domain fact types\n                fact_type = fact.get('type', 'unknown')\n                stats.domain_fact_types[fact_type] = stats.domain_fact_types.get(fact_type, 0) + 1\n        \n        # Domain classification\n        if 'domain_classification' in data and data['domain_classification']:\n            domain_info = data['domain_classification']\n            domain_name = domain_info.get('domain', 'unknown')\n            stats.domain_distribution[domain_name] = stats.domain_distribution.get(domain_name, 0) + 1\n        \n        # Processing time\n        if 'processing_time' in data:\n            processing_times.append(data['processing_time'])\n            stats.total_processing_time += data['processing_time']\n    \n    # Calculate averages\n    if core_confidences:\n        stats.avg_core_confidence = statistics.mean(core_confidences)\n        \n    if domain_confidences:\n        stats.avg_domain_confidence = statistics.mean(domain_confidences)\n        \n    if processing_times:\n        stats.avg_processing_time_per_doc = statistics.mean(processing_times)\n    \n    return stats\n\n\ndef compare_extraction_results(old_dir: Path, new_dir: Path) -> Dict[str, Any]:\n    \"\"\"Compare semantic extraction results between two directories.\"\"\"\n    \n    print(f\"\\n🔍 Semantic Extraction Analysis\")\n    print(\"=\" * 70)\n    \n    # Analyze both directories\n    print(f\"\\n📁 Analyzing old extraction: {old_dir}\")\n    old_stats = analyze_extraction_directory(old_dir)\n    \n    print(f\"📁 Analyzing new extraction: {new_dir}\")\n    new_stats = analyze_extraction_directory(new_dir)\n    \n    # Calculate improvements\n    improvements = {}\n    \n    if old_stats.file_count > 0 and new_stats.file_count > 0:\n        # Core extraction improvements\n        if old_stats.core_facts > 0:\n            core_fact_change = ((new_stats.core_facts - old_stats.core_facts) / old_stats.core_facts) * 100\n        else:\n            core_fact_change = 100 if new_stats.core_facts > 0 else 0\n            \n        # Domain extraction is new capability\n        domain_fact_improvement = new_stats.domain_facts  # Absolute count since it's new\n        \n        # Legacy extraction changes\n        legacy_fact_change = 0\n        if old_stats.legacy_facts > 0:\n            legacy_fact_change = ((new_stats.legacy_facts - old_stats.legacy_facts) / old_stats.legacy_facts) * 100\n            \n        # Confidence improvements\n        confidence_change = 0\n        if old_stats.avg_core_confidence > 0:\n            confidence_change = ((new_stats.avg_core_confidence - old_stats.avg_core_confidence) / old_stats.avg_core_confidence) * 100\n        \n        improvements = {\n            'core_facts': core_fact_change,\n            'domain_facts': domain_fact_improvement,\n            'legacy_facts': legacy_fact_change,\n            'confidence': confidence_change,\n        }\n    \n    # Print detailed results\n    print(f\"\\n📊 Extraction Results Summary\")\n    print(\"-\" * 70)\n    \n    print(f\"\\n📄 Files Processed:\")\n    print(f\"  Old: {old_stats.file_count} files\")\n    print(f\"  New: {new_stats.file_count} files\")\n    \n    print(f\"\\n🎯 Fact Extraction (Two-Tier System):\")\n    print(f\"  Core Facts (Tier 1 - Universal):\")\n    print(f\"    Old: {old_stats.core_facts}\")\n    print(f\"    New: {new_stats.core_facts}\")\n    if 'core_facts' in improvements:\n        print(f\"    Change: {improvements['core_facts']:+.1f}%\")\n    \n    print(f\"\\n  Domain Facts (Tier 2 - Specialized):\")\n    print(f\"    Old: {old_stats.domain_facts}\")\n    print(f\"    New: {new_stats.domain_facts}\")\n    if new_stats.domain_facts > old_stats.domain_facts:\n        print(f\"    🆕 NEW CAPABILITY: +{new_stats.domain_facts - old_stats.domain_facts} domain facts\")\n    \n    print(f\"\\n  Legacy Facts (Backward Compatibility):\")\n    print(f\"    Old: {old_stats.legacy_facts}\")\n    print(f\"    New: {new_stats.legacy_facts}\")\n    if 'legacy_facts' in improvements:\n        print(f\"    Change: {improvements['legacy_facts']:+.1f}%\")\n    \n    print(f\"\\n💎 Quality Metrics:\")\n    print(f\"  Core Fact Confidence:\")\n    print(f\"    Old: {old_stats.avg_core_confidence:.3f}\")\n    print(f\"    New: {new_stats.avg_core_confidence:.3f}\")\n    if 'confidence' in improvements:\n        print(f\"    Change: {improvements['confidence']:+.1f}%\")\n    \n    if new_stats.avg_domain_confidence > 0:\n        print(f\"\\n  Domain Fact Confidence: {new_stats.avg_domain_confidence:.3f}\")\n    \n    print(f\"\\n🏷️ Domain Coverage:\")\n    if new_stats.domain_distribution:\n        for domain, count in sorted(new_stats.domain_distribution.items(), key=lambda x: x[1], reverse=True):\n            percentage = (count / new_stats.file_count) * 100\n            print(f\"  {domain}: {count} files ({percentage:.1f}%)\")\n    else:\n        print(f\"  No domain classification data available\")\n    \n    print(f\"\\n🔍 Core Fact Types (Tier 1):\")\n    if new_stats.core_fact_types:\n        for fact_type, count in sorted(new_stats.core_fact_types.items(), key=lambda x: x[1], reverse=True)[:10]:\n            print(f\"  {fact_type}: {count} facts\")\n    else:\n        print(f\"  No core fact type data available\")\n    \n    print(f\"\\n🎯 Domain Fact Types (Tier 2):\")\n    if new_stats.domain_fact_types:\n        for fact_type, count in sorted(new_stats.domain_fact_types.items(), key=lambda x: x[1], reverse=True)[:10]:\n            print(f\"  {fact_type}: {count} facts\")\n    else:\n        print(f\"  No domain fact type data available\")\n    \n    print(f\"\\n👥 Entity Detection:\")\n    print(f\"  Total Entities:\")\n    print(f\"    Old: {old_stats.legacy_entities}\")\n    print(f\"    New: {new_stats.legacy_entities}\")\n    \n    if new_stats.entity_types_found:\n        print(f\"\\n  Entity Types Found:\")\n        for entity_type, count in sorted(new_stats.entity_types_found.items(), key=lambda x: x[1], reverse=True)[:8]:\n            print(f\"    {entity_type}: {count} entities\")\n    \n    print(f\"\\n⚡ Performance:\")\n    print(f\"  Average Processing Time per Document:\")\n    print(f\"    Old: {old_stats.avg_processing_time_per_doc:.3f}s\")\n    print(f\"    New: {new_stats.avg_processing_time_per_doc:.3f}s\")\n    \n    if old_stats.avg_processing_time_per_doc > 0:\n        perf_change = ((new_stats.avg_processing_time_per_doc - old_stats.avg_processing_time_per_doc) / old_stats.avg_processing_time_per_doc) * 100\n        print(f\"    Change: {perf_change:+.1f}% {'(slower)' if perf_change > 0 else '(faster)'}\")\n    \n    # Overall assessment\n    print(f\"\\n✨ Two-Tier Extraction Assessment:\")\n    \n    total_new_facts = new_stats.core_facts + new_stats.domain_facts\n    total_old_facts = old_stats.core_facts + old_stats.legacy_facts  # Approximate comparison\n    \n    if total_new_facts > total_old_facts * 1.5:\n        print(f\"  🎉 MAJOR IMPROVEMENT: {total_new_facts - total_old_facts:+d} more facts extracted\")\n    elif total_new_facts > total_old_facts * 1.2:\n        print(f\"  ✅ GOOD IMPROVEMENT: {total_new_facts - total_old_facts:+d} more facts extracted\")\n    elif total_new_facts > total_old_facts:\n        print(f\"  📈 MODEST IMPROVEMENT: {total_new_facts - total_old_facts:+d} more facts extracted\")\n    else:\n        print(f\"  ⚠️  No significant fact count improvement\")\n    \n    if new_stats.domain_facts > 0:\n        print(f\"  🆕 NEW CAPABILITY: Domain-aware extraction active\")\n        print(f\"      • {new_stats.domain_facts} domain-specific facts extracted\")\n        print(f\"      • {len(new_stats.domain_distribution)} domains detected\")\n        \n        if new_stats.avg_domain_confidence > 0.8:\n            print(f\"      • High domain confidence: {new_stats.avg_domain_confidence:.2f}\")\n    \n    if new_stats.core_facts > 0:\n        print(f\"  🎯 CORE EXTRACTION: Universal fact extraction active\")\n        print(f\"      • {new_stats.core_facts} core facts (who/what/when/how much)\")\n        print(f\"      • {len(new_stats.core_fact_types)} fact types identified\")\n        \n        if new_stats.avg_core_confidence > 0.7:\n            print(f\"      • Good core confidence: {new_stats.avg_core_confidence:.2f}\")\n    \n    # Architecture benefits\n    print(f\"\\n🏗️ Architecture Benefits:\")\n    print(f\"  • Modular design: Core + Domain extraction\")\n    print(f\"  • Extensible: Easy to add new domains\")\n    print(f\"  • Scalable: Domain classification guides extraction\")\n    print(f\"  • Compatible: Maintains legacy extraction for comparison\")\n    \n    if new_stats.domain_distribution:\n        most_common_domain = max(new_stats.domain_distribution.items(), key=lambda x: x[1])\n        print(f\"  • Primary domain detected: {most_common_domain[0]} ({most_common_domain[1]} files)\")\n    \n    return {\n        'old_stats': old_stats,\n        'new_stats': new_stats,\n        'improvements': improvements,\n        'assessment': {\n            'total_new_facts': total_new_facts,\n            'total_old_facts': total_old_facts,\n            'has_domain_extraction': new_stats.domain_facts > 0,\n            'has_core_extraction': new_stats.core_facts > 0,\n        }\n    }\n\n\ndef export_comparison_report(results: Dict, output_path: Path):\n    \"\"\"Export detailed comparison report to JSON.\"\"\"\n    \n    # Convert dataclass objects to dicts for JSON serialization\n    export_data = {\n        'old_stats': {\n            'file_count': results['old_stats'].file_count,\n            'legacy_facts': results['old_stats'].legacy_facts,\n            'legacy_entities': results['old_stats'].legacy_entities,\n            'core_facts': results['old_stats'].core_facts,\n            'domain_facts': results['old_stats'].domain_facts,\n            'avg_core_confidence': results['old_stats'].avg_core_confidence,\n            'avg_domain_confidence': results['old_stats'].avg_domain_confidence,\n            'avg_processing_time_per_doc': results['old_stats'].avg_processing_time_per_doc,\n            'domain_distribution': results['old_stats'].domain_distribution,\n            'core_fact_types': results['old_stats'].core_fact_types,\n            'domain_fact_types': results['old_stats'].domain_fact_types,\n        },\n        'new_stats': {\n            'file_count': results['new_stats'].file_count,\n            'legacy_facts': results['new_stats'].legacy_facts,\n            'legacy_entities': results['new_stats'].legacy_entities,\n            'core_facts': results['new_stats'].core_facts,\n            'domain_facts': results['new_stats'].domain_facts,\n            'avg_core_confidence': results['new_stats'].avg_core_confidence,\n            'avg_domain_confidence': results['new_stats'].avg_domain_confidence,\n            'avg_processing_time_per_doc': results['new_stats'].avg_processing_time_per_doc,\n            'domain_distribution': results['new_stats'].domain_distribution,\n            'core_fact_types': results['new_stats'].core_fact_types,\n            'domain_fact_types': results['new_stats'].domain_fact_types,\n        },\n        'improvements': results['improvements'],\n        'assessment': results['assessment'],\n        'analysis_timestamp': '2025-09-14',  # Current date\n        'extraction_architecture': 'two_tier_core_plus_domain'\n    }\n    \n    with open(output_path, 'w') as f:\n        json.dump(export_data, f, indent=2)\n    \n    print(f\"\\n💾 Detailed report saved to: {output_path}\")\n\n\ndef main():\n    \"\"\"Main comparison function.\"\"\"\n    import sys\n    \n    if len(sys.argv) < 2:\n        print(\"Usage: python compare-semantic-extraction.py <base_dir>\")\n        print(\"  Compares old_semantic_quality_filtered/ vs semantic_quality_filtered/\")\n        print(\"\\nOr: python compare-semantic-extraction.py <old_dir> <new_dir>\")\n        print(\"  Compares specified directories with .metadata.json files\")\n        sys.exit(1)\n    \n    if len(sys.argv) == 2:\n        # Use default directory names\n        base_dir = Path(sys.argv[1])\n        old_dir = base_dir / \"old_semantic_quality_filtered\"\n        new_dir = base_dir / \"semantic_quality_filtered\"\n    else:\n        # Use specified directories\n        old_dir = Path(sys.argv[1])\n        new_dir = Path(sys.argv[2])\n    \n    # Run comparison\n    results = compare_extraction_results(old_dir, new_dir)\n    \n    # Export detailed report\n    report_path = Path(\"semantic_extraction_comparison.json\")\n    export_comparison_report(results, report_path)\n    \n    print(f\"\\n🎯 Summary: Two-tier semantic extraction analysis complete!\")\n    print(f\"   Core facts: {results['new_stats'].core_facts}\")\n    print(f\"   Domain facts: {results['new_stats'].domain_facts}\")\n    print(f\"   Total improvement: {results['assessment']['total_new_facts'] - results['assessment']['total_old_facts']:+d} facts\")\n\n\nif __name__ == \"__main__\":\n    main()