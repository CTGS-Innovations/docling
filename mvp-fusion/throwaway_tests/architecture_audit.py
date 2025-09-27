#!/usr/bin/env python3
"""
GOAL: Map complete document processing architecture end-to-end
REASON: Need to understand full execution path before debugging specific stages
PROBLEM: Testing components in isolation instead of auditing actual execution flow
"""

def map_processing_architecture():
    """Map the complete document processing architecture"""
    print("📋 COMPLETE DOCUMENT PROCESSING ARCHITECTURE")
    print("=" * 60)
    
    print("🏗️ EXECUTION PATH:")
    print("-" * 40)
    print("1. fusion_cli.py main()")
    print("   ↓")
    print("2. PipelinePhase.execute()")
    print("   ↓") 
    print("3. ServiceProcessor.process_files_service()")
    print("   ↓")
    print("4. ServiceProcessor._process_single_document()")
    print("   ↓")
    print("5. ServiceProcessor._extract_universal_entities()")
    print("   ↓")
    print("6. FLPC Engine entity extraction")
    print("   ↓")
    print("7. EntityNormalizer.canonicalize_entities()")
    print("   ↓")
    print("8. EntityNormalizer._perform_global_replacement()")
    print("   ↓")
    print("9. Final markdown with ||entity||id|| tags")
    
    print()
    print("🔍 STAGE BREAKDOWN:")
    print("-" * 40)
    
    stages = [
        {
            "name": "Stage 1: Document Ingestion",
            "file": "fusion_cli.py",
            "function": "main() → PipelinePhase.execute()",
            "purpose": "CLI argument parsing, file validation, pipeline setup",
            "input": "File path or URL",
            "output": "Validated input for processing"
        },
        {
            "name": "Stage 2: Service Processing", 
            "file": "pipeline/legacy/service_processor.py",
            "function": "process_files_service() → _process_single_document()",
            "purpose": "Document classification, pipeline routing",
            "input": "File path",
            "output": "InMemoryDocument object"
        },
        {
            "name": "Stage 3: Entity Extraction",
            "file": "pipeline/legacy/service_processor.py", 
            "function": "_extract_universal_entities()",
            "purpose": "FLPC pattern matching, entity detection",
            "input": "Document text content",
            "output": "Raw entities dict {measurement: [...], range_indicator: [...]}"
        },
        {
            "name": "Stage 4: Entity Normalization",
            "file": "knowledge/extractors/entity_normalizer.py",
            "function": "canonicalize_entities()",
            "purpose": "Entity deduplication, canonicalization, SI conversion",
            "input": "Raw entities dict",
            "output": "Canonical entities list with normalized values and IDs"
        },
        {
            "name": "Stage 5: Text Replacement",
            "file": "knowledge/extractors/entity_normalizer.py",
            "function": "_perform_global_replacement()",
            "purpose": "Replace original text with ||canonical||id|| tags",
            "input": "Original text + canonical entities",
            "output": "Tagged markdown content"
        },
        {
            "name": "Stage 6: Output Generation",
            "file": "pipeline/legacy/service_processor.py",
            "function": "File writing and YAML frontmatter",
            "purpose": "Generate final .md and .json files",
            "input": "Tagged content + metadata",
            "output": "Final output files"
        }
    ]
    
    for i, stage in enumerate(stages, 1):
        print(f"\n📊 {stage['name']}")
        print(f"   File: {stage['file']}")
        print(f"   Function: {stage['function']}")
        print(f"   Purpose: {stage['purpose']}")
        print(f"   Input: {stage['input']}")
        print(f"   Output: {stage['output']}")
    
    print()
    print("🎯 CRITICAL POINTS TO AUDIT:")
    print("-" * 40)
    print("• Stage 3: Does FLPC detect all measurements?")
    print("• Stage 4: Are all detected entities normalized?") 
    print("• Stage 5: Does text replacement work correctly?")
    print("• Integration: Do entities flow correctly between stages?")
    
    print()
    print("📋 AUDIT PLAN:")
    print("-" * 40)
    print("1. Trace single document through all 6 stages")
    print("2. Verify data at each stage boundary")
    print("3. Identify exact stage where measurements are lost")
    print("4. Fix root cause at identified stage")

if __name__ == "__main__":
    map_processing_architecture()