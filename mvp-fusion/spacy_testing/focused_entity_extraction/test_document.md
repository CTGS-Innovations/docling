# Entity Extraction Comprehensive Test Document
## Testing Framework for Core 8 Entity Recognition

**Document Purpose:** This document contains precisely counted entities for validation of the MVP-Fusion extraction pipeline.
**Test Date:** January 15, 2024
**Version:** 1.0

---

## SECTION 1: PERSON ENTITIES (Total: 25 persons)

### 1.1 Standard Names (10 persons)
1. **John Smith**, Chief Executive Officer at Global Dynamics Corporation, reported strong earnings.
2. **Mary Johnson**, Director of Engineering, will present at the conference on March 20, 2024.
3. **Robert Chen**, Senior Analyst, completed the regulatory review yesterday.
4. **Sarah Williams-Brown**, Vice President of Operations, manages 500 employees.
5. **Dr. Michael O'Brien**, Chief Medical Officer, published new safety guidelines.
6. **Jennifer Martinez**, Compliance Manager at OSHA, reviewed 50 cases last month.
7. **David Kim**, Lead Inspector, identified critical violations at the facility.
8. **Lisa Anderson**, Safety Coordinator, implemented new protocols saving $2.5 million.
9. **James Wilson**, Regional Director, oversees operations in New York and California.
10. **Patricia Thompson**, Quality Assurance Specialist, achieved 99.5% accuracy rate.

### 1.2 Challenging Names (8 persons)
11. **Xi Zhang**, Software Engineer, developed the new monitoring system.
12. **José García-López**, Environmental Consultant, assessed 12 sites in Texas.
13. **Priya Patel**, Data Scientist, analyzed 10,000 records for compliance.
14. **François Dubois**, International Liaison, coordinates with EU offices.
15. **Yuki Tanaka**, Project Manager, delivered ahead of schedule.
16. **Ahmed Al-Rashid**, Security Specialist, enhanced protocols by 40%.
17. **Olga Volkov**, Research Director at Moscow Institute, published findings.
18. **João Silva Santos**, Brazilian Operations Manager, expanded to 5 cities.

### 1.3 Edge Cases (7 persons)
19. **Van Der Berg**, Consultant (last name only with title), advised on restructuring.
20. **Dr. Li** (title with short name), presented breakthrough research.
21. **Madonna** (single name), celebrity spokesperson for safety campaign.
22. **John John** (repeated name), Analyst at Tech Corp.
23. **Mary Mary Quite Contrary** (unusual but real name), Marketing Director.
24. **Bob "The Builder" Johnson** (nickname), Construction Supervisor.
25. **Sir Charles Winchester III**, Chairman Emeritus, founded the organization.

---

## SECTION 2: ORGANIZATION ENTITIES (Total: 30 organizations)

### 2.1 Government Agencies (10 organizations)
1. **OSHA** (Occupational Safety and Health Administration) issued new guidelines.
2. The **Department of Labor** announced updated regulations effective June 1, 2024.
3. **EPA** (Environmental Protection Agency) fined three companies $5 million total.
4. The **Centers for Disease Control and Prevention** (CDC) released health advisories.
5. **National Institute for Occupational Safety and Health** (NIOSH) conducted studies.
6. The **Federal Aviation Administration** (FAA) approved new safety measures.
7. **Department of Transportation** (DOT) implemented stricter requirements.
8. The **Food and Drug Administration** (FDA) recalled 15 products.
9. **Consumer Product Safety Commission** (CPSC) issued warnings.
10. The **Nuclear Regulatory Commission** (NRC) inspected 20 facilities.

### 2.2 Companies (15 organizations)
11. **Microsoft Corporation** invested $100 million in safety technology.
12. **Amazon Web Services, Inc.** expanded data centers to 5 new locations.
13. **General Electric Company** (GE) reported 25% improvement in safety metrics.
14. **Johnson & Johnson** developed new protective equipment.
15. **3M Company** supplied 1 million respirators to healthcare facilities.
16. **Boeing Corporation** enhanced aircraft safety systems.
17. **Tesla, Inc.** achieved zero workplace injuries for 365 days.
18. **Walmart Inc.** trained 50,000 employees in new safety protocols.
19. **Apple Inc.** reduced workplace incidents by 60%.
20. **Google LLC** implemented AI-powered safety monitoring.
21. **Facebook Technologies, LLC** (Meta) upgraded VR training systems.
22. **United Parcel Service** (UPS) delivered to 200 countries safely.
23. **FedEx Corporation** maintained 99.9% delivery accuracy.
24. **Lockheed Martin Corporation** completed defense contracts worth $10 billion.
25. **Raytheon Technologies** developed advanced safety sensors.

