---
conversion:
  engine: mvp-fusion-highspeed
  page_count: 1
  conversion_time_ms: 0.09955000132322311
  source_file: money_range_test.md
  format: MD
content_analysis:
  has_text_content: true
  has_tables: false
  has_images: false
  has_formulas: true
  has_code: false
  has_links: false
  has_lists: true
  has_headers: true
  has_footnotes: false
  has_citations: false
  has_structured_data: false
processing: {stage: completed, content_length: 637}
domain_classification:
  routing: {skip_entity_extraction: false, enable_deep_domain_extraction: false, domain_specialization_route: general}
  top_domains: [engagement, business_intelligence, private_equity, emerging_tech, policy_legislation]
  top_document_types: [twitter_thread, exam, investment_prospectus, invoice, term_sheet]
  domains:
    engagement: 15.9
    business_intelligence: 11.1
    private_equity: 10.9
    emerging_tech: 8.2
    policy_legislation: 6.8
    grants_funding: 6.4
    lab_tech: 5.5
    growth_metrics: 4.2
    acquisition_metrics: 4.2
    sales_conversion: 4.2
    devops: 3.7
    market_customer: 3.7
    investment_terms: 3.6
    angel_investment: 3.6
    investment: 3.2
    real_estate_law: 2.3
    market_dynamics: 2.3
  document_types:
    twitter_thread: 24.2
    exam: 16.1
    investment_prospectus: 13.4
    invoice: 13.4
    term_sheet: 8.1
    test_report: 4.5
    trademark_application: 4.5
    case_study: 3.6
    sales_report: 3.6
    trade_confirmation: 3.6
    email_campaign: 3.4
    blog_post: 1.8
raw_entities:
  person: []
  org: []
  gpe:
  - value: dol
    text: dol
    type: GPE
    span: {start: 275, end: 278}
    metadata: {subcategory: us_government_agencies}
  location: []
  date: []
  time: []
  money:
  - value: $10M to $20M
    text: $10M to $20M
    type: MONEY
    span: {start: 0, end: 12}
  - value: $1.5 billion to $2.3 billion
    text: $1.5 billion to $2.3 billion
    type: MONEY
    span: {start: 0, end: 28}
  - value: 60 to 70 billion dollars
    text: 60 to 70 billion dollars
    type: MONEY
    span: {start: 0, end: 24}
  - value: $500K-$1M
    text: $500K-$1M
    type: MONEY
    span: {start: 0, end: 9}
  - value: $55.7B
    text: $55.7B
    type: MONEY
    span: {start: 0, end: 6}
  phone: []
  email: []
  url: []
  regulation: []
  measurement:
  - value: 10M
    text: 10M
    type: MEASUREMENT
    span: {start: 0, end: 3}
  - value: 20M
    text: 20M
    type: MEASUREMENT
    span: {start: 0, end: 3}
  - value: 1M
    text: 1M
    type: MEASUREMENT
    span: {start: 0, end: 2}
  - value: 10-15 kg
    text: 10-15 kg
    type: MEASUREMENT
    span: {start: 0, end: 8}
  - value: 5 to 10 feet
    text: 5 to 10 feet
    type: MEASUREMENT
    span: {start: 0, end: 12}
  - value: 100g
    text: 100g
    type: MEASUREMENT
    span: {start: 0, end: 4}
  - value: 200g
    text: 200g
    type: MEASUREMENT
    span: {start: 0, end: 4}
  - value: 1.5m
    text: 1.5m
    type: MEASUREMENT
    span: {start: 0, end: 4}
  - value: 2.0m
    text: 2.0m
    type: MEASUREMENT
    span: {start: 0, end: 4}
  - value: 28 G
    text: 28 G
    type: MEASUREMENT
    span: {start: 0, end: 4}
  - value: 60% to 70%
    text: 60% to 70%
    type: MEASUREMENT
    span: {start: 0, end: 10}
  - value: 20%
    text: 20%
    type: MEASUREMENT
    span: {start: 0, end: 3}
  - value: 5% - 15%
    text: 5% - 15%
    type: MEASUREMENT
    span: {start: 0, end: 8}
  - value: 2%
    text: 2%
    type: MEASUREMENT
    span: {start: 0, end: 2}
  - value: 8%
    text: 8%
    type: MEASUREMENT
    span: {start: 0, end: 2}
  - value: 12.5%
    text: 12.5%
    type: MEASUREMENT
    span: {start: 0, end: 5}
entity_insights:
  has_financial_data: true
  has_contact_info: false
  has_temporal_data: false
  has_external_references: false
  total_entities_found: 22
