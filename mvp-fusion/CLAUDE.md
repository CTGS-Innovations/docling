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

---
**These rules prevent codebase clutter and maintain focus on performance and clarity.**