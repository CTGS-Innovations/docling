#!/usr/bin/env python3
"""
Extract organizations from the concatenated 'all_organizations' field
This field contains comma-separated lists of US organization names
"""

import os
import re
from datasets import load_dataset

BASE = os.path.join(os.getcwd(), "data")
OUTPUT_DIR = os.path.join(BASE, "500k_ner")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_organizations_from_concatenated_list(output_text):
    """Extract organizations from the concatenated list format in JSON output"""
    organizations = set()
    
    # Look for the "all_organizations" pattern in the text
    # The SQL query creates lists like: [org1,org2,org3] or [org1]
    
    # Try to find JSON-like structure first
    try:
        import json
        data = json.loads(output_text)
        if 'organizations' in data:
            for org_entry in data['organizations']:
                if isinstance(org_entry, dict) and 'name' in org_entry:
                    org_name = org_entry['name'].strip()
                    if len(org_name) >= 2:
                        organizations.add(org_name)
    except:
        pass
    
    # Also extract using regex patterns
    # Pattern to match: "name": "organization_name"
    name_pattern = r'"name": "([^"]+)"'
    matches = re.findall(name_pattern, output_text, re.IGNORECASE)
    
    for org_name in matches:
        cleaned = org_name.strip()
        if len(cleaned) >= 2 and cleaned.lower() not in ['', 'null', 'none', 'unknown']:
            organizations.add(cleaned)
    
    return organizations

def clean_organization_name(org_name):
    """Clean and normalize organization names"""
    if not org_name:
        return None
    
    # Basic cleanup
    org_name = org_name.strip()
    org_name = re.sub(r'\s+', ' ', org_name)  # Normalize whitespace
    org_name = org_name.strip('"\'.,;:!?[]')  # Remove quotes, punctuation, brackets
    
    # Skip if too short or clearly not a real organization
    if len(org_name) < 2:
        return None
    
    skip_patterns = [
        r'^[A-Z]{1,2}$',  # Single/double letters
        r'^\d+$',  # Just numbers
        r'^[^a-zA-Z]+$',  # No letters at all
    ]
    
    for pattern in skip_patterns:
        if re.match(pattern, org_name, re.IGNORECASE):
            return None
    
    return org_name

def main():
    print("🚀 Extracting Organizations from Concatenated Lists in 500K NER Dataset")
    
    try:
        # Load dataset
        dataset = load_dataset("adambuttrick/500K-ner-indexes-multiple-organizations-locations-alpaca-format-json-response-all-cases")
        data = dataset['train']
        
        print(f"✅ Dataset loaded: {len(data):,} examples")
        
        all_organizations = set()
        total_org_mentions = 0
        
        print(f"\n🔍 Extracting organizations from concatenated lists...")
        
        for i, example in enumerate(data):
            if i % 25000 == 0:
                print(f"  Processed {i:,}/{len(data):,} examples... Found {len(all_organizations):,} unique orgs")
            
            output_text = example.get('output', '')
            if output_text:
                orgs = extract_organizations_from_concatenated_list(output_text)
                
                for org in orgs:
                    cleaned = clean_organization_name(org)
                    if cleaned:
                        all_organizations.add(cleaned)
                        total_org_mentions += 1
        
        print(f"\n🎉 EXTRACTION COMPLETE!")
        print(f"📊 Total examples processed: {len(data):,}")
        print(f"📊 Total organization mentions: {total_org_mentions:,}")
        print(f"📊 Unique organizations found: {len(all_organizations):,}")
        
        # Save all organizations
        output_file = os.path.join(OUTPUT_DIR, "concatenated_us_organizations_500k.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            for org in sorted(all_organizations):
                f.write(org + '\n')
        
        print(f"💾 Saved organizations to: {output_file}")
        
        # Also save as CSV
        csv_file = os.path.join(OUTPUT_DIR, "concatenated_us_organizations_500k.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("organization_name\n")
            for org in sorted(all_organizations):
                f.write(f'"{org}"\n')
        
        print(f"💾 Also saved as CSV: {csv_file}")
        
        # Show sample of extracted organizations
        print(f"\n📋 Sample of extracted organizations:")
        sample_orgs = sorted(all_organizations)[:30]
        for i, org in enumerate(sample_orgs, 1):
            print(f"  {i:2d}. {org}")
        
        if len(all_organizations) > 30:
            print(f"  ... and {len(all_organizations) - 30:,} more")
        
        # Check for interesting patterns
        university_count = sum(1 for org in all_organizations if 'university' in org.lower())
        hospital_count = sum(1 for org in all_organizations if any(term in org.lower() for term in ['hospital', 'medical', 'health']))
        institute_count = sum(1 for org in all_organizations if 'institute' in org.lower())
        
        print(f"\n📊 Organization type breakdown:")
        print(f"  Universities: {university_count:,}")
        print(f"  Hospitals/Medical: {hospital_count:,}")
        print(f"  Institutes: {institute_count:,}")
        print(f"  Other: {len(all_organizations) - university_count - hospital_count - institute_count:,}")
        
        print(f"\n🎯 Progress toward 100K target: {len(all_organizations):,}/100,000 ({len(all_organizations)/100000*100:.1f}%)")
        
        if len(all_organizations) >= 100000:
            print("🏆 TARGET ACHIEVED! We have 100K+ organizations!")
        else:
            needed = 100000 - len(all_organizations)
            print(f"📈 Need {needed:,} more to reach 100K")
            if needed < 10000:
                print("🔥 Very close to target! This dataset might get us there.")
        
        return len(all_organizations)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

if __name__ == "__main__":
    main()