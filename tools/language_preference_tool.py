"""
Language Preference Tool
========================

Tool for setting and confirming user language preferences.

This tool allows users to:
- Confirm detected language
- Set a different language
- Update their language preference

Author: Socializer Development Team
Date: 2024-11-12
"""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional


class LanguagePreferenceInput(BaseModel):
    """Input for language preference tool."""
    language: str = Field(
        description="The language to set as user preference (e.g., 'English', 'German', 'Spanish', 'French', etc.)"
    )
    confirmed: bool = Field(
        default=True,
        description="Whether the user has confirmed this language choice"
    )


class LanguagePreferenceTool(BaseTool):
    """
    Tool for managing user language preferences.
    
    This tool allows the AI to set or update the user's preferred language
    for conversations. It should be called when:
    - User confirms their language
    - User explicitly sets a language preference
    - Auto-detection finds high-confidence language
    
    Example usage:
        - User says "Yes, I speak German" → Call with language="German", confirmed=True
        - User says "Please use Spanish" → Call with language="Spanish", confirmed=True
        - AI detects high confidence → Call with language="German", confirmed=True
    """
    
    name: str = "set_language_preference"
    description: str = """Set or update the user's preferred language for conversations.
    
    Use this tool when:
    - User confirms their language (e.g., "Yes, German is correct")
    - User explicitly requests a language (e.g., "Please speak Spanish")
    - You detect a language with high confidence
    
    Args:
        language: The language name in English (e.g., "German", "Spanish", "French")
        confirmed: Set to True when user has confirmed
    
    Returns:
        Success message confirming the language was set
    """
    
    args_schema: type[BaseModel] = LanguagePreferenceInput
    
    data_manager: any = Field(exclude=True)
    user_id: int = Field(exclude=True)
    
    def __init__(self, data_manager, user_id: int):
        """
        Initialize language preference tool.
        
        Args:
            data_manager: DataManager instance
            user_id: ID of the user
        """
        super().__init__(data_manager=data_manager, user_id=user_id)
    
    def _run(self, language: str, confirmed: bool = True) -> str:
        """
        Set user's language preference.
        
        Args:
            language: Language to set
            confirmed: Whether user confirmed
            
        Returns:
            Success message
        """
        try:
            # Validate language (basic check)
            language = language.strip().title()
            
            # Set the preference
            success = self.data_manager.set_user_preference(
                user_id=self.user_id,
                preference_type="communication",
                preference_key="preferred_language",
                preference_value=language,
                confidence=0.95 if confirmed else 0.8
            )
            
            if success:
                print(f"✅ Language preference set: {language} for user {self.user_id}")
                return f"Language preference set to {language}. I will continue our conversation in {language}."
            else:
                return f"Failed to save language preference. Please try again."
                
        except Exception as e:
            print(f"❌ Error setting language preference: {e}")
            return f"Error: {str(e)}"
    
    async def _arun(self, language: str, confirmed: bool = True) -> str:
        """Async version."""
        return self._run(language, confirmed)
