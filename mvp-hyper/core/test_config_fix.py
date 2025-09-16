#!/usr/bin/env python3
"""
Test script to verify that the enhanced dictionary configuration is being loaded correctly.
"""

import yaml
from enhanced_classification_with_entities import EnhancedClassifierWithEntities

def test_enhanced_dictionary_loading():
    """Test if the enhanced dictionary is being loaded with config."""
    
    # Load config
    with open('.config/mvp-simple.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print("🔧 Testing enhanced dictionary loading...")
    print(f"Config dictionary file: {config.get('classification', {}).get('dictionary_file', 'Not set')}")
    
    # Initialize classifier with config
    classifier = EnhancedClassifierWithEntities(config=config)
    
    # Debug: Check if dictionary was loaded
    print(f"\nDictionary config keys: {list(classifier.dictionary_config.keys())}")
    print(f"Dictionary path used: {classifier.dictionary_config}")
    
    # Check if ai_ml domain exists
    if 'ai_ml' in classifier.dictionary_config:
        print(f"AI/ML domain found with {len(classifier.dictionary_config['ai_ml'])} categories")
        # Check AI/ML terms
        ai_ml_data = classifier.dictionary_config['ai_ml']
        if 'algorithms' in ai_ml_data:
            ai_ml_terms = ai_ml_data['algorithms']
            print(f"AI/ML algorithms: {len(ai_ml_terms)} terms")
            diffusion_terms = [term for term in ai_ml_terms if 'diffusion' in term.lower()]
            print(f"Diffusion-related terms: {diffusion_terms}")
    else:
        print("❌ AI/ML domain not found in dictionary config!")
    
    # Check if automatons were built
    print(f"\nAutomatons built: {len(classifier.domain_automatons)}")
    print(f"Domain automatons: {list(classifier.domain_automatons.keys())}")
    
    # Test if ahocorasick is available
    print("AhoCorasick availability check:")
    
    try:
        import ahocorasick
        print("✅ ahocorasick module imported successfully")
    except ImportError:
        print("❌ ahocorasick module not available!")
    
    # Test text with AI/ML terms that should be in enhanced dictionary
    test_text = """
    This paper presents a diffusion probabilistic model for image generation.
    We train our model on CIFAR10 dataset using denoising score matching.
    The diffusion process gradually adds noise to the data.
    """
    
    # Classify the test text
    result = classifier.classify_and_extract(test_text, "test_diffusion.md")
    
    print("\n📊 Classification Results:")
    print(f"Primary domain: {result.get('primary_domain', 'Unknown')}")
    print(f"Domain percentages: {result.get('domain_percentages', {})}")
    
    # Check if it correctly identifies as AI/ML
    if result.get('primary_domain') == 'ai_ml':
        print("✅ SUCCESS: Correctly classified as AI/ML domain")
        return True
    else:
        print("❌ FAILURE: Incorrect classification")
        print("   Expected: ai_ml")
        print(f"   Got: {result.get('primary_domain')}")
        return False

if __name__ == "__main__":
    success = test_enhanced_dictionary_loading()
    exit(0 if success else 1)