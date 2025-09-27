---
conversion:
  engine: mvp-fusion-highspeed
  page_count: 1
  conversion_time_ms: 0.09752193000167608
  source_file: bytedance_test.md
  format: MD
content_analysis:
  has_text_content: true
  has_tables: false
  has_images: false
  has_formulas: false
  has_code: false
  has_links: false
  has_lists: true
  has_headers: true
  has_footnotes: false
  has_citations: false
  has_structured_data: false
processing: {stage: completed, content_length: 200}
domain_classification:
  routing: {skip_entity_extraction: false, enable_deep_domain_extraction: false, domain_specialization_route: general}
  top_domains: [api_integration, platforms, conversion_optimization, funding_trends, grants_funding]
  top_document_types: [exam, api_documentation, service_agreement, receiving_report, investment_prospectus]
  domains:
    api_integration: 15.9
    platforms: 13.9
    conversion_optimization: 13.9
    funding_trends: 11.9
    grants_funding: 11.9
    engagement: 11.9
    software_development: 11.9
    real_estate_law: 8.5
  document_types:
    exam: 27.1
    api_documentation: 13.6
    service_agreement: 13.6
    receiving_report: 11.3
    investment_prospectus: 11.3
    stress_test: 11.3
    twitter_thread: 6.8
    press_release: 5.1
raw_entities:
  person: []
  org:
  - value: ByteDance
    text: ByteDance
    type: ORG
    span: {start: 12, end: 21}
  - value: TikTok
    text: TikTok
    type: ORG
    span: {start: 92, end: 98}
  - value: Sequoia Capital
    text: Sequoia Capital
    type: ORG
    span: {start: 127, end: 142}
  - value: Apple Inc
    text: Apple Inc
    type: ORG
    span: {start: 172, end: 181}
  - value: Microsoft
    text: Microsoft
    type: ORG
    span: {start: 190, end: 199}
  - value: Tesla
    text: Tesla
    type: ORG
    span: {start: 183, end: 188}
  - value: Apple Inc
    text: Apple Inc
    type: ORG
    span: {start: 172, end: 181}
  - value: Microsoft
    text: Microsoft
    type: ORG
    span: {start: 190, end: 199}
  - value: Tesla
    text: Tesla
    type: ORG
    span: {start: 183, end: 188}
  gpe:
  - value: Other
    text: Other
    type: GPE
    span: {start: 145, end: 150}
    metadata: {subcategory: us_government_agencies}
  location: []
  date: []
  time: []
  money: []
  phone: []
  email: []
  url: []
  regulation: []
  measurement: []
entity_insights:
  has_financial_data: false
  has_contact_info: false
  has_temporal_data: false
  has_external_references: false
  total_entities_found: 10
