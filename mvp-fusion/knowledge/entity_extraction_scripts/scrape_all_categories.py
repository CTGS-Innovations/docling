#!/usr/bin/env python3
"""
Scrape all categories from urllist.txt with pagination
Extract companies from pages 1-2 of each category, organizing by domain
"""

import os
import time
import csv
import json
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

class ComprehensiveCategoryMarketCapScraper:
    def __init__(self):
        self.base_url = "https://companiesmarketcap.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory
        self.output_dir = "data/companies_all_categories"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/by_category", exist_ok=True)
    
    def extract_category_name_from_url(self, url):
        """Extract clean category name from URL"""
        try:
            # Parse URL path
            path = urlparse(url).path
            # Get the category part (first directory)
            category_slug = path.split('/')[1] if path.split('/') else 'unknown'
            
            # Convert to readable name
            category_name = category_slug.replace('-', ' ').title()
            
            return category_name, category_slug
        except:
            return "Unknown Category", "unknown"
    
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
    
    def scrape_category_pages(self, category_url, category_name, max_pages=2):
        """Scrape companies from a specific category with pagination"""
        print(f"\n📊 Scraping {category_name}...")
        
        companies = []
        page = 1
        
        while page <= max_pages:
            try:
                # Construct page URL based on pagination pattern
                if page == 1:
                    # For page 1, use the base URL
                    page_url = category_url
                else:
                    # For pages 2+, add ?page=N
                    page_url = f"{category_url}?page={page}"
                
                print(f"  📄 Page {page}: {page_url}")
                
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
                    print(f"    ❌ No companies found on page {page} - stopping")
                    break
                
                companies.extend(page_companies)
                print(f"    ✅ Found {len(page_companies)} companies")
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"    ❌ Error on page {page}: {e}")
                break
        
        print(f"✅ {category_name}: {len(companies)} total companies")
        return companies
    
    def load_category_urls(self, filename="urllist.txt"):
        """Load category URLs from file"""
        try:
            with open(filename, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            print(f"📋 Loaded {len(urls)} category URLs")
            return urls
        except Exception as e:
            print(f"❌ Error loading URLs: {e}")
            return []
    
    def save_category_data(self, category_name, category_slug, companies):
        """Save data for a single category"""
        if not companies:
            return
        
        # Save category-specific JSON
        cat_json = f"{self.output_dir}/by_category/{category_slug}.json"
        with open(cat_json, 'w', encoding='utf-8') as f:
            json.dump({
                'category': category_name,
                'slug': category_slug,
                'count': len(companies),
                'companies': companies
            }, f, indent=2, ensure_ascii=False)
        
        # Save category-specific CSV
        cat_csv = f"{self.output_dir}/by_category/{category_slug}.csv"
        fieldnames = ['rank', 'name', 'market_cap', 'price', 'country', 'category']
        with open(cat_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for company in companies:
                writer.writerow(company)
        
        # Save company names only (for entity corpus)
        cat_names = f"{self.output_dir}/by_category/{category_slug}_names.txt"
        with open(cat_names, 'w', encoding='utf-8') as f:
            for company in companies:
                if company.get('name'):
                    f.write(company['name'] + '\n')
    
    def run_comprehensive_scraping(self):
        """Run scraping for all categories in urllist.txt"""
        print("🚀 STARTING COMPREHENSIVE CATEGORY SCRAPING")
        print("Pages per category: 1-2")
        print("=" * 80)
        
        # Load URLs
        urls = self.load_category_urls()
        if not urls:
            print("❌ No URLs to process")
            return
        
        all_companies = []
        category_summary = {}
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"\n[{i}/{len(urls)}] Processing: {url}")
                
                # Extract category info
                category_name, category_slug = self.extract_category_name_from_url(url)
                
                # Scrape companies
                companies = self.scrape_category_pages(url, category_name, max_pages=2)
                
                if companies:
                    # Save category data
                    self.save_category_data(category_name, category_slug, companies)
                    
                    # Add to master list
                    all_companies.extend(companies)
                    category_summary[category_name] = len(companies)
                    
                    print(f"💾 Saved {len(companies)} companies for {category_name}")
                else:
                    print(f"❌ No companies found for {category_name}")
                
                # Rate limiting between categories
                time.sleep(2)
                
                # Save intermediate results every 10 categories
                if i % 10 == 0:
                    self.save_master_results(all_companies, category_summary, f"intermediate_{i}")
                
            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                continue
        
        # Final save
        print(f"\n🎉 SCRAPING COMPLETE!")
        print(f"📊 Total companies scraped: {len(all_companies)}")
        print(f"📁 Categories processed: {len(category_summary)}")
        
        if all_companies:
            self.save_master_results(all_companies, category_summary, "final")
            
            # Show top categories by company count
            print(f"\n📊 TOP CATEGORIES BY COMPANY COUNT:")
            top_categories = sorted(category_summary.items(), key=lambda x: x[1], reverse=True)[:10]
            for cat, count in top_categories:
                print(f"  {cat}: {count} companies")
        
        return all_companies, category_summary
    
    def save_master_results(self, all_companies, category_summary, suffix=""):
        """Save master results files"""
        
        # Save complete dataset JSON
        json_file = f"{self.output_dir}/companies_all_categories_{suffix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_companies': len(all_companies),
                'categories_processed': len(category_summary),
                'category_summary': category_summary,
                'companies': all_companies
            }, f, indent=2, ensure_ascii=False)
        
        # Save complete CSV
        csv_file = f"{self.output_dir}/companies_all_categories_{suffix}.csv"
        if all_companies:
            fieldnames = ['rank', 'name', 'market_cap', 'price', 'country', 'category']
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for company in all_companies:
                    writer.writerow(company)
        
        # Save all company names (for entity corpus)
        names_file = f"{self.output_dir}/all_company_names_{suffix}.txt"
        with open(names_file, 'w', encoding='utf-8') as f:
            for company in all_companies:
                if company.get('name'):
                    f.write(company['name'] + '\n')
        
        print(f"💾 Saved master files:")
        print(f"  📋 JSON: {json_file}")
        print(f"  📊 CSV: {csv_file}")
        print(f"  📝 Names: {names_file}")

def main():
    scraper = ComprehensiveCategoryMarketCapScraper()
    
    # Run comprehensive scraping
    companies, summary = scraper.run_comprehensive_scraping()
    
    if companies:
        print(f"\n✅ SUCCESS! Scraped {len(companies)} companies across {len(summary)} categories")
        print(f"🚀 Data ready for entity corpus integration")
    else:
        print(f"\n❌ FAILED! No companies scraped")

if __name__ == "__main__":
    main()