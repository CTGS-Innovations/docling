---
conversion:
  engine: mvp-fusion-highspeed
  page_count: 1
  conversion_time_ms: 0.12706895358860493
  source_file: range_test_input.txt
  format: TXT
content_analysis:
  has_text_content: true
  has_tables: false
  has_images: false
  has_formulas: false
  has_code: false
  has_links: false
  has_lists: true
  has_headers: false
  has_footnotes: false
  has_citations: false
  has_structured_data: false
processing: {stage: completed, content_length: 311}
domain_classification:
  routing: {skip_entity_extraction: false, enable_deep_domain_extraction: false, domain_specialization_route: general}
  top_domains: [data_science_ai, private_equity, safety_compliance, planning_scheduling, quality_control]
  top_document_types: [regulation, clinical_research, corrective_action, product_review, design_specification]
  domains:
    data_science_ai: 15.3
    private_equity: 11.2
    safety_compliance: 10.0
    planning_scheduling: 7.6
    quality_control: 7.6
    customer_success: 6.5
    api_integration: 6.5
    hr_tech: 6.5
    customer_experience: 6.5
    compliance: 5.6
    specialties: 5.6
    alternative_funding: 5.5
    feature_comparison: 5.5
  document_types:
    regulation: 18.3
    clinical_research: 16.5
    corrective_action: 12.8
    product_review: 11.5
    design_specification: 9.2
    customer_feedback: 9.2
    production_schedule: 9.2
    engineering_drawing: 9.2
    forum_discussion: 4.1
raw_entities:
  person: []
  org: []
  gpe:
  - value: dra
    text: dra
    type: GPE
    span: {start: 27, end: 30}
    metadata: {subcategory: us_government_agencies}
  location: []
  date: []
  time: []
  money: []
  measurement:
  - value: -37 inches
    text: -37 inches
    type: MEASUREMENT_LENGTH
    span: {start: 0, end: 10}
  - value: -94 cm
    text: -94 cm
    type: MEASUREMENT_LENGTH
    span: {start: 0, end: 6}
  - value: ' 10 feet'
    text: ' 10 feet'
    type: MEASUREMENT_LENGTH
    span: {start: 0, end: 8}
  - value: -30 mi
    text: -30 mi
    type: MEASUREMENT_LENGTH
    span: {start: 0, end: 6}
  - value: ' 75 pounds'
    text: ' 75 pounds'
    type: MEASUREMENT_WEIGHT
    span: {start: 0, end: 10}
  - value: -30 minutes
    text: -30 minutes
    type: MEASUREMENT_TIME
    span: {start: 0, end: 11}
  - value: ' -20°F'
    text: ' -20°F'
    type: MEASUREMENT_TEMPERATURE
    span: {start: 0, end: 6}
  - value: ' 120°F'
    text: ' 120°F'
    type: MEASUREMENT_TEMPERATURE
    span: {start: 0, end: 6}
  range_indicator:
  - value: '-'
    text: '-'
    type: RANGE_INDICATOR
    span: {start: 0, end: 1}
  - value: between
    text: between
    type: RANGE_INDICATOR
    span: {start: 0, end: 7}
  - value: to
    text: to
    type: RANGE_INDICATOR
    span: {start: 0, end: 2}
  - value: and
    text: and
    type: RANGE_INDICATOR
    span: {start: 0, end: 3}
  - value: through
    text: through
    type: RANGE_INDICATOR
    span: {start: 0, end: 7}
  phone: []
  email: []
  url: []
  regulation: []
entity_insights:
  has_financial_data: false
  has_contact_info: false
  has_temporal_data: false
  has_external_references: false
  total_entities_found: 14
