# GPE Taxonomy (2025_09_22)

This directory contains geopolitical entities for NER/NPE extraction. These lists focus on sovereign states, governments, political organizations, and administrative entities that have governing authority or political significance.

Categories and guidance:
- countries: sovereign nations and states
- major_cities: cities with significant political/administrative importance
- us_states: United States federal states and territories
- us_government_agencies: federal agencies, departments, and bureaus
- major_city_governments: city government references and administrative entities
- state_governments: state-level government references
- federal_provincial_governments: federal and provincial government entities
- government_forms: various forms of government references
- sovereign_entities_official_names: official names and formal designations
- regional_political_entities: political regions and administrative divisions
- regional_and_geopolitical_blocs: political alliances and regional organizations
- international_organizations: multinational political and governmental bodies
- collective_forms: collective political entity references
- demonyms_individuals: nationality and citizenship identifiers
- language_linked_identities: language-based political/cultural identities

NER mapping:
- Map these to GPE; reserve LOC for physical geographic features. When a name is ambiguous (e.g., "Congo"), prefer GPE if the context is governmental/political, otherwise use LOC for physical geographic references.
- Focus on entities with governing authority, political sovereignty, or administrative function
- Include both formal names and common colloquial references

File naming: <slug>_2025_09_22.txt