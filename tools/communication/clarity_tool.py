"""
Clarify Communication Tool with OTE Compliance

LOCATION: tools/communication/clarity_tool.py
PURPOSE: Translate and clarify cross-cultural communication with OTE tracking

TRACE POINTS:
    - VALIDATE: Input validation
    - DETECT: Language detection
    - TRANSLATE: LLM translation
    - CLARIFY: Explanation generation
    
DEPENDENCIES:
    - LLM instance (ChatOpenAI, ChatAnthropic, etc.)
    
OTE COMPLIANCE:
    - Observability: All translations logged with timing
    - Traceability: Trace markers for translation flow
    - Evaluation: Translation performance, language detection metrics
"""

from typing import Type, Optional, Any, Dict
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.utils import get_logger, observe, traceable

# Get logger for this module
logger = get_logger(__name__)


class ClarifyCommunicationInput(BaseModel):
    """
    Input schema for ClarifyCommunicationTool.
    
    Attributes:
        text: The text that needs clarification or translation
        source_language: Source language if known (optional)
        target_language: Target language (default: English)
        context: Additional context about the conversation (optional)
    """
    text: str = Field(..., description="The text that needs clarification or translation")
    source_language: Optional[str] = Field(None, description="Source language if known")
    target_language: Optional[str] = Field("English", description="Target language (default: English)")
    context: Optional[str] = Field(None, description="Additional context about the conversation")


