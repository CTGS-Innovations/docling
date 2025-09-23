# Clean Architecture Testing Instructions
## How to Test the New Processor System

### 📋 **Quick Start**

The new clean architecture is ready for testing! Here are the working commands:

```bash
# Test all processors with the entity extraction document
python test_architecture.py --test-all

# Compare processor performance 
python test_architecture.py --compare

# Benchmark person extraction (5 iterations)
python test_architecture.py --benchmark

# Test individual processors
python test_architecture.py --minimal      # Minimal baseline
python test_architecture.py --persons      # Person extraction only  
python test_architecture.py --flpc         # FLPC optimized
```

---

## 🎯 **Test Document**

**File**: `../cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md`

**Expected Entities** (Ground Truth):
- **PERSON**: 25 unique individuals  
- **ORGANIZATION**: 30 organizations
- **LOCATION**: 20 locations
- **GPE**: 8 geopolitical entities
- **DATE**: 15 specific dates
- **TIME**: 8 specific times
- **MONEY**: 20 monetary amounts
- **MEASUREMENT**: 20 measurements

**Total**: 146 entities across all types

---

## 🧪 **Available Processors**

### 1. **Minimal Baseline** (`--minimal`)
- **Purpose**: Speed baseline measurement
- **Expected**: <1ms processing, 0 entities
- **Use**: Measure pure overhead

### 2. **Fast Person Processor** (`--persons`) 
- **Purpose**: Person extraction only
- **Expected**: ~100ms processing, 25+ persons
- **Use**: Test person detection accuracy vs speed

### 3. **FLPC Optimized Processor** (`--flpc`)
- **Purpose**: Full entity extraction with FLPC
- **Expected**: <30ms processing (vs 425ms current)
- **Use**: Test complete replacement for ServiceProcessor

---

## 📊 **Performance Targets**

### Current Baseline (ServiceProcessor)
- **Document Processing Phase**: 425ms
- **Speed**: 254 pages/sec  
- **Status**: 🔴 **BOTTLENECK** (91% of total pipeline time)

### Target Performance (FLPC Optimized)
- **Document Processing Phase**: <30ms
- **Speed**: 3,600+ pages/sec
- **Improvement**: **14x faster**

---

## 🔍 **Testing Scenarios**

### **Scenario 1: Processor Comparison**
```bash
python test_architecture.py --compare
```

**What it tests**:
- All processors with same input document
- Performance ranking (fastest to slowest)
- Entity detection accuracy vs expected counts
- Speed improvement calculations

**Expected output**:
```
🏆 PERFORMANCE RANKING
🥇 Minimal Baseline: 0.01ms (990,099 pages/sec)
🥈 FLPC Optimized: 2.5ms (2,400 pages/sec) 
🥉 Fast Person: 102ms (59 pages/sec)
```

### **Scenario 2: Person Extraction Benchmark**
```bash
python test_architecture.py --benchmark --iterations 10
```

**What it tests**:
- Person detection accuracy (target: 25 persons)
- Processing speed consistency
- Comparison with 425ms baseline
- Target achievement (<30ms)

**Expected output**:
```
📊 BENCHMARK RESULTS:
   Average: 98.2ms
   Best: 89.5ms
   Worst: 105.1ms
   Persons: 27.0 average
   Target: <30ms (current baseline: 425ms)
   🟡 GOOD PROGRESS - Close to target
```

### **Scenario 3: Individual Processor Testing**
```bash
python test_architecture.py --flpc
```

**What it tests**:
- Single processor performance
- Entity extraction breakdown by type
- Success/failure status
- Detailed timing information

---

## 🎯 **Success Criteria**

### ✅ **Architecture Validation**
- [ ] All processors load successfully
- [ ] Same input/output format preserved  
- [ ] Performance tracking works
- [ ] Error handling works

### ✅ **Performance Targets**
- [ ] FLPC Optimized: <30ms processing
- [ ] Person Processor: 25+ persons detected
- [ ] Speed improvement: >10x vs 425ms baseline
- [ ] Entity accuracy: >80% of expected counts

### ✅ **A/B Testing**
- [ ] Can compare processors side-by-side
- [ ] Performance ranking works
- [ ] Configuration-based selection
- [ ] Easy to add new processors

---

## 🚀 **Expected Results**

Based on initial testing, you should see:

1. **Minimal Baseline**: <1ms (pure speed test)
2. **Person Processor**: ~100ms with 25+ persons (4x faster than current)
3. **FLPC Optimized**: <30ms with full entity extraction (14x faster)

### **Key Validation Points**:
- Person detection should find names like "John Smith", "Mary Johnson", "José García-López"
- Entity counts should approach expected ground truth values
- Processing times should be dramatically faster than 425ms baseline
- All processors should return same result format for compatibility

---

## 🔧 **Troubleshooting**

### Common Issues:

1. **Import Errors** (AC classifier not found):
   ```
   ⚠️ AhoCorasick classifier initialization failed
   ```
   **Solution**: This is expected - processors fall back to simpler extraction

2. **Document Not Found**:
   ```
   ⚠️ Test document not found, using simple content
   ```
   **Solution**: Verify path to entity extraction test document

3. **Zero Entities**:
   ```
   📊 Entities found: 0
   ```
   **Solution**: Normal for Minimal Baseline, check FLPC/Person processors

---

## 📈 **Integration Path**

Once testing validates performance:

1. **Phase 1**: Replace ServiceProcessor with FLPC Optimized in main pipeline
2. **Phase 2**: Add configuration-based processor selection  
3. **Phase 3**: A/B test in production with performance monitoring
4. **Phase 4**: Add custom processors for specific use cases

The clean architecture makes this integration safe and reversible!