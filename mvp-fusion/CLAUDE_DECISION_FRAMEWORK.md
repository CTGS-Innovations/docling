# PROBLEM-STRATEGY-RATING DECISION FRAMEWORK
## Mandatory Rule for Solution Decision Making

### 🚨 **WHEN TO USE THIS FRAMEWORK**
- Before proposing ANY technical solution
- When multiple implementation approaches exist
- When user has provided explicit strategy/constraints
- Before making architectural decisions

### 📋 **MANDATORY 3-STEP PROCESS**

#### **STEP 1: STATE THE CURRENT PROBLEM**
```
PROBLEM:
- What specific issue are we trying to solve?
- What evidence shows this is broken?
- What are the symptoms/manifestations?
- What is the scope and impact?
```

#### **STEP 2: RESTATE THE CURRENT STRATEGY**
```
STRATEGY:
- What approach did the user specify?
- What are the explicit constraints/requirements?
- What should NOT be changed/touched?
- What is the preferred implementation order?
- What are the success criteria?
```

#### **STEP 3: RATE OPTIONS AGAINST STRATEGY**
```
OPTION EVALUATION:

Option A: [Description]
- Alignment with Strategy: ✅/❌
- Reasoning: [How it supports/contradicts strategy]
- Score: [High/Medium/Low]

Option B: [Description]  
- Alignment with Strategy: ✅/❌
- Reasoning: [How it supports/contradicts strategy]
- Score: [High/Medium/Low]

WINNER: [Option with highest score that follows strategy]
RATIONALE: [Why this option best serves the strategy]
```

### 🚫 **FORBIDDEN ACTIONS**
- Proposing solutions that contradict stated strategy
- Offering "better alternatives" to user's explicit approach
- Prioritizing "industry best practices" over user strategy
- Making changes to working systems without explicit permission

### ✅ **SUCCESS CRITERIA**
- Chosen solution directly implements user's strategy
- No working functionality is broken or modified
- Implementation follows user's specified order/constraints
- Solution addresses the problem without scope creep

### 📝 **EXAMPLE APPLICATION**

**PROBLEM**: Range detection inconsistency - `30-37 inches` missed while `76-94 cm` detected

**STRATEGY**: 
- Keep existing DATE/TIME/MONEY/MEASUREMENT detection working
- Add post-processing to identify ranges from detected entities
- Preserve processing order: DATE → TIME → MONEY → MEASUREMENT
- Do not modify working pattern detection

**OPTION EVALUATION**:

Option A: Modify FLPC patterns to detect ranges directly
- Alignment with Strategy: ❌
- Reasoning: Contradicts "keep existing detection working" and "post-processing" directive
- Score: Low

Option B: Add post-processing normalization to link detected entities into ranges
- Alignment with Strategy: ✅
- Reasoning: Preserves working detection, adds post-processing exactly as specified
- Score: High

**WINNER**: Option B
**RATIONALE**: Only option that follows the explicit strategy of post-processing enhancement

### 🎯 **ENFORCEMENT**
This framework must be used before proposing any solution. Failure to follow this process leads to:
- Misaligned solutions
- Broken working functionality  
- Wasted development time
- Loss of user confidence

### 📊 **BENEFITS**
- Forces alignment with user strategy
- Prevents scope creep and feature drift
- Ensures working systems remain intact
- Creates objective decision criteria
- Eliminates personal bias in solution selection