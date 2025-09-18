# MVP-FUSION DEVELOPMENT RULES

## CORE PRINCIPLE: SINGLE SOURCE OF TRUTH

### **Rule #1: No Redundant Files**
- One solution per problem
- No iterations, experiments, or "backup" implementations
- Delete replaced files immediately
- Clean, definitive implementations only

### **Rule #2: Clean Architecture**
- Pay setup costs once, not incrementally
- Initialization phase separate from processing
- Direct, minimal processing paths
- No nested abstractions or complex pipelines

### **Rule #3: Code Quality Standards**
- Well-commented, self-documenting code
- Clear variable names and function purposes  
- Production-ready, not experimental
- Single responsibility per class/function

### **Rule #4: Performance First**
- Every design decision optimized for speed
- Measure performance, don't assume
- Use proven patterns (like MVP-Hyper's approach)
- Eliminate overhead at every level

### **Rule #5: File Organization**
```
mvp-fusion/
├── ultra_fast_fusion.py     # THE solution (replaces pipeline/, fusion/)
├── fusion_cli.py           # Clean CLI interface
├── config/                 # Configuration only
└── CLAUDE.md              # These rules
```

### **Rule #9: Python Virtual Environment - MANDATORY**
**CRITICAL**: When working in `/home/corey/projects/docling/mvp-fusion/`:
- **ALWAYS** use the .venv-clean virtual environment for ALL Python commands
- **NEVER** run `python` directly - always use `source .venv-clean/bin/activate && python`
- This applies to: testing, running scripts, installing packages, debugging

**Examples:**
```bash
# ✅ CORRECT
cd /home/corey/projects/docling/mvp-fusion
source .venv-clean/bin/activate && python fusion_cli.py --help

# ❌ WRONG  
cd /home/corey/projects/docling/mvp-fusion
python fusion_cli.py --help
```

## IMPLEMENTATION GUIDELINES

### **Before Creating New Files:**
1. Can this be added to existing file?
2. Does this replace existing functionality?
3. Is this the definitive solution?
4. Will this create confusion or redundancy?

### **When Modifying Code:**
1. Update existing file, don't create new version
2. Remove replaced functionality immediately  
3. Maintain single source of truth
4. Comment why changes improve performance

### **Quality Gates:**
- No duplicate functionality across files
- No experimental or "temp" files in production
- Clear performance improvements documented
- Single, obvious entry point for each capability

### **Rule #7: Temporary File Naming Convention**
For testing, trials, and temporary code that will be removed:
- **Always append `_TMP` to filename**: `test_extraction_TMP.py`
- **Use for**: validation scripts, experimental code, testing utilities
- **Purpose**: Clear identification of files to be removed after testing
- **Cleanup**: Remove all `_TMP` files before production deployment

**Examples:**
```
✅ Good: validation_script_TMP.py, test_performance_TMP.py
❌ Bad: test.py, temp_file.py, experimental_code.py
```

---

## COMMUNICATION STYLE

### **Rule #6: Clear Decision Points**
When presenting options or asking questions:

🔴 **DECISION NEEDED** 🔴
- Use red blocks for critical decisions
- Put the question/action at the top, not buried in text
- Provide clear options (A, B, C)
- Make the call-to-action obvious

**Example:**
```
🔴 **DECISION NEEDED** 🔴
Should I implement X or Y approach?
Option A: Quick fix (5 min)
Option B: Full refactor (30 min)
```

### **Rule #8: CRITICAL - Stop and Discuss Before Pivoting**
When errors or failures occur:

🛑 **MANDATORY DISCUSSION BEFORE ACTION** 🛑
- **NEVER** immediately implement fixes or workarounds
- **STOP** and analyze the root problem first
- **DISCUSS** the issue and potential approaches with user
- **AVOID** hard pivots without consultation
- **ASK** before changing architecture or adding fallbacks

**Process:**
1. **Identify**: What exactly failed and why?
2. **Analyze**: What are the real options to fix it?
3. **Discuss**: Present options and get user direction
4. **Then** implement the chosen approach

**Critical Flaw to Avoid:**
❌ Error occurs → immediately implement fallback/fix
✅ Error occurs → stop → discuss → get direction → implement

### **Rule #10: Inline Test Documentation - MANDATORY**
When using Python `-c` commands for testing or debugging:

**ALWAYS** include a brief comment block at the top explaining:
- **GOAL**: What I'm trying to test
- **REASON**: Why I need to test this  
- **PROBLEM**: What I think might be wrong

**Example Format:**
```python
python -c "
# GOAL: Test if semantic fact extractor works after method fix
# REASON: Pipeline runs all stages but generates no JSON files
# PROBLEM: Missing _extract_entity_context method causing extractor to fail

# ... actual test code here ...
"
```

**Purpose**: User can read the comment to understand the test context when execution isn't visible.

---
**These rules prevent codebase clutter and maintain focus on performance and clarity.**