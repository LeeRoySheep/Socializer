"""
GeminiSchemaValidator - Schema Validation for Gemini API
=========================================================

This module validates tool schemas against Gemini API requirements.

Author: AI Assistant
Date: 2025-10-22
"""

from typing import Any, Dict, List, Type, get_args, get_origin
from pydantic import BaseModel
import inspect


class GeminiSchemaValidator:
    """
    Validates Pydantic schemas for Gemini API compatibility.
    
    Gemini Requirements:
    --------------------
    1. No Union types (except Optional[T] which is Union[T, None])
    2. No complex nested arrays without item definitions
    3. All fields must have descriptions
    4. Optional fields should have default values
    5. No recursive schemas
    
    Usage:
    ------
    ```python
    validator = GeminiSchemaValidator()
    is_valid, errors = validator.validate(MyToolInput)
    
    if not is_valid:
        for error in errors:
            print(f"Error: {error}")
    ```
    """
    
    # Types that Gemini supports natively
    SUPPORTED_SIMPLE_TYPES = {
        str, int, float, bool
    }
    
    # Complex types that need special handling
    SUPPORTED_COMPLEX_TYPES = {
        list, dict
    }
    
    def __init__(self):
        """Initialize the validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, schema: Type[BaseModel]) -> tuple[bool, List[str], List[str]]:
        """
        Validate a Pydantic schema for Gemini compatibility.
        
        Parameters:
        -----------
        schema : Type[BaseModel]
            The Pydantic model to validate
        
        Returns:
        --------
        tuple[bool, List[str], List[str]]
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        if not issubclass(schema, BaseModel):
            self.errors.append(f"{schema} is not a Pydantic BaseModel")
            return False, self.errors, self.warnings
        
        # Validate each field
        for field_name, field_info in schema.model_fields.items():
            self._validate_field(field_name, field_info, schema.__name__)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_field(self, field_name: str, field_info: Any, schema_name: str):
        """
        Validate a single field in the schema.
        
        Parameters:
        -----------
        field_name : str
            Name of the field
        field_info : FieldInfo
            Pydantic field information
        schema_name : str
            Name of the parent schema
        """
        # Check for description
        if not field_info.description:
            self.errors.append(
                f"{schema_name}.{field_name}: Missing description"
            )
        
        # Get field type
        field_type = field_info.annotation
        
        # Check if field is Optional (Union with None)
        origin = get_origin(field_type)
        args = get_args(field_type)
        is_optional = origin and str(origin) == 'typing.Union' and type(None) in args
        
        # Check for Optional fields without defaults
        if is_optional:
            # For Optional fields, check if there's a default
            from pydantic_core import PydanticUndefined
            has_default = field_info.default is not PydanticUndefined and field_info.default is not None
            has_factory = field_info.default_factory is not None
            
            if not has_default and not has_factory:
                self.warnings.append(
                    f"{schema_name}.{field_name}: Optional field should have a default value for Gemini compatibility"
                )
        
        # Validate field type
        self._validate_type(field_name, field_type, schema_name)
    
    def _validate_type(self, field_name: str, field_type: Any, schema_name: str):
        """
        Validate a field's type for Gemini compatibility.
        
        Parameters:
        -----------
        field_name : str
            Name of the field
        field_type : Any
            The type annotation
        schema_name : str
            Name of the parent schema
        """
        origin = get_origin(field_type)
        args = get_args(field_type)
        
        # Handle Optional types (Union[T, None])
        if origin is type(None) or (origin and str(origin) == 'typing.Union'):
            if args:
                # Check if it's Optional[T] (Union[T, None])
                if type(None) in args:
                    # Get the non-None type
                    non_none_types = [t for t in args if t is not type(None)]
                    if len(non_none_types) == 1:
                        # This is Optional[T], validate T
                        self._validate_type(field_name, non_none_types[0], schema_name)
                        return
                    else:
                        self.errors.append(
                            f"{schema_name}.{field_name}: Union types (except Optional) "
                            f"are not supported by Gemini"
                        )
                        return
                else:
                    self.errors.append(
                        f"{schema_name}.{field_name}: Union types are not supported by Gemini"
                    )
                    return
        
        # Handle List types
        if origin is list:
            if not args:
                self.errors.append(
                    f"{schema_name}.{field_name}: List must specify item type (e.g., List[str])"
                )
            else:
                # Validate list item type
                item_type = args[0]
                if item_type not in self.SUPPORTED_SIMPLE_TYPES:
                    self.warnings.append(
                        f"{schema_name}.{field_name}: List of complex types may cause issues"
                    )
        
        # Handle Dict types
        elif origin is dict:
            if not args or len(args) < 2:
                self.errors.append(
                    f"{schema_name}.{field_name}: Dict must specify key and value types "
                    f"(e.g., Dict[str, Any])"
                )
        
        # Check if it's a simple supported type
        elif field_type in self.SUPPORTED_SIMPLE_TYPES:
            # All good
            pass
        
        # Check if it's a nested Pydantic model
        elif inspect.isclass(field_type) and issubclass(field_type, BaseModel):
            self.warnings.append(
                f"{schema_name}.{field_name}: Nested Pydantic models may cause issues with Gemini"
            )
        
        # Unknown type
        else:
            self.warnings.append(
                f"{schema_name}.{field_name}: Type {field_type} may not be fully supported"
            )
    
    def validate_multiple(
        self, 
        schemas: List[Type[BaseModel]]
    ) -> Dict[str, tuple[bool, List[str], List[str]]]:
        """
        Validate multiple schemas at once.
        
        Parameters:
        -----------
        schemas : List[Type[BaseModel]]
            List of Pydantic models to validate
        
        Returns:
        --------
        Dict[str, tuple[bool, List[str], List[str]]]
            Dictionary mapping schema names to validation results
        """
        results = {}
        for schema in schemas:
            schema_name = schema.__name__
            results[schema_name] = self.validate(schema)
        return results
    
    def print_report(self, schema: Type[BaseModel]):
        """
        Print a validation report for a schema.
        
        Parameters:
        -----------
        schema : Type[BaseModel]
            The schema to validate and report on
        """
        is_valid, errors, warnings = self.validate(schema)
        
        print(f"\n{'='*60}")
        print(f"Validation Report: {schema.__name__}")
        print(f"{'='*60}")
        
        if is_valid:
            print("✅ Schema is Gemini-compatible!")
        else:
            print("❌ Schema has errors!")
        
        if errors:
            print(f"\n🔴 Errors ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")
        
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  - {warning}")
        
        if not errors and not warnings:
            print("\n✨ Perfect! No issues found.")
        
        print(f"{'='*60}\n")
