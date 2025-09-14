#!/usr/bin/env python3
"""
Test script to demonstrate the three-tier pipeline
"""

import os
import tempfile
from pathlib import Path

# Create test content for different domains
test_documents = {
    "business_example.md": """
# Acme Corporation Business Plan

Acme Corp, a technology company founded by CEO John Smith, announced a $50 million Series B funding round led by Venture Capital Partners. The company is located in San Francisco, California.

Contact Information:
- Email: info@acmecorp.com
- Phone: (555) 123-4567
- Website: https://www.acmecorp.com

## Market Analysis

The company struggles with manual data processing workflows that are time-consuming and expensive, creating significant bottlenecks in operations. 

The market for automated workflow solutions is estimated to be worth $2.5 billion and growing at 25% annually. There's a clear opportunity for AI-driven automation tools in the enterprise sector.

## Innovation & Competition

Our breakthrough approach to machine learning represents a novel solution for process automation. Key competitors include TechFlow Inc. and DataStream Corporation, but our partnership with Microsoft Corporation provides strategic advantages.

## Challenges

Current pain points include difficulty integrating legacy systems, expensive maintenance costs, and barriers to user adoption among enterprise clients.
""",

    "research_paper.md": """
# Denoising Diffusion Probabilistic Models

Jonathan Ho, Ajay Jain, Pieter Abbeel
UC Berkeley
{jho,ajay_jain,pabbeel}@berkeley.edu

## Abstract

We present high quality image synthesis results using diffusion probabilistic models, trained on the CIFAR-10 dataset. Our approach demonstrates superior performance on the ImageNet benchmark with FID scores of 3.17.

## Method

We propose a novel denoising technique that leverages transformer architectures. The DiffusionNet algorithm achieves state-of-the-art results by optimizing the reverse diffusion process.

## Experimental Results

Our experiments on the CelebA-HQ dataset show significant improvements over baseline methods. The DDPM framework outperforms previous approaches by 15% on standard metrics.

Stanford University and MIT have collaborated on similar research, but our approach using reinforcement learning represents a breakthrough innovation in generative modeling.
""",

    "safety_document.md": """
# OSHA Workplace Safety Guidelines

## Hazard Identification and Control

Employers must comply with 29 CFR 1910.95 regarding occupational noise exposure. Workers exposed to noise levels exceeding 90 decibels require hearing protection equipment.

## Personal Protective Equipment (PPE)

Required safety equipment includes:
- Hard hats for construction work
- Safety glasses in manufacturing areas  
- Hearing protection when noise exceeds 85 dB
- Respirators in areas with airborne contaminants

## Emergency Procedures

In case of accidents, employers must:
1. Provide immediate medical attention
2. Report incidents within 24 hours to OSHA
3. Conduct thorough incident investigations
4. Implement corrective actions to prevent recurrence

Competent persons shall conduct daily safety inspections. Any violations may result in citations and penalties up to $70,000 for willful violations.

## Training Requirements

All employees must receive safety training before starting work. Specialized training is required for:
- Confined space entry (29 CFR 1910.146)
- Lockout/tagout procedures (29 CFR 1910.147)  
- Hazard communication (29 CFR 1910.1200)
"""
}

def create_test_files():
    """Create test files in a temporary directory."""
    test_dir = Path("test_input")
    test_dir.mkdir(exist_ok=True)
    
    for filename, content in test_documents.items():
        file_path = test_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"✅ Created {len(test_documents)} test files in {test_dir}")
    return test_dir

def run_pipeline_tests():
    """Run the pipeline with different tier configurations."""
    
    test_dir = create_test_files()
    
    print("\n" + "="*60)
    print("🚀 TESTING THREE-TIER PIPELINE")
    print("="*60)
    
    # Test 1: Baseline (just markdown conversion)
    print("\n📋 Test 1: Baseline Processing (--baseline)")
    os.system(f"python mvp-hyper-pipeline.py {test_dir} --output test_output_baseline --baseline")
    
    # Test 2: Tier 1 only (document classification)
    print("\n📊 Test 2: Tier 1 Classification (--tier1-only)")
    os.system(f"python mvp-hyper-pipeline.py {test_dir} --output test_output_tier1 --tier1-only")
    
    # Test 3: Tier 1 + 2 (classification + domain tagging)
    print("\n🏷️  Test 3: Tier 1+2 Pre-tagging (--tier2-only)")
    os.system(f"python mvp-hyper-pipeline.py {test_dir} --output test_output_tier2 --tier2-only")
    
    # Test 4: Full pipeline (all three tiers)
    print("\n🧠 Test 4: Full Pipeline (default)")
    os.system(f"python mvp-hyper-pipeline.py {test_dir} --output test_output_full")
    
    print("\n" + "="*60)
    print("✅ PIPELINE TESTING COMPLETE")
    print("="*60)
    
    # Show results comparison
    print("\n📁 Output directories created:")
    for output_dir in ["test_output_baseline", "test_output_tier1", "test_output_tier2", "test_output_full"]:
        if Path(output_dir).exists():
            files = list(Path(output_dir).glob("*"))
            print(f"  {output_dir}: {len(files)} files")
    
    print("\n🔍 To compare results, examine the front matter in:")
    print("  - test_output_tier1/business_example.md   (classification only)")
    print("  - test_output_tier2/business_example.md   (+ domain tagging)")  
    print("  - test_output_full/business_example.md    (+ semantic extraction)")
    print("  - test_output_full/business_example.metadata.json (semantic facts)")

if __name__ == "__main__":
    run_pipeline_tests()