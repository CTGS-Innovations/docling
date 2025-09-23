#!/usr/bin/env python3
"""
Test Import Issues - Identify Unicode/Import Problems
====================================================

GOAL: Fix import chain to enable sidecar processor testing
REASON: Pipeline fails with Unicode errors when importing processors  
PROBLEM: Need to isolate and fix import issues for A/B testing

This tests individual imports to find the exact failure point.
"""

def test_processors_import():
    """Test if we can import processors without Unicode errors."""
    print("🔍 Testing processor imports...")
    
    try:
        from pipeline.processors import ProcessorFactory
        print("✅ ProcessorFactory import OK")
        
        # Test factory creation
        available = ProcessorFactory.get_available_processors()
        print(f"✅ Available processors: {available}")
        
        # Test ServiceProcessor creation
        config = {'max_workers': 2}
        service_processor = ProcessorFactory.create('service_processor', config)
        print("✅ ServiceProcessor creation OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Processor import failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_legacy_imports():
    """Test legacy processor imports individually."""
    print("\n🔍 Testing legacy imports...")
    
    import sys
    from pathlib import Path
    
    # Add legacy path
    legacy_path = Path(__file__).parent.parent / 'pipeline' / 'legacy'
    sys.path.insert(0, str(legacy_path))
    
    # Test ServiceProcessor
    try:
        from service_processor import ServiceProcessor
        print("✅ ServiceProcessor direct import OK")
    except Exception as e:
        print(f"❌ ServiceProcessor direct import failed: {e}")
    
    # Test FusionPipeline
    try:
        # This should fail due to relative imports
        from fusion_pipeline import FusionPipeline
        print("✅ FusionPipeline direct import OK")
    except Exception as e:
        print(f"❌ FusionPipeline direct import failed: {e}")
        print("   (Expected due to relative imports)")

if __name__ == "__main__":
    print("🚀 Import Issue Diagnosis")
    print("=" * 50)
    
    success = test_processors_import()
    test_legacy_imports()
    
    if success:
        print("\n🟢 **SUCCESS**: Imports working - can proceed with sidecar")
    else:
        print("\n🔴 **BLOCKED**: Import issues need fixing before sidecar")