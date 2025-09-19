#!/usr/bin/env python3
"""
Entity-Specific Normalizers
===========================

Future home for specialized entity normalization modules:
- person_normalizer.py: Person name canonicalization, title extraction
- org_normalizer.py: Organization name variants, acronym expansion
- location_normalizer.py: Address standardization, geocoding
- date_normalizer.py: Date/time format standardization
- currency_normalizer.py: Real-time exchange rate integration

Each normalizer follows the established pattern:
1. Load configuration from YAML
2. Extract entities with span information
3. Apply normalization to canonical forms
4. Return structured schema: original + normalized data
"""

# Future imports will be added here as normalizers are implemented
# from .person_normalizer import PersonNormalizer
# from .org_normalizer import OrganizationNormalizer
# from .location_normalizer import LocationNormalizer

__all__ = [
    # Will be populated as normalizers are added
]