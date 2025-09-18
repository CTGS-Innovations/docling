#!/usr/bin/env python3
"""
Foundation Corpus Builder - 100K/100K/100K Strategy
====================================================
Builds the foundational entity corpus with memory-optimized allocation:
- 100K first names (highest frequency, global coverage)
- 100K last names (broad surname coverage) 
- 100K organizations (Fortune 500 + startups + VCs + universities)

Total Memory Target: ~92MB (well under 1GB limit)
Performance Target: >100K entities/second disambiguation
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional
from collections import Counter, defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FoundationCorpusBuilder:
    """
    Builds the foundational 100K/100K/100K entity corpus from high-quality sources.
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent / "foundation_data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage for entities with frequency tracking
        self.first_names = Counter()
        self.last_names = Counter()  
        self.organizations = Counter()
        
        # Quality scores (source reliability)
        self.source_weights = {
            'manual_curated': 10.0,     # Fortune 500, major VCs
            'government_data': 8.0,      # Census data, SEC filings
            'academic_verified': 7.0,    # University rankings
            'ner_datasets': 6.0,        # CoNLL-2003, WikiANN
            'company_registries': 5.0,   # Business registrations
            'web_verified': 3.0,        # Crunchbase, verified sources
            'web_scraped': 1.0          # General web scraping
        }
        
        # Statistics tracking
        self.build_stats = defaultdict(int)
        
    def build_foundation_corpus(self) -> Dict[str, List[str]]:
        """
        Main method to build the 100K/100K/100K foundation corpus.
        
        Returns:
            Dictionary with the final corpus data
        """
        logger.info("🚀 Building Foundation Corpus: 100K/100K/100K Strategy")
        logger.info("=" * 60)
        
        # Phase 1: Manual curated high-value entities
        logger.info("📋 Phase 1: Manual Curated Entities")
        self._add_manual_curated_organizations()
        self._add_common_names_foundation()
        
        # Phase 2: Download government/verified data  
        logger.info("📊 Phase 2: Government & Verified Data")
        self._add_government_data()
        self._add_university_rankings()
        
        # Phase 3: Process NER datasets (if available)
        logger.info("🔬 Phase 3: NER Dataset Processing")
        self._process_available_ner_datasets()
        
        # Phase 4: Web APIs and verified sources
        logger.info("🌐 Phase 4: API & Verified Sources")
        self._add_verified_web_sources()
        
        # Phase 5: Filter and rank to 100K each
        logger.info("🎯 Phase 5: Ranking & Filtering to 100K Each")
        final_corpus = self._rank_and_filter_to_100k()
        
        # Phase 6: Save and validate
        logger.info("💾 Phase 6: Save & Validate")
        self._save_foundation_corpus(final_corpus)
        self._validate_corpus_quality(final_corpus)
        
        return final_corpus
    
    def _add_manual_curated_organizations(self):
        """Add manually curated high-priority organizations."""
        logger.info("  🏢 Adding manually curated organizations...")
        
        # Fortune 500 tech companies (high priority)
        fortune_500_tech = [
            "Apple", "Microsoft", "Alphabet", "Google", "Amazon", "Meta", "Facebook", 
            "Tesla", "NVIDIA", "Intel", "Oracle", "Salesforce", "Adobe", "IBM", 
            "Cisco", "Qualcomm", "Broadcom", "Texas Instruments", "Advanced Micro Devices",
            "Netflix", "PayPal", "Intuit", "ServiceNow", "Workday", "Snowflake"
        ]
        
        # Major VC firms (founder intelligence priority)
        major_vc_firms = [
            "Sequoia Capital", "Andreessen Horowitz", "Benchmark", "Accel Partners",
            "Greylock Partners", "Kleiner Perkins", "Lightspeed Venture Partners",
            "Bessemer Venture Partners", "Index Ventures", "General Catalyst",
            "Founders Fund", "Thrive Capital", "Tiger Global Management", "Coatue Management",
            "Insight Partners", "GV", "Google Ventures", "Microsoft Ventures", "Intel Capital",
            "NEA", "Norwest Venture Partners", "Battery Ventures", "Matrix Partners",
            "Mayfield Fund", "Menlo Ventures", "Redpoint Ventures", "Scale Venture Partners",
            "Spark Capital", "Union Square Ventures", "Village Global", "First Round Capital"
        ]
        
        # Major PE firms
        major_pe_firms = [
            "Blackstone", "KKR", "Apollo Global Management", "The Carlyle Group",
            "TPG", "Warburg Pincus", "Bain Capital", "CVC Capital Partners",
            "EQT Partners", "Silver Lake", "Vista Equity Partners", "Thoma Bravo",
            "Francisco Partners", "Permira", "Hellman & Friedman", "Leonard Green & Partners"
        ]
        
        # Accelerators and incubators
        accelerators = [
            "Y Combinator", "Techstars", "500 Startups", "500 Global", "Plug and Play",
            "Alchemist Accelerator", "AngelPad", "Dreamit Ventures", "Founder Institute",
            "MassChallenge", "SOSV", "Betaworks", "Science Inc", "Idealab", "Rocket Internet"
        ]
        
        # Major startups and unicorns (founder intelligence targets)
        major_startups = [
            "OpenAI", "Anthropic", "SpaceX", "Stripe", "ByteDance", "TikTok", "Canva",
            "Databricks", "Figma", "Notion", "Discord", "Clubhouse", "Robinhood", 
            "Coinbase", "Binance", "Airbnb", "Uber", "Lyft", "DoorDash", "Instacart",
            "Shopify", "Zoom", "Slack", "Atlassian", "Asana", "Monday.com", "Miro",
            "GitLab", "GitHub", "Docker", "Kubernetes", "MongoDB", "Redis", "Elastic"
        ]
        
        # Add all with high weight
        for org in fortune_500_tech + major_vc_firms + major_pe_firms + accelerators + major_startups:
            self.organizations[org] += self.source_weights['manual_curated']
        
        self.build_stats['manual_orgs'] = len(fortune_500_tech + major_vc_firms + major_pe_firms + accelerators + major_startups)
        logger.info(f"    Added {self.build_stats['manual_orgs']} high-priority organizations")
    
    def _add_common_names_foundation(self):
        """Add foundation of most common first and last names."""
        logger.info("  👤 Adding common name foundations...")
        
        # Most common US first names (manually curated for quality)
        common_first_names_male = [
            "james", "john", "robert", "michael", "william", "david", "richard", "joseph",
            "thomas", "christopher", "charles", "daniel", "matthew", "anthony", "mark",
            "donald", "steven", "paul", "andrew", "joshua", "kenneth", "kevin", "brian",
            "george", "timothy", "ronald", "jason", "edward", "jeffrey", "ryan", "jacob",
            "gary", "nicholas", "eric", "jonathan", "stephen", "larry", "justin", "scott",
            "brandon", "benjamin", "samuel", "gregory", "alexander", "patrick", "frank",
            "raymond", "jack", "dennis", "jerry", "tyler", "aaron", "jose", "henry",
            "adam", "douglas", "nathan", "peter", "zachary", "kyle", "noah", "alan",
            "ethan", "jeremy", "lionel", "angel", "jordan", "wayne", "arthur", "sean",
            "felix", "carl", "harold", "ralph", "eugene", "philip", "nathan"
        ]
        
        common_first_names_female = [
            "mary", "patricia", "jennifer", "linda", "elizabeth", "barbara", "susan",
            "jessica", "sarah", "karen", "nancy", "lisa", "betty", "helen", "sandra",
            "donna", "carol", "ruth", "sharon", "michelle", "laura", "sarah", "kimberly",
            "deborah", "dorothy", "lisa", "nancy", "karen", "betty", "helen", "sandra",
            "donna", "carol", "ruth", "sharon", "michelle", "laura", "emily", "kimberly",
            "deborah", "dorothy", "amy", "angela", "ashley", "brenda", "emma", "olivia",
            "cynthia", "marie", "janet", "catherine", "frances", "christine", "samantha",
            "debra", "rachel", "carolyn", "janet", "virginia", "maria", "heather", "diane"
        ]
        
        # Tech industry names (higher priority for founder intelligence)
        tech_names_male = [
            "elon", "jeff", "bill", "steve", "tim", "satya", "sundar", "jensen", "marc",
            "reid", "peter", "sam", "brian", "travis", "drew", "jack", "evan", "kevin",
            "logan", "alex", "eric", "paul", "mark", "larry", "sergey", "palmer", "jared"
        ]
        
        tech_names_female = [
            "sheryl", "meg", "ginni", "safra", "ruth", "susan", "diane", "marissa",
            "julia", "melinda", "whitney", "aileen", "ann", "reshma", "kiran", "padmasree"
        ]
        
        # Most common surnames (global coverage)
        common_last_names = [
            "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis",
            "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson",
            "thomas", "taylor", "moore", "jackson", "martin", "lee", "perez", "thompson",
            "white", "harris", "sanchez", "clark", "ramirez", "lewis", "robinson", "walker",
            "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill", "flores",
            "green", "adams", "nelson", "baker", "hall", "rivera", "campbell", "mitchell",
            "carter", "roberts", "gomez", "phillips", "evans", "turner", "diaz", "parker",
            "cruz", "edwards", "collins", "reyes", "stewart", "morris", "morales", "murphy",
            "cook", "rogers", "gutierrez", "ortiz", "morgan", "cooper", "peterson", "bailey",
            "reed", "kelly", "howard", "ramos", "kim", "cox", "ward", "richardson", "watson",
            "brooks", "chavez", "wood", "james", "bennett", "gray", "mendoza", "ruiz", "hughes",
            "price", "alvarez", "castillo", "sanders", "patel", "myers", "long", "ross", "foster",
            "jimenez", "powell", "jenkins", "perry", "russell", "sullivan", "bell", "coleman",
            "butler", "henderson", "barnes", "gonzales", "fisher", "vasquez", "simmons", "romero",
            "jordan", "patterson", "alexander", "hamilton", "graham", "reynolds", "griffin", "wallace"
        ]
        
        # Tech industry surnames (higher weight)
        tech_surnames = [
            "musk", "bezos", "gates", "jobs", "cook", "nadella", "pichai", "huang", "zuckerberg",
            "page", "brin", "dorsey", "kalanick", "chesky", "spiegel", "systrom", "krieger",
            "altman", "wojcicki", "sandberg", "whitman", "thiel", "hoffman", "andreessen",
            "horowitz", "sacca", "calacanis", "rose", "ohanian", "graham", "livingston"
        ]
        
        # Add names with appropriate weights
        weight = self.source_weights['manual_curated']
        
        for name in common_first_names_male + common_first_names_female:
            self.first_names[name] += weight
        
        for name in tech_names_male + tech_names_female:
            self.first_names[name] += weight * 1.5  # Higher weight for tech names
            
        for name in common_last_names:
            self.last_names[name] += weight
            
        for name in tech_surnames:
            self.last_names[name] += weight * 2.0  # Much higher weight for tech surnames
        
        self.build_stats['manual_first_names'] = len(common_first_names_male + common_first_names_female + tech_names_male + tech_names_female)
        self.build_stats['manual_last_names'] = len(common_last_names + tech_surnames)
        
        logger.info(f"    Added {self.build_stats['manual_first_names']} first names")
        logger.info(f"    Added {self.build_stats['manual_last_names']} last names")
    
    def _add_government_data(self):
        """Add government and official data sources."""
        logger.info("  🏛️ Adding government data sources...")
        
        # US Census most popular names (if we can access)
        # For now, add known government agencies
        government_agencies = [
            "Securities and Exchange Commission", "SEC", "Food and Drug Administration", "FDA",
            "Environmental Protection Agency", "EPA", "Federal Trade Commission", "FTC",
            "Federal Communications Commission", "FCC", "Department of Justice", "DOJ",
            "Internal Revenue Service", "IRS", "National Security Agency", "NSA",
            "Federal Bureau of Investigation", "FBI", "Central Intelligence Agency", "CIA",
            "Department of Defense", "DOD", "Pentagon", "NASA", "NOAA", "CDC", "NIH", "NSF",
            "Department of Energy", "DOE", "Department of Agriculture", "USDA"
        ]
        
        weight = self.source_weights['government_data']
        for agency in government_agencies:
            self.organizations[agency] += weight
        
        self.build_stats['government_orgs'] = len(government_agencies)
        logger.info(f"    Added {self.build_stats['government_orgs']} government agencies")
    
    def _add_university_rankings(self):
        """Add top universities from global rankings."""
        logger.info("  🎓 Adding top universities...")
        
        top_universities = [
            "Harvard University", "Harvard", "Stanford University", "Stanford",
            "Massachusetts Institute of Technology", "MIT", "University of Cambridge", "Cambridge",
            "University of Oxford", "Oxford", "Yale University", "Yale", "Princeton University", "Princeton",
            "Columbia University", "Columbia", "University of Pennsylvania", "UPenn", "Cornell University", "Cornell",
            "Dartmouth College", "Dartmouth", "Brown University", "Brown", "Duke University", "Duke",
            "Northwestern University", "Northwestern", "University of Chicago", "UChicago",
            "California Institute of Technology", "Caltech", "Carnegie Mellon University", "CMU",
            "University of California Berkeley", "UC Berkeley", "Berkeley", "UCLA", "University of Southern California", "USC",
            "Georgia Institute of Technology", "Georgia Tech", "University of Washington", "UW",
            "University of Texas at Austin", "UT Austin", "University of Michigan", "UMich",
            "University of Illinois", "UIUC", "Purdue University", "Purdue", "Imperial College London", "Imperial",
            "ETH Zurich", "EPFL", "Tsinghua University", "Tsinghua", "Peking University", "Peking",
            "National University of Singapore", "NUS", "Nanyang Technological University", "NTU"
        ]
        
        weight = self.source_weights['academic_verified']
        for university in top_universities:
            self.organizations[university] += weight
        
        self.build_stats['universities'] = len(set(top_universities))  # Remove duplicates for count
        logger.info(f"    Added {self.build_stats['universities']} top universities")
    
    def _process_available_ner_datasets(self):
        """Process NER datasets if libraries are available."""
        logger.info("  🔬 Processing NER datasets...")
        
        try:
            # Try to import datasets library
            from datasets import load_dataset
            logger.info("    📚 datasets library available - processing CoNLL-2003...")
            self._process_conll2003_dataset()
        except ImportError:
            logger.info("    ⚠️ datasets library not available - skipping NER datasets")
            logger.info("    💡 Install with: pip install datasets transformers")
    
    def _process_conll2003_dataset(self):
        """Process CoNLL-2003 dataset for high-quality person/org names."""
        try:
            from datasets import load_dataset
            
            logger.info("    📊 Loading CoNLL-2003 dataset...")
            dataset = load_dataset("eriktks/conll2003")
            
            person_count = 0
            org_count = 0
            weight = self.source_weights['ner_datasets']
            
            # Process train split only for speed
            for example in dataset['train']:
                tokens = example['tokens']
                ner_tags = example['ner_tags']
                
                current_entity = []
                current_type = None
                
                for token, tag in zip(tokens, ner_tags):
                    if tag in [1, 2]:  # B-PER, I-PER
                        if tag == 1 and current_entity:  # New entity starting
                            self._process_ner_entity(current_entity, current_type, weight)
                            current_entity = [token]
                        else:
                            current_entity.append(token)
                        current_type = 'PER'
                    elif tag in [3, 4]:  # B-ORG, I-ORG
                        if tag == 3 and current_entity:  # New entity starting
                            self._process_ner_entity(current_entity, current_type, weight)
                            current_entity = [token]
                        else:
                            current_entity.append(token)
                        current_type = 'ORG'
                    else:
                        if current_entity:
                            self._process_ner_entity(current_entity, current_type, weight)
                            current_entity = []
                            current_type = None
                
                # Process final entity
                if current_entity:
                    self._process_ner_entity(current_entity, current_type, weight)
            
            logger.info(f"    ✅ Processed CoNLL-2003: {self.build_stats['conll_persons']} persons, {self.build_stats['conll_orgs']} orgs")
            
        except Exception as e:
            logger.error(f"    ❌ Error processing CoNLL-2003: {e}")
    
    def _process_ner_entity(self, entity_tokens: List[str], entity_type: str, weight: float):
        """Process an entity from NER dataset."""
        if not entity_tokens or not entity_type:
            return
        
        full_name = ' '.join(entity_tokens).strip()
        full_name = self._clean_entity_name(full_name)
        
        if not full_name or len(full_name) < 2:
            return
        
        if entity_type == 'PER':
            self._process_person_name_ner(full_name, weight)
            self.build_stats['conll_persons'] = self.build_stats.get('conll_persons', 0) + 1
        elif entity_type == 'ORG':
            self.organizations[full_name] += weight
            self.build_stats['conll_orgs'] = self.build_stats.get('conll_orgs', 0) + 1
    
    def _process_person_name_ner(self, full_name: str, weight: float):
        """Process person name from NER and extract components."""
        name_parts = full_name.split()
        
        if len(name_parts) >= 1:
            first_name = name_parts[0].lower()
            if self._is_valid_name_component(first_name):
                self.first_names[first_name] += weight
        
        if len(name_parts) >= 2:
            last_name = name_parts[-1].lower()
            if self._is_valid_name_component(last_name):
                self.last_names[last_name] += weight
    
    def _clean_entity_name(self, name: str) -> str:
        """Clean extracted entity name."""
        name = name.strip('.,;:!?()[]{}"\'-')
        name = ' '.join(name.split())
        
        # Filter out obvious non-names
        if any(char.isdigit() for char in name):
            return ""
        if len(name.split()) > 5:
            return ""
        
        return name
    
    def _is_valid_name_component(self, name: str) -> bool:
        """Check if name component is valid."""
        if len(name) < 2 or len(name) > 25:
            return False
        if not name.replace('-', '').replace("'", '').isalpha():
            return False
        if name.lower() in ['the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'inc', 'corp', 'ltd']:
            return False
        return True
    
    def _add_verified_web_sources(self):
        """Add entities from verified web sources and APIs."""
        logger.info("  🌐 Adding verified web sources...")
        
        # For now, add known high-value entities
        # In production, this would call APIs like Crunchbase, etc.
        
        additional_startups = [
            "Stripe", "Shopify", "Square", "Block", "Plaid", "Brex", "Ramp", "Mercury",
            "Chime", "SoFi", "Affirm", "Klarna", "Afterpay", "NuBank", "Revolut",
            "Monzo", "N26", "Wise", "Remitly", "Robinhood", "Coinbase", "Kraken",
            "FTX", "Binance", "Chainalysis", "ConsenSys", "OpenSea", "Uniswap",
            "Compound", "Aave", "MakerDAO", "Chainlink", "Polygon", "Solana"
        ]
        
        ai_companies = [
            "OpenAI", "Anthropic", "DeepMind", "Stability AI", "Midjourney", "Runway",
            "Character AI", "Jasper", "Copy.ai", "Grammarly", "Notion", "Otter.ai",
            "Hugging Face", "Weights & Biases", "Scale AI", "Labelbox", "Snorkel AI",
            "DataRobot", "H2O.ai", "Databricks", "Snowflake", "Palantir", "C3.ai"
        ]
        
        weight = self.source_weights['web_verified']
        for company in additional_startups + ai_companies:
            self.organizations[company] += weight
        
        self.build_stats['web_verified_orgs'] = len(additional_startups + ai_companies)
        logger.info(f"    Added {self.build_stats['web_verified_orgs']} verified organizations")
    
    def _rank_and_filter_to_100k(self) -> Dict[str, List[str]]:
        """Rank entities by score and filter to top 100K each."""
        logger.info("  🎯 Ranking and filtering to 100K each...")
        
        # Get top 100K of each category
        top_first_names = [name for name, score in self.first_names.most_common(100000)]
        top_last_names = [name for name, score in self.last_names.most_common(100000)]
        top_organizations = [org for org, score in self.organizations.most_common(100000)]
        
        logger.info(f"    Selected top 100K first names from {len(self.first_names)} candidates")
        logger.info(f"    Selected top 100K last names from {len(self.last_names)} candidates")
        logger.info(f"    Selected top 100K organizations from {len(self.organizations)} candidates")
        
        return {
            'first_names': top_first_names,
            'last_names': top_last_names,
            'organizations': top_organizations
        }
    
    def _save_foundation_corpus(self, corpus: Dict[str, List[str]]):
        """Save the foundation corpus to files."""
        logger.info("  💾 Saving foundation corpus...")
        
        # Save individual text files
        for category, entities in corpus.items():
            output_file = self.output_dir / f"{category}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                for entity in entities:
                    f.write(f"{entity}\n")
            logger.info(f"    Saved {len(entities):,} {category} to {output_file}")
        
        # Save combined JSON with metadata
        json_output = self.output_dir / "foundation_corpus.json"
        corpus_data = {
            'corpus': corpus,
            'stats': dict(self.build_stats),
            'total_entities': sum(len(entities) for entities in corpus.values()),
            'memory_estimate_mb': self._estimate_memory_usage(corpus),
            'build_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(corpus_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"    Saved complete corpus metadata to {json_output}")
    
    def _estimate_memory_usage(self, corpus: Dict[str, List[str]]) -> float:
        """Estimate memory usage in MB."""
        total_chars = 0
        for entities in corpus.values():
            total_chars += sum(len(entity) for entity in entities)
        
        # String storage + Aho-Corasick overhead
        string_memory = total_chars / 1024 / 1024  # MB
        aho_corasick_memory = len(corpus) * 8  # ~8MB per automaton estimate
        
        return string_memory + aho_corasick_memory
    
    def _validate_corpus_quality(self, corpus: Dict[str, List[str]]):
        """Validate the quality of the built corpus."""
        logger.info("  ✅ Validating corpus quality...")
        
        # Check for expected entities
        expected_first_names = ['john', 'mary', 'james', 'sarah', 'michael', 'elon', 'tim']
        expected_orgs = ['Apple', 'Google', 'Microsoft', 'Sequoia Capital', 'Y Combinator']
        
        first_names_found = sum(1 for name in expected_first_names if name in corpus['first_names'])
        orgs_found = sum(1 for org in expected_orgs if org in corpus['organizations'])
        
        logger.info(f"    Quality check - Expected first names found: {first_names_found}/{len(expected_first_names)}")
        logger.info(f"    Quality check - Expected organizations found: {orgs_found}/{len(expected_orgs)}")
        
        # Memory validation
        estimated_memory = self._estimate_memory_usage(corpus)
        logger.info(f"    Estimated memory usage: {estimated_memory:.1f}MB")
        
        if estimated_memory > 1000:  # 1GB
            logger.warning(f"    ⚠️ Memory usage exceeds 1GB limit!")
        else:
            logger.info(f"    ✅ Memory usage within 1GB limit")

def main():
    """Main function to build foundation corpus."""
    print("🚀 Foundation Corpus Builder - 100K/100K/100K Strategy")
    print("=" * 60)
    
    builder = FoundationCorpusBuilder()
    corpus = builder.build_foundation_corpus()
    
    print(f"\n✅ Foundation corpus completed!")
    print(f"   📊 First Names: {len(corpus['first_names']):,}")
    print(f"   📊 Last Names: {len(corpus['last_names']):,}")
    print(f"   📊 Organizations: {len(corpus['organizations']):,}")
    print(f"   📊 Total Entities: {sum(len(entities) for entities in corpus.values()):,}")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Test integration with EntityDisambiguator")
    print(f"   2. Benchmark performance and memory usage")
    print(f"   3. Build domain-specific vocabularies")
    
    return corpus

if __name__ == "__main__":
    main()