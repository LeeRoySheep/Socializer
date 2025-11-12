"""
Performance Metrics - Evaluation Component

LOCATION: app/utils/metrics.py
PURPOSE: Track and evaluate system performance

PRINCIPLE: Evaluation (E in OTE)
    - Record operation metrics
    - Calculate success rates
    - Identify performance issues
    - Enable comparison and optimization

USAGE:
    from app.utils import metrics_tracker
    
    metrics_tracker.record("operation_name", duration=0.5, success=True)
    report = metrics_tracker.get_report()
    anomalies = metrics_tracker.detect_anomalies()
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
from statistics import mean, stdev


@dataclass
class OperationMetrics:
    """
    Metrics for a single operation type.
    
    Attributes:
        operation: Operation name
        count: Total executions
        successes: Successful executions
        failures: Failed executions
        total_time: Total execution time
        avg_time: Average execution time
        min_time: Minimum execution time
        max_time: Maximum execution time
        std_dev: Standard deviation of execution times
        success_rate: Percentage of successful executions
    """
    operation: str
    count: int = 0
    successes: int = 0
    failures: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    std_dev: float = 0.0
    success_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'operation': self.operation,
            'calls': self.count,
            'successes': self.successes,
            'failures': self.failures,
            'avg_time': f"{self.avg_time:.3f}s",
            'min_time': f"{self.min_time:.3f}s",
            'max_time': f"{self.max_time:.3f}s",
            'total_time': f"{self.total_time:.3f}s",
            'success_rate': f"{self.success_rate:.1f}%",
            'std_dev': f"{self.std_dev:.3f}s" if self.count > 1 else "N/A"
        }


class PerformanceMetrics:
    """
    Track performance metrics for evaluation.
    
    Tracks execution time, success/failure rates, and other metrics
    for all operations. Enables performance comparison and
    anomaly detection.
    
    Attributes:
        metrics (Dict[str, OperationMetrics]): Metrics by operation name
        detailed_times (Dict[str, List[float]]): All execution times
        
    Example:
        >>> tracker = PerformanceMetrics()
        >>> tracker.record("save_user", duration=0.5, success=True)
        >>> tracker.record("save_user", duration=0.3, success=True)
        >>> report = tracker.get_report()
        >>> print(report["save_user"]["avg_time"])
        0.400s
    """
    
    def __init__(self):
        """Initialize metrics tracker."""
        self.metrics: Dict[str, OperationMetrics] = defaultdict(
            lambda: OperationMetrics(operation="")
        )
        self.detailed_times: Dict[str, List[float]] = defaultdict(list)
        self.start_time = datetime.now()
    
    def record(self, operation: str, duration: float, success: bool = True, 
               **extra_metrics):
        """
        Record operation execution metrics.
        
        Args:
            operation: Operation name
            duration: Execution time in seconds
            success: Whether operation succeeded
            **extra_metrics: Additional metrics to store
            
        Example:
            >>> tracker.record("db_query", duration=0.25, success=True, rows=100)
        """
        m = self.metrics[operation]
        
        # Update operation name if first entry
        if m.count == 0:
            m.operation = operation
        
        # Update counts
        m.count += 1
        if success:
            m.successes += 1
        else:
            m.failures += 1
        
        # Update time metrics
        m.total_time += duration
        m.min_time = min(m.min_time, duration)
        m.max_time = max(m.max_time, duration)
        
        # Store for statistics
        self.detailed_times[operation].append(duration)
        
        # Calculate statistics
        times = self.detailed_times[operation]
        m.avg_time = mean(times)
        if len(times) > 1:
            m.std_dev = stdev(times)
        
        # Calculate success rate
        m.success_rate = (m.successes / m.count) * 100
    
    def get_report(self, operation: Optional[str] = None) -> Dict[str, Dict]:
        """
        Get metrics report.
        
        Args:
            operation: Specific operation to report on (None for all)
            
        Returns:
            Dictionary of metrics by operation name
            
        Example:
            >>> report = tracker.get_report()
            >>> print(report["save_user"]["avg_time"])
            0.450s
        """
        if operation:
            if operation not in self.metrics:
                return {}
            return {operation: self.metrics[operation].to_dict()}
        
        return {
            op: metrics.to_dict()
            for op, metrics in self.metrics.items()
        }
    
    def detect_anomalies(self, 
                        error_threshold: float = 0.1,
                        slow_threshold: float = 5.0) -> List[str]:
        """
        Detect performance anomalies (bug finding).
        
        Args:
            error_threshold: Error rate threshold (0.1 = 10%)
            slow_threshold: Slow operation threshold in seconds
            
        Returns:
            List of anomaly descriptions
            
        Example:
            >>> anomalies = tracker.detect_anomalies()
            >>> for anomaly in anomalies:
            ...     print(anomaly)
            ⚠️  HIGH ERROR RATE in save_preference: 15.5% (threshold: 10%)
            🐌 SLOW OPERATION db_query: 6.2s (threshold: 5s)
        """
        anomalies = []
        
        for operation, m in self.metrics.items():
            # Check error rate
            error_rate = m.failures / m.count if m.count > 0 else 0
            if error_rate > error_threshold:
                anomalies.append(
                    f"⚠️  HIGH ERROR RATE in {operation}: "
                    f"{error_rate*100:.1f}% (threshold: {error_threshold*100:.0f}%)"
                )
            
            # Check slow operations
            if m.avg_time > slow_threshold:
                anomalies.append(
                    f"🐌 SLOW OPERATION {operation}: "
                    f"{m.avg_time:.2f}s (threshold: {slow_threshold:.0f}s)"
                )
            
            # Check high variance (inconsistent performance)
            if m.count > 5 and m.std_dev > m.avg_time:
                anomalies.append(
                    f"📊 HIGH VARIANCE in {operation}: "
                    f"std_dev={m.std_dev:.2f}s > avg={m.avg_time:.2f}s"
                )
        
        return anomalies
    
    def compare(self, other: 'PerformanceMetrics') -> Dict[str, Dict[str, Any]]:
        """
        Compare metrics with another tracker (optimization comparison).
        
        Args:
            other: Another PerformanceMetrics instance
            
        Returns:
            Dictionary showing differences
            
        Example:
            >>> before = PerformanceMetrics()
            >>> # ... record metrics ...
            >>> after = PerformanceMetrics()
            >>> # ... record new metrics ...
            >>> comparison = before.compare(after)
            >>> print(comparison["save_user"]["improvement"])
            25.0%  # 25% faster
        """
        comparison = {}
        
        # Find common operations
        common_ops = set(self.metrics.keys()) & set(other.metrics.keys())
        
        for op in common_ops:
            old_m = self.metrics[op]
            new_m = other.metrics[op]
            
            # Calculate improvements
            time_diff = new_m.avg_time - old_m.avg_time
            time_improvement = -(time_diff / old_m.avg_time) * 100 if old_m.avg_time > 0 else 0
            
            success_diff = new_m.success_rate - old_m.success_rate
            
            comparison[op] = {
                'old_avg_time': f"{old_m.avg_time:.3f}s",
                'new_avg_time': f"{new_m.avg_time:.3f}s",
                'time_change': f"{time_diff:+.3f}s",
                'improvement': f"{time_improvement:+.1f}%",
                'old_success_rate': f"{old_m.success_rate:.1f}%",
                'new_success_rate': f"{new_m.success_rate:.1f}%",
                'success_change': f"{success_diff:+.1f}%",
            }
        
        return comparison
    
    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()
        self.detailed_times.clear()
        self.start_time = datetime.now()
    
    def uptime(self) -> float:
        """Get tracker uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


# Global metrics tracker instance
metrics_tracker = PerformanceMetrics()


def get_metrics_report() -> Dict[str, Dict]:
    """
    Get global metrics report.
    
    Returns:
        Dictionary of all tracked metrics
    """
    return metrics_tracker.get_report()


def detect_issues() -> List[str]:
    """
    Detect performance issues in global metrics.
    
    Returns:
        List of detected anomalies
    """
    return metrics_tracker.detect_anomalies()
