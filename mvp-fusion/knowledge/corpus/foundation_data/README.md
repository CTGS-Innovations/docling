# Foundation Data Directory

## Overview
This directory contains reference datasets used by MVP-Fusion's entity extraction and validation systems. The data is organized using a **versioned files + symlinks** pattern for flexibility and maintainability.

## File Structure Pattern

### Versioned Data Files
- `countries_2025_09_18.txt` - Country names (dated version)
- `us_states_2025_09_18.txt` - US state names (dated version)  
- `major_cities_2025_09_18.txt` - Major world cities (dated version)
- `unicorn_companies_2025_09_18.txt` - High-value startup companies (dated version)
- `investors_2025_09_18.txt` - Investment firms and VCs (dated version)
- `organizations_2025_09_18.txt` - General organizations (dated version)
- `first_names_2025_09_18.txt` - Common first names (dated version)
- `last_names_2025_09_18.txt` - Common last names (dated version)
- `us_government_agencies_2025_09_18.txt` - US government agencies (dated version)

### Active Symlinks (Used by Code)
- `countries.txt` → `countries_2025_09_18.txt`
- `us_states.txt` → `us_states_2025_09_18.txt`
- `major_cities.txt` → `major_cities_2025_09_18.txt`
- `unicorn_companies.txt` → `unicorn_companies_2025_09_18.txt`
- `investors.txt` → `investors_2025_09_18.txt`

## Why This Pattern?

### Benefits
1. **Version Control**: Keep multiple versions of datasets with clear dates
2. **Code Stability**: Application code always imports consistent filenames
3. **Easy Switching**: Change active dataset by updating one symlink
4. **Historical Tracking**: Maintain audit trail of data updates
5. **Testing**: Switch to test datasets without code changes

### Usage Examples

#### Switch to Different Dataset Version
```bash
# If you get a new countries list
ln -sf countries_2025_12_01.txt countries.txt
```

#### Add Test Dataset
```bash
# Create test dataset
ln -sf countries_test_small.txt countries.txt
# Run tests
# Switch back
ln -sf countries_2025_09_18.txt countries.txt
```

#### Update Single Dataset
```bash
# Add new unicorn companies file
cp new_unicorns.txt unicorn_companies_2025_12_15.txt
ln -sf unicorn_companies_2025_12_15.txt unicorn_companies.txt
```

## File Format
All files are plain text with one entry per line:
```
Texas
California
New York
...
```

## Used By
- `knowledge/corpus/geographic_data.py` - Main reference data loader
- `knowledge/extractors/comprehensive_entity_extractor.py` - Entity validation
- Entity enrichment and classification pipelines

## Maintenance
- **Adding new data**: Create dated file, update symlink
- **Testing**: Temporarily point symlinks to test files
- **Rollback**: Simply revert symlink to previous version
- **Cleanup**: Remove old dated files when no longer needed

## Current Active Versions
- Countries: 2025-09-18 (198 countries)
- US States: 2025-09-18 (50 states)
- Major Cities: 2025-09-18 (995 cities)
- Unicorn Companies: 2025-09-18 (1,183 companies)
- Investors: 2025-09-18 (1,324 firms)