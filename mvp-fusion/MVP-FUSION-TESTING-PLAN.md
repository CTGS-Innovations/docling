# MVP-FUSION I/O + CPU SERVICE ARCHITECTURE IMPLEMENTATION

## **OBJECTIVE**
Transform MVP-Fusion from single-threaded `[Main]` processing to clean I/O + CPU service architecture with proper worker attribution and phase visibility.

## **CORE PRINCIPLES**
1. **Single Source of Truth**: One definitive implementation, no duplicates
2. **Clean Architecture**: I/O worker handles file operations, CPU workers handle processing
3. **Performance First**: Async queue between I/O and CPU, no blocking
4. **Clear Observability**: Phase-worker logging shows exactly what's happening where
5. **Service-Ready**: Deployable on edge locations with separated concerns

## **LOGGING ARCHITECTURE**

### **Phase-Worker Attribution Format:**
```
[PHASE-WORKER] module_name - Message (optional metrics)
```

### **Log Levels:**
- **STAGING-MAIN**: Service coordination, startup/shutdown, final results
- **CONVERSION-IO**: File reading, PDF conversion, markdown loading
- **QUEUE-IO**: Work queue operations with system metrics (queue, RAM, CPU)
- **CLASSIFICATION-CPU1/CPU2**: Document type detection, pattern loading
- **ENRICHMENT-CPU1/CPU2**: Entity enhancement, relationship processing
- **SEMANTICS-CPU1/CPU2**: Entity extraction, semantic analysis
- **WRITER-IO**: Disk persistence operations
- **INFO-MAIN**: System configuration, deployment profile

### **Target Flow Example (2 files):**
```
[INFO-MAIN] deployment_manager - Workers: 2, Memory: 6553MB
[STAGING-MAIN] service_processor - Starting I/O + CPU service: 1 I/O + 2 CPU workers
[CONVERSION-IO] service_processor - Converting PDF: Complex2.pdf
[QUEUE-IO] service_processor - Queued: Complex2.pdf (queue: 1/100, ram: 45%, cpu: 23%)
[CLASSIFICATION-CPU1] aho_corasick_engine - Loaded modular patterns: Domains 209
[SEMANTICS-CPU1] semantic_fact_extractor - Global entities: person:139, org:4, loc:2
[WRITER-IO] service_processor - Writing JSON knowledge: Complex2.json
[STAGING-MAIN] service_processor - Service processing complete: 2 results in 1.87s
```

## **IMPLEMENTATION CHECKLIST**

### **Phase 1: Logging Infrastructure**  READY TO IMPLEMENT
- [ ] Update `utils/logging_config.py` to support phase-worker format
- [ ] Add system metrics collection (psutil for RAM/CPU at queue handoffs)
- [ ] Test new logging format with simple example
- [ ] Verify worker thread name mapping works correctly

### **Phase 2: ServiceProcessor Integration** =Ë PLANNED
- [ ] Modify `fusion_cli.py` to use ServiceProcessor instead of FusionPipeline
- [ ] Update CLI to instantiate ServiceProcessor with config
- [ ] Route file processing through `process_files_service()` method
- [ ] Test basic I/O + CPU separation with sample files

### **Phase 3: Real Processing Integration** = DESIGN PHASE  
- [ ] Connect I/O worker to actual PDF conversion (not mock content)
- [ ] Connect CPU workers to real entity extraction pipeline
- [ ] Integrate with existing `knowledge/extractors/` modules
- [ ] Route classification through CPU workers properly

### **Phase 4: Queue Implementation** =Ê DESIGN PHASE
- [ ] Implement `WorkItem` dataclass for queue messages
- [ ] Add queue size monitoring and backpressure handling
- [ ] Implement system metrics at handoff points (queue, RAM, CPU)
- [ ] Add queue timeout and error handling

### **Phase 5: Testing & Validation** >ê TESTING PHASE
- [ ] Test with single file processing
- [ ] Test with batch processing (5+ files)
- [ ] Verify I/O worker shows in logs during PDF conversion
- [ ] Verify CPU workers show proper entity extraction
- [ ] Compare performance vs old pipeline

### **Phase 6: Cleanup** >ù CLEANUP PHASE
- [ ] Remove old FusionPipeline references once ServiceProcessor works
- [ ] Clean up any duplicate logging statements
- [ ] Update documentation and examples
- [ ] Verify no performance regressions

## **CURRENT STATUS**
- **Architecture Design**:  Complete
- **Logging Design**:  Complete  
- **Implementation**: = Ready to start Phase 1

## **CONCERNS & MITIGATIONS**

### **Performance Concerns**: L None
- Queue operations are O(1)
- System metrics are cached/non-blocking
- Async I/O + CPU is faster than sequential
- Only exposes existing bottlenecks

### **Complexity Concerns**:  Managed
- ServiceProcessor encapsulates all complexity
- Clear separation of concerns
- Existing CLI interface unchanged
- Fallback to old pipeline if needed

### **Integration Risk**:  Low
- Can test alongside existing pipeline
- Phase rollout reduces risk
- Worker attribution is additive
- No breaking changes to output

## **SUCCESS CRITERIA**
1.  **I/O worker visible** in logs during file operations
2.  **CPU workers visible** in logs during entity extraction  
3.  **System metrics** show queue health at handoffs
4.  **Performance maintained** or improved vs current pipeline
5.  **Clean logs** with no duplicate [Main] entries
6.  **Service architecture** ready for edge deployment

## **NEXT STEPS**
1. **Phase 1**: Implement logging infrastructure with phase-worker format
2. **Test**: Verify new logging with simple ServiceProcessor test
3. **Phase 2**: Replace FusionPipeline in main CLI
4. **Validate**: Ensure I/O worker shows during real processing