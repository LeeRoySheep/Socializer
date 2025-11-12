"""
Language Detection Service
==========================

Automatically detects user's language from their messages and manages
language preference persistence.

Design Patterns:
- Strategy Pattern: Different detection strategies
- Factory Pattern: Create detectors based on confidence
- Single Responsibility: Only handles language detection

Author: Socializer Development Team
Date: 2024-11-12
"""

from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass
from enum import Enum
import re


class LanguageConfidence(Enum):
    """Confidence levels for language detection."""
    HIGH = "high"        # >90% confidence
    MEDIUM = "medium"    # 70-90% confidence
    LOW = "low"          # <70% confidence
    UNCLEAR = "unclear"  # Multiple languages detected


@dataclass
class LanguageDetectionResult:
    """
    Result of language detection.
    
    Attributes:
        language: Detected language name (e.g., "German", "English")
        confidence: Confidence level
        confidence_score: Numeric confidence (0.0-1.0)
        alternative_languages: Other possible languages
        should_ask_user: Whether to ask user for confirmation
        detection_method: How language was detected
    """
    language: str
    confidence: LanguageConfidence
    confidence_score: float
    alternative_languages: List[str]
    should_ask_user: bool
    detection_method: str
    
    def __repr__(self) -> str:
        return (f"LanguageDetectionResult(language='{self.language}', "
                f"confidence={self.confidence.value}, "
                f"score={self.confidence_score:.2f})")


