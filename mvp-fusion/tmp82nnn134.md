---
conversion:
  description: High-Speed Document Conversion & Analysis
  yaml_engine: mvp-fusion-yaml-v1
  yaml_schema_version: '1.0'
  conversion_method: mvp-fusion-highspeed
  extractor: HighSpeed_Markdown_General
  source_type: file
  source_path: /tmp/tmp82nnn134.txt
  filename: tmp82nnn134.txt
  file_extension: .txt
  format: TXT
  size_bytes: 927
  size_human: 927 B
  conversion_date: '2025-09-22T16:26:05'
  page_count: 0
content_analysis:
  has_tables: false
  has_images: false
  has_formulas: false
  has_code: false
  has_links: false
  has_lists: false
  has_headers: false
  has_footnotes: false
  has_citations: false
  has_structured_data: false
processing: {stage: converted, conversion_time_ms: 1.016375026665628, content_length: 927}
domain_classification:
  routing: {skip_entity_extraction: false, enable_deep_domain_extraction: false, domain_specialization_route: general}
  top_domains: [emerging_tech, federal_agencies, venture_capital, programming_languages, grants_funding]
  top_document_types: [investment_prospectus, sec_filing, press_release, pitch_deck, aml_report]
  domains:
    emerging_tech: 11.7
    federal_agencies: 6.8
    venture_capital: 5.2
    programming_languages: 5.0
    grants_funding: 3.9
    investment: 3.9
    team_hiring: 3.6
    private_equity: 3.4
    feature_comparison: 3.3
    startup_operations: 3.0
    legal_compliance: 2.8
    market_analysis: 2.8
    api_integration: 2.6
    enterprise_software: 2.6
    automation: 2.6
    software_development: 2.3
    data_science_ai: 2.3
    security_compliance: 2.3
    clinical: 2.3
    payments: 2.3
    practice_areas: 2.3
    production: 2.0
    hr_tech: 2.0
    product_development: 2.0
    regulatory_standards: 2.0
    due_diligence: 1.7
    technology: 1.7
    strategic_rationale: 1.7
    agencies: 1.7
    clinical_research: 1.7
    real_estate_law: 1.6
    operations: 1.4
    policy_legislation: 1.4
    regulatory_legal: 1.4
    trade_regulations: 0.9
  document_types:
    investment_prospectus: 12.4
    sec_filing: 10.3
    press_release: 8.7
    pitch_deck: 7.4
    aml_report: 6.2
    osha_report: 6.2
    articles_of_incorporation: 4.9
    api_documentation: 4.9
    news_article: 4.9
    stress_test: 4.1
    equipment_manual: 4.1
    fda_submission: 4.1
    payment_processing: 4.1
    trademark_application: 4.1
    forum_discussion: 3.7
    influencer_content: 3.7
    board_resolution: 3.1
    non_conformance: 2.9
raw_entities:
  person:
  - value: Goldman Sachs
    text: Goldman Sachs
    type: PERSON
    span: {start: 738, end: 751}
  - value: Wilson Sonsini Goodrich
    text: Wilson Sonsini Goodrich
    type: PERSON
    span: {start: 795, end: 818}
  - value: James Anderson
    text: James Anderson
    type: PERSON
    span: {start: 875, end: 889}
  - value: founder Mark Roberts
    text: founder Mark Roberts
    type: PERSON
    span: {start: 905, end: 925}
  org:
  - value: ACME Corp
    text: ACME Corp
    type: ORG
    span: {start: 408, end: 417}
  location: []
  gpe: []
  date:
  - value: March 15, 2024
    text: March 15, 2024
    type: DATE
    span: {start: 0, end: 14}
  time: []
  money:
  - value: $5.2 million
    text: $5.2 million
    type: MONEY
    span: {start: 0, end: 12}
  phone: []
  email: []
  url: []
  regulation: []
  measurement:
  - value: 5.2 m
    text: 5.2 m
    type: MEASUREMENT
    span: {start: 0, end: 5}
  - value: 12 m
    text: 12 m
    type: MEASUREMENT
    span: {start: 0, end: 4}
entity_insights:
  has_financial_data: true
  has_contact_info: false
  has_temporal_data: true
  has_external_references: false
  total_entities_found: 9
