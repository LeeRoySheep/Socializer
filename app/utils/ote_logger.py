"""
OTE Logger - Observability, Traceability, Evaluation

LOCATION: app/utils/ote_logger.py
PURPOSE: Comprehensive logging following OTE principles

PRINCIPLES:
    O - Observability: All operations logged with timestamps and context
    T - Traceability: Clear paths through code with trace markers
    E - Evaluation: Performance metrics for optimization

USAGE:
    from app.utils import OTELogger, get_logger
    
    logger = get_logger(__name__)
    logger.info("Operation started")
    logger.trace("TRACE_POINT_1", "Validation complete")
    logger.observe("operation_name", duration=0.5, success=True)
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class OTELogger:
    """
    Logger implementing OTE principles.
    
    Provides enhanced logging with:
    - Timestamps on all messages (Observability)
    - Trace markers for debugging (Traceability)  
    - Operation metrics (Evaluation)
    
    Attributes:
        name (str): Logger name (usually module name)
        logger (logging.Logger): Underlying Python logger
        trace_enabled (bool): Whether to log trace messages
        
    Example:
        >>> logger = OTELogger("my_module")
        >>> logger.info("Starting process")
        [2024-11-12 11:30:45] INFO [my_module] Starting process
        
        >>> logger.trace("VALIDATE", "Input validated successfully")
        [2024-11-12 11:30:45] DEBUG [my_module] TRACE:VALIDATE → Input validated successfully
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize OTE logger.
        
        Args:
            name: Logger name (typically __name__ of module)
            level: Logging level (default: INFO)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.trace_enabled = True
        
        # Create formatter with timestamp
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def debug(self, message: str, **context):
        """
        Log debug message with context.
        
        Args:
            message: Debug message
            **context: Additional context to log
        """
        if context:
            message = f"{message} | {self._format_context(context)}"
        self.logger.debug(message)
    
    def info(self, message: str, **context):
        """
        Log info message with context.
        
        Args:
            message: Info message  
            **context: Additional context to log
        """
        if context:
            message = f"{message} | {self._format_context(context)}"
        self.logger.info(message)
    
    def warning(self, message: str, **context):
        """
        Log warning message with context.
        
        Args:
            message: Warning message
            **context: Additional context to log
        """
        if context:
            message = f"{message} | {self._format_context(context)}"
        self.logger.warning(message)
    
    def error(self, message: str, **context):
        """
        Log error message with context.
        
        Args:
            message: Error message
            **context: Additional context to log
        """
        if context:
            message = f"{message} | {self._format_context(context)}"
        self.logger.error(message)
    
    def trace(self, trace_point: str, message: str, **context):
        """
        Log trace message for debugging code paths (Traceability).
        
        Trace messages help follow execution flow during debugging.
        Format: TRACE:{trace_point} → {message}
        
        Args:
            trace_point: Name of trace point (e.g., "VALIDATE", "DB_SAVE")
            message: What happened at this trace point
            **context: Additional context
            
        Example:
            >>> logger.trace("VALIDATE", "User input validated", user_id=123)
            [2024-11-12 11:30:45] DEBUG [module] TRACE:VALIDATE → User input validated | user_id=123
        """
        if not self.trace_enabled:
            return
        
        trace_msg = f"TRACE:{trace_point} → {message}"
        if context:
            trace_msg = f"{trace_msg} | {self._format_context(context)}"
        
        self.logger.debug(trace_msg)
    
    def observe(self, operation: str, duration: Optional[float] = None, 
                success: Optional[bool] = None, **metrics):
        """
        Log operation metrics for evaluation (Observability + Evaluation).
        
        Args:
            operation: Operation name
            duration: Execution duration in seconds
            success: Whether operation succeeded
            **metrics: Additional metrics to log
            
        Example:
            >>> logger.observe("save_preference", duration=0.45, success=True, records=10)
            [2024-11-12 11:30:45] INFO [module] OBSERVE:save_preference | duration=0.450s | success=True | records=10
        """
        obs_msg = f"OBSERVE:{operation}"
        
        context = {}
        if duration is not None:
            context['duration'] = f"{duration:.3f}s"
        if success is not None:
            context['success'] = success
        context.update(metrics)
        
        if context:
            obs_msg = f"{obs_msg} | {self._format_context(context)}"
        
        self.logger.info(obs_msg)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context dictionary for logging.
        
        Args:
            context: Context key-value pairs
            
        Returns:
            Formatted string like "key1=value1 | key2=value2"
        """
        return " | ".join(f"{k}={v}" for k, v in context.items())


# Global logger registry
_loggers: Dict[str, OTELogger] = {}


def get_logger(name: str, level: int = logging.INFO) -> OTELogger:
    """
    Get or create OTE logger for a module.
    
    Uses singleton pattern to ensure same logger instance
    is returned for the same module name.
    
    Args:
        name: Module name (use __name__)
        level: Logging level
        
    Returns:
        OTELogger instance
        
    Example:
        >>> from app.utils import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    if name not in _loggers:
        _loggers[name] = OTELogger(name, level)
    return _loggers[name]


def configure_logging(level: int = logging.INFO, 
                     log_file: Optional[str] = None):
    """
    Configure global logging settings.
    
    Args:
        level: Global logging level
        log_file: Optional file to write logs to
        
    Example:
        >>> configure_logging(logging.DEBUG, "app.log")
    """
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )
