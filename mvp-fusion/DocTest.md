---
conversion:
  engine: mvp-fusion-highspeed
  page_count: 1
  conversion_time_ms: 4.448120016604662
  source_file: DocTest.pdf
  format: PDF
content_analysis:
  has_pdf_content: true
  has_tables: false
  has_images: false
  has_formulas: false
  has_code: false
  has_links: false
  has_lists: false
  has_headers: true
  has_footnotes: true
  has_citations: false
  has_structured_data: false
processing: {stage: completed, content_length: 1681}
domain_classification:
  routing: {skip_entity_extraction: false, enable_deep_domain_extraction: false, domain_specialization_route: general}
  top_domains: [legal_compliance, sales_conversion, feature_comparison, private_equity, contracts]
  top_document_types: [receiving_report, product_review, sales_receipt, regulation, influencer_content]
  domains:
    legal_compliance: 11.0
    sales_conversion: 9.6
    feature_comparison: 8.2
    private_equity: 6.0
    contracts: 5.6
    emerging_tech: 4.8
    research: 4.2
    employment_law: 4.2
    logistics_shipping: 4.2
    policy_legislation: 4.0
    payments: 3.7
    institutional_investors: 3.3
    data_science_ai: 3.3
    due_diligence: 2.4
    programming_languages: 2.4
    market_analysis: 2.0
    management: 1.9
    software_development: 1.9
    federal_agencies: 1.6
    cloud_infrastructure: 1.6
    cost_management: 1.4
    regulatory_standards: 1.4
    product_development: 1.4
    content_creation: 1.4
    engagement: 1.4
    conditions: 1.2
    methods: 1.2
    database: 1.2
    trends_viral: 1.2
    real_estate_law: 1.2
    agencies: 1.2
  document_types:
    receiving_report: 10.1
    product_review: 9.9
    sales_receipt: 9.5
    regulation: 7.9
    influencer_content: 7.2
    contract: 6.8
    nda: 5.3
    vendor_agreement: 4.2
    legal_brief: 4.2
    lab_report: 3.3
    articles_of_incorporation: 3.2
    linkedin_post: 3.2
    trade_confirmation: 2.6
    general_ledger: 2.6
    financial_report: 2.6
    iso_document: 2.6
    trend_analysis: 2.6
    forum_discussion: 2.4
    consent_form: 2.1
    lease_agreement: 2.1
    test_report: 2.1
    twitter_thread: 1.6
    status_report: 1.6
raw_entities:
  person: []
  org:
  - value: NVIDIA Corporation
    text: NVIDIA Corporation
    type: ORG
    span: {start: 113, end: 131}
  - value: NVIDIA
    text: NVIDIA
    type: ORG
    span: {start: 135, end: 141}
  - value: terms and conditions
    text: terms and conditions
    type: ORG
    span: {start: 342, end: 362}
  - value: t cup
    text: t cup
    type: ORG
    span: {start: 903, end: 908}
  - value: the industry
    text: the industry
    type: ORG
    span: {start: 1091, end: 1103}
  gpe:
  - value: essen
    text: essen
    type: GPE
    span: {start: 1341, end: 1346}
    metadata: {subcategory: major_cities}
  - value: fec
    text: fec
    type: GPE
    span: {start: 68, end: 71}
    metadata: {subcategory: us_government_agencies}
  - value: loc
    text: loc
    type: GPE
    span: {start: 147, end: 150}
    metadata: {subcategory: us_government_agencies}
  - value: dol
    text: dol
    type: GPE
    span: {start: 394, end: 397}
    metadata: {subcategory: us_government_agencies}
  - value: sec
    text: sec
    type: GPE
    span: {start: 413, end: 416}
    metadata: {subcategory: us_government_agencies}
  - value: cia
    text: cia
    type: GPE
    span: {start: 951, end: 954}
    metadata: {subcategory: us_government_agencies}
  - value: ssa
    text: ssa
    type: GPE
    span: {start: 1459, end: 1462}
    metadata: {subcategory: us_government_agencies}
  location:
  - value: indus
    text: indus
    type: LOC
    span: {start: 1059, end: 1064}
    metadata: {subcategory: rivers}
  - value: essen
    text: essen
    type: LOC
    span: {start: 1341, end: 1346}
    metadata: {subcategory: urban_settlements}
  date: []
  time: []
  money: []
  phone: []
  email: []
  url: []
  regulation: []
  measurement:
  - value: 000 G
    text: 000 G
    type: MEASUREMENT
    span: {start: 0, end: 5}
