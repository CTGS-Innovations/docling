#!/usr/bin/env python3
"""
Generate domain-specific entity lists using working OpenAI model (gpt-4o-mini)
Updated to handle JSON wrapped in markdown
"""

import os
import json
import time
import re
from openai import OpenAI

# Domain definitions for founder intelligence  
DOMAINS = {
    "biotech_pharma": {
        "name": "Biotech and Pharmaceutical Companies",
        "description": "Biotechnology companies, pharmaceutical companies, medical device manufacturers, clinical research organizations, and life sciences companies",
        "target_count": 500
    },
    "fintech_crypto": {
        "name": "Fintech and Cryptocurrency Companies", 
        "description": "Financial technology companies, cryptocurrency exchanges, blockchain companies, payment processors, neobanks, and digital banking platforms",
        "target_count": 500
    },
    "ai_ml": {
        "name": "AI and Machine Learning Companies",
        "description": "Artificial intelligence companies, machine learning platforms, computer vision companies, NLP companies, and AI infrastructure providers",
        "target_count": 500
    }
}

# Years to iterate through (can expand to full 2015-2025 range)
YEARS = [2025, 2024, 2023, 2022, 2021]

def setup_openai_client():
    """Setup OpenAI client with working model"""
    api_key = "NO_KEY"
    return OpenAI(api_key=api_key)

def extract_json_from_response(content):
    """Extract JSON from markdown-wrapped response"""
    # Try direct JSON parsing first
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass
    
    # Look for JSON wrapped in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Look for any JSON-like structure
    json_match = re.search(r'\{.*?\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    print(f"❌ Could not extract JSON from: {content[:200]}...")
    return None

def generate_yearly_companies(client, domain_key, domain_info, year, count=50):
    """Generate companies for a specific domain and year"""
    
    print(f"\n🤖 Generating {count} {domain_info['name']} for {year}")
    
    prompt = f"""Generate a list of the top {count} most prominent {domain_info['name']} that were particularly successful, notable, or market-leading specifically in {year}.

Focus on companies that were:
- Market leaders or notable players in {year}
- Recently funded, launched, or gained prominence in {year}
- Had significant business milestones in {year}
- Were frequently mentioned in business media during {year}
- {domain_info['description']}

Prioritize US-based companies, but include major international players that were significant in the US market during {year}.

Return ONLY a JSON object with this exact structure:
{{
    "year": {year},
    "domain": "{domain_info['name']}",
    "companies": [
        "Company Name 1",
        "Company Name 2"
    ]
}}

Requirements:
- Use official company names
- No explanations or additional text outside the JSON
- Exactly {count} company names
- Focus on companies that were specifically relevant/prominent in {year}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using working model
            messages=[
                {
                    "role": "system", 
                    "content": f"You are an expert in business history and market analysis. Generate accurate lists of companies that were specifically prominent in given years. Focus on {year} specifically."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from potentially markdown-wrapped response
        data = extract_json_from_response(content)
        
        if data and 'companies' in data:
            companies = data['companies']
            print(f"✅ Generated {len(companies)} companies for {year}")
            print(f"📋 Sample: {', '.join(companies[:5])}")
            return companies
        else:
            print(f"❌ Failed to extract companies for {year}")
            print(f"Raw response: {content[:300]}...")
            return []
            
    except Exception as e:
        print(f"❌ API error for {year}: {e}")
        return []

def test_single_domain():
    """Test with one domain to verify quality"""
    
    print("🧪 TESTING DOMAIN GENERATION WITH WORKING MODEL")
    print("Testing: Fintech companies for recent years")
    print("=" * 60)
    
    try:
        client = setup_openai_client()
        print("✅ OpenAI client initialized (gpt-4o-mini)")
    except Exception as e:
        print(f"❌ Failed to setup OpenAI: {e}")
        return
    
    # Test with fintech for 3 years
    domain_key = "fintech_crypto"
    domain_info = DOMAINS[domain_key]
    test_years = [2024, 2023, 2022]
    
    all_companies = {}
    total_generated = 0
    
    for year in test_years:
        companies = generate_yearly_companies(client, domain_key, domain_info, year, count=20)  # Smaller test
        
        if companies:
            all_companies[year] = companies
            total_generated += len(companies)
            
            # Save individual year results
            os.makedirs("data/test_working", exist_ok=True)
            with open(f"data/test_working/fintech_{year}.json", 'w') as f:
                json.dump({
                    "year": year,
                    "domain": domain_info['name'],
                    "companies": companies
                }, f, indent=2)
        
        # Rate limiting
        time.sleep(2)
    
    # Analysis
    print(f"\n📊 TEST RESULTS:")
    print(f"Years processed: {len(all_companies)}")
    print(f"Total companies: {total_generated}")
    
    if all_companies:
        # Check quality
        all_names = []
        for year, companies in all_companies.items():
            print(f"\n📅 {year} ({len(companies)} companies):")
            for i, company in enumerate(companies[:8], 1):
                print(f"  {i:2d}. {company}")
            all_names.extend([c.lower() for c in companies])
        
        unique_names = set(all_names)
        duplicate_rate = (len(all_names) - len(unique_names)) / len(all_names) * 100
        
        print(f"\n🔍 Quality Analysis:")
        print(f"Unique companies: {len(unique_names)}")
        print(f"Duplicate rate: {duplicate_rate:.1f}% (some overlap expected)")
        
        # Check for obvious issues
        suspicious = [name for name in unique_names if len(name) < 3 or name.isdigit()]
        if suspicious:
            print(f"🚨 Suspicious entries: {suspicious}")
        else:
            print("✅ No obvious quality issues detected")
        
        print(f"\n🎯 VERDICT:")
        if len(unique_names) >= 30 and duplicate_rate < 50:
            print("✅ Quality looks good! Ready to scale up.")
            return True
        else:
            print("❌ Quality issues detected. Review prompts.")
            return False
    else:
        print("❌ No companies generated")
        return False

if __name__ == "__main__":
    success = test_single_domain()
    
    if success:
        print(f"\n🚀 Ready to proceed with full generation!")
        print(f"Estimated cost for 12 domains × 5 years × 50 companies:")
        print(f"~3,000 companies × $0.15 per 1K tokens = ~$0.45 total")
    else:
        print(f"\n🔧 Fix quality issues before scaling")