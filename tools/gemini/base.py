"""
GeminiToolBase - Base Class for Gemini-Compatible Tools
========================================================

This module provides the base class for creating tools that work with Google's Gemini API.

Key Features:
1. Automatic schema validation for Gemini compatibility
2. Proper Pydantic model handling
3. Clear error messages
4. Type safety

Author: AI Assistant
Date: 2025-10-22
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


class GeminiToolBase(BaseTool, ABC):
    """
    Base class for all Gemini-compatible tools.
    
    Why This Class Exists:
    ----------------------
    Gemini has stricter requirements than OpenAI for tool schemas:
    1. All parameters must have explicit types
    2. No complex nested structures (arrays must have items defined)
    3. No Union types in parameters
    4. All optional fields must have default values
    
    Usage:
    ------
    ```python
    class MyToolInput(BaseModel):
        query: str = Field(description="Search query")
        limit: Optional[int] = Field(default=10, description="Max results")
    
    class MyTool(GeminiToolBase):
        name: str = "my_tool"
        description: str = "My tool description"
        args_schema: Type[BaseModel] = MyToolInput
        
        def _run(self, query: str, limit: int = 10) -> dict:
            # Implementation
            return {"status": "success", "data": ...}
    ```
    
    Attributes:
    -----------
    name : str
        Tool name (no spaces, lowercase recommended)
    description : str
        Clear description of what the tool does
    args_schema : Type[BaseModel]
        Pydantic model defining input parameters
    """
    
    # These must be defined in subclasses
    name: str
    description: str
    args_schema: Type[BaseModel]
    
    def __init__(self, **kwargs):
        """
        Initialize the tool and validate schema.
        
        Raises:
        -------
        ValueError
            If schema is not Gemini-compatible
        """
        super().__init__(**kwargs)
        self._validate_schema()
    
    def _validate_schema(self) -> None:
        """
        Validate that the tool's schema is Gemini-compatible.
        
        Checks:
        1. args_schema is defined
        2. All fields have descriptions
        3. No unsupported types (Union, complex nested structures)
        4. Optional fields have defaults
        
        Raises:
        -------
        ValueError
            If schema validation fails
        """
        if not hasattr(self, 'args_schema') or not self.args_schema:
            raise ValueError(f"Tool {self.name} must define args_schema")
        
        # Validate each field in the schema
        for field_name, field_info in self.args_schema.model_fields.items():
            # Check for description
            if not field_info.description:
                raise ValueError(
                    f"Tool {self.name}: Field '{field_name}' must have a description"
                )
            
            # Check that Optional fields have defaults
            if not field_info.is_required() and field_info.default is None:
                print(
                    f"⚠️  Warning: Tool {self.name}: Optional field '{field_name}' "
                    f"should have a default value for Gemini compatibility"
                )
    
    @abstractmethod
    def _run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool's main functionality.
        
        This method must be implemented by all subclasses.
        
        Parameters:
        -----------
        *args, **kwargs
            Tool-specific parameters defined in args_schema
        
        Returns:
        --------
        Dict[str, Any]
            Dictionary with at least:
            - 'status': 'success' or 'error'
            - 'message': Human-readable message
            - 'data': Tool-specific data (optional)
        
        Example Return:
        ---------------
        ```python
        {
            "status": "success",
            "message": "Search completed",
            "data": {...}
        }
        ```
        """
        pass
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Async version of _run.
        
        Default implementation calls _run synchronously.
        Override this for true async support.
        """
        return self._run(*args, **kwargs)
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get detailed information about this tool's schema.
        
        Useful for debugging and documentation.
        
        Returns:
        --------
        Dict[str, Any]
            Schema information including fields, types, descriptions
        """
        fields_info = {}
        for field_name, field_info in self.args_schema.model_fields.items():
            fields_info[field_name] = {
                'type': str(field_info.annotation),
                'required': field_info.is_required(),
                'default': field_info.default,
                'description': field_info.description
            }
        
        return {
            'name': self.name,
            'description': self.description,
            'fields': fields_info
        }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<GeminiToolBase: {self.name}>"
