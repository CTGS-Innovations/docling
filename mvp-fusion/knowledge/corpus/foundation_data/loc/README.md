# LOC Taxonomy (2025_09_22)

This directory contains non-political location categories for NER/NPE extraction. These lists avoid sovereign/political entities covered by GPE and focus on physical and geographic features plus settlement names.

Categories and guidance:
- continents: 7 standard continents
- oceans: 5 oceans
- seas_and_gulfs: major seas, gulfs, large bays
- lakes: large lakes/reservoirs (incl. endorheic seas)
- rivers: major world rivers
- mountain_ranges: named ranges
- mountains_peaks: notable peaks
- deserts: major deserts
- islands_archipelagos: significant islands and island groups
- peninsulas: major peninsulas
- bays_straits_channels: bays, straits, channels
- forests: notable forests/biomes
- valleys_canyons: named valleys and canyon systems
- plateaus_plains: plateaus, plains, steppes
- parks_protected_areas: globally known protected areas
- geographic_regions: non-political macroregions (colloquial/historical)
- urban_settlements: cities/towns (seeded from major cities list)

NER mapping:
- Map these to LOC; reserve GPE for governments, countries, states, and city governments. When a name is ambiguous (e.g., "Congo"), prefer the GPE list if the context is governmental/political, otherwise LOC.

File naming: <slug>_2025_09_22.txt