entity_insights:
  has_financial_data: false
  has_contact_info: false
  has_temporal_data: false
  has_external_references: false
  total_entities_found: 15
normalization:
  normalization_method: mvp-fusion-canonicalization
  processing_time_ms: 76.44937909208238
  statistics:
    processing_time_ms: 76.44937909208238
    original_entity_count: 15
    normalized_entity_count: 15
    entity_reduction_percent: 0.0
    entity_types_processed: 15
    canonical_forms_created: 15
    total_mentions: 15
    performance_metrics: {entities_per_ms: 0.19620826458162172, memory_efficient: false, edge_compatible: true}
  canonical_entities:
  - id: org001
    type: ORG
    normalized: NVIDIA Corporation
    aliases: []
    count: 1
    mentions:
    - text: NVIDIA Corporation
      span: {start: 113, end: 131}
    metadata:
      id: org001
      canonical: NVIDIA Corporation
      aliases: []
      mentions:
      - text: NVIDIA Corporation
        span: {start: 113, end: 131}
      count: 1
  - id: org002
    type: ORG
    normalized: NVIDIA
    aliases: []
    count: 1
    mentions:
    - text: NVIDIA
      span: {start: 135, end: 141}
    metadata:
      id: org002
      canonical: NVIDIA
      aliases: []
      mentions:
      - text: NVIDIA
        span: {start: 135, end: 141}
      count: 1
  - id: org003
    type: ORG
    normalized: terms and conditions
    aliases: []
    count: 1
    mentions:
    - text: terms and conditions
      span: {start: 342, end: 362}
    metadata:
      id: org003
      canonical: terms and conditions
      aliases: []
      mentions:
      - text: terms and conditions
        span: {start: 342, end: 362}
      count: 1
  - id: org004
    type: ORG
    normalized: t cup
    aliases: []
    count: 1
    mentions:
    - text: t cup
      span: {start: 903, end: 908}
    metadata:
      id: org004
      canonical: t cup
      aliases: []
      mentions:
      - text: t cup
        span: {start: 903, end: 908}
      count: 1
  - id: org005
    type: ORG
    normalized: the industry
    aliases: []
    count: 1
    mentions:
    - text: the industry
      span: {start: 1091, end: 1103}
    metadata:
      id: org005
      canonical: the industry
      aliases: []
      mentions:
      - text: the industry
        span: {start: 1091, end: 1103}
      count: 1
  - id: gpe001
    type: GPE
    normalized: essen
    aliases: []
    count: 1
    mentions:
    - text: essen
      span: {start: 1341, end: 1346}
      subcategory: major_cities
    metadata:
      subcategory: major_cities
      gpe_type: city
      political_level: municipal
      normalization_confidence: 0.8
      standardization_applied: false
  - id: gpe002
    type: GPE
    normalized: fec
    aliases: []
    count: 1
    mentions:
    - text: fec
      span: {start: 68, end: 71}
      subcategory: us_government_agencies
    metadata:
      subcategory: us_government_agencies
      gpe_type: geopolitical_entity
      political_level: unknown
      normalization_confidence: 0.7
      standardization_applied: false
  - id: gpe003
    type: GPE
    normalized: loc
    aliases: []
    count: 1
    mentions:
    - text: loc
      span: {start: 147, end: 150}
      subcategory: us_government_agencies
    metadata:
      subcategory: us_government_agencies
      gpe_type: geopolitical_entity
      political_level: unknown
      normalization_confidence: 0.7
      standardization_applied: false
  - id: gpe004
    type: GPE
    normalized: dol
    aliases: []
    count: 1
    mentions:
    - text: dol
      span: {start: 394, end: 397}
      subcategory: us_government_agencies
    metadata:
      subcategory: us_government_agencies
      gpe_type: geopolitical_entity
      political_level: unknown
      normalization_confidence: 0.7
      standardization_applied: false
  - id: gpe005
    type: GPE
    normalized: sec
    aliases: []
    count: 1
    mentions:
    - text: sec
      span: {start: 413, end: 416}
      subcategory: us_government_agencies
    metadata:
      subcategory: us_government_agencies
      gpe_type: geopolitical_entity
      political_level: unknown
      normalization_confidence: 0.7
      standardization_applied: false
  - id: gpe006
    type: GPE
    normalized: cia
    aliases: []
    count: 1
    mentions:
    - text: cia
      span: {start: 951, end: 954}
      subcategory: us_government_agencies
    metadata:
      subcategory: us_government_agencies
      gpe_type: geopolitical_entity
      political_level: unknown
      normalization_confidence: 0.7
      standardization_applied: false
  - id: gpe007
    type: GPE
    normalized: ssa
    aliases: []
    count: 1
    mentions:
    - text: ssa
      span: {start: 1459, end: 1462}
      subcategory: us_government_agencies
    metadata:
      subcategory: us_government_agencies
      gpe_type: geopolitical_entity
      political_level: unknown
      normalization_confidence: 0.7
      standardization_applied: false
  - id: loc001
    type: LOCATION
    normalized: indus
    aliases: []
    count: 1
    mentions:
    - text: indus
      span: {start: 1059, end: 1064}
      subcategory: rivers
    metadata:
      subcategory: rivers
      location_type: natural_feature
      normalization_confidence: 0.85
      standardization_applied: false
      geographic_level: hydrographic_feature
  - id: loc002
    type: LOCATION
    normalized: essen
    aliases: []
    count: 1
    mentions:
    - text: essen
      span: {start: 1341, end: 1346}
      subcategory: urban_settlements
    metadata:
      subcategory: urban_settlements
      location_type: location
      normalization_confidence: 0.7
      standardization_applied: false
      geographic_level: geographic_feature
  - id: meas001
    type: MEASUREMENT
    normalized: '0.0'
    aliases: []
    count: 1
    mentions:
    - text: 000 G
      span: {start: 0, end: 5}
    metadata:
      value: 0.0
      unit: G
      si_value: 0.0
      si_unit: kilograms
      measurement_type: weight
      display_value: 0.0 G (0.00 kilograms)
  entity_reduction_percent: 0.0