normalization:
  normalization_method: mvp-fusion-canonicalization
  processing_time_ms: 39.590772008523345
  statistics:
    processing_time_ms: 39.590772008523345
    original_entity_count: 9
    normalized_entity_count: 9
    entity_reduction_percent: 0.0
    entity_types_processed: 9
    canonical_forms_created: 9
    total_mentions: 9
    performance_metrics: {entities_per_ms: 0.2273257010007894, memory_efficient: true, edge_compatible: true}
  canonical_entities:
  - id: p001
    type: PERSON
    normalized: Goldman Sachs
    aliases: []
    count: 1
    mentions:
    - text: Goldman Sachs
      span: {start: 738, end: 751}
    metadata: null
  - id: p002
    type: PERSON
    normalized: Wilson Sonsini Goodrich
    aliases: []
    count: 1
    mentions:
    - text: Wilson Sonsini Goodrich
      span: {start: 795, end: 818}
    metadata: null
  - id: p003
    type: PERSON
    normalized: James Anderson
    aliases: []
    count: 1
    mentions:
    - text: James Anderson
      span: {start: 875, end: 889}
    metadata: null
  - id: p004
    type: PERSON
    normalized: founder Mark Roberts
    aliases: []
    count: 1
    mentions:
    - text: founder Mark Roberts
      span: {start: 905, end: 925}
    metadata: null
  - id: org001
    type: ORG
    normalized: ACME Corp
    aliases: []
    count: 1
    mentions:
    - text: ACME Corp
      span: {start: 408, end: 417}
    metadata:
      id: org001
      canonical: ACME Corp
      aliases: []
      mentions:
      - text: ACME Corp
        span: {start: 408, end: 417}
      count: 1
  - id: d001
    type: DATE
    normalized: '2024-03-15'
    aliases: []
    count: 1
    mentions:
    - text: March 15, 2024
      span: {start: 0, end: 14}
    metadata:
      original_format: March 15, 2024
      iso_date: '2024-03-15'
      epoch_timestamp: 1710460800
      day_of_week: Friday
      quarter: Q1
      fiscal_year: FY2024
      relative_reference: past
      year: 2024
      month: 3
      day: 15
  - id: mon001
    type: MONEY
    normalized: '5200000.0'
    aliases: []
    count: 1
    mentions:
    - text: $5.2 million
      span: {start: 0, end: 12}
    metadata:
      currency: USD
      original_value: 5.2
      magnitude: million
      multiplier: 1000000
      formatted: USD 5,200,000.00
  - id: meas001
    type: MEASUREMENT
    normalized: '5.2'
    aliases: []
    count: 1
    mentions:
    - text: 5.2 m
      span: {start: 0, end: 5}
    metadata:
      value: 5.2
      unit: m
      si_value: 5.2
      si_unit: meters
      measurement_type: length
      display_value: 5.2 m (5.20 meters)
  - id: meas002
    type: MEASUREMENT
    normalized: '12.0'
    aliases: []
    count: 1
    mentions:
    - text: 12 m
      span: {start: 0, end: 4}
    metadata:
      value: 12.0
      unit: m
      si_value: 12.0
      si_unit: meters
      measurement_type: length
      display_value: 12.0 m (12.00 meters)
  entity_reduction_percent: 0.0
  performance: {entities_per_ms: 0.2273257010007894, edge_compatible: true}
---


Dr. John Smith, CEO of ACME Corporation, announced today that the company has secured ||5200000.0||mon001|| in Series A funding. 
The investment round was led by Sarah Johnson from Venture Capital Partners, with participation from Michael Brown and Lisa Wilson.
The funding will be used to expand operations in California and hire additional engineering talent.

According to the press release dated ||2024-03-15||d001||, ||ACME Corp||org001|| expects to increase headcount by 50% over the next 12 months.
Chief Technology Officer David Chen stated that the company will focus on developing new AI-powered solutions.
Board member Dr. Elizabeth Taylor emphasized the importance of regulatory compliance in the healthcare sector.

The transaction was facilitated by ||Goldman Sachs||p001|| Securities, with legal counsel provided by ||Wilson Sonsini Goodrich||p002|| & Rosati.
Key investors include former Google executive ||James Anderson||p003|| and Netflix co-||founder Mark Roberts||p004||.