normalization:
  normalization_method: mvp-fusion-canonicalization
  processing_time_ms: 0.23866305127739906
  statistics:
    processing_time_ms: 0.23866305127739906
    original_entity_count: 14
    normalized_entity_count: 9
    entity_reduction_percent: 35.714285714285715
    entity_types_processed: 9
    canonical_forms_created: 9
    total_mentions: 9
    performance_metrics: {entities_per_ms: 37.710068449343936, memory_efficient: true, edge_compatible: true}
  canonical_entities:
  - id: gpe001
    type: GPE
    normalized: dra
    aliases: []
    count: 1
    mentions:
    - text: dra
      span: {start: 27, end: 30}
      subcategory: us_government_agencies
    metadata:
      subcategory: us_government_agencies
      gpe_type: geopolitical_entity
      political_level: unknown
      normalization_confidence: 0.7
      standardization_applied: false
  - id: meas001
    type: MEASUREMENT
    normalized: '0.9398'
    aliases: []
    count: 1
    mentions:
    - text: -37 inches
      span: {start: 0, end: 10}
    metadata:
      value: 37.0
      unit: inches
      si_value: 0.9398
      si_unit: meters
      measurement_type: length
      display_value: 37.0 inches (0.94 meters)
  - id: meas002
    type: MEASUREMENT
    normalized: '0.94'
    aliases: []
    count: 1
    mentions:
    - text: -94 cm
      span: {start: 0, end: 6}
    metadata:
      value: 94.0
      unit: cm
      si_value: 0.9400000000000001
      si_unit: meters
      measurement_type: length
      display_value: 94.0 cm (0.94 meters)
  - id: meas003
    type: MEASUREMENT
    normalized: '3.048'
    aliases: []
    count: 1
    mentions:
    - text: 10 feet
      span: {start: 0, end: 8}
    metadata:
      value: 10.0
      unit: feet
      si_value: 3.048
      si_unit: meters
      measurement_type: length
      display_value: 10.0 feet (3.05 meters)
  - id: meas004
    type: MEASUREMENT
    normalized: '48280.2'
    aliases: []
    count: 1
    mentions:
    - text: -30 mi
      span: {start: 0, end: 6}
    metadata:
      value: 30.0
      unit: mi
      si_value: 48280.2
      si_unit: meters
      measurement_type: length
      display_value: 30.0 mi (48280.20 meters)
  - id: meas005
    type: MEASUREMENT
    normalized: '34.0194'
    aliases: []
    count: 1
    mentions:
    - text: 75 pounds
      span: {start: 0, end: 10}
    metadata:
      value: 75.0
      unit: pounds
      si_value: 34.0194
      si_unit: kilograms
      measurement_type: weight
      display_value: 75.0 pounds (34.02 kilograms)
  - id: meas006
    type: MEASUREMENT
    normalized: '1800.0'
    aliases: []
    count: 1
    mentions:
    - text: -30 minutes
      span: {start: 0, end: 11}
    metadata:
      value: 30.0
      unit: minutes
      si_value: 1800.0
      si_unit: seconds
      measurement_type: time
      display_value: 30.0 minutes (1800.00 seconds)
  - id: meas007
    type: MEASUREMENT
    normalized: '-6.67'
    aliases: []
    count: 1
    mentions:
    - text: -20°F
      span: {start: 0, end: 6}
    metadata:
      value: 20.0
      unit: °F
      si_value: -6.666666666666667
      si_unit: celsius
      measurement_type: temperature
      display_value: 20.0 °F (-6.67 celsius)
  - id: meas008
    type: MEASUREMENT
    normalized: '48.89'
    aliases: []
    count: 1
    mentions:
    - text: 120°F
      span: {start: 0, end: 6}
    metadata:
      value: 120.0
      unit: °F
      si_value: 48.888888888888886
      si_unit: celsius
      measurement_type: temperature
      display_value: 120.0 °F (48.89 celsius)
  entity_reduction_percent: 35.714285714285715
---

Safety requirements for handrail installation:
- Handrail height must be 30-37 inches (76-94 cm)
- Distance between supports: 6 to ||3.048||meas003|| maximum
- Weight capacity: between 50 and ||34.0194||meas005|| minimum
- Response time: 15-30 minutes for emergency access
- Temperature tolerance: ||-6.67||meas007|| through ||48.89||meas008|| operating range