class ClarifyCommunicationTool(BaseTool):
    """
    Tool to clarify communication and translate between users with OTE tracking.
    
    This tool helps bridge language barriers and cultural misunderstandings by
    providing translations and explanations. All operations are logged and timed
    for performance monitoring.
    
    OTE Compliance:
        - All translations observed with timing
        - Trace markers show translation flow
        - Language detection logged
        - Success/failure rates tracked
    
    Attributes:
        name: Tool name for LLM
        description: Tool description for LLM
        args_schema: Pydantic schema for validation
        llm: Language model for translation and clarification
    
    Example:
        >>> from llm_manager import LLMManager
        >>> llm = LLMManager.get_llm("gpt-4")
        >>> tool = ClarifyCommunicationTool(llm=llm)
        >>> result = tool.run({
        ...     "text": "Bonjour",
        ...     "target_language": "English"
        ... })
        >>> print(result["clarification"])
        "Hello" in English. This is a common French greeting...
    """
    
    name: str = "clarify_communication"
    description: str = """Use this tool when users don't understand each other or when translation/clarification is needed.
    
    This tool helps with:
    - Translating foreign language text
    - Explaining phrases or cultural context
    - Detecting misunderstandings
    - Providing clear explanations
    - Bridging language barriers
    
    Input should include the text that needs clarification."""
    args_schema: Type[BaseModel] = ClarifyCommunicationInput
    llm: Any = None  # Language model instance
    
    def __init__(self, llm=None, **data):
        """
        Initialize ClarifyCommunicationTool.
        
        Args:
            llm: Language model instance for translation
            **data: Additional Pydantic model data
            
        Note:
            If llm is None, tool will attempt to import from global context
        """
        super().__init__(**data)
        
        # Set LLM (Pydantic workaround)
        if llm is not None:
            object.__setattr__(self, 'llm', llm)
        else:
            # Fallback: try to import global llm
            logger.warning("No LLM provided, attempting to use global llm")
            try:
                from ai_chatagent import llm as global_llm
                object.__setattr__(self, 'llm', global_llm)
            except ImportError:
                logger.error("Failed to import global llm")
        
        logger.trace("INIT", "ClarifyCommunicationTool initialized")
        logger.observe("init_complete", has_llm=bool(self.llm))
    
    @observe("clarify_communication")
    def _run(self, text: str, source_language: Optional[str] = None, 
             target_language: str = "English", context: Optional[str] = None) -> Dict[str, Any]:
        """
        Clarify communication by translating and explaining text with OTE tracking.
        
        TRACE PATH:
            1. VALIDATE → Input validation
            2. DETECT → Language detection
            3. TRANSLATE → LLM translation
            4. CLARIFY → Generate explanation
        
        Args:
            text: Text to clarify or translate
            source_language: Source language (optional, auto-detect if None)
            target_language: Target language (default: English)
            context: Additional context (optional)
            
        Returns:
            Dictionary with translation, clarification, and metadata
        """
        # TRACE POINT 1: Validation
        logger.trace("VALIDATE", f"Validating text length={len(text)}, target={target_language}")
        
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return {
                "error": "No text provided for clarification",
                "original_text": text
            }
        
        # TRACE POINT 2: Detect foreign language
        logger.trace("DETECT", "Detecting foreign characters")
        has_foreign_chars = any(ord(char) > 127 for char in text)
        logger.observe("language_detected", has_foreign_chars=has_foreign_chars)
        
        # TRACE POINT 3: Translate and clarify
        try:
            return self._translate_and_clarify(
                text=text,
                source_language=source_language,
                target_language=target_language,
                context=context,
                has_foreign_chars=has_foreign_chars
            )
        except Exception as e:
            logger.error(f"Error clarifying communication: {str(e)}", exc_info=True)
            logger.observe("clarify_complete", success=False, error=str(e))
            return {
                "error": f"Error clarifying communication: {str(e)}",
                "original_text": text
            }
    
    @traceable()
    @observe("translate_clarify")
    def _translate_and_clarify(
        self,
        text: str,
        source_language: Optional[str],
        target_language: str,
        context: Optional[str],
        has_foreign_chars: bool
    ) -> Dict[str, Any]:
        """
        Use LLM to translate and explain text.
        
        TRACE PATH:
            TRANSLATE → Build prompt → LLM call → Format response
        
        Args:
            text: Text to clarify
            source_language: Source language
            target_language: Target language
            context: Additional context
            has_foreign_chars: Whether text has non-ASCII characters
            
        Returns:
            Dictionary with clarification results
        """
        logger.trace("TRANSLATE", f"Translating from {source_language or 'auto'} to {target_language}")
        
        # Build clarification prompt
        clarification_prompt = f"""You are a translation and communication clarification assistant in PROACTIVE MODE.

Text to clarify: "{text}"
Source language: {source_language or "Auto-detect"}
Target language: {target_language}
Context: {context or "General conversation"}

IMPORTANT: Be direct and helpful. DO NOT ask if they want help. PROVIDE the help immediately.

Provide immediately:
1. Direct translation to {target_language} (if foreign language detected)
2. Clear explanation of what was meant
3. Cultural context if relevant
4. Clarification of any ambiguity

Format: Start with the translation/clarification directly. Be concise and clear.
Example: "They said: [translation]. This means [explanation]."

DO NOT say "Would you like me to..." or "I can help..." - JUST HELP."""

        # Call LLM
        logger.trace("LLM_CALL", "Invoking LLM for clarification")
        response = self.llm.invoke(clarification_prompt)
        
        result = {
            "original_text": text,
            "has_foreign_language": has_foreign_chars,
            "source_language": source_language or "Auto-detected",
            "target_language": target_language,
            "clarification": response.content,
            "suggested_response": f"Based on '{text}', here's what they meant: {response.content}"
        }
        
        logger.observe(
            "clarify_complete",
            text_length=len(text),
            response_length=len(response.content),
            has_foreign=has_foreign_chars,
            success=True
        )
        
        return result
    
    @observe("clarify_invoke")
    def invoke(self, input_data: Any) -> Dict[str, Any]:
        """
        Handle tool invocation with flexible input format.
        
        Supports dict with parameters or string with just text.
        
        Args:
            input_data: Input (dict or string)
            
        Returns:
            Clarification results
        """
        logger.trace("INVOKE", f"Tool invoked with type: {type(input_data)}")
        
        try:
            if isinstance(input_data, dict):
                return self._run(**input_data)
            elif isinstance(input_data, str):
                return self._run(text=input_data)
            else:
                logger.warning(f"Invalid input format: {type(input_data)}")
                return {"error": "Invalid input format for clarify_communication"}
        except Exception as e:
            logger.error(f"Error in invoke: {str(e)}", exc_info=True)
            return {"error": f"Error in clarify_communication: {str(e)}"}
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Async version of run.
        
        Note:
            Currently calls sync version. Can be optimized for async LLM calls.
        """
        return self._run(*args, **kwargs)
