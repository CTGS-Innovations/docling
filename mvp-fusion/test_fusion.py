#!/usr/bin/env python3
"""
MVP-Fusion Quick Test Script
============================

Simple test to verify all components work together.
Run this to test the complete MVP-Fusion pipeline.
"""

import sys
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.fusion_pipeline import FusionPipeline
from fusion.fusion_engine import FusionEngine


def test_fusion_engine():
    """Test the fusion engine components."""
    print("🔧 Testing Fusion Engine...")
    
    try:
        engine = FusionEngine()
        
        test_text = """
        OSHA regulation 29 CFR 1926.95 requires workers to wear hard hats.
        Contact safety@company.com for $2,500 training on March 15, 2024.
        Call (555) 123-4567 for more information about PPE requirements.
        Temperature must be maintained between 65-75°F in work areas.
        """
        
        start_time = time.time()
        result = engine.process_text(test_text, "test.txt")
        processing_time = time.time() - start_time
        
        if 'entities' in result:
            entities_found = sum(len(v) if isinstance(v, list) else 1 
                               for v in result['entities'].values())
            print(f"  ✅ Engine test passed")
            print(f"     Processing time: {processing_time*1000:.2f}ms")
            print(f"     Entities found: {entities_found}")
            print(f"     Entity types: {list(result['entities'].keys())}")
            
            # Show engine status
            status = engine.get_engine_status()
            print(f"     Engine status: {status}")
            return True
        else:
            print(f"  ❌ No entities found in result")
            return False
            
    except Exception as e:
        print(f"  ❌ Engine test failed: {e}")
        return False


def test_pipeline():
    """Test the complete pipeline."""
    print("\n🚀 Testing Complete Pipeline...")
    
    try:
        pipeline = FusionPipeline()
        
        # Create test content
        test_content = """
        # Safety Training Document
        
        This document outlines OSHA safety requirements for construction workers.
        
        ## Personal Protective Equipment (PPE)
        
        According to 29 CFR 1926.95, all workers must wear:
        - Hard hats in designated areas
        - Safety glasses when operating equipment
        - High-visibility clothing during roadwork
        
        ## Training Requirements
        
        Contact the safety coordinator at safety@company.com to schedule training.
        Training sessions cost $2,500 per group and must be completed by March 15, 2024.
        
        For immediate assistance, call (555) 123-4567 during business hours (8:00 AM - 5:00 PM).
        
        ## Environmental Compliance
        
        EPA regulation 40 CFR 261.1 requires proper disposal of hazardous materials.
        Temperature in storage areas must be maintained between 65-75°F.
        
        All monitoring systems must use software version 2.1.3 or higher for compliance reporting.
        """
        
        start_time = time.time()
        result = pipeline.process_document("test_document.txt", test_content)
        processing_time = time.time() - start_time
        
        if result['status'] == 'success':
            metadata = result['processing_metadata']
            print(f"  ✅ Pipeline test passed")
            print(f"     Processing time: {processing_time*1000:.2f}ms")
            print(f"     Pages/sec: {metadata['pages_per_sec']:.1f}")
            print(f"     Entities found: {metadata['entities_found']}")
            print(f"     Engine used: {metadata['engine_used']}")
            
            # Check outputs
            outputs = result.get('output_paths', {})
            print(f"     Generated outputs: {list(outputs.keys())}")
            
            # Verify files exist
            for output_type, path in outputs.items():
                if Path(path).exists():
                    size = Path(path).stat().st_size
                    print(f"       {output_type}: {path} ({size} bytes)")
                else:
                    print(f"       ❌ {output_type}: {path} (not found)")
            
            return True
        else:
            print(f"  ❌ Pipeline failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"  ❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """Quick performance test."""
    print("\n⚡ Running Performance Test...")
    
    try:
        pipeline = FusionPipeline()
        
        # Simple test content
        test_content = "OSHA requires safety training. Contact safety@company.com for $500 training."
        
        # Run multiple iterations
        iterations = 10
        start_time = time.time()
        
        results = []
        for i in range(iterations):
            result = pipeline.process_document(f"perf_test_{i}.txt", test_content)
            results.append(result)
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r['status'] == 'success')
        
        if successful > 0:
            docs_per_sec = successful / total_time
            avg_time_ms = (total_time / successful) * 1000
            
            print(f"  ✅ Performance test completed")
            print(f"     Iterations: {iterations}")
            print(f"     Successful: {successful}/{iterations}")
            print(f"     Rate: {docs_per_sec:.1f} docs/sec")
            print(f"     Avg time: {avg_time_ms:.2f}ms per doc")
            
            # Get detailed metrics
            metrics = pipeline.get_performance_metrics()
            print(f"     Pipeline pages/sec: {metrics.get('pages_per_second', 0):.1f}")
            
            return True
        else:
            print(f"  ❌ All performance tests failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Performance test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 MVP-Fusion System Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test fusion engine
    if test_fusion_engine():
        tests_passed += 1
    
    # Test pipeline
    if test_pipeline():
        tests_passed += 1
    
    # Test performance
    if test_performance():
        tests_passed += 1
    
    # Summary
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! MVP-Fusion is ready to use.")
        print("\nTo run the command-line interface:")
        print("  python fusion_cli.py --performance-test")
        print("  python fusion_cli.py --file your_document.txt")
        print("  python fusion_cli.py --directory ~/documents/")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)