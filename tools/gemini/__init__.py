"""
Gemini Tool Integration Package
================================

This package provides OOP classes for creating Gemini-compatible tools.

Key Components:
- GeminiToolBase: Base class for all Gemini tools
- GeminiSchemaValidator: Validates tool schemas for Gemini API
- GeminiResponseHandler: Processes tool results for Gemini

Usage:
    from tools.gemini import GeminiToolBase
    
    class MyTool(GeminiToolBase):
        name = "my_tool"
        description = "My tool description"
        # ... implement _run method
"""

from .base import GeminiToolBase
from .validator import GeminiSchemaValidator
from .response_handler import GeminiResponseHandler

__all__ = [
    'GeminiToolBase',
    'GeminiSchemaValidator', 
    'GeminiResponseHandler'
]

__version__ = '1.0.0'
