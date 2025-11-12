"""
OTE Decorators - Easy Integration

LOCATION: app/utils/decorators.py
PURPOSE: Decorators for applying OTE principles

DECORATORS:
    @observe: Add observability logging
    @traceable: Add traceability markers
    @evaluate: Add performance metrics
    
USAGE:
    from app.utils.decorators import observe, evaluate
    
    @observe("user_save")
    @evaluate
    def save_user(user_id, data):
        # Function automatically gets:
        # - Entry/exit logging
        # - Execution timing
        # - Error tracking
        # - Performance metrics
        pass
"""

import time
import functools
from typing import Callable, Any
from datetime import datetime

from app.utils.ote_logger import get_logger
from app.utils.metrics import metrics_tracker


def observe(operation_name: str = None, log_args: bool = False, log_result: bool = False):
    """
    Decorator for observability (O in OTE).
    
    Logs function entry, exit, duration, and exceptions.
    Provides complete visibility into function execution.
    
    Args:
        operation_name: Name for operation (defaults to function name)
        log_args: Whether to log function arguments
        log_result: Whether to log return value
        
    Example:
        >>> @observe("save_user", log_args=True)
        ... def save_user(user_id: int, data: dict):
        ...     return {"success": True}
        
        # Logs:
        # ⏱️  START [2024-11-12 11:30:45] save_user
        # ✅ END [2024-11-12 11:30:46] save_user (Duration: 0.523s)
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            start_timestamp = datetime.now().isoformat()
            
            # Log entry
            entry_msg = f"⏱️  START [{start_timestamp}] {op_name}"
            if log_args:
                entry_msg += f" | args={args} kwargs={kwargs}"
            logger.info(entry_msg)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log success
                duration = time.time() - start_time
                end_msg = (
                    f"✅ END [{datetime.now().isoformat()}] {op_name} "
                    f"(Duration: {duration:.3f}s)"
                )
                if log_result:
                    end_msg += f" | result={result}"
                logger.info(end_msg)
                
                return result
                
            except Exception as e:
                # Log failure
                duration = time.time() - start_time
                logger.error(
                    f"❌ FAILED [{datetime.now().isoformat()}] {op_name} "
                    f"(Duration: {duration:.3f}s) | Error: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


def traceable(trace_points: bool = True):
    """
    Decorator for traceability (T in OTE).
    
    Adds trace markers at function entry and exit.
    Helps track code execution flow during debugging.
    
    Args:
        trace_points: Whether to log trace markers
        
    Example:
        >>> @traceable()
        ... def process_data(data):
        ...     # Your code here
        ...     return result
        
        # Logs:
        # TRACE:ENTER:process_data → Starting execution
        # TRACE:EXIT:process_data → Completed successfully
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        func_name = func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if trace_points:
                logger.trace(f"ENTER:{func_name}", "Starting execution")
            
            try:
                result = func(*args, **kwargs)
                
                if trace_points:
                    logger.trace(f"EXIT:{func_name}", "Completed successfully")
                
                return result
                
            except Exception as e:
                if trace_points:
                    logger.trace(
                        f"ERROR:{func_name}",
                        f"Failed with error: {str(e)}"
                    )
                raise
        
        return wrapper
    return decorator


def evaluate(track_performance: bool = True, 
             detect_anomalies: bool = False):
    """
    Decorator for evaluation (E in OTE).
    
    Records performance metrics for optimization and comparison.
    Can detect anomalies in function performance.
    
    Args:
        track_performance: Whether to track metrics
        detect_anomalies: Whether to check for anomalies
        
    Example:
        >>> @evaluate(track_performance=True)
        ... def expensive_operation():
        ...     # Function execution is timed
        ...     # Metrics are recorded automatically
        ...     pass
        
        # Later:
        >>> from app.utils import metrics_tracker
        >>> report = metrics_tracker.get_report()
        >>> print(report["expensive_operation"]["avg_time"])
        2.543s
    """
    def decorator(func: Callable) -> Callable:
        func_name = func.__name__
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
                
            except Exception as e:
                success = False
                raise
                
            finally:
                if track_performance:
                    duration = time.time() - start_time
                    metrics_tracker.record(func_name, duration, success)
                    
                    # Log metrics
                    logger.observe(func_name, duration=duration, success=success)
                    
                    # Detect anomalies if enabled
                    if detect_anomalies:
                        anomalies = metrics_tracker.detect_anomalies()
                        for anomaly in anomalies:
                            if func_name in anomaly:
                                logger.warning(f"ANOMALY DETECTED: {anomaly}")
        
        return wrapper
    return decorator


def ote_complete(operation_name: str = None):
    """
    Decorator combining all OTE principles.
    
    Applies @observe, @traceable, and @evaluate in one decorator.
    Use this for critical functions that need full OTE coverage.
    
    Args:
        operation_name: Name for operation (defaults to function name)
        
    Example:
        >>> @ote_complete("critical_save")
        ... def save_important_data(data):
        ...     # Gets full OTE coverage:
        ...     # - Observable logging
        ...     # - Trace markers
        ...     # - Performance metrics
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        # Apply all OTE decorators
        func = observe(operation_name)(func)
        func = traceable()(func)
        func = evaluate()(func)
        return func
    return decorator


def retry_with_trace(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator to retry failed operations with trace logging.
    
    Useful for operations that may fail temporarily (network, database).
    Logs each attempt with trace markers.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Delay between retries in seconds
        
    Example:
        >>> @retry_with_trace(max_attempts=3, delay=2.0)
        ... def call_external_api():
        ...     # Will retry up to 3 times if it fails
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        func_name = func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.trace(
                        f"RETRY:{func_name}",
                        f"Attempt {attempt}/{max_attempts}"
                    )
                    
                    result = func(*args, **kwargs)
                    
                    if attempt > 1:
                        logger.info(
                            f"✅ {func_name} succeeded on attempt {attempt}/{max_attempts}"
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"⚠️  {func_name} failed on attempt {attempt}/{max_attempts}: {str(e)}"
                    )
                    
                    if attempt < max_attempts:
                        logger.trace(
                            f"RETRY:{func_name}",
                            f"Waiting {delay}s before retry"
                        )
                        time.sleep(delay)
            
            # All attempts failed
            logger.error(
                f"❌ {func_name} failed after {max_attempts} attempts"
            )
            raise last_exception
        
        return wrapper
    return decorator
