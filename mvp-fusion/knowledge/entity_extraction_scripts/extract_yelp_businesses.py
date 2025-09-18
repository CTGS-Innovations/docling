#!/usr/bin/env python3
"""
Extract US business names from Yelp Open Dataset
https://huggingface.co/datasets/yashraizada/yelp-open-dataset-business

This dataset contains millions of Yelp business listings, primarily US-based.
Using streaming mode to handle the large dataset efficiently.
"""

import os
import re
from datasets import load_dataset

BASE = os.path.join(os.getcwd(), "data")
OUTPUT_DIR = os.path.join(BASE, "yelp_businesses")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_business_name(business_name):
    """Clean and normalize business names"""
    if not business_name:
        return None
    
    # Basic cleanup
    business_name = business_name.strip()
    business_name = re.sub(r'\s+', ' ', business_name)  # Normalize whitespace
    
    # Skip if too short or clearly not a real business
    if len(business_name) < 2:
        return None
    
    # Skip common non-business patterns
    skip_patterns = [
        r'^[A-Z]{1,2}$',  # Single/double letters
        r'^\d+$',  # Just numbers
        r'^[^a-zA-Z]+$',  # No letters at all
        r'^(test|demo|sample|example)$',  # Test entries
    ]
    
    for pattern in skip_patterns:
        if re.match(pattern, business_name, re.IGNORECASE):
            return None
    
    return business_name

def is_us_business(business_data):
    """Check if business is US-based using location fields"""
    # Check country field if available
    country = business_data.get('country', '').strip().upper()
    if country and country not in ['US', 'USA', 'UNITED STATES', '']:
        return False
    
    # Check state field for US states
    state = business_data.get('state', '').strip().upper()
    us_states = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
        # Full state names
        'ALABAMA', 'ALASKA', 'ARIZONA', 'ARKANSAS', 'CALIFORNIA', 'COLORADO', 'CONNECTICUT', 'DELAWARE', 'FLORIDA', 'GEORGIA', 'HAWAII', 'IDAHO', 'ILLINOIS', 'INDIANA', 'IOWA', 'KANSAS', 'KENTUCKY', 'LOUISIANA', 'MAINE', 'MARYLAND', 'MASSACHUSETTS', 'MICHIGAN', 'MINNESOTA', 'MISSISSIPPI', 'MISSOURI', 'MONTANA', 'NEBRASKA', 'NEVADA', 'NEW HAMPSHIRE', 'NEW JERSEY', 'NEW MEXICO', 'NEW YORK', 'NORTH CAROLINA', 'NORTH DAKOTA', 'OHIO', 'OKLAHOMA', 'OREGON', 'PENNSYLVANIA', 'RHODE ISLAND', 'SOUTH CAROLINA', 'SOUTH DAKOTA', 'TENNESSEE', 'TEXAS', 'UTAH', 'VERMONT', 'VIRGINIA', 'WASHINGTON', 'WEST VIRGINIA', 'WISCONSIN', 'WYOMING'
    }
    
    if state in us_states:
        return True
    
    # If no clear location indicators, assume US (since this is Yelp US dataset)
    return True

def main():
    print("🚀 Extracting US Business Names from Yelp Open Dataset")
    print("Dataset: yashraizada/yelp-open-dataset-business")
    print("Using streaming mode for efficient processing...")
    
    try:
        # Load dataset in streaming mode
        dataset = load_dataset("yashraizada/yelp-open-dataset-business", streaming=True)
        
        print(f"✅ Dataset loaded in streaming mode")
        
        # Check available splits
        if hasattr(dataset, 'keys'):
            splits = list(dataset.keys())
            print(f"📊 Available splits: {splits}")
            # Use train split or first available split
            if 'train' in splits:
                data_stream = dataset['train']
            else:
                split_name = splits[0]
                data_stream = dataset[split_name]
                print(f"Using split: {split_name}")
        else:
            data_stream = dataset
        
        # Show first example to understand structure
        print("\n🔍 Examining dataset structure...")
        first_example = next(iter(data_stream))
        print("First example fields:")
        for key, value in first_example.items():
            print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
        
        # Reset stream and process
        data_stream = load_dataset("yashraizada/yelp-open-dataset-business", streaming=True)
        if hasattr(dataset, 'keys'):
            if 'train' in list(dataset.keys()):
                data_stream = data_stream['train']
            else:
                data_stream = data_stream[list(dataset.keys())[0]]
        
        us_businesses = set()
        total_processed = 0
        us_count = 0
        
        print(f"\n🔍 Processing Yelp businesses...")
        
        for i, business in enumerate(data_stream):
            total_processed += 1
            
            if total_processed % 50000 == 0:
                print(f"  Processed {total_processed:,} businesses... Found {len(us_businesses):,} unique US businesses")
            
            # Extract business name
            business_name = None
            for name_field in ['name', 'business_name', 'title', 'business_id']:
                if name_field in business:
                    business_name = business[name_field]
                    break
            
            if not business_name:
                continue
            
            # Check if US-based
            if is_us_business(business):
                us_count += 1
                cleaned_name = clean_business_name(business_name)
                if cleaned_name:
                    us_businesses.add(cleaned_name)
            
            # Limit processing for testing (remove this in production)
            if total_processed >= 500000:  # Process up to 500K for now
                break
        
        print(f"\n🎉 YELP EXTRACTION COMPLETE!")
        print(f"📊 Total businesses processed: {total_processed:,}")
        print(f"📊 US businesses found: {us_count:,}")
        print(f"📊 Unique business names: {len(us_businesses):,}")
        
        # Save businesses
        output_file = os.path.join(OUTPUT_DIR, "yelp_us_businesses.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            for business in sorted(us_businesses):
                f.write(business + '\n')
        
        print(f"💾 Saved US businesses to: {output_file}")
        
        # Also save as CSV
        csv_file = os.path.join(OUTPUT_DIR, "yelp_us_businesses.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("business_name\n")
            for business in sorted(us_businesses):
                f.write(f'"{business}"\n')
        
        print(f"💾 Also saved as CSV: {csv_file}")
        
        # Show sample of extracted businesses
        print(f"\n📋 Sample of Yelp US businesses:")
        sample_businesses = sorted(us_businesses)[:25]
        for i, business in enumerate(sample_businesses, 1):
            print(f"  {i:2d}. {business}")
        
        if len(us_businesses) > 25:
            print(f"  ... and {len(us_businesses) - 25:,} more")
        
        print(f"\n🎯 Yelp contribution toward 100K target: {len(us_businesses):,} new organizations")
        
        return len(us_businesses)
        
    except Exception as e:
        print(f"❌ Error loading Yelp dataset: {e}")
        print("This might be due to:")
        print("  - Dataset access permissions")
        print("  - Network connectivity issues")
        print("  - Dataset structure changes")
        return 0

if __name__ == "__main__":
    main()