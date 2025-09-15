# High-Performance NLP Benchmark Plan
## Based on AI Recommendations for 1000+ pages/sec Target

**Current Status:** Enhanced regex achieved 670 pages/sec, spaCy only 15.5 pages/sec  
**Target:** 1000+ pages/sec for entity extraction from markdown documents  
**Use Case:** OSHA/safety documents, standards, organizations, measurements  

---

## **Priority 1: Exact-term (Gazetteer) Matchers**
*Best for: Organizations, standards (OSHA, CFR, ISO), chemical names*

| Library | Priority | Expected Performance | Installation | Benchmark Order |
|---------|----------|---------------------|--------------|-----------------|
| **pyahocorasick** | 🟢 HIGH | 2000+ pages/sec | `pip install pyahocorasick` | **#1** |
| **marisa-trie** | 🟢 HIGH | 1500+ pages/sec | `pip install marisa-trie` | **#2** |
| **flashtext2** | 🟡 MED | 1200+ pages/sec | `pip install flashtext` | **#3** |

### Why These First:
- Perfect for our OSHA standards lists (CFR 1926.95, ISO 9001, etc.)
- Organization dictionaries (Department of Labor, OSHA, etc.)
- Chemical entity gazetteers (asbestos, benzene, formaldehyde)
- Pre-compiled dictionaries = instant startup

---

## **Priority 2: Pattern Engines (Regex Replacement)**
*Best for: emails, URLs, measurements, citations, requirements language*

| Library | Priority | Expected Performance | Installation | Benchmark Order |
|---------|----------|---------------------|--------------|-----------------|
| **Hyperscan/Vectorscan** | 🟢 HIGH | 3000+ pages/sec | `pip install hyperscan` | **#4** |
| **RE2 (pyre2)** | 🟢 HIGH | 1800+ pages/sec | `pip install pyre2` | **#5** |

### Why These:
- Replace our current regex patterns with SIMD-optimized engines
- Multi-regex compilation (compile once, scan thousands of times)
- Perfect for our requirements patterns ("must", "shall", "required to")

---

## **Priority 3: Tokenization/Windowing**
*Best for: relationship extraction, sentence-level analysis*

| Library | Priority | Expected Performance | Installation | Benchmark Order |
|---------|----------|---------------------|--------------|-----------------|
| **BlingFire** | 🟡 MED | 2500+ pages/sec | `pip install blingfire` | **#6** |

### Why This:
- Extremely fast tokenization for windowed relationship extraction
- Find "OSHA requires safety training" relationships
- Minimal overhead compared to spaCy tokenization

---

## **Priority 4: Sidecar Binaries (Ultimate Performance)**
*Best for: maximum speed when Python overhead is the bottleneck*

| Tool | Priority | Expected Performance | Installation | Benchmark Order |
|------|----------|---------------------|--------------|-----------------|
| **ripgrep (rg)** | 🟢 HIGH | 5000+ pages/sec | System package | **#7** |
| **ugrep** | 🟡 MED | 4000+ pages/sec | Compile from source | **#8** |

### Why These:
- Bypass Python overhead entirely
- JSON output for easy parsing
- Best for massive gazetteer lists
- Can process files in parallel

---

## **Benchmark Execution Plan**

### **Phase 1: Quick Wins (Libraries #1-3)**
Test gazetteer matchers with our existing entity lists:
```python
# Test with OSHA standards dictionary
osha_standards = ["CFR 1926.95", "OSHA 3162", "ISO 9001", "ANSI Z87.1", ...]
organizations = ["Department of Labor", "OSHA", "EPA", "CDC", ...]
chemicals = ["asbestos", "benzene", "lead", "silica", ...]
```

### **Phase 2: Pattern Engines (Libraries #4-5)**
Replace our regex patterns with optimized engines:
```python
# Compile once, use thousands of times
requirements_patterns = [r"\b(must|shall|required to)\s+\w+", ...]
measurement_patterns = [r"\d+\s*(percent|hours|days)", ...]
email_patterns = [r"\b[\w.-]+@[\w.-]+\.\w+\b", ...]
```

### **Phase 3: Advanced (Libraries #6-8)**
Test tokenization and sidecar approaches for maximum performance.

---

## **Success Criteria**

| Performance Tier | Pages/Sec | Memory Usage | Use Case |
|------------------|-----------|--------------|----------|
| 🎯 **Target Met** | 1000+ | < 500MB | Real-time classification |
| 🚀 **Exceeded** | 2000+ | < 500MB | High-throughput processing |
| ⚡ **Ultimate** | 5000+ | < 1GB | Batch processing mode |

---

## **Expected Results Prediction**

Based on our current 670 pages/sec with basic regex:

1. **pyahocorasick**: Should easily hit 1500+ pages/sec for dictionary lookups
2. **Hyperscan**: Should achieve 2000+ pages/sec for pattern matching  
3. **ripgrep sidecar**: Could reach 3000-5000+ pages/sec for combined processing

**Bottom Line:** We should be able to **exceed our 1000+ pages/sec target** with the right combination of these tools.

---

## **Implementation Strategy**

1. **Start with #1-2**: Quick wins with gazetteer matching
2. **Combine approaches**: Use pyahocorasick for dictionaries + Hyperscan for patterns
3. **Measure carefully**: Track both throughput and entity quality
4. **Optimize iteratively**: Fine-tune based on real performance data

This should give us a **much better foundation** for the FutureState enhanced classification than any deep learning approach!