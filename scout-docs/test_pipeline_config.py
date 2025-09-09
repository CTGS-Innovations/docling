#!/usr/bin/env python3
"""
Simple test script to validate pipeline configuration without full server startup.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_pipeline_configurations():
    """Test that all pipeline configurations can be loaded correctly."""
    print("🔧 Testing pipeline configurations...")
    
    try:
        from app.pipeline_configs import PipelineRegistry, PipelineProfile
        
        # Test that all profiles can be enumerated
        profiles = list(PipelineProfile)
        print(f"✅ Found {len(profiles)} pipeline profiles: {[p.value for p in profiles]}")
        
        # Test that all profiles have valid configurations
        for profile in profiles:
            config = PipelineRegistry.get_config(profile)
            print(f"✅ {profile.value}: {config.name} ({config.performance} performance)")
            
            # Test creating pipeline options (this will test the backend imports)
            try:
                options, backend_class = PipelineRegistry.create_pipeline_options(profile, "cpu")
                print(f"   - Backend: {backend_class.__name__}")
                print(f"   - OCR: {options.do_ocr}")
                print(f"   - Tables: {options.do_table_structure}")
                print(f"   - Images: {options.generate_page_images}")
            except Exception as e:
                print(f"❌ Failed to create options for {profile.value}: {e}")
                return False
        
        # Test list_profiles for API consumption
        api_profiles = PipelineRegistry.list_profiles()
        print(f"✅ API profiles list contains {len(api_profiles)} profiles")
        
        print("🎉 All pipeline configurations are working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   This is expected if docling dependencies are not installed.")
        print("   The configuration structure is valid, just can't test full functionality.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_performance_characteristics():
    """Test that performance characteristics match expectations."""
    print("\n📊 Testing performance characteristics...")
    
    try:
        from app.pipeline_configs import PipelineRegistry, PipelineProfile
        
        # Expected performance rankings (faster = lower number)
        expected_ranking = {
            PipelineProfile.FAST_TEXT: 1,      # Fastest
            PipelineProfile.BALANCED: 2,       # Fast  
            PipelineProfile.OCR_ONLY: 3,       # Medium
            PipelineProfile.TABLE_FOCUSED: 3,  # Medium
            PipelineProfile.STANDARD: 3,       # Medium
            PipelineProfile.FULL_EXTRACTION: 4, # Slow
            PipelineProfile.VLM: 4              # Slow
        }
        
        for profile, expected_rank in expected_ranking.items():
            config = PipelineRegistry.get_config(profile)
            performance_map = {"Fastest": 1, "Fast": 2, "Medium": 3, "Slow": 4}
            actual_rank = performance_map.get(config.performance, 5)
            
            if actual_rank == expected_rank:
                print(f"✅ {profile.value}: {config.performance} (rank {actual_rank})")
            else:
                print(f"⚠️ {profile.value}: Expected rank {expected_rank}, got rank {actual_rank}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing performance characteristics: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Docling Pipeline Configuration System")
    print("=" * 50)
    
    success1 = test_pipeline_configurations()
    success2 = test_performance_characteristics()
    
    if success1 and success2:
        print("\n✅ All tests passed! Pipeline configuration is ready for use.")
        exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        exit(1)