"""Observability module for logging, tracing, and metrics.

This module provides comprehensive observability features:
- Structured logging with multiple levels
- Distributed tracing for agent workflows
- Performance metrics collection
- Execution time tracking
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from pathlib import Path


class ObservabilityManager:
    """Manages logging, tracing, and metrics for the code review system."""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        """Initialize observability manager.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for log output
        """
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file
        self.traces: List[Dict] = []
        self.metrics: Dict[str, List[float]] = {}
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up structured logging configuration."""
        # Create logs directory if it doesn't exist
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=self.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.log_file) if self.log_file else logging.NullHandler()
            ]
        )
        
        # Get logger
        self.logger = logging.getLogger("CodeReview-AI-Agent")
        self.logger.setLevel(self.log_level)
        
        self.logger.info("Observability system initialized")
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific component.
        
        Args:
            name: Logger name (usually module name)
        
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    @contextmanager
    def trace_operation(self, operation_name: str, **metadata):
        """Context manager for tracing operations.
        
        Usage:
            with observability.trace_operation("code_analysis", language="python"):
                # perform operation
                pass
        
        Args:
            operation_name: Name of the operation
            **metadata: Additional metadata to log
        """
        trace_id = f"{operation_name}_{int(time.time() * 1000)}"
        start_time = time.time()
        
        trace_data = {
            'trace_id': trace_id,
            'operation': operation_name,
            'start_time': datetime.now().isoformat(),
            'metadata': metadata,
            'status': 'started'
        }
        
        self.logger.info(f"[TRACE] Starting: {operation_name}", extra={'trace_id': trace_id})
        
        try:
            yield trace_id
            
            # Operation succeeded
            duration = time.time() - start_time
            trace_data['status'] = 'success'
            trace_data['duration_seconds'] = duration
            trace_data['end_time'] = datetime.now().isoformat()
            
            self.traces.append(trace_data)
            self.record_metric(f"{operation_name}_duration", duration)
            
            self.logger.info(
                f"[TRACE] Completed: {operation_name} in {duration:.2f}s",
                extra={'trace_id': trace_id, 'duration': duration}
            )
            
        except Exception as e:
            # Operation failed
            duration = time.time() - start_time
            trace_data['status'] = 'error'
            trace_data['error'] = str(e)
            trace_data['duration_seconds'] = duration
            trace_data['end_time'] = datetime.now().isoformat()
            
            self.traces.append(trace_data)
            
            self.logger.error(
                f"[TRACE] Failed: {operation_name} after {duration:.2f}s - {str(e)}",
                extra={'trace_id': trace_id, 'error': str(e)},
                exc_info=True
            )
            
            raise
    
    def record_metric(self, metric_name: str, value: float):
        """Record a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append(value)
        self.logger.debug(f"[METRIC] {metric_name}: {value}")
    
    def get_metric_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric.
        
        Args:
            metric_name: Name of the metric
        
        Returns:
            Dictionary with min, max, avg, count
        """
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {'count': 0}
        
        values = self.metrics[metric_name]
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'total': sum(values)
        }
    
    def get_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all metrics.
        
        Returns:
            Dictionary of metric statistics
        """
        return {
            name: self.get_metric_stats(name)
            for name in self.metrics.keys()
        }
    
    def get_traces(self, status: Optional[str] = None) -> List[Dict]:
        """Get recorded traces, optionally filtered by status.
        
        Args:
            status: Optional status filter ('success', 'error', 'started')
        
        Returns:
            List of trace dictionaries
        """
        if status:
            return [t for t in self.traces if t['status'] == status]
        return self.traces
    
    def export_traces(self, filepath: str):
        """Export traces to a JSON file.
        
        Args:
            filepath: Path to save traces
        """
        with open(filepath, 'w') as f:
            json.dump(self.traces, f, indent=2)
        
        self.logger.info(f"Exported {len(self.traces)} traces to {filepath}")
    
    def export_metrics(self, filepath: str):
        """Export metrics to a JSON file.
        
        Args:
            filepath: Path to save metrics
        """
        metrics_data = {
            'metrics': self.get_all_metrics(),
            'raw_values': self.metrics,
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        self.logger.info(f"Exported metrics to {filepath}")
    
    def print_summary(self):
        """Print a summary of observability data."""
        print("\n" + "="*70)
        print("📊 Observability Summary")
        print("="*70)
        
        # Traces summary
        total_traces = len(self.traces)
        successful = len([t for t in self.traces if t['status'] == 'success'])
        failed = len([t for t in self.traces if t['status'] == 'error'])
        
        print(f"\n🔍 Traces:")
        print(f"   Total: {total_traces}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        
        # Metrics summary
        print(f"\n📈 Metrics:")
        for metric_name, stats in self.get_all_metrics().items():
            if stats['count'] > 0:
                print(f"   {metric_name}:")
                print(f"      Count: {stats['count']}")
                print(f"      Avg: {stats['avg']:.3f}")
                print(f"      Min: {stats['min']:.3f}")
                print(f"      Max: {stats['max']:.3f}")
        
        print("="*70)


# Global observability instance
_observability: Optional[ObservabilityManager] = None


def get_observability(log_level: str = "INFO", 
                     log_file: Optional[str] = "logs/code_review.log") -> ObservabilityManager:
    """Get or create the global observability manager.
    
    Args:
        log_level: Logging level
        log_file: Log file path
    
    Returns:
        ObservabilityManager instance
    """
    global _observability
    if _observability is None:
        _observability = ObservabilityManager(log_level, log_file)
    return _observability
