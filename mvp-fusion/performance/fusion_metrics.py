#!/usr/bin/env python3
"""
Fusion Metrics - Performance Monitoring System
==============================================

Real-time performance tracking and analysis for MVP-Fusion pipeline.
Monitors all components and provides detailed performance insights.
"""

import time
import logging
import psutil
import threading
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time."""
    timestamp: float
    pages_per_sec: float
    chars_per_sec: float
    memory_usage_mb: float
    cpu_percent: float
    active_workers: int
    queue_size: int


class FusionMetrics:
    """
    Comprehensive performance monitoring for MVP-Fusion.
    
    Features:
    - Real-time performance tracking
    - Memory and CPU monitoring
    - Component-level metrics
    - Performance alerts
    - Historical data analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize metrics collection."""
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Monitoring configuration
        monitoring_config = config.get('monitoring', {})
        self.enable_realtime = monitoring_config.get('enable_realtime_monitoring', True)
        self.collect_timing = monitoring_config.get('collect_timing_metrics', True)
        self.collect_memory = monitoring_config.get('collect_memory_metrics', True)
        self.performance_alerts = monitoring_config.get('enable_performance_alerts', True)
        self.slowdown_threshold = monitoring_config.get('slowdown_threshold', 0.5)
        
        # Performance targets
        targets = config.get('performance', {})
        self.target_pages_per_sec = targets.get('target_pages_per_sec', 10000)
        self.target_memory_gb = targets.get('max_memory_usage_gb', 16)
        
        # Metrics storage
        self.metrics = defaultdict(float)
        self.counters = defaultdict(int)
        self.timings = defaultdict(list)
        self.snapshots = deque(maxlen=1000)  # Last 1000 snapshots
        
        # Component metrics
        self.component_metrics = {
            'fusion_engine': defaultdict(float),
            'aho_corasick': defaultdict(float),
            'flpc_engine': defaultdict(float),
            'pattern_router': defaultdict(float),
            'batch_processor': defaultdict(float),
            'pipeline': defaultdict(float)
        }
        
        # Monitoring thread
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Performance alerts
        self.alerts = []
        self.last_alert_time = {}
        
        # System monitoring
        self.process = psutil.Process()
        
        self.logger.info("Fusion metrics system initialized")
        
        if self.enable_realtime:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start real-time monitoring thread."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        self.logger.info("Real-time monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop running in background thread."""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                self._check_performance_alerts()
                time.sleep(1.0)  # Collect every second
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)  # Back off on error
    
    def _collect_system_metrics(self):
        """Collect system-level performance metrics."""
        try:
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.metrics['memory_usage_mb'] = memory_mb
            
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            self.metrics['cpu_percent'] = cpu_percent
            
            # System metrics
            system_memory = psutil.virtual_memory()
            self.metrics['system_memory_percent'] = system_memory.percent
            self.metrics['system_cpu_percent'] = psutil.cpu_percent()
            
            # Create snapshot
            snapshot = PerformanceSnapshot(
                timestamp=time.time(),
                pages_per_sec=self.metrics.get('pages_per_sec', 0),
                chars_per_sec=self.metrics.get('chars_per_sec', 0),
                memory_usage_mb=memory_mb,
                cpu_percent=cpu_percent,
                active_workers=self.metrics.get('active_workers', 0),
                queue_size=self.metrics.get('queue_size', 0)
            )
            
            self.snapshots.append(snapshot)
            
        except Exception as e:
            self.logger.warning(f"Failed to collect system metrics: {e}")
    
    def record_processing_time(self, component: str, operation: str, duration_ms: float):
        """Record processing time for a component operation."""
        if not self.collect_timing:
            return
        
        key = f"{component}_{operation}_time_ms"
        self.metrics[key] = duration_ms
        self.timings[key].append(duration_ms)
        
        # Keep only recent timings (last 100)
        if len(self.timings[key]) > 100:
            self.timings[key] = self.timings[key][-100:]
        
        # Update component metrics
        if component in self.component_metrics:
            self.component_metrics[component][f"{operation}_time_ms"] = duration_ms
            self.component_metrics[component][f"{operation}_count"] += 1
    
    def record_throughput(self, component: str, pages: int, chars: int, duration_seconds: float):
        """Record throughput metrics."""
        if duration_seconds <= 0:
            return
        
        pages_per_sec = pages / duration_seconds
        chars_per_sec = chars / duration_seconds
        
        self.metrics[f"{component}_pages_per_sec"] = pages_per_sec
        self.metrics[f"{component}_chars_per_sec"] = chars_per_sec
        self.metrics['pages_per_sec'] = pages_per_sec  # Global metric
        self.metrics['chars_per_sec'] = chars_per_sec  # Global metric
        
        # Update component metrics
        if component in self.component_metrics:
            self.component_metrics[component]['pages_per_sec'] = pages_per_sec
            self.component_metrics[component]['chars_per_sec'] = chars_per_sec
            self.component_metrics[component]['pages_processed'] += pages
            self.component_metrics[component]['chars_processed'] += chars
    
    def record_entity_extraction(self, component: str, entities_found: int, entity_types: int):
        """Record entity extraction metrics."""
        self.metrics[f"{component}_entities_found"] = entities_found
        self.metrics[f"{component}_entity_types"] = entity_types
        
        self.counters[f"{component}_total_entities"] += entities_found
        self.counters[f"{component}_extraction_calls"] += 1
        
        if component in self.component_metrics:
            self.component_metrics[component]['entities_found'] += entities_found
            self.component_metrics[component]['extraction_calls'] += 1
    
    def record_routing_decision(self, strategy: str, confidence: float, routing_time_ms: float):
        """Record pattern routing metrics."""
        self.counters[f"routing_{strategy}"] += 1
        self.counters['routing_decisions'] += 1
        
        self.metrics['routing_confidence'] = confidence
        self.metrics['routing_time_ms'] = routing_time_ms
        
        self.component_metrics['pattern_router']['decisions'] += 1
        self.component_metrics['pattern_router']['avg_confidence'] = (
            (self.component_metrics['pattern_router']['avg_confidence'] * 
             (self.component_metrics['pattern_router']['decisions'] - 1) + confidence) /
            self.component_metrics['pattern_router']['decisions']
        )
    
    def record_batch_processing(self, batch_size: int, processing_time_ms: float, 
                               parallel_workers: int):
        """Record batch processing metrics."""
        self.metrics['batch_size'] = batch_size
        self.metrics['batch_processing_time_ms'] = processing_time_ms
        self.metrics['active_workers'] = parallel_workers
        
        self.counters['batches_processed'] += 1
        self.counters['documents_in_batches'] += batch_size
        
        # Calculate batch efficiency
        theoretical_time = processing_time_ms * parallel_workers
        actual_time = processing_time_ms
        efficiency = min(1.0, theoretical_time / actual_time) if actual_time > 0 else 0
        
        self.metrics['batch_efficiency'] = efficiency
        self.component_metrics['batch_processor']['efficiency'] = efficiency
    
    def _check_performance_alerts(self):
        """Check for performance issues and generate alerts."""
        if not self.performance_alerts:
            return
        
        current_time = time.time()
        
        # Check pages per second
        current_pps = self.metrics.get('pages_per_sec', 0)
        if current_pps < self.target_pages_per_sec * self.slowdown_threshold:
            self._generate_alert(
                'performance_slowdown',
                f"Performance below target: {current_pps:.1f} pages/sec (target: {self.target_pages_per_sec})",
                current_time
            )
        
        # Check memory usage
        memory_gb = self.metrics.get('memory_usage_mb', 0) / 1024
        if memory_gb > self.target_memory_gb * 0.9:  # 90% of limit
            self._generate_alert(
                'high_memory_usage',
                f"High memory usage: {memory_gb:.1f} GB (limit: {self.target_memory_gb} GB)",
                current_time
            )
        
        # Check CPU usage
        cpu_percent = self.metrics.get('cpu_percent', 0)
        if cpu_percent > 95:
            self._generate_alert(
                'high_cpu_usage',
                f"High CPU usage: {cpu_percent:.1f}%",
                current_time
            )
    
    def _generate_alert(self, alert_type: str, message: str, timestamp: float):
        """Generate a performance alert."""
        # Rate limiting - don't spam alerts
        last_alert = self.last_alert_time.get(alert_type, 0)
        if timestamp - last_alert < 30:  # 30 second cooldown
            return
        
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': timestamp,
            'metrics_snapshot': dict(self.metrics)
        }
        
        self.alerts.append(alert)
        self.last_alert_time[alert_type] = timestamp
        
        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        self.logger.warning(f"Performance Alert [{alert_type}]: {message}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            'timestamp': time.time(),
            'global_metrics': dict(self.metrics),
            'counters': dict(self.counters),
            'component_metrics': {k: dict(v) for k, v in self.component_metrics.items()},
            'recent_alerts': self.alerts[-10:] if self.alerts else []
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary with key metrics."""
        # Calculate averages from recent snapshots
        recent_snapshots = list(self.snapshots)[-60:]  # Last 60 seconds
        
        if recent_snapshots:
            avg_pps = sum(s.pages_per_sec for s in recent_snapshots) / len(recent_snapshots)
            avg_memory = sum(s.memory_usage_mb for s in recent_snapshots) / len(recent_snapshots)
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
        else:
            avg_pps = self.metrics.get('pages_per_sec', 0)
            avg_memory = self.metrics.get('memory_usage_mb', 0)
            avg_cpu = self.metrics.get('cpu_percent', 0)
        
        return {
            'performance': {
                'current_pages_per_sec': self.metrics.get('pages_per_sec', 0),
                'avg_pages_per_sec_1min': avg_pps,
                'target_pages_per_sec': self.target_pages_per_sec,
                'performance_ratio': avg_pps / self.target_pages_per_sec if self.target_pages_per_sec > 0 else 0
            },
            'resource_usage': {
                'memory_usage_mb': avg_memory,
                'memory_usage_gb': avg_memory / 1024,
                'cpu_percent': avg_cpu,
                'target_memory_gb': self.target_memory_gb
            },
            'processing_stats': {
                'total_documents': self.counters.get('documents_in_batches', 0),
                'total_batches': self.counters.get('batches_processed', 0),
                'total_entities': self.counters.get('fusion_engine_total_entities', 0),
                'routing_decisions': self.counters.get('routing_decisions', 0)
            },
            'engine_performance': {
                'aho_corasick_calls': self.counters.get('aho_corasick_extraction_calls', 0),
                'flpc_calls': self.counters.get('flpc_engine_extraction_calls', 0),
                'routing_accuracy': self.component_metrics['pattern_router'].get('avg_confidence', 0)
            },
            'alerts': {
                'total_alerts': len(self.alerts),
                'recent_alerts': len([a for a in self.alerts if time.time() - a['timestamp'] < 300])  # Last 5 min
            }
        }
    
    def export_metrics(self, filepath: str):
        """Export all metrics to JSON file."""
        export_data = {
            'export_timestamp': time.time(),
            'config': self.config,
            'current_metrics': self.get_current_metrics(),
            'performance_summary': self.get_performance_summary(),
            'snapshots': [asdict(s) for s in list(self.snapshots)],
            'timing_history': {k: list(v) for k, v in self.timings.items()},
            'alerts_history': self.alerts
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Metrics exported to {filepath}")
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        self.metrics.clear()
        self.counters.clear()
        self.timings.clear()
        self.snapshots.clear()
        self.alerts.clear()
        self.last_alert_time.clear()
        
        for component_metrics in self.component_metrics.values():
            component_metrics.clear()
        
        self.logger.info("All metrics reset")
    
    def __del__(self):
        """Cleanup on destruction."""
        self.stop_monitoring()


if __name__ == "__main__":
    # Simple test
    config = {
        'monitoring': {
            'enable_realtime_monitoring': True,
            'enable_performance_alerts': True
        },
        'performance': {
            'target_pages_per_sec': 10000
        }
    }
    
    metrics = FusionMetrics(config)
    
    # Simulate some metrics
    metrics.record_processing_time('fusion_engine', 'classification', 5.2)
    metrics.record_throughput('pipeline', 100, 50000, 0.1)
    metrics.record_entity_extraction('fusion_engine', 25, 8)
    metrics.record_routing_decision('hybrid', 0.85, 1.2)
    
    print("Fusion Metrics Test:")
    print("Current metrics:", metrics.get_current_metrics())
    print("Performance summary:", metrics.get_performance_summary())
    
    # Test export
    metrics.export_metrics('/tmp/test_metrics.json')
    print("Metrics exported to /tmp/test_metrics.json")
    
    metrics.stop_monitoring()