---



# Page 1

Contract for Purchase of GPUs 
This Agreement is made effective as of [Effective Date], by and between ||NVIDIA Corporation||org001|| Corporation 
("||NVIDIA||org002||"), located at [||NVIDIA||org002|| Address], and [Purchaser Name], located at [Purchaser 
Address]. 
WHEREAS, ||NVIDIA||org002|| agrees to sell, and [Purchaser Name] agrees to purchase, a total of 
1,000,000 GPUs under the ||terms and conditions||org003|| set forth herein. 
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt 
ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation 
ullamco laboris nisi ut aliquip ex ea commodo consequat. 
The delivery of GPUs shall be completed on or before [Delivery Date], and payment shall be 
made in full to [Payment Account Info] within 30 days of delivery. 
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla 
pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt 
mollit anim id est laborum. 
Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum 
has been ||the industry||org005||'s standard dummy text ever since the 1500s, when an unknown 
printer took a galley of type and scrambled it to make a type specimen book. It has survived 
not only five centuries, but also the leap into electronic typesetting, remaining essentially 
unchanged. It was popularised in the 1960s with the release of Letraset sheets containing 
Lorem Ipsum passages, and more recently with desktop publishing software like Aldus 
PageMaker including versions of Lorem Ipsum. 
This contract shall be governed by and construed in accordance with the laws of [Governing 
Law State]. 