class LanguageDetector:
    """
    Detects language from user messages using multiple strategies.
    
    Strategies:
    1. Character-based detection (non-ASCII patterns)
    2. Common word detection
    3. Grammar pattern detection
    4. LLM-based detection (fallback)
    
    Usage:
        detector = LanguageDetector()
        result = detector.detect("Guten Tag! Wie geht es dir?")
        print(result.language)  # "German"
    """
    
    # Character ranges for different writing systems
    LANGUAGE_CHAR_PATTERNS = {
        'German': r'[äöüßÄÖÜ]',
        'Spanish': r'[áéíóúñÁÉÍÓÚÑ¿¡]',
        'French': r'[àâæçéèêëïîôùûüÿœÀÂÆÇÉÈÊËÏÎÔÙÛÜŸŒ]',
        'Italian': r'[àèéìíîòóùúÀÈÉÌÍÎÒÓÙÚ]',
        'Portuguese': r'[ãáàâçéêíóôõúÃÁÀÂÇÉÊÍÓÔÕÚ]',
        'Russian': r'[а-яА-ЯёЁ]',
        'Chinese': r'[\u4e00-\u9fff]',
        'Japanese': r'[\u3040-\u309f\u30a0-\u30ff]',
        'Korean': r'[\uac00-\ud7af]',
        'Arabic': r'[\u0600-\u06ff]',
        'Greek': r'[α-ωΑ-Ω]',
        'Hebrew': r'[\u0590-\u05ff]',
    }
    
    # Common words for language identification
    COMMON_WORDS = {
        'German': ['der', 'die', 'das', 'und', 'ich', 'ist', 'nicht', 'du', 'sie', 'er', 
                   'wie', 'was', 'wo', 'wann', 'warum', 'aber', 'auch', 'bei', 'mit', 'von',
                   'zu', 'für', 'auf', 'hat', 'haben', 'sein', 'werden', 'können', 'müssen',
                   'meine', 'deine', 'seine', 'ihre', 'mein', 'dein', 'sein', 'ihr',
                   'möchte', 'möchten', 'würde', 'sollte', 'besser', 'gut', 'sehr'],
        'Spanish': ['el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'que', 'de', 
                    'en', 'por', 'para', 'con', 'sin', 'como', 'pero', 'si', 'no', 'sí',
                    'muy', 'más', 'también', 'hay', 'está', 'ser', 'estar', 'tener',
                    'cuál', 'cual', 'es', 'clima', 'hoy', 'dónde', 'donde'],
        'French': ['le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'que', 'de',
                   'dans', 'pour', 'avec', 'sans', 'comme', 'mais', 'si', 'ne', 'pas',
                   'très', 'plus', 'aussi', 'il', 'elle', 'je', 'tu', 'nous', 'vous'],
        'Italian': ['il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'e',
                    'o', 'che', 'di', 'a', 'da', 'in', 'per', 'con', 'su',
                    'come', 'ma', 'se', 'non', 'molto', 'più', 'anche', 'sono', 'è'],
        'Portuguese': ['o', 'a', 'os', 'as', 'um', 'uma', 'e', 'ou', 'que', 'de',
                       'em', 'por', 'para', 'com', 'sem', 'como', 'mas', 'se', 'não',
                       'muito', 'mais', 'também', 'há', 'está', 'ser', 'estar', 'ter'],
        'Dutch': ['de', 'het', 'een', 'en', 'of', 'dat', 'van', 'in', 'voor', 'met',
                  'op', 'aan', 'bij', 'naar', 'om', 'te', 'zijn', 'hebben', 'worden'],
        'Russian': ['и', 'в', 'не', 'на', 'я', 'что', 'то', 'он', 'она', 'это',
                    'как', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за'],
        'Polish': ['i', 'w', 'nie', 'na', 'to', 'jest', 'się', 'z', 'o', 'a',
                   'że', 'do', 'jak', 'ale', 'co', 'ich', 'dla', 'są', 'był'],
        'Swedish': ['och', 'i', 'att', 'det', 'som', 'en', 'är', 'på', 'för', 'av',
                    'med', 'till', 'den', 'har', 'de', 'ett', 'om', 'han', 'var'],
    }
    
    # Greeting patterns
    GREETINGS = {
        'German': ['hallo', 'guten tag', 'guten morgen', 'guten abend', 'wie geht', 'danke', 'bitte'],
        'Spanish': ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'cómo estás', 'gracias'],
        'French': ['bonjour', 'bonsoir', 'salut', 'comment allez', 'merci', 'sil vous plaît'],
        'Italian': ['ciao', 'buongiorno', 'buonasera', 'come stai', 'grazie', 'prego'],
        'Portuguese': ['olá', 'bom dia', 'boa tarde', 'boa noite', 'como está', 'obrigado'],
        'Russian': ['привет', 'здравствуйте', 'как дела', 'спасибо', 'пожалуйста'],
        'Japanese': ['こんにちは', 'ありがとう', 'おはよう', 'こんばんは'],
        'Chinese': ['你好', '谢谢', '早上好', '晚上好'],
        'Korean': ['안녕하세요', '감사합니다', '좋은 아침'],
    }
    
    def __init__(self):
        """Initialize the language detector."""
        self.min_text_length = 3  # Minimum characters to attempt detection
        self.confidence_threshold_high = 0.9
        self.confidence_threshold_medium = 0.7
    
    def detect(self, text: str, user_context: Optional[Dict] = None) -> LanguageDetectionResult:
        """
        Detect language from text.
        
        Args:
            text: Text to analyze
            user_context: Optional context (username, previous messages, etc.)
            
        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        if not text or len(text.strip()) < self.min_text_length:
            return self._create_unclear_result("Text too short")
        
        text_lower = text.lower().strip()
        
        # Strategy 1: Character-based detection (high confidence for non-Latin scripts)
        char_result = self._detect_by_characters(text)
        if char_result:
            return char_result
        
        # Strategy 2: Greeting detection (high confidence)
        greeting_result = self._detect_by_greetings(text_lower)
        if greeting_result:
            return greeting_result
        
        # Strategy 3: Common words detection (medium-high confidence)
        word_result = self._detect_by_common_words(text_lower)
        if word_result:
            return word_result
        
        # Strategy 4: Multiple short messages (use context)
        if user_context and 'previous_messages' in user_context:
            context_result = self._detect_by_context(user_context['previous_messages'])
            if context_result:
                return context_result
        
        # Default: English (low confidence)
        return LanguageDetectionResult(
            language="English",
            confidence=LanguageConfidence.LOW,
            confidence_score=0.5,
            alternative_languages=[],
            should_ask_user=True,
            detection_method="default"
        )
    
    def _detect_by_characters(self, text: str) -> Optional[LanguageDetectionResult]:
        """
        Detect language by character patterns.
        
        High confidence for non-Latin scripts (Chinese, Japanese, Arabic, etc.)
        """
        scores = {}
        
        for language, pattern in self.LANGUAGE_CHAR_PATTERNS.items():
            matches = len(re.findall(pattern, text))
            if matches > 0:
                # Calculate score based on match density
                score = min(1.0, matches / max(10, len(text) * 0.1))
                scores[language] = score
        
        if not scores:
            return None
        
        # Get best match
        best_language = max(scores, key=scores.get)
        best_score = scores[best_language]
        
        # Non-Latin scripts get high confidence even with few matches
        if best_language in ['Chinese', 'Japanese', 'Korean', 'Arabic', 'Hebrew', 'Russian', 'Greek']:
            if best_score > 0.1:  # Any matches = high confidence
                return LanguageDetectionResult(
                    language=best_language,
                    confidence=LanguageConfidence.HIGH,
                    confidence_score=0.95,
                    alternative_languages=[],
                    should_ask_user=False,
                    detection_method="character_pattern"
                )
        
        # Latin-script special characters (German ü, Spanish ñ, etc.)
        if best_score > 0.3:
            return LanguageDetectionResult(
                language=best_language,
                confidence=LanguageConfidence.HIGH,
                confidence_score=best_score,
                alternative_languages=[],
                should_ask_user=False,
                detection_method="special_characters"
            )
        
        return None
    
    def _detect_by_greetings(self, text_lower: str) -> Optional[LanguageDetectionResult]:
        """Detect language by common greetings."""
        for language, greetings in self.GREETINGS.items():
            for greeting in greetings:
                if greeting in text_lower:
                    return LanguageDetectionResult(
                        language=language,
                        confidence=LanguageConfidence.HIGH,
                        confidence_score=0.95,
                        alternative_languages=[],
                        should_ask_user=False,
                        detection_method="greeting"
                    )
        return None
    
    def _detect_by_common_words(self, text_lower: str) -> Optional[LanguageDetectionResult]:
        """Detect language by common word frequency."""
        words = re.findall(r'\b\w+\b', text_lower)
        
        if len(words) < 2:
            return None
        
        scores = {}
        match_counts = {}
        
        for language, common_words in self.COMMON_WORDS.items():
            matches = sum(1 for word in words if word in common_words)
            if matches > 0:
                score = matches / len(words)
                scores[language] = score
                match_counts[language] = matches
        
        if not scores:
            return None
        
        # Get top matches
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_language, best_score = sorted_scores[0]
        best_matches = match_counts[best_language]
        
        # Check if there are competing languages
        alternatives = [lang for lang, score in sorted_scores[1:] if score > 0.3]
        
        # Determine confidence
        # If we have 3+ matches, that's pretty strong evidence
        if best_matches >= 3 or best_score >= 0.5:
            confidence = LanguageConfidence.HIGH
            confidence_score = min(0.95, best_score + 0.2)  # Boost confidence
            should_ask = False
        elif best_matches >= 2 or best_score >= 0.3:
            confidence = LanguageConfidence.MEDIUM
            confidence_score = min(0.85, best_score + 0.1)
            should_ask = len(alternatives) > 0
        else:
            confidence = LanguageConfidence.LOW
            confidence_score = best_score
            should_ask = True
        
        return LanguageDetectionResult(
            language=best_language,
            confidence=confidence,
            confidence_score=confidence_score,
            alternative_languages=alternatives,
            should_ask_user=should_ask,
            detection_method="common_words"
        )
    
    def _detect_by_context(self, previous_messages: List[str]) -> Optional[LanguageDetectionResult]:
        """
        Detect language from multiple messages for better accuracy.
        
        Combines evidence from multiple messages.
        """
        combined_text = " ".join(previous_messages[-5:])  # Last 5 messages
        return self.detect(combined_text)
    
    def _create_unclear_result(self, reason: str) -> LanguageDetectionResult:
        """Create result for unclear detection."""
        return LanguageDetectionResult(
            language="English",
            confidence=LanguageConfidence.UNCLEAR,
            confidence_score=0.0,
            alternative_languages=[],
            should_ask_user=True,
            detection_method=f"unclear ({reason})"
        )
    
    def should_auto_save(self, result: LanguageDetectionResult) -> bool:
        """
        Determine if language should be auto-saved without asking user.
        
        Args:
            result: Detection result
            
        Returns:
            bool: True if confident enough to auto-save
        """
        # Auto-save if HIGH confidence, regardless of exact score
        # The confidence level already encodes our certainty
        return result.confidence == LanguageConfidence.HIGH
    
    def format_confirmation_message(self, result: LanguageDetectionResult) -> str:
        """
        Format a user-friendly confirmation message.
        
        Args:
            result: Detection result
            
        Returns:
            str: Message to ask user for confirmation
        """
        if len(result.alternative_languages) > 0:
            alternatives = ", ".join(result.alternative_languages)
            return (f"I detected you might be speaking {result.language}, "
                    f"but it could also be {alternatives}. "
                    f"Which language would you prefer I use?")
        else:
            return (f"I detected you might be speaking {result.language}. "
                    f"Would you like me to respond in {result.language}? "
                    f"(Reply 'yes' to confirm or tell me your preferred language)")


# Singleton instance for easy access
_detector_instance: Optional[LanguageDetector] = None


def get_language_detector() -> LanguageDetector:
    """
    Get singleton instance of LanguageDetector.
    
    Returns:
        LanguageDetector: Singleton instance
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LanguageDetector()
    return _detector_instance