### 2.3 Educational Institutions (5 organizations)
26. **Massachusetts Institute of Technology** (MIT) researched new materials.
27. **Stanford University** partnered with industry on safety innovations.
28. **Harvard Business School** published case studies on workplace safety.
29. The **University of California, Berkeley** trained 500 safety professionals.
30. **Johns Hopkins University** developed medical safety protocols.

---

## SECTION 3: LOCATION ENTITIES (Total: 20 locations)

### 3.1 Cities (10 locations)
Operations expanded to: **New York City**, **Los Angeles**, **Chicago**, **Houston**, **Phoenix**, **Philadelphia**, **San Antonio**, **San Diego**, **Dallas**, and **San Jose**.

### 3.2 States and Countries (10 locations)
International presence in: **California**, **Texas**, **Florida**, **United States**, **Canada**, **United Kingdom**, **Germany**, **Japan**, **Australia**, and **Brazil**.

---

## SECTION 4: GPE ENTITIES (Geopolitical Entities) (Total: 8 GPEs)
The **United States** government, working with **China**, **Russia**, **India**, the **European Union**, **Mexico**, **South Korea**, and **Israel** on international standards.

---

## SECTION 5: DATE ENTITIES (Total: 15 dates)

1. Implementation begins on **January 1, 2024**
2. First review scheduled for **February 15, 2024**
3. Quarterly report due **March 31, 2024**
4. Training completion by **April 30, 2024**
5. Mid-year assessment on **June 30, 2024**
6. Policy effective from **July 1, 2024**
7. Audit scheduled for **August 15-20, 2024**
8. Compliance deadline: **September 30, 2024**
9. Conference dates: **October 10-12, 2024**
10. Annual review on **November 15, 2024**
11. Year-end report by **December 31, 2024**
12. Historical reference: **March 15, 1991** regulations
13. Previous update: **June 1, 2020**
14. Original implementation: **January 26, 1989**
15. Future planning for **January 1, 2025**

---

## SECTION 6: TIME ENTITIES (Total: 8 times)

Meetings scheduled at: **9:00 AM**, **10:30 AM**, **12:00 PM** (noon), **2:15 PM**, **3:45 PM**, **5:00 PM**, **6:30 PM**, and **11:59 PM**.

---

## SECTION 7: MONEY ENTITIES (Total: 20 money amounts)

### 7.1 Budget Items (10 amounts)
1. Safety equipment budget: **$500,000**
2. Training allocation: **$1.2 million**
3. Compliance software: **$250,000**
4. Consulting fees: **$75,000**
5. Insurance premiums: **$3.5 million**
6. Facility upgrades: **$10 million**
7. Emergency fund: **$500,000**
8. Research grants: **$2.8 million**
9. Legal reserves: **$1.5 million**
10. Technology investments: **$5.2 million**

### 7.2 Fines and Penalties (10 amounts)
11. Maximum OSHA fine: **$14,502** per violation
12. Serious violation: **$1,000** minimum
13. Willful violation: **$10,000** to **$145,027**
14. Repeat violation: **$145,027** maximum
15. Failure to abate: **$14,502** per day
16. Total penalties collected: **$50 million**
17. Average fine: **$3,500**
18. Largest single fine: **$2.3 million**
19. Settlement amount: **$750,000**
20. Cost savings achieved: **$100 million**

---

## SECTION 8: PERCENT ENTITIES (Total: 15 percentages)

1. Safety improvement: **25%** reduction in incidents
2. Compliance rate: **98.5%** of facilities
3. Training completion: **100%** of employees
4. Cost reduction: **15%** year-over-year
5. Efficiency gain: **30%** in processing time
6. Market share: **45.5%** of industry
7. Customer satisfaction: **92%** positive feedback
8. Error rate: **0.5%** (half percent)
9. Growth projection: **10-15%** range
10. Productivity increase: **20%**
11. Waste reduction: **35%**
12. Energy savings: **18.5%**
13. Attendance rate: **97%**
14. Success rate: **88%**
15. Participation: **75%** of eligible workers

---

## SECTION 9: SPECIAL ENTITIES

### 9.1 Phone Numbers (10 phone numbers)
Contact numbers: **(800) 321-6742**, **(202) 693-1999**, **(877) 889-5627**, **(617) 565-9860**, **(212) 337-2378**, **(404) 562-2300**, **(312) 353-2220**, **(214) 767-4731**, **(303) 844-1600**, **(415) 975-4310**.

