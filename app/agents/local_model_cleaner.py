"""
Local Model Response Cleaner (MCP Compatible)

LOCATION: app/agents/local_model_cleaner.py
PURPOSE: Clean and format responses from local LLM models (LM Studio, Ollama)

Implements MCP (Model Context Protocol) standards for:
- Structured tool definitions
- Standardized response format
- Clean tool invocation

This module provides utilities to detect, parse, and clean local model responses.
"""

import json
import re
from pathlib import Path
from typing import Any, Optional, Tuple, List, Dict

from langchain_core.messages import AIMessage

from app.utils import get_logger

logger = get_logger(__name__)

# Load MCP tools schema
TOOLS_SCHEMA_PATH = Path(__file__).parent.parent / "config" / "tools_schema.json"


def load_tools_schema() -> Dict:
    """Load the MCP tools schema from JSON file."""
    try:
        if TOOLS_SCHEMA_PATH.exists():
            with open(TOOLS_SCHEMA_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load tools schema: {e}")
    return {"tools": [], "response_format": {}}




class LocalModelCleaner:
    """
    Cleans and formats responses from local LLM models.
    
    Handles:
    - Model artifacts (turn markers, special tokens)
    - Raw search output formatting
    - Response quality improvement
    - Tool name mapping (local model names → actual tool names)
    """
    
    # Tool name mappings: local model may use different names
    TOOL_NAME_MAPPING = {
        'get_weather': 'web_search',
        'weather': 'web_search',
        'search': 'web_search',
        'tavily_search': 'web_search',
        'google_search': 'web_search',
        'get_news': 'web_search',
        'get_conversation': 'recall_last_conversation',
        'recall_conversation': 'recall_last_conversation',
        'get_memory': 'recall_last_conversation',
        'remember': 'recall_last_conversation',
        'translate': 'clarify_communication',
        'clarify': 'clarify_communication',
        'get_preference': 'user_preference',
        'get_user_preference': 'user_preference',
        'set_preference': 'user_preference',
        'evaluate_skill': 'skill_evaluator',
        'check_skill': 'skill_evaluator',
        'set_language': 'set_language_preference',
        'language': 'set_language_preference',
        'format': 'format_output',
        'event': 'life_event',
        'add_event': 'life_event',
    }
    
    # Common local model artifacts to remove
    ARTIFACTS = [
        r'<end_of_turn>',
        r'<start_of_turn>',
        r'<start_of_turn>user',
        r'<start_of_turn>model',
        r'<start_of_turn>system',
        r'<\|im_end\|>',
        r'<\|im_start\|>',
        r'<\|end\|>',
        r'<\|assistant\|>',
        r'<\|user\|>',
        r'<\|system\|>',
        r'</s>',
        r'<s>',
        r'\[INST\]',
        r'\[/INST\]',
        r'<<SYS>>',
        r'<</SYS>>',
        r'<\|endoftext\|>',
        r'<\|pad\|>',
        r'<think>.*?</think>',  # Remove thinking tags
        r'<start_of_turn>.*?(?=<start_of_turn>|$)',  # Remove extra turns
    ]
    
    # Patterns indicating raw search output (not natural response)
    RAW_OUTPUT_PATTERNS = [
        r'^[\*\#]+\s*Search results for',  # **Search results for...
        r'^Results from (web_search|tavily)',
        r'easeweather\.com',
        r'weather25\.com',
        r'Close menu\s*\n',
        r'\d+\.\d+\.\s+\d+\.\d+\.\s+\d+%',  # Raw weather data pattern
    ]
    
    # Port patterns for local model detection
    LOCAL_MODEL_PORTS = ['1234', '11434']
    LOCAL_IPS = ['localhost', '127.0.0.1', '192.168.', '10.', '172.16.', '172.17.', 
                 '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
                 '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
                 '172.30.', '172.31.']
    
    # Cloud API endpoints that should NEVER be treated as local
    CLOUD_ENDPOINTS = ['api.openai.com', 'openai.com', 'api.anthropic.com', 
                       'generativelanguage.googleapis.com', 'aiplatform.googleapis.com']
    
    @classmethod
    def is_local_model(cls, model_name: str = "", endpoint: str = "") -> bool:
        """
        Detect if the LLM is a local model based on endpoint or model name.
        
        Args:
            model_name: Name of the model
            endpoint: API endpoint URL
            
        Returns:
            bool: True if this appears to be a local model
        """
        # First, check if it's definitely a CLOUD endpoint (never local)
        if endpoint:
            endpoint_lower = endpoint.lower()
            for cloud_host in cls.CLOUD_ENDPOINTS:
                if cloud_host in endpoint_lower:
                    return False  # Definitely cloud, not local
        
        # Check endpoint for local indicators
        if endpoint:
            endpoint_lower = endpoint.lower()
            for port in cls.LOCAL_MODEL_PORTS:
                if f':{port}' in endpoint_lower:
                    return True
            for ip in cls.LOCAL_IPS:
                if ip in endpoint_lower:
                    return True
        
        # If no endpoint provided, model name alone is NOT enough to determine local
        # (prevents false positives when using cloud APIs with generic model names)
        if not endpoint:
            return False
        
        # Check model name for local indicators (only if endpoint is set and not cloud)
        if model_name:
            model_lower = model_name.lower()
            local_indicators = ['lm-studio', 'lmstudio', 'ollama', 'gguf', 'ggml']
            for indicator in local_indicators:
                if indicator in model_lower:
                    return True
        
        return False
    
    @classmethod
    def parse_json_tool_calls(cls, content: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Parse JSON tool calls from response content.
        
        Local models should output JSON with this structure:
        {
            "formatted_output": null | "natural response text",
            "tool_calls": [{"name": "...", "arguments": {...}}]
        }
        
        - If formatted_output is null/None: tools need to be executed
        - If formatted_output has text: return that as the final response
        
        Args:
            content: Response content that may contain JSON tool calls
            
        Returns:
            Tuple of (tool_calls_list, response_text):
            - tool_calls_list: List of parsed tool call dicts, or None if not found
            - response_text: Natural text response if found in JSON, or None
        """
        if not content:
            return None, None
        
        # Clean artifacts first
        cleaned = cls.clean_response(content)
        
        # Pattern 1: Look for proper structured JSON with formatted_output
        structured_pattern = r'\{[\s\S]*?"formatted_output"[\s\S]*?\}'
        match = re.search(structured_pattern, cleaned)
        if match:
            try:
                # Find the complete JSON object
                json_str = cls._extract_complete_json(cleaned, match.start())
                if json_str:
                    parsed = json.loads(json_str)
                    
                    if isinstance(parsed, dict):
                        formatted = parsed.get('formatted_output')
                        tool_calls = parsed.get('tool_calls', [])
                        
                        # If formatted_output has content, return it as final response
                        if formatted and isinstance(formatted, str) and len(formatted) > 5:
                            logger.info(f"✅ Found formatted_output: {formatted[:50]}...")
                            return None, formatted
                        
                        # If formatted_output is null/None, extract tool calls
                        if tool_calls and isinstance(tool_calls, list):
                            valid_calls = [tc for tc in tool_calls if isinstance(tc, dict) and 'name' in tc]
                            if valid_calls:
                                logger.info(f"🔧 Parsed {len(valid_calls)} tool calls (formatted_output=null)")
                                return valid_calls, None
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Structured JSON parse failed: {e}")
        
        # Pattern 2: Fallback - Array of tool calls (legacy format)
        array_patterns = [
            r'\[[\s\S]*?\{[\s\S]*?"name"[\s\S]*?\}[\s\S]*?\]',  # Array with name field
        ]
        
        for pattern in array_patterns:
            match = re.search(pattern, cleaned)
            if match:
                try:
                    json_str = match.group(0)
                    parsed = json.loads(json_str)
                    
                    if isinstance(parsed, list) and len(parsed) > 0:
                        # Check for formatted_output or response field in any item
                        for item in parsed:
                            if isinstance(item, dict):
                                # Check formatted_output first
                                formatted = item.get('formatted_output')
                                if formatted and isinstance(formatted, str) and len(formatted) > 5:
                                    logger.info(f"✅ Found formatted_output in array: {formatted[:50]}...")
                                    return None, formatted
                                
                                # Check response field (alternative)
                                response = item.get('response')
                                if response and isinstance(response, str) and len(response) > 10:
                                    if '_tool' not in response.lower() and 'needed' not in response.lower():
                                        logger.info(f"✅ Found response in array: {response[:50]}...")
                                        return None, response
                        
                        # Extract tool calls
                        tool_calls = [item for item in parsed if isinstance(item, dict) and 'name' in item]
                        if tool_calls:
                            logger.info(f"🔧 Parsed {len(tool_calls)} JSON tool calls (legacy format)")
                            return tool_calls, None
                            
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"JSON parse error: {e}")
                    continue
        
        return None, None
    
    @classmethod
    def get_local_model_system_prompt(cls, user_language: str, available_tools: List[Dict] = None) -> str:
        """
        Generate MCP-compatible system prompt for local models.
        
        Uses the tools_schema.json for standardized tool definitions.
        
        Args:
            user_language: User's preferred language
            available_tools: List of available tool definitions (optional override)
            
        Returns:
            str: MCP-formatted system prompt addition
        """
        # Load MCP schema
        schema = load_tools_schema()
        tools = schema.get("tools", [])
        
        # Override with provided tools if available
        if available_tools:
            # Merge: use schema tools but filter by available names
            available_names = {t.get('name') for t in available_tools}
            tools = [t for t in tools if t.get('name') in available_names]
            
            # Add any tools not in schema
            schema_names = {t.get('name') for t in tools}
            for t in available_tools:
                if t.get('name') not in schema_names:
                    tools.append({
                        "name": t.get('name'),
                        "description": t.get('description', ''),
                        "parameters": {"type": "object", "properties": {}}
                    })
        
        # Build MCP-style tools documentation
        tools_doc = cls._format_mcp_tools(tools)
        
        return f"""
## MCP PROTOCOL - SOCIAL SKILLS COACHING

### YOUR ROLE:
You are a **Social Skills Coach** - warm, empathetic, and supportive. 
ALWAYS be in coaching mode - help users improve their communication skills in every interaction.

### TOOL USAGE GUIDELINES:

**LANGUAGE DETECTION (CHECK FIRST!):**
If user writes in a DIFFERENT language than "{user_language}":
→ Call `set_language_preference` with the detected language
→ Example: User says "Hello" but {user_language} is not English → use set_language_preference(language="English", confirmed=true)

**AUTOMATIC:**
- `skill_evaluator`: System calls every 5th message
- `clarify_communication`: When message is unclear

**ON REQUEST:**
- `web_search`: For information (weather, news)
- `recall_last_conversation`: For previous conversations  
- `user_preference`: For settings
- `life_event`: For important events

**GREETINGS (if language matches):**
- Respond directly, NO tools needed

### RESPONSE FORMAT:

**Direct response (greetings, simple questions):**
```json
{{"formatted_output": "Your coaching response in {user_language}", "tool_calls": []}}
```

**Tool call needed:**
```json
{{"formatted_output": null, "tool_calls": [{{"name": "tool_name", "arguments": {{...}}}}]}}
```

### AVAILABLE TOOLS:
{tools_doc}

### EXAMPLES:

Greeting (direct coaching response):
```json
{{"formatted_output": "Hallo! Schön, dass du da bist! Wie kann ich dir heute bei deiner sozialen Entwicklung helfen?", "tool_calls": []}}
```

User message unclear (use clarify_communication):
```json
{{"formatted_output": null, "tool_calls": [{{"name": "clarify_communication", "arguments": {{"text": "user's unclear message", "target_language": "{user_language}"}}}}]}}
```

Information request (use web_search):
```json
{{"formatted_output": null, "tool_calls": [{{"name": "web_search", "arguments": {{"query": "weather in Berlin"}}}}]}}
```

### RULES:
1. ALWAYS maintain coaching tone - be encouraging and supportive
2. For greetings: respond directly with warmth
3. Use `clarify_communication` if user's message needs clarification
4. ONLY use tool names from the list above
5. Respond in **{user_language}**
"""
    
    @classmethod
    def _format_mcp_tools(cls, tools: List[Dict]) -> str:
        """Format tools in MCP documentation style."""
        if not tools:
            return "No tools available."
        
        lines = []
        for tool in tools:
            name = tool.get('name', 'unknown')
            desc = tool.get('description', '')
            params = tool.get('parameters', {}).get('properties', {})
            required = tool.get('parameters', {}).get('required', [])
            
            # Format parameters
            param_strs = []
            for pname, pinfo in params.items():
                ptype = pinfo.get('type', 'any')
                pdesc = pinfo.get('description', '')
                req = '*' if pname in required else ''
                param_strs.append(f"    - {pname}{req} ({ptype}): {pdesc}")
            
            params_doc = "\n".join(param_strs) if param_strs else "    (no parameters)"
            
            lines.append(f"**{name}**: {desc}\n  Parameters:\n{params_doc}")
        
        return "\n\n".join(lines)
    
    @classmethod
    def _extract_complete_json(cls, content: str, start_pos: int) -> Optional[str]:
        """Extract a complete JSON object starting at the given position."""
        try:
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(content[start_pos:], start_pos):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if in_string:
                    continue
                    
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return content[start_pos:i+1]
            
            return None
        except Exception:
            return None
    
    @classmethod
    def map_tool_name(cls, tool_name: str) -> str:
        """
        Map local model tool names to actual tool names.
        
        Args:
            tool_name: Tool name from local model
            
        Returns:
            str: Mapped tool name or original if no mapping exists
        """
        mapped = cls.TOOL_NAME_MAPPING.get(tool_name.lower(), tool_name)
        if mapped != tool_name:
            logger.info(f"🔄 Mapped tool name: {tool_name} → {mapped}")
        return mapped
    
    @classmethod
    def map_tool_arguments(cls, tool_name: str, args: Dict, user_language: str) -> Dict:
        """
        Map and fix tool arguments for the actual tool.
        
        Args:
            tool_name: Original tool name from local model
            args: Original arguments
            user_language: User's preferred language
            
        Returns:
            Dict: Fixed arguments for the actual tool
        """
        fixed_args = args.copy() if args else {}
        mapped_name = cls.map_tool_name(tool_name)
        
        # Fix arguments based on mapped tool
        if mapped_name == 'web_search':
            # Map location to query for weather searches
            if 'location' in fixed_args and 'query' not in fixed_args:
                location = fixed_args.pop('location')
                # Check if it was a weather request
                if tool_name.lower() in ['get_weather', 'weather']:
                    fixed_args['query'] = f"weather in {location}"
                else:
                    fixed_args['query'] = location
            # Ensure query exists
            if 'query' not in fixed_args:
                fixed_args['query'] = str(args) if args else "search"
                
        elif mapped_name == 'recall_last_conversation':
            # Ensure user_id is present
            if 'user_id' not in fixed_args and 'is_id' in fixed_args:
                fixed_args['user_id'] = fixed_args.pop('is_id')
                
        elif mapped_name == 'clarify_communication':
            # Fix target_language
            if 'target_language' not in fixed_args or fixed_args.get('target_language', '').lower() == 'english':
                if user_language and user_language.lower() != 'english':
                    fixed_args['target_language'] = user_language
        
        return fixed_args
    
    @classmethod
    def fix_tool_call_language(cls, tool_calls: List[Dict], user_language: str) -> List[Dict]:
        """
        Fix tool call arguments to use correct user language.
        
        Local models often default to English for target_language.
        This fixes them to use the user's actual preference.
        
        Args:
            tool_calls: List of parsed tool call dictionaries
            user_language: User's preferred language
            
        Returns:
            List[Dict]: Fixed tool calls
        """
        if not tool_calls or not user_language:
            return tool_calls
        
        fixed_calls = []
        for call in tool_calls:
            call_copy = call.copy()
            args = call_copy.get('arguments', call_copy.get('args', {}))
            
            if isinstance(args, dict):
                # Fix target_language if it's set to English but user prefers something else
                if 'target_language' in args:
                    if args['target_language'].lower() == 'english' and user_language.lower() != 'english':
                        logger.info(f"🔧 Fixed target_language: English → {user_language}")
                        args['target_language'] = user_language
                
                # Also check for 'language' field
                if 'language' in args:
                    if args['language'].lower() == 'english' and user_language.lower() != 'english':
                        logger.info(f"🔧 Fixed language: English → {user_language}")
                        args['language'] = user_language
                
                call_copy['arguments'] = args
            
            fixed_calls.append(call_copy)
        
        return fixed_calls
    
    @classmethod
    def generate_error_message(cls, llm: Any, user_language: str, error_context: str = "") -> str:
        """
        Generate error message in user's language using the LLM.
        
        Args:
            llm: The language model to use for generation
            user_language: User's preferred language
            error_context: Optional context about what went wrong
            
        Returns:
            str: Natural error message in user's language
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        try:
            prompt_messages = [
                SystemMessage(content=(
                    f"You are a friendly assistant. Generate a SHORT, natural apology message "
                    f"in {user_language}. The message should say you couldn't process the request "
                    f"properly and ask the user to try again. Keep it under 30 words. "
                    f"Do NOT include any JSON, code, or special formatting."
                )),
                HumanMessage(content=f"Generate the error message in {user_language}.")
            ]
            
            response = llm.invoke(prompt_messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean any artifacts from the error message too
            cleaned = cls.clean_response(content)
            
            if cleaned and len(cleaned) > 5:
                logger.info(f"✅ Generated error message in {user_language}")
                return cleaned
                
        except Exception as e:
            logger.warning(f"Failed to generate error message: {e}")
        
        # Fallback if LLM generation fails
        return "I couldn't process your request. Please try again."
    
    # Patterns to detect tool intent from user messages
    TOOL_INTENT_PATTERNS = {
        'web_search': [
            r'weather',  # Any mention of weather
            r'forecast',
            r'temperature',
            r'clima',  # Spanish for weather
            r'tiempo',  # Spanish for weather/time
            r'wetter',  # German for weather
            r'\b(search|look up|find|google|buscar)\b',
            r'\b(news|latest|current events|noticias)\b',
            r'\bwho is\b',
            r'\bquien es\b',  # Spanish "who is"
            r'\bwhat is happening\b',
            r'\bwhat.{0,20}(in|at|for)\s+\w+',  # "what ... in Berlin"
        ],
        'recall_last_conversation': [
            r'\b(remember|recall|what did|last time)\b',
            r'\bprevious (conversation|chat|discussion)\b',
            r'\bwhat we talked about\b',
            r'\brecuerdas\b',  # Spanish "remember"
            r'\b(earlier|before|yesterday)\b.*\b(said|told|mentioned)\b',
            r'\bdo you (remember|recall)\b',
            r'\bconversation history\b',
            r'\bmemory\b',
        ],
        'clarify_communication': [
            r'\b(translate|translation|traducir)\b',
            r'\b(clarify|unclear|rephrase)\b',
            r'\bhow (do|should) I say\b',
            r'\bwhat does.*mean\b',
        ],
        'user_preference': [
            r'\bmy (preference|setting|config)\b',
            r'\b(change|update|set) my\b',
            r'\bsettings\b',
        ],
        'skill_evaluator': [
            r'\b(evaluate|assess|rate|score) my (skill|communication|social)\b',
            r'\bhow am i doing\b',
            r'\bmy progress\b',
            r'\btraining\b',
            r'\bskill (level|evaluation|assessment)\b',
            r'\b(improve|practice|learn) (social|communication)\b',
        ],
        'life_event': [
            r'\b(important|significant) (event|happening|thing)\b',
            r'\blife event\b',
            r'\b(birthday|wedding|graduation|anniversary|promotion)\b',
            r'\bjust (got|had|received)\b',
        ],
    }
    
    @classmethod
    def detect_tool_intent(cls, user_message: str) -> Optional[Dict]:
        """
        Detect if a user message should trigger a tool call.
        
        This is a fallback for when local models don't output proper JSON tool calls.
        
        Args:
            user_message: The user's original message
            
        Returns:
            Optional[Dict]: Tool call dict with 'name' and 'arguments', or None
        """
        if not user_message:
            logger.debug("detect_tool_intent: empty message")
            return None
        
        msg_lower = user_message.lower()
        logger.info(f"🔍 detect_tool_intent checking: '{msg_lower[:80]}...'")
        
        for tool_name, patterns in cls.TOOL_INTENT_PATTERNS.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, msg_lower, re.IGNORECASE):
                        logger.info(f"✅ Detected tool intent: {tool_name} (pattern: {pattern})")
                        
                        # Build arguments based on tool type
                        args = {}
                        if tool_name == 'web_search':
                            args['query'] = user_message
                        elif tool_name == 'clarify_communication':
                            args['text'] = user_message
                        elif tool_name == 'recall_last_conversation':
                            args = {}  # user_id will be added by caller
                        elif tool_name == 'skill_evaluator':
                            args = {'skill_type': 'general'}  # user_id will be added by caller
                        elif tool_name == 'life_event':
                            args = {'event_type': 'general', 'description': user_message}
                        elif tool_name == 'user_preference':
                            args = {'preference_type': 'general'}
                        
                        return {
                            'name': tool_name,
                            'arguments': args,
                            'detected_by': 'intent_pattern'
                        }
                except Exception as e:
                    logger.warning(f"Regex error for pattern {pattern}: {e}")
        
        logger.info(f"❌ No tool intent detected for: '{msg_lower[:50]}...'")
        return None
    
    @classmethod
    def clean_response(cls, content: str) -> str:
        """
        Remove local model artifacts from response content.
        
        Args:
            content: Raw response content from local model
            
        Returns:
            str: Cleaned content
        """
        if not content:
            return content
        
        cleaned = content
        
        # First: Remove everything after <start_of_turn>user (hallucinated conversations)
        # This catches when the model generates fake user messages
        turn_markers = ['<start_of_turn>user', '<start_of_turn>\nuser', '\n<start_of_turn>']
        for marker in turn_markers:
            if marker in cleaned:
                cleaned = cleaned.split(marker)[0]
        
        # Remove all known artifacts
        for pattern in cls.ARTIFACTS:
            try:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
            except re.error:
                # Fallback to simple string replacement
                cleaned = cleaned.replace(pattern.replace(r'\|', '|').replace(r'\\', ''), '')
        
        # Clean up excessive whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Max 2 newlines
        cleaned = re.sub(r' {2,}', ' ', cleaned)  # Max 1 space
        cleaned = cleaned.strip()
        
        return cleaned
    
    @classmethod
    def is_raw_output(cls, content: str) -> bool:
        """
        Detect if content appears to be raw/unformatted search output.
        
        Args:
            content: Response content to check
            
        Returns:
            bool: True if content looks like raw output
        """
        if not content:
            return False
        
        for pattern in cls.RAW_OUTPUT_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                logger.debug(f"Detected raw output pattern: {pattern}")
                return True
        
        return False
    
    @classmethod
    def format_raw_search_output(cls, content: str, user_language: str = "English") -> str:
        """
        Convert raw search output into a natural response.
        
        Args:
            content: Raw search-like content
            user_language: User's preferred language for response
            
        Returns:
            str: Formatted natural response
        """
        # Extract key information from raw search output
        cleaned = cls.clean_response(content)
        
        # Remove markdown headers and formatting artifacts
        cleaned = re.sub(r'^#+\s*', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\*\*Search results for.*?\*\*:?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'Results from \w+:', '', cleaned, flags=re.IGNORECASE)
        
        # Remove URLs and website artifacts
        cleaned = re.sub(r'https?://\S+', '', cleaned)
        cleaned = re.sub(r'\w+\.(com|org|net|io)\s*', '', cleaned)
        cleaned = re.sub(r'Close menu', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up again
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        if not cleaned:
            return "I found some information but couldn't format it properly. Could you rephrase your question?"
        
        return cleaned
    
    @classmethod
    def process_response(cls, response: AIMessage, model_name: str = "", 
                        endpoint: str = "", user_language: str = "English",
                        tool_executor: Any = None) -> Tuple[AIMessage, Optional[List[Dict]]]:
        """
        Process a response from a local model, cleaning and formatting as needed.
        
        This method handles the common issues with local LLMs:
        1. JSON tool calls in content (instead of proper tool_calls)
        2. Model artifacts like <end_of_turn>
        3. Raw search output needing formatting
        4. Wrong target_language (defaulting to English)
        
        Args:
            response: The AIMessage response from the model
            model_name: Name of the model
            endpoint: API endpoint URL
            user_language: User's preferred language
            tool_executor: Optional callable to execute parsed tool calls
            
        Returns:
            Tuple of (AIMessage, parsed_tool_calls):
            - AIMessage: Cleaned/formatted response
            - parsed_tool_calls: List of tool calls to execute, or None
        """
        # Only process if it's a local model
        if not cls.is_local_model(model_name, endpoint):
            return response, None
        
        content = response.content if hasattr(response, 'content') else str(response)
        
        if not content or not isinstance(content, str):
            return response, None
        
        original_length = len(content)
        logger.info(f"🏠 Processing local model response ({original_length} chars)")
        
        # Step 1: Check for JSON tool calls in content
        parsed_tools, natural_response = cls.parse_json_tool_calls(content)
        
        # If we found a natural response in the JSON, return it directly
        if natural_response:
            logger.info(f"✅ Using natural response from JSON")
            return AIMessage(content=natural_response), None
        
        # If we found tool calls, fix language and return them for execution
        if parsed_tools:
            # Fix wrong target_language
            fixed_tools = cls.fix_tool_call_language(parsed_tools, user_language)
            logger.info(f"🔧 Returning {len(fixed_tools)} parsed tool calls for execution")
            return response, fixed_tools
        
        # Step 2: Clean artifacts
        cleaned = cls.clean_response(content)
        
        # Step 3: Check if it's raw output and format it
        if cls.is_raw_output(cleaned):
            logger.info("🔧 Detected raw search output from local model, formatting...")
            cleaned = cls.format_raw_search_output(cleaned, user_language)
        
        # Log if significant changes were made
        if len(cleaned) < original_length * 0.9:  # More than 10% removed
            logger.info(f"🧹 Cleaned local model response: {original_length} -> {len(cleaned)} chars")
        
        # Return cleaned response
        if cleaned != content:
            return AIMessage(content=cleaned), None
        
        return response, None
    
    @classmethod
    def extract_weather_info(cls, content: str) -> Optional[str]:
        """
        Extract weather information from raw search output.
        
        Args:
            content: Raw content potentially containing weather data
            
        Returns:
            Optional[str]: Extracted weather info or None
        """
        # Look for temperature patterns
        temp_patterns = [
            r'(\+?\-?\d+)°[CF]?',  # +41°, -5°C, etc.
            r'temperature[:\s]+(\d+)',
            r'(\d+)\s*degrees',
        ]
        
        temperatures = []
        for pattern in temp_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            temperatures.extend(matches)
        
        # Look for weather conditions
        conditions = []
        condition_patterns = [
            r'(sunny|cloudy|rainy|snowy|windy|foggy|clear|overcast|partly cloudy)',
            r'(snow|rain|fog|mist|drizzle|thunderstorm)',
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            conditions.extend(matches)
        
        if temperatures or conditions:
            parts = []
            if temperatures:
                parts.append(f"Temperature: {temperatures[0]}°")
            if conditions:
                parts.append(f"Conditions: {conditions[0].title()}")
            return " | ".join(parts)
        
        return None
