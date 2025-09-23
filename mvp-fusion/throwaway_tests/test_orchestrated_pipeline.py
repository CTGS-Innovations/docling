#!/usr/bin/env python3
"""
Test Orchestrated Pipeline
==========================

GOAL: Verify the 7-stage orchestrated pipeline works correctly
REASON: Need baseline working pipeline before applying optimizations
PROBLEM: Ensuring all stages execute in sequence with proper data flow
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_orchestrated_pipeline():
    """Test the new orchestrated pipeline with isolated stages."""
    print("🧪 Testing Orchestrated Pipeline")
    print("=" * 60)
    
    # Import the orchestrated pipeline
    from pipeline.orchestrated_pipeline import OrchestratedPipeline
    
    # Load configuration
    import yaml
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Create pipeline instance
    pipeline = OrchestratedPipeline(config)
    
    print(f"✅ Pipeline initialized with {len(pipeline.stages)} stages")
    
    # Find test files
    test_files = []
    test_dir = Path('/home/corey/projects/docling/cli/data/pdf')
    if test_dir.exists():
        test_files = list(test_dir.glob('*.pdf'))[:2]  # Just 2 files for testing
    
    if not test_files:
        print("❌ No test files found")
        return False
    
    print(f"📁 Testing with {len(test_files)} files:")
    for f in test_files:
        print(f"   - {f.name}")
    
    # Process through pipeline
    metadata = {
        'output_dir': Path('/tmp/orchestrated_test'),
        'extractor_name': 'highspeed_markdown_general'
    }
    
    print("\n🚀 Running pipeline...")
    results = pipeline.process(test_files, metadata)
    
    # Check results
    print(f"\n📊 RESULTS:")
    print(f"   Success: {results['success']}")
    print(f"   Files Processed: {results['files_processed']}")
    print(f"   Total Time: {results['total_pipeline_ms']:.2f}ms")
    
    # Verify all 7 stages executed
    stage_count = len(results['stage_results'])
    if stage_count == 7:
        print(f"   ✅ All 7 stages executed")
    else:
        print(f"   ❌ Only {stage_count} stages executed (expected 7)")
        return False
    
    # Show stage breakdown
    print(f"\n📈 STAGE BREAKDOWN:")
    for stage in results['stage_results']:
        status = "✅" if stage['success'] else "❌"
        print(f"   {status} Stage {stage['stage_num']}: {stage['stage_name']} - {stage['timing_ms']:.2f}ms")
    
    # Check output files were created
    output_dir = Path(metadata['output_dir'])
    if output_dir.exists():
        output_files = list(output_dir.glob('*'))
        print(f"\n📁 Output files created: {len(output_files)}")
        for f in output_files[:5]:  # Show first 5
            print(f"   - {f.name}")
    
    return results['success']

if __name__ == "__main__":
    success = test_orchestrated_pipeline()
    exit(0 if success else 1)