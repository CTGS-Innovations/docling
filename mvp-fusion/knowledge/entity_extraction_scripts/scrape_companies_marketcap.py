#!/usr/bin/env python3
"""
Scrape comprehensive company data from companiesmarketcap.com
Extract: Rank, Name, Market Cap, Price, Country for all categories
"""

import os
import time
import csv
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

class CompanyMarketCapScraper:
    def __init__(self):
        self.base_url = "https://companiesmarketcap.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory
        self.output_dir = "data/companies_marketcap"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_all_categories(self):
        """Scrape all available categories from the main page"""
        print("🔍 Scraping all categories...")
        
        try:
            response = self.session.get(f"{self.base_url}/all-categories/")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            categories = []
            
            # Look for category links
            # Categories are typically in a list or grid format
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and ('largest-' in href or '/category/' in href or href.count('/') == 2):
                    category_url = urljoin(self.base_url, href)
                    category_name = link.get_text(strip=True)
                    
                    if category_name and len(category_name) > 3:
                        categories.append({
                            'name': category_name,
                            'url': category_url,
                            'slug': href.strip('/')
                        })
            
            # Remove duplicates
            seen_urls = set()
            unique_categories = []
            for cat in categories:
                if cat['url'] not in seen_urls:
                    seen_urls.add(cat['url'])
                    unique_categories.append(cat)
            
            print(f"✅ Found {len(unique_categories)} categories")
            return unique_categories
            
        except Exception as e:
            print(f"❌ Error scraping categories: {e}")
            return []
    
    def extract_company_data(self, row):
        """Extract company data from a table row"""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 7:  # Need at least 7 columns based on observed format
                return None
            
            # Based on observed format:
            # Column 0: Empty (icons/logos)
            # Column 1: Rank
            # Column 2: Company name + ticker
            # Column 3: Market cap
            # Column 4: Price  
            # Column 5: Change percentage
            # Column 6: Empty
            # Column 7: Country
            
            company_data = {}
            
            # Rank (column 1)
            rank_text = cells[1].get_text(strip=True)
            try:
                company_data['rank'] = int(rank_text) if rank_text.isdigit() else None
            except:
                company_data['rank'] = None
            
            # Company name (column 2) - clean ticker symbol
            name_text = cells[2].get_text(strip=True)
            # Remove ticker symbols (usually all caps at the end)
            # Pattern: Remove anything that looks like a ticker (e.g., "DSY.PA", "MPWR", "6701.T")
            clean_name = re.sub(r'[A-Z0-9]+\.[A-Z]+$', '', name_text)  # Remove exchange tickers like DSY.PA, 6701.T
            clean_name = re.sub(r'[A-Z]{2,6}$', '', clean_name)  # Remove simple tickers like MPWR
            company_data['name'] = clean_name.strip()
            
            # Market cap (column 3)
            market_cap_text = cells[3].get_text(strip=True)
            if '$' in market_cap_text:
                company_data['market_cap'] = market_cap_text
            else:
                company_data['market_cap'] = None
            
            # Price (column 4)
            price_text = cells[4].get_text(strip=True)
            if '$' in price_text:
                company_data['price'] = price_text
            else:
                company_data['price'] = None
            
            # Country (column 7)
            if len(cells) >= 8:
                country_text = cells[7].get_text(strip=True)
                company_data['country'] = country_text if country_text else None
            else:
                company_data['country'] = None
            
            # Validate we have essential data
            if (company_data.get('name') and 
                len(company_data['name']) > 2 and 
                company_data.get('rank') is not None):
                return company_data
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting company data: {e}")
            return None
    
    def scrape_category_companies(self, category_url, category_name, max_pages=10):
        """Scrape companies from a specific category with pagination"""
        print(f"\n📊 Scraping {category_name}...")
        
        companies = []
        page = 1
        
        while page <= max_pages:
            try:
                # Construct page URL based on pagination pattern
                if page == 1:
                    # For page 1, try the base URL first
                    page_url = category_url
                else:
                    # For pages 2+, add ?page=N
                    if '?' in category_url:
                        page_url = f"{category_url}&page={page}"
                    else:
                        page_url = f"{category_url}?page={page}"
                
                print(f"  📄 Scraping page {page}: {page_url}")
                
                response = self.session.get(page_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for company tables
                tables = soup.find_all('table')
                page_companies = []
                
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header row
                        company_data = self.extract_company_data(row)
                        if company_data:
                            company_data['category'] = category_name
                            page_companies.append(company_data)
                
                if not page_companies:
                    print(f"    ❌ No companies found on page {page} - stopping pagination")
                    break
                
                companies.extend(page_companies)
                print(f"    ✅ Found {len(page_companies)} companies on page {page}")
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"    ❌ Error on page {page}: {e}")
                break
        
        print(f"✅ {category_name}: {len(companies)} companies total")
        return companies
    
    def save_companies(self, all_companies, filename_prefix="companies_marketcap"):
        """Save companies organized by category"""
        
        # Organize companies by category
        companies_by_category = {}
        for company in all_companies:
            category = company.get('category', 'Unknown')
            if category not in companies_by_category:
                companies_by_category[category] = []
            companies_by_category[category].append(company)
        
        # Save complete dataset
        json_file = f"{self.output_dir}/{filename_prefix}_complete.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(companies_by_category, f, indent=2, ensure_ascii=False)
        
        # Save CSV with all data
        csv_file = f"{self.output_dir}/{filename_prefix}_complete.csv"
        if all_companies:
            fieldnames = ['rank', 'name', 'market_cap', 'price', 'country', 'category']
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for company in all_companies:
                    writer.writerow(company)
        
        # Save separate files by category for entity corpus
        category_dir = f"{self.output_dir}/by_category"
        os.makedirs(category_dir, exist_ok=True)
        
        for category, companies in companies_by_category.items():
            # Clean category name for filename
            safe_category = re.sub(r'[^\w\-_]', '_', category.lower().replace(' ', '_'))
            
            # Save category-specific JSON
            cat_json = f"{category_dir}/{safe_category}.json"
            with open(cat_json, 'w', encoding='utf-8') as f:
                json.dump({
                    'category': category,
                    'count': len(companies),
                    'companies': companies
                }, f, indent=2, ensure_ascii=False)
            
            # Save category-specific company names (for entity corpus)
            cat_names = f"{category_dir}/{safe_category}_names.txt"
            with open(cat_names, 'w', encoding='utf-8') as f:
                for company in companies:
                    if company.get('name'):
                        f.write(company['name'] + '\n')
        
        # Save all company names (for entity corpus)
        all_names_file = f"{self.output_dir}/{filename_prefix}_all_names.txt"
        with open(all_names_file, 'w', encoding='utf-8') as f:
            for company in all_companies:
                if company.get('name'):
                    f.write(company['name'] + '\n')
        
        print(f"💾 Saved to:")
        print(f"  📋 Complete JSON: {json_file}")
        print(f"  📊 Complete CSV: {csv_file}")
        print(f"  📁 By category: {category_dir}/ ({len(companies_by_category)} categories)")
        print(f"  📝 All names: {all_names_file}")
        
        return companies_by_category
    
    def run_full_scrape(self, max_categories=20, max_pages_per_category=5):
        """Run full scraping process"""
        print("🚀 STARTING COMPREHENSIVE COMPANY SCRAPING")
        print(f"Max categories: {max_categories}, Max pages per category: {max_pages_per_category}")
        print("=" * 60)
        
        # Get all categories
        categories = self.get_all_categories()
        
        if not categories:
            print("❌ No categories found")
            return
        
        # Limit categories for testing
        if len(categories) > max_categories:
            categories = categories[:max_categories]
            print(f"📊 Limited to first {max_categories} categories for testing")
        
        all_companies = []
        
        for i, category in enumerate(categories, 1):
            try:
                print(f"\n[{i}/{len(categories)}] {category['name']}")
                
                companies = self.scrape_category_companies(
                    category['url'], 
                    category['name'], 
                    max_pages_per_category
                )
                
                all_companies.extend(companies)
                
                # Save intermediate results
                if len(all_companies) % 500 == 0:
                    self.save_companies(all_companies, f"companies_partial_{len(all_companies)}")
                
                time.sleep(2)  # Rate limiting between categories
                
            except Exception as e:
                print(f"❌ Error processing {category['name']}: {e}")
                continue
        
        # Final save
        print(f"\n🎉 SCRAPING COMPLETE!")
        print(f"📊 Total companies scraped: {len(all_companies)}")
        
        if all_companies:
            self.save_companies(all_companies, "companies_marketcap_final")
            
            # Show category breakdown
            categories_count = {}
            for company in all_companies:
                cat = company.get('category', 'Unknown')
                categories_count[cat] = categories_count.get(cat, 0) + 1
            
            print(f"\n📊 BREAKDOWN BY CATEGORY:")
            for cat, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count} companies")
        
        return all_companies

def main():
    scraper = CompanyMarketCapScraper()
    
    # Test with limited scope first
    companies = scraper.run_full_scrape(max_categories=5, max_pages_per_category=3)
    
    if len(companies) > 100:
        print(f"\n✅ SUCCESS! Scraped {len(companies)} companies")
        print(f"🚀 Ready to scale up to full scraping")
    else:
        print(f"\n🔧 Need to debug scraping logic")

if __name__ == "__main__":
    main()