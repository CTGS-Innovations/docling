```json
{
  "entities": {
    "Organizations": [
      {
        "id": "org_osha",
        "canonical_name": "Occupational Safety and Health Administration",
        "aliases": ["OSHA"],
        "type": "regulatory_agency"
      },
      {
        "id": "org_dol",
        "canonical_name": "United States Department of Labor",
        "aliases": ["U.S. Department of Labor", "Dept. of Labor"],
        "type": "federal_agency"
      },
      {
        "id": "org_oshrc",
        "canonical_name": "Occupational Safety and Health Review Commission",
        "aliases": ["OSHRC"],
        "type": "review_commission"
      }
    ],
    "Standards": [
      {
        "id": "std_1926_1050_1060",
        "canonical_name": "29 CFR 1926.1050-1060",
        "type": "osha_standard"
      },
      {
        "id": "std_1926_451",
        "canonical_name": "29 CFR 1926.451 Subpart L",
        "type": "osha_standard"
      },
      {
        "id": "act_osh_1970",
        "canonical_name": "Occupational Safety and Health Act of 1970",
        "aliases": ["OSH Act of 1970"],
        "type": "federal_legislation"
      }
    ],
    "Equipment": {
      "Ladders": [
        {"id": "eq_portable", "canonical_name": "Portable Ladder"},
        {"id": "eq_stepladder", "canonical_name": "Stepladder"},
        {"id": "eq_fixed", "canonical_name": "Fixed Ladder"},
        {"id": "eq_jobmade", "canonical_name": "Job-made Ladder"},
        {"id": "eq_ext_trestle", "canonical_name": "Extension Trestle Ladder"},
        {"id": "eq_through_fixed", "canonical_name": "Through Fixed Ladder"},
        {"id": "eq_sidestep_fixed", "canonical_name": "Side-step Fixed Ladder"},
        {"id": "eq_parapet", "canonical_name": "Parapet Ladder"},
        {"id": "eq_double_cleat", "canonical_name": "Double-cleat Ladder"},
        {"id": "eq_single_cleat", "canonical_name": "Single-cleat Ladder"}
      ],
      "Stairways": [
        {"id": "eq_stair_temp", "canonical_name": "Temporary Stairway"},
        {"id": "eq_stair_perm", "canonical_name": "Permanent Stairway"}
      ],
      "Components": [
        {"id": "comp_rungs", "canonical_name": "Rungs"},
        {"id": "comp_cleats", "canonical_name": "Cleats"},
        {"id": "comp_side_rails", "canonical_name": "Side Rails"},
        {"id": "comp_cages", "canonical_name": "Cages"},
        {"id": "comp_wells", "canonical_name": "Wells"},
        {"id": "comp_safety_dev", "canonical_name": "Ladder Safety Devices"},
        {"id": "comp_grab_rails", "canonical_name": "Grab Rails"},
        {"id": "comp_handrails", "canonical_name": "Handrails"},
        {"id": "comp_stair_rails", "canonical_name": "Stair Rails"},
        {"id": "comp_midrails", "canonical_name": "Midrails"},
        {"id": "comp_platforms", "canonical_name": "Platforms"},
        {"id": "comp_treads", "canonical_name": "Treads"},
        {"id": "comp_risers", "canonical_name": "Risers"}
      ]
    },
    "Hazards": [
      {"id": "hz_falls", "canonical_name": "Falls"},
      {"id": "hz_slippery", "canonical_name": "Slippery Surfaces"},
      {"id": "hz_defective", "canonical_name": "Defective Ladders"},
      {"id": "hz_obstructions", "canonical_name": "Obstructions"}
    ],
    "Programs": [
      {"id": "prog_consult", "canonical_name": "Consultation Services"},
      {"id": "prog_vpp", "canonical_name": "Voluntary Protection Program (VPP)", "aliases": ["VPP"]},
      {"id": "prog_partnership", "canonical_name": "Strategic Partnership Program"},
      {"id": "prog_alliance", "canonical_name": "Alliance Program"},
      {"id": "prog_state_plans", "canonical_name": "State Plans"},
      {"id": "prog_sharp", "canonical_name": "Safety and Health Achievement Recognition Program (SHARP)", "aliases": ["SHARP"]},
      {"id": "prog_osha_institute", "canonical_name": "OSHA Training Institute"}
    ]
  },
  "relationships": [
    {"subject": "org_osha", "predicate": "issues", "object": "std_1926_1050_1060"},
    {"subject": "std_1926_1050_1060", "predicate": "applies_to", "object": ["eq_stair_temp", "eq_stair_perm", "eq_portable", "eq_fixed"]},
    {"subject": "org_osha", "predicate": "governed_by", "object": "act_osh_1970"},
    {"subject": "org_oshrc", "predicate": "reviews", "object": "osha_compliance_decisions"},
    {"subject": "hz_defective", "predicate": "affects", "object": "eq_portable"},
    {"subject": "prog_vpp", "predicate": "administered_by", "object": "org_osha"}
  ],
  "facts": [
    {
      "id": "fact_001",
      "subject": "Employers",
      "predicate": "must_provide",
      "object": "Stairway or ladder at all worker points of access",
      "condition": "Break in elevation ≥ 19 inches without ramp/runway/hoist",
      "source": "Page 3"
    },
    {
      "id": "fact_002",
      "subject": "Employers",
      "predicate": "must_keep_clear",
      "object": "Single point of access between levels",
      "condition": "If blocked, provide second point of access",
      "source": "Page 3"
    },
    {
      "id": "fact_003",
      "subject": "Employers",
      "predicate": "must_install",
      "object": "Stairway and ladder fall protection systems",
      "condition": "Before employees use them",
      "source": "Page 3"
    },
    {
      "id": "fact_004",
      "subject": "Ladders",
      "predicate": "must_be_free_of",
      "object": "Oil, grease, slipping hazards",
      "source": "Page 4"
    },
    {
      "id": "fact_005",
      "subject": "Ladders",
      "predicate": "must_not_be",
      "object": "Loaded beyond rated capacity",
      "source": "Page 4"
    },
    {
      "id": "fact_006",
      "subject": "Fixed Ladders",
      "predicate": "must_have",
      "object": "Ladder safety devices, lifelines, or cages/wells",
      "condition": "If total climb ≥ 24 feet",
      "source": "Page 5"
    },
    {
      "id": "fact_007",
      "subject": "Defective Ladders",
      "predicate": "must_be",
      "object": "Tagged 'Do Not Use' or withdrawn from service",
      "source": "Page 8"
    },
    {
      "id": "fact_008",
      "subject": "Stairways",
      "predicate": "must_be_installed",
      "object": "At 30°–50° from horizontal",
      "source": "Page 8"
    },
    {
      "id": "fact_009",
      "subject": "Stair Rail Systems",
      "predicate": "must_be",
      "object": "≥ 36 inches in height if installed after March 15, 1991",
      "source": "Page 9"
    },
    {
      "id": "fact_010",
      "subject": "Employers",
      "predicate": "must_train",
      "object": "Employees on fall hazards, proper stair/ladder use, load capacities",
      "source": "Page 10"
    }
  ]
}

```
