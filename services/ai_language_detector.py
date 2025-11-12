"""
AI-Based Language Detection Service
====================================

Uses LLM to detect user's language with high accuracy and creates a tool
to ask users for confirmation when uncertain.

Design Patterns:
- Strategy Pattern: AI-based detection strategy
- Factory Pattern: Create confirmation messages in detected language
- Single Responsibility: Only handles language detection

Author: Socializer Development Team
Date: 2024-11-12
"""

from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum
import json


class LanguageConfidence(Enum):
    """Confidence levels for language detection."""
    HIGH = "high"        # >90% confidence - auto-save
    MEDIUM = "medium"    # 70-90% confidence - ask user
    LOW = "low"          # <70% confidence - ask user
    UNCLEAR = "unclear"  # Multiple languages detected - ask user


@dataclass
class LanguageDetectionResult:
    """
    Result of AI-based language detection.
    
    Attributes:
        language: Detected language name (e.g., "German", "English")
        confidence: Confidence level
        confidence_score: Numeric confidence (0.0-1.0)
        alternative_languages: Other possible languages
        should_ask_user: Whether to ask user for confirmation
        detection_method: Always "ai" for this implementation
        confirmation_message: Message to ask user (in their language)
    """
    language: str
    confidence: LanguageConfidence
    confidence_score: float
    alternative_languages: list
    should_ask_user: bool
    detection_method: str
    confirmation_message: Optional[str] = None
    
    def __repr__(self) -> str:
        return (f"LanguageDetectionResult(language='{self.language}', "
                f"confidence={self.confidence.value}, "
                f"score={self.confidence_score:.2f})")


class AILanguageDetector:
    """
    AI-based language detector using LLM for accurate detection.
    
    This detector uses the chat agent's LLM to analyze text and determine
    the language with high accuracy. It also generates confirmation messages
    in the detected language for user verification.
    
    Benefits over word-list approach:
    - Much more accurate (handles context, slang, mixed languages)
    - Supports all languages (not limited to predefined lists)
    - Understands nuance and context
    - Can generate natural confirmation messages
    
    Usage:
        detector = AILanguageDetector(llm)
        result = detector.detect("Guten Tag! Wie geht es dir?")
        if result.should_ask_user:
            print(result.confirmation_message)
    """
    
    def __init__(self, llm):
        """
        Initialize AI language detector.
        
        Args:
            llm: Language model instance (ChatOpenAI, ChatGoogleGenerativeAI, etc.)
        """
        self.llm = llm
        self.min_text_length = 3
        self.confidence_threshold_high = 0.9
        self.confidence_threshold_medium = 0.7
    
    def detect(self, text: str, user_context: Optional[Dict] = None) -> LanguageDetectionResult:
        """
        Detect language from text using AI.
        
        Args:
            text: Text to analyze
            user_context: Optional context (unused in AI version)
            
        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        if not text or len(text.strip()) < self.min_text_length:
            return self._create_unclear_result("Text too short")
        
        # Use LLM to detect language
        prompt = f"""Analyze the language of this text and respond with ONLY a JSON object (no markdown, no code blocks):

Text: "{text}"

Respond with exactly this JSON structure:
{{
    "language": "English|German|Spanish|French|Italian|Portuguese|Russian|Chinese|Japanese|Korean|Arabic|Dutch|Polish|Swedish|other",
    "confidence": 0.95,
    "reasoning": "brief explanation"
}}