normalization:
  normalization_method: mvp-fusion-canonicalization
  processing_time_ms: 0.5982010625302792
  statistics:
    processing_time_ms: 0.5982010625302792
    original_entity_count: 22
    normalized_entity_count: 22
    entity_reduction_percent: 0.0
    entity_types_processed: 22
    canonical_forms_created: 22
    total_mentions: 22
    performance_metrics: {entities_per_ms: 36.77693233600103, memory_efficient: true, edge_compatible: true}
  canonical_entities:
  - id: gpe001
    type: GPE
    normalized: dol
    aliases: []
    count: 1
    mentions:
    - text: dol
      span: {start: 275, end: 278}
      subcategory: us_government_agencies
    metadata:
      subcategory: us_government_agencies
      gpe_type: geopolitical_entity
      political_level: unknown
      normalization_confidence: 0.7
      standardization_applied: false
  - id: mon001
    type: MONEY
    normalized: '10000000.0'
    aliases: []
    count: 1
    mentions:
    - text: $10M to $20M
      span: {start: 0, end: 12}
    metadata:
      currency: USD
      original_value: 10.0
      magnitude: M
      multiplier: 1000000
      formatted: USD 10,000,000.00
  - id: mon002
    type: MONEY
    normalized: '1500000000.0'
    aliases: []
    count: 1
    mentions:
    - text: $1.5 billion to $2.3 billion
      span: {start: 0, end: 28}
    metadata:
      currency: USD
      original_value: 1.5
      magnitude: billion
      multiplier: 1000000000
      formatted: USD 1,500,000,000.00
  - id: mon003
    type: MONEY
    normalized: '60000000000000.0'
    aliases: []
    count: 1
    mentions:
    - text: 60 to 70 billion dollars
      span: {start: 0, end: 24}
    metadata:
      currency: USD
      original_value: 60.0
      magnitude: t
      multiplier: 1000000000000
      formatted: USD 60,000,000,000,000.00
  - id: mon004
    type: MONEY
    normalized: '500000.0'
    aliases: []
    count: 1
    mentions:
    - text: $500K-$1M
      span: {start: 0, end: 9}
    metadata:
      currency: USD
      original_value: 500.0
      magnitude: K
      multiplier: 1000
      formatted: USD 500,000.00
  - id: mon005
    type: MONEY
    normalized: '55700000000.0'
    aliases: []
    count: 1
    mentions:
    - text: $55.7B
      span: {start: 0, end: 6}
    metadata:
      currency: USD
      original_value: 55.7
      magnitude: B
      multiplier: 1000000000
      formatted: USD 55,700,000,000.00
  - id: meas001
    type: MEASUREMENT
    normalized: '10.0'
    aliases: []
    count: 1
    mentions:
    - text: 10M
      span: {start: 0, end: 3}
    metadata:
      value: 10.0
      unit: M
      si_value: 10.0
      si_unit: meters
      measurement_type: length
      display_value: 10.0 M (10.00 meters)
  - id: meas002
    type: MEASUREMENT
    normalized: '20.0'
    aliases: []
    count: 1
    mentions:
    - text: 20M
      span: {start: 0, end: 3}
    metadata:
      value: 20.0
      unit: M
      si_value: 20.0
      si_unit: meters
      measurement_type: length
      display_value: 20.0 M (20.00 meters)
  - id: meas003
    type: MEASUREMENT
    normalized: '1.0'
    aliases: []
    count: 1
    mentions:
    - text: 1M
      span: {start: 0, end: 2}
    metadata:
      value: 1.0
      unit: M
      si_value: 1.0
      si_unit: meters
      measurement_type: length
      display_value: 1.0 M (1.00 meters)
  - id: meas004
    type: MEASUREMENT
    normalized: '15.0'
    aliases: []
    count: 1
    mentions:
    - text: 10-15 kg
      span: {start: 0, end: 8}
    metadata:
      value: 15.0
      unit: kg
      si_value: 15.0
      si_unit: kilograms
      measurement_type: weight
      display_value: 15.0 kg (15.00 kilograms)
  - id: meas005
    type: MEASUREMENT
    normalized: '5.0'
    aliases: []
    count: 1
    mentions:
    - text: 5 to 10 feet
      span: {start: 0, end: 12}
    metadata:
      value: 5.0
      unit: to
      si_value: 5.0
      si_unit: to
      measurement_type: unknown
      display_value: 5.0 to
  - id: meas006
    type: MEASUREMENT
    normalized: '0.1'
    aliases: []
    count: 1
    mentions:
    - text: 100g
      span: {start: 0, end: 4}
    metadata:
      value: 100.0
      unit: g
      si_value: 0.1
      si_unit: kilograms
      measurement_type: weight
      display_value: 100.0 g (0.10 kilograms)
  - id: meas007
    type: MEASUREMENT
    normalized: '0.2'
    aliases: []
    count: 1
    mentions:
    - text: 200g
      span: {start: 0, end: 4}
    metadata:
      value: 200.0
      unit: g
      si_value: 0.2
      si_unit: kilograms
      measurement_type: weight
      display_value: 200.0 g (0.20 kilograms)
  - id: meas008
    type: MEASUREMENT
    normalized: '1.5'
    aliases: []
    count: 1
    mentions:
    - text: 1.5m
      span: {start: 0, end: 4}
    metadata:
      value: 1.5
      unit: m
      si_value: 1.5
      si_unit: meters
      measurement_type: length
      display_value: 1.5 m (1.50 meters)
  - id: meas009
    type: MEASUREMENT
    normalized: '2.0'
    aliases: []
    count: 1
    mentions:
    - text: 2.0m
      span: {start: 0, end: 4}
    metadata:
      value: 2.0
      unit: m
      si_value: 2.0
      si_unit: meters
      measurement_type: length
      display_value: 2.0 m (2.00 meters)
  - id: meas010
    type: MEASUREMENT
    normalized: '0.028'
    aliases: []
    count: 1
    mentions:
    - text: 28 G
      span: {start: 0, end: 4}
    metadata:
      value: 28.0
      unit: G
      si_value: 0.028
      si_unit: kilograms
      measurement_type: weight
      display_value: 28.0 G (0.03 kilograms)
  - id: meas011
    type: MEASUREMENT
    normalized: '60.0'
    aliases: []
    count: 1
    mentions:
    - text: 60% to 70%
      span: {start: 0, end: 10}
    metadata:
      value: 60.0
      unit: '%'
      si_value: 60.0
      si_unit: percent
      measurement_type: percentage
      display_value: 60.0 % (60.00 percent)
  - id: meas012
    type: MEASUREMENT
    normalized: '20.0'
    aliases: []
    count: 1
    mentions:
    - text: 20%
      span: {start: 0, end: 3}
    metadata:
      value: 20.0
      unit: '%'
      si_value: 20.0
      si_unit: percent
      measurement_type: percentage
      display_value: 20.0 % (20.00 percent)
  - id: meas013
    type: MEASUREMENT
    normalized: '5.0'
    aliases: []
    count: 1
    mentions:
    - text: 5% - 15%
      span: {start: 0, end: 8}
    metadata:
      value: 5.0
      unit: '%'
      si_value: 5.0
      si_unit: percent
      measurement_type: percentage
      display_value: 5.0 % (5.00 percent)
  - id: meas014
    type: MEASUREMENT
    normalized: '2.0'
    aliases: []
    count: 1
    mentions:
    - text: 2%
      span: {start: 0, end: 2}
    metadata:
      value: 2.0
      unit: '%'
      si_value: 2.0
      si_unit: percent
      measurement_type: percentage
      display_value: 2.0 % (2.00 percent)
  - id: meas015
    type: MEASUREMENT
    normalized: '8.0'
    aliases: []
    count: 1
    mentions:
    - text: 8%
      span: {start: 0, end: 2}
    metadata:
      value: 8.0
      unit: '%'
      si_value: 8.0
      si_unit: percent
      measurement_type: percentage
      display_value: 8.0 % (8.00 percent)
  - id: meas016
    type: MEASUREMENT
    normalized: '12.5'
    aliases: []
    count: 1
    mentions:
    - text: 12.5%
      span: {start: 0, end: 5}
    metadata:
      value: 12.5
      unit: '%'
      si_value: 12.5
      si_unit: percent
      measurement_type: percentage
      display_value: 12.5 % (12.50 percent)
  entity_reduction_percent: 0.0
---

---
title: "Money and Percentage Range Test"
---

# Money and Percentage Range Test

Testing improved money, percentage, and measurement patterns:

## Money Ranges
- Investment round: $||10.0||meas001|| to $||20.0||meas002||
- Valuation range: ||1500000000.0||mon002||  
- Funding: ||60000000000000.0||mon003||
- Seed funding: $500K-$||1.0||meas003||

## Percentage Ranges
- Success rate: ||60.0||meas011||
- Market share: 15-||20.0||meas012||
- Growth rate: ||5.0||meas013||
- Conversion: between ||2.0||meas014|| and ||8.0||meas015||

## Measurements with Ranges
- Weight: ||15.0||meas004||
- Distance: ||5.0||meas005||
- Volume: ||0.1||meas006|| to ||0.2||meas007||
- Height: ||1.5||meas008|| - ||2.0||meas009||

## Simple Values (should still work)
- Price: ||55700000000.0||mon005||
- Rate: ||12.5||meas016||
- Weight: ||0.028||meas010||