### 9.2 Regulations (10 regulations)
Key regulations: **29 CFR 1910.132**, **29 CFR 1926.95**, **29 CFR 1910.134**, **OSHA 3124-12R**, **ISO 9001:2015**, **ANSI Z359.11**, **NFPA 70E**, **EPA 40 CFR 264**, **DOT 49 CFR 172**, **FDA 21 CFR 211**.

### 9.3 URLs (5 URLs)
Resources available at: **https://www.osha.gov**, **http://www.cdc.gov/niosh**, **https://www.epa.gov/compliance**, **https://www.iso.org/standards**, **http://www.ansi.org**.

### 9.4 Measurements (20 measurements)
- Fall protection required above **6 feet** (1.8 meters) in construction
- Guardrails must be **42 inches** (107 cm) high
- Toe boards minimum **4 inches** (10 cm) high
- Safety nets within **30 feet** (9.1 meters)
- Ladder side rails extend **3 feet** (0.9 meters)
- Stairway width minimum **22 inches** (56 cm)
- Handrail height **30-37 inches** (76-94 cm)
- Landing depth **30 inches** (76 cm) minimum
- Riser height maximum **9.5 inches** (24 cm)
- Tread depth minimum **9.5 inches** (24 cm)
- Door swing clearance **20 inches** (51 cm)
- Scaffold width minimum **18 inches** (46 cm)
- Clearance from power lines **10 feet** (3 meters)
- Excavation depth requiring protection **5 feet** (1.5 meters)
- Noise exposure limit **90 decibels** for 8 hours
- Weight capacity **250 pounds** (113 kg) per person
- Temperature range **-20°F to 120°F** (-29°C to 49°C)
- Visibility distance **500 feet** (152 meters)
- Response time **15 minutes** maximum
- Storage height limit **15 feet** (4.6 meters)

---

## SECTION 10: RELATIONSHIPS AND RULES

### 10.1 Organizational Relationships
- **John Smith** reports to **Mary Johnson** at **Global Dynamics Corporation**
- **OSHA** oversees compliance at **Amazon Web Services, Inc.**
- **Dr. Michael O'Brien** collaborates with **Johns Hopkins University**
- **Jennifer Martinez** coordinates between **OSHA** and **EPA**
- **Microsoft Corporation** partners with **MIT** on research

### 10.2 Compliance Rules
1. All employees at **facilities over 10,000 square feet** must complete safety training within **30 days**
2. Companies with more than **$500,000** in federal contracts require additional certifications
3. Violations exceeding **$100,000** trigger automatic review by **Department of Labor**
4. International operations in **European Union** must comply with both **OSHA** and **ISO** standards
5. Any incident resulting in **3 or more** injuries requires reporting within **8 hours**

### 10.3 Financial Rules
- Fines increase by **10%** for each repeated violation
- Companies save approximately **$4** for every **$1** invested in safety
- Insurance premiums reduced by **15%** with perfect safety record
- Training investments over **$50,000** qualify for tax credits
- Penalties double if violations occur within **12 months**

---

## VALIDATION SUMMARY

**Expected Entity Counts:**
- PERSON: 25 unique individuals
- ORGANIZATION: 30 organizations (10 government, 15 companies, 5 educational)
- LOCATION: 20 locations (10 cities, 10 states/countries)
- GPE: 8 geopolitical entities
- DATE: 15 specific dates
- TIME: 8 specific times
- MONEY: 20 monetary amounts
- PERCENT: 15 percentages

**Additional Entities:**
- PHONE: 10 phone numbers
- REGULATION: 10 regulatory references
- URL: 5 web addresses
- MEASUREMENT: 20 measurements with units

**Total Core 8 Entities: 141**
**Total Additional Entities: 45**
**Grand Total: 186 entities**

---

## TEST VALIDATION RULES

1. **Person Detection Rule**: System should detect exactly 25 persons, including challenging names
2. **Role Extraction Rule**: Each person with a title should have role extracted
3. **Organization Linking Rule**: Persons should be linked to their mentioned organizations
4. **Money Normalization Rule**: All money amounts should be normalized to numeric values
5. **Date Parsing Rule**: All date formats should be correctly parsed
6. **Measurement Conversion Rule**: Measurements with dual units should link both values
7. **Regulation Identification Rule**: All regulatory references should be categorized
8. **Relationship Extraction Rule**: "reports to", "oversees", "partners with" relationships should be identified
9. **Compliance Rule Extraction**: Conditional statements with thresholds should be extracted as rules
10. **Span Accuracy Rule**: Each entity should have accurate character position spans

---

*End of Test Document - Version 1.0*
*This document contains controlled entity counts for validation purposes*