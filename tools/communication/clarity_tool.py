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
    description: str = """SOCIAL COACHING TOOL - Use for analyzing communication quality.
    
    PRIORITY ORDER:
    1. EMPATHY CHECK (first!) - Is the message kind, respectful? Could it hurt feelings?
    2. CLARITY CHECK - Is the message clear and understandable?
    3. TRANSLATION (last, only if needed) - Translate only if different language
    
    Use for: rude messages, conflicts, miscommunication, unclear wording.
    NOT primarily a translation tool!"""
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
        
        # Build clarification prompt - EMPATHY FIRST, TRANSLATION SECOND
        clarification_prompt = f"""You are a SOCIAL SKILLS COACH analyzing communication.

Text to analyze: "{text}"
Target language: {target_language}
Context: {context or "General conversation"}

ANALYZE THIS MESSAGE AND RESPOND WITH THIS EXACT FORMAT:

EMPATHY_STATUS: [PROBLEMATIC or OK]
REASON: [Why it's problematic or why it's fine]
COACHING: [Your coaching advice - explain impact and suggest better alternatives]

PRIORITY ORDER:
1. **EMPATHY CHECK (MOST IMPORTANT)**: Is this message kind? Could it hurt feelings?
2. **CLARITY CHECK**: Is it clear and understandable?
3. **TRANSLATION**: Only if text is in different language than {target_language}

If the message contains insults, aggression, or unkind words:
- Set EMPATHY_STATUS: PROBLEMATIC
- Explain in COACHING why it's hurtful and how to express it better

Respond in {target_language}."""

        # Call LLM
        logger.trace("LLM_CALL", "Invoking LLM for clarification")
        response = self.llm.invoke(clarification_prompt)
        
        # Build structured result with clear empathy focus
        analysis = response.content
        
        # Detect if message is problematic - LLM explicitly states this
        is_problematic = "EMPATHY_STATUS: PROBLEMATIC" in analysis or "EMPATHY_STATUS:PROBLEMATIC" in analysis
        
        if is_problematic:
            logger.info(f"⚠️  EMPATHY ISSUE DETECTED - LLM marked as PROBLEMATIC")
        
        result = {
            "original_text": text,
            "EMPATHY_ISSUE_DETECTED": is_problematic,
            "coaching_analysis": analysis,
            "action_required": "TEACH_BETTER_COMMUNICATION" if is_problematic else "NONE",
            "instruction_for_ai": (
                f"⚠️ THIS MESSAGE IS PROBLEMATIC! You MUST teach the user why '{text}' is hurtful and suggest a better way to communicate. "
                f"Analysis: {analysis[:200]}..."
            ) if is_problematic else f"Message analyzed: {analysis[:200]}..."
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