Requirements:
- language: The full English name of the detected language
- confidence: A number between 0.0 and 1.0
- reasoning: One sentence explaining why
- If multiple languages, pick the dominant one
- If unsure, set confidence < 0.7"""

        try:
            # Get LLM response
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON response
            result = json.loads(response_text)
            
            language = result.get("language", "English")
            confidence_score = float(result.get("confidence", 0.5))
            reasoning = result.get("reasoning", "")
            
            # Determine confidence level
            if confidence_score >= self.confidence_threshold_high:
                confidence = LanguageConfidence.HIGH
                should_ask = False
            elif confidence_score >= self.confidence_threshold_medium:
                confidence = LanguageConfidence.MEDIUM
                should_ask = True
            else:
                confidence = LanguageConfidence.LOW
                should_ask = True
            
            # Generate confirmation message if needed
            confirmation_msg = None
            if should_ask:
                confirmation_msg = self._generate_confirmation_message(language, text)
            
            return LanguageDetectionResult(
                language=language,
                confidence=confidence,
                confidence_score=confidence_score,
                alternative_languages=[],
                should_ask_user=should_ask,
                detection_method="ai",
                confirmation_message=confirmation_msg
            )
            
        except Exception as e:
            print(f"⚠️ AI language detection failed: {e}")
            # Fallback to English with low confidence
            return LanguageDetectionResult(
                language="English",
                confidence=LanguageConfidence.LOW,
                confidence_score=0.5,
                alternative_languages=[],
                should_ask_user=True,
                detection_method="ai_fallback",
                confirmation_message="Would you like to set English as your preferred language? Reply 'yes' to confirm or tell me your preferred language."
            )
    
    def _generate_confirmation_message(self, language: str, sample_text: str) -> str:
        """
        Generate a confirmation message in the detected language.
        
        Args:
            language: Detected language name
            sample_text: Sample of user's text for context
            
        Returns:
            Confirmation message in the detected language
        """
        prompt = f"""Generate a friendly confirmation message asking if the user wants to set {language} as their preferred language.

Requirements:
- Write the ENTIRE message in {language} (not English!)
- Keep it short (1-2 sentences)
- Be friendly and natural
- Ask them to confirm or tell you their preferred language
- Use natural phrasing for that language

Respond with ONLY the message text, no quotes, no JSON, no markdown."""

        try:
            response = self.llm.invoke(prompt)
            return response.content.strip().strip('"').strip("'")
        except Exception as e:
            print(f"⚠️ Failed to generate confirmation: {e}")
            # Fallback messages in various languages
            fallback_messages = {
                "German": "Möchten Sie Deutsch als Ihre bevorzugte Sprache einstellen? Bitte bestätigen Sie oder sagen Sie mir Ihre bevorzugte Sprache.",
                "Spanish": "¿Le gustaría establecer el español como su idioma preferido? Por favor confirme o dígame su idioma preferido.",
                "French": "Souhaitez-vous définir le français comme langue préférée? Veuillez confirmer ou me dire votre langue préférée.",
                "Italian": "Vuoi impostare l'italiano come lingua preferita? Conferma o dimmi la tua lingua preferita.",
                "Portuguese": "Gostaria de definir o português como seu idioma preferido? Por favor, confirme ou me diga seu idioma preferido.",
                "Russian": "Хотите установить русский язык в качестве предпочтительного? Пожалуйста, подтвердите или скажите мне ваш предпочтительный язык.",
            }
            return fallback_messages.get(
                language,
                f"Would you like to set {language} as your preferred language? Please confirm or tell me your preferred language."
            )
    
    def _create_unclear_result(self, reason: str) -> LanguageDetectionResult:
        """Create result for unclear cases."""
        return LanguageDetectionResult(
            language="English",
            confidence=LanguageConfidence.UNCLEAR,
            confidence_score=0.0,
            alternative_languages=[],
            should_ask_user=True,
            detection_method="unclear",
            confirmation_message="What is your preferred language for our conversation?"
        )
    
    def should_auto_save(self, result: LanguageDetectionResult) -> bool:
        """
        Determine if language preference should be auto-saved.
        
        Args:
            result: Detection result
            
        Returns:
            True if confidence is high enough to auto-save
        """
        return result.confidence == LanguageConfidence.HIGH and result.confidence_score >= 0.9
    
    def format_confirmation_message(self, result: LanguageDetectionResult) -> str:
        """
        Format a user-friendly confirmation message.
        
        Args:
            result: Detection result
            
        Returns:
            Formatted confirmation message
        """
        if result.confirmation_message:
            return result.confirmation_message
        
        # Fallback if no confirmation message generated
        return f"I detected that you're speaking {result.language}. Would you like me to continue in {result.language}?"


# Singleton instance
_detector_instance = None


def get_language_detector(llm) -> AILanguageDetector:
    """
    Get singleton language detector instance.
    
    Args:
        llm: Language model instance
        
    Returns:
        AILanguageDetector instance
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = AILanguageDetector(llm)
    return _detector_instance
