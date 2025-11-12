"""
Utility Modules for Socializer

LOCATION: app/utils/
PURPOSE: Shared utilities following OTE principles
    - Observability: Comprehensive logging with timestamps
    - Traceability: Clear code paths and error tracking
    - Evaluation: Performance metrics and comparison

Modules:
    - ote_logger: OTE-compliant logging
    - metrics: Performance tracking and evaluation
    - decorators: Reusable decorators for OTE compliance
"""

from app.utils.ote_logger import OTELogger, get_logger
from app.utils.metrics import PerformanceMetrics, metrics_tracker
from app.utils.decorators import observe, traceable, evaluate

__all__ = [
    'OTELogger',
    'get_logger',
    'PerformanceMetrics',
    'metrics_tracker',
    'observe',
    'traceable',
    'evaluate',
]