normalization:
  normalization_method: mvp-fusion-canonicalization
  processing_time_ms: 75.35102998372167
  statistics:
    processing_time_ms: 75.35102998372167
    original_entity_count: 10
    normalized_entity_count: 10
    entity_reduction_percent: 0.0
    entity_types_processed: 10
    canonical_forms_created: 10
    total_mentions: 10
    performance_metrics: {entities_per_ms: 0.1327121872409751, memory_efficient: false, edge_compatible: true}
  canonical_entities:
  - id: org001
    type: ORG
    normalized: ByteDance
    aliases: []
    count: 1
    mentions:
    - text: ByteDance
      span: {start: 12, end: 21}
    metadata:
      id: org001
      canonical: ByteDance
      aliases: []
      mentions:
      - text: ByteDance
        span: {start: 12, end: 21}
      count: 1
      premium_metadata:
        subcategory: unicorn_company
        premium_source: unicorn
        confidence: 0.9
        entity_class: premium_startup
        high_value_entity: true
  - id: org002
    type: ORG
    normalized: TikTok
    aliases: []
    count: 1
    mentions:
    - text: TikTok
      span: {start: 92, end: 98}
    metadata:
      id: org002
      canonical: TikTok
      aliases: []
      mentions:
      - text: TikTok
        span: {start: 92, end: 98}
      count: 1
      premium_metadata:
        subcategory: standard_organization
        premium_source: standard
        confidence: 0.7
        entity_class: organization
        high_value_entity: false
  - id: org003
    type: ORG
    normalized: Sequoia Capital
    aliases: []
    count: 1
    mentions:
    - text: Sequoia Capital
      span: {start: 127, end: 142}
    metadata:
      id: org003
      canonical: Sequoia Capital
      aliases: []
      mentions:
      - text: Sequoia Capital
        span: {start: 127, end: 142}
      count: 1
      premium_metadata:
        subcategory: investor_company
        premium_source: investor
        confidence: 0.85
        entity_class: investment_firm
        high_value_entity: true
  - id: org004
    type: ORG
    normalized: Apple Inc
    aliases: []
    count: 1
    mentions:
    - text: Apple Inc
      span: {start: 172, end: 181}
    metadata:
      id: org004
      canonical: Apple Inc
      aliases: []
      mentions:
      - text: Apple Inc
        span: {start: 172, end: 181}
      count: 1
      premium_metadata:
        subcategory: standard_organization
        premium_source: standard
        confidence: 0.7
        entity_class: organization
        high_value_entity: false
  - id: org005
    type: ORG
    normalized: Microsoft
    aliases: []
    count: 1
    mentions:
    - text: Microsoft
      span: {start: 190, end: 199}
    metadata:
      id: org005
      canonical: Microsoft
      aliases: []
      mentions:
      - text: Microsoft
        span: {start: 190, end: 199}
      count: 1
      premium_metadata:
        subcategory: investor_company
        premium_source: investor
        confidence: 0.85
        entity_class: investment_firm
        high_value_entity: true
  - id: org006
    type: ORG
    normalized: Tesla
    aliases: []
    count: 1
    mentions:
    - text: Tesla
      span: {start: 183, end: 188}
    metadata:
      id: org006
      canonical: Tesla
      aliases: []
      mentions:
      - text: Tesla
        span: {start: 183, end: 188}
      count: 1
      premium_metadata:
        subcategory: standard_organization
        premium_source: standard
        confidence: 0.7
        entity_class: organization
        high_value_entity: false
  - id: org007
    type: ORG
    normalized: Apple Inc
    aliases: []
    count: 1
    mentions:
    - text: Apple Inc
      span: {start: 172, end: 181}
    metadata:
      id: org007
      canonical: Apple Inc
      aliases: []
      mentions:
      - text: Apple Inc
        span: {start: 172, end: 181}
      count: 1
      premium_metadata:
        subcategory: standard_organization
        premium_source: standard
        confidence: 0.7
        entity_class: organization
        high_value_entity: false
  - id: org008
    type: ORG
    normalized: Microsoft
    aliases: []
    count: 1
    mentions:
    - text: Microsoft
      span: {start: 190, end: 199}
    metadata:
      id: org008
      canonical: Microsoft
      aliases: []
      mentions:
      - text: Microsoft
        span: {start: 190, end: 199}
      count: 1
      premium_metadata:
        subcategory: investor_company
        premium_source: investor
        confidence: 0.85
        entity_class: investment_firm
        high_value_entity: true
  - id: org009
    type: ORG
    normalized: Tesla
    aliases: []
    count: 1
    mentions:
    - text: Tesla
      span: {start: 183, end: 188}
    metadata:
      id: org009
      canonical: Tesla
      aliases: []
      mentions:
      - text: Tesla
        span: {start: 183, end: 188}
      count: 1
      premium_metadata:
        subcategory: standard_organization
        premium_source: standard
        confidence: 0.7
        entity_class: organization
        high_value_entity: false
  - id: gpe001
    type: GPE
    normalized: Other
    aliases: []
    count: 1
    mentions:
    - text: Other
      span: {start: 145, end: 150}
      subcategory: us_government_agencies
    metadata:
      subcategory: us_government_agencies
      gpe_type: geopolitical_entity
      political_level: unknown
      normalization_confidence: 0.75
      standardization_applied: false
  entity_reduction_percent: 0.0
---

---
title: "||ByteDance||org001|| Test"
---

# ||ByteDance||org001|| Test

||ByteDance||org001|| is a unicorn company that owns ||TikTok||org002||. They received funding from ||Sequoia Capital||org003||.

||Other||gpe001|| companies mentioned: ||Apple Inc||org007||, ||Tesla||org009||, ||Microsoft||org008||.