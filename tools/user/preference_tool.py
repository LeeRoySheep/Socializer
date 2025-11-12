"""
User Preference Tool with OTE Compliance

LOCATION: tools/user/preference_tool.py
PURPOSE: Manage user preferences with encryption and OTE tracking

TRACE POINTS:
    - VALIDATE: Input validation
    - DECRYPT: Decryption of sensitive data
    - ENCRYPT: Encryption of sensitive data
    - DB_GET: Database retrieval
    - DB_SET: Database save
    - DB_DELETE: Database deletion

DEPENDENCIES:
    - datamanager.DataManager
    - app.security.encryption (optional, for encryption)
    
OTE COMPLIANCE:
    - Observability: All operations logged with timing
    - Traceability: Trace markers for each step
    - Evaluation: Success/failure tracking, performance metrics
"""

from typing import Type, Optional, Any, Dict, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from datamanager.data_manager import DataManager
from app.utils import get_logger, observe, traceable, evaluate

# Get logger for this module
logger = get_logger(__name__)


class UserPreferenceInput(BaseModel):
    """
    Input schema for UserPreferenceTool.
    
    Attributes:
        action: Action to perform (get, set, delete)
        user_id: The ID of the user
        preference_type: Category of preference (optional for get, required for set/delete)
        preference_key: Specific preference key (required for set/delete)
        preference_value: Value to set (required for set)
        confidence: Confidence score 0-1 (optional, default 1.0)
    """
    action: str = Field(description="Action to perform: get, set, or delete")
    user_id: int = Field(description="The ID of the user")
    preference_type: Optional[str] = Field(default=None, description="Category of preference")
    preference_key: Optional[str] = Field(default=None, description="Specific preference key")
    preference_value: Optional[str] = Field(default=None, description="Value to set")
    confidence: Optional[float] = Field(default=None, description="Confidence score 0-1")


class UserPreferenceTool(BaseTool):
    """
    Tool for managing user preferences with encryption for sensitive data.
    
    This tool provides secure storage and retrieval of user preferences with
    automatic encryption for sensitive data types (personal_info, contact, etc.).
    
    OTE Compliance:
        - All operations are observed with timing
        - Trace markers show execution flow
        - Success/failure rates tracked
        - Encryption performance monitored
    
    Attributes:
        name: Tool name for LLM
        description: Tool description for LLM
        args_schema: Pydantic schema for validation
        dm: DataManager instance for database operations
        encryptor: Encryption handler (optional)
    
    Example:
        >>> tool = UserPreferenceTool(data_manager)
        >>> result = tool.run({
        ...     "action": "set",
        ...     "user_id": 123,
        ...     "preference_type": "personal_info",
        ...     "preference_key": "name",
        ...     "preference_value": "John Doe"
        ... })
        >>> print(result["status"])
        success
    """
    
    name: str = "user_preference"
    description: str = (
        "Manage user preferences (ENCRYPTED). "
        "Use this tool to get, set, or delete user preferences. "
        "Personal data (name, DOB, sensitive info) is automatically encrypted."
    )
    args_schema: Type[BaseModel] = UserPreferenceInput
    dm: DataManager = None
    encryptor: Optional[Any] = None
    
    def __init__(self, data_manager: DataManager):
        """
        Initialize UserPreferenceTool with encryption support.
        
        Args:
            data_manager: DataManager instance for database operations
            
        Note:
            Encryption is optional. If unavailable, data is stored unencrypted
            with a warning logged.
        """
        super().__init__()
        self.dm = data_manager
        
        # Initialize encryption for sensitive data
        logger.trace("INIT", "Initializing encryption")
        try:
            from app.security.encryption import get_encryptor
            self.encryptor = get_encryptor()
            logger.info("✅ Encryption initialized successfully")
        except ImportError:
            logger.warning("⚠️  Encryption module not available, data will be stored unencrypted!")
            self.encryptor = None
        except Exception as e:
            logger.error(f"⚠️  Could not initialize encryption: {e}")
            self.encryptor = None
    
    @observe("user_preference_run")
    @evaluate(detect_anomalies=True)
    def _run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute the preference tool with OTE tracking.
        
        TRACE PATH:
            1. VALIDATE → Input validation
            2. Action-specific path:
               - GET: DECRYPT → DB_GET
               - SET: ENCRYPT → DB_SET
               - DELETE: DB_DELETE
        
        Args:
            action: The action to perform (get/set/delete)
            user_id: The ID of the user
            preference_type: The type/category of preference
            preference_key: The specific preference key
            preference_value: The value to set
            confidence: Confidence score (0-1)
            
        Returns:
            Dictionary with status, message, and relevant data
            
        Raises:
            No exceptions raised - all errors returned in response dict
        """
        # Handle both direct kwargs and input dict
        if not kwargs and args and isinstance(args[0], dict):
            kwargs = args[0]
        
        action = kwargs.get("action", "").lower()
        user_id = kwargs.get("user_id")
        
        # TRACE POINT 1: Validation
        logger.trace("VALIDATE", f"Validating input for action={action}, user_id={user_id}")
        
        if not user_id:
            logger.warning("Validation failed: missing user_id")
            return {"status": "error", "message": "user_id is required"}
        
        try:
            if action == "get":
                return self._handle_get(user_id, kwargs)
            elif action == "set":
                return self._handle_set(user_id, kwargs)
            elif action == "delete":
                return self._handle_delete(user_id, kwargs)
            else:
                logger.warning(f"Invalid action: {action}")
                return {
                    "status": "error",
                    "message": f"Invalid action: {action}. Must be one of: get, set, delete"
                }
                
        except Exception as e:
            logger.error(f"Error in UserPreferenceTool: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error in UserPreferenceTool: {str(e)}"
            }
    
    @traceable()
    @observe("preference_get")
    def _handle_get(self, user_id: int, kwargs: dict) -> Dict[str, Any]:
        """
        Handle GET action - retrieve preferences.
        
        TRACE PATH:
            GET → DB_GET → DECRYPT (if sensitive)
        
        Args:
            user_id: User ID
            kwargs: Request parameters
            
        Returns:
            Dictionary with retrieved preferences
        """
        preference_type = kwargs.get("preference_type")
        
        # TRACE POINT 2: Database retrieval
        logger.trace("DB_GET", f"Retrieving preferences for user={user_id}, type={preference_type}")
        preferences_dict = self.dm.get_user_preferences(user_id, preference_type)
        
        # Decrypt sensitive preferences
        decrypted_prefs = []
        
        if preferences_dict:
            for full_key, value in preferences_dict.items():
                # Split "personal_info.favorite_color" -> ["personal_info", "favorite_color"]
                if '.' in full_key:
                    pref_type, pref_key = full_key.split('.', 1)
                else:
                    pref_type = "general"
                    pref_key = full_key
                
                # TRACE POINT 3: Decryption check
                decrypted_value = value
                is_encrypted = False
                
                if self.encryptor and self._is_sensitive_type(pref_type):
                    if value and self.encryptor.is_encrypted(value):
                        logger.trace("DECRYPT", f"Decrypting {full_key}")
                        try:
                            decrypted_value = self.encryptor.decrypt(value)
                            is_encrypted = True
                        except Exception as e:
                            logger.error(f"Decryption error for {full_key}: {e}")
                
                decrypted_prefs.append({
                    "preference_type": pref_type,
                    "preference_key": pref_key,
                    "preference_value": decrypted_value,
                    "encrypted": is_encrypted
                })
        
        logger.observe("get_complete", records=len(decrypted_prefs), encrypted=bool(self.encryptor))
        
        return {
            "status": "success",
            "preferences": decrypted_prefs,
            "total": len(decrypted_prefs),
            "encryption_enabled": bool(self.encryptor)
        }
    
    @traceable()
    @observe("preference_set")
    def _handle_set(self, user_id: int, kwargs: dict) -> Dict[str, Any]:
        """
        Handle SET action - save preference.
        
        TRACE PATH:
            SET → VALIDATE → ENCRYPT (if sensitive) → DB_SET
        
        Args:
            user_id: User ID
            kwargs: Request parameters
            
        Returns:
            Dictionary with save result
        """
        required = ["preference_type", "preference_key", "preference_value"]
        if not all(k in kwargs for k in required):
            logger.warning(f"Missing required fields for SET: {required}")
            return {
                "status": "error",
                "message": f"Missing required fields. Required: {', '.join(required)}"
            }
        
        preference_value = kwargs["preference_value"]
        preference_type = kwargs["preference_type"]
        
        # TRACE POINT 4: Encryption check
        is_encrypted = False
        if self.encryptor and self._is_sensitive_type(preference_type):
            logger.trace("ENCRYPT", f"Encrypting {preference_type}.{kwargs['preference_key']}")
            try:
                preference_value = self.encryptor.encrypt(preference_value)
                is_encrypted = True
            except Exception as e:
                logger.error(f"Encryption failed: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Encryption failed: {str(e)}"
                }
        
        # TRACE POINT 5: Database save
        logger.trace("DB_SET", f"Saving preference to database")
        success = self.dm.set_user_preference(
            user_id=user_id,
            preference_type=preference_type,
            preference_key=kwargs["preference_key"],
            preference_value=preference_value,
            confidence=kwargs.get("confidence", 1.0)
        )
        
        if success:
            logger.observe("set_complete", encrypted=is_encrypted, success=True)
            return {
                "status": "success",
                "message": "Preference set successfully (encrypted)" if is_encrypted else "Preference set successfully",
                "encrypted": is_encrypted
            }
        else:
            logger.observe("set_complete", encrypted=is_encrypted, success=False)
            return {
                "status": "error",
                "message": "Failed to set preference"
            }
    
    @traceable()
    @observe("preference_delete")
    def _handle_delete(self, user_id: int, kwargs: dict) -> Dict[str, Any]:
        """
        Handle DELETE action - remove preferences.
        
        TRACE PATH:
            DELETE → VALIDATE → DB_DELETE
        
        Args:
            user_id: User ID
            kwargs: Request parameters
            
        Returns:
            Dictionary with deletion result
        """
        preference_type = kwargs.get("preference_type")
        preference_key = kwargs.get("preference_key")
        
        if not preference_type and not preference_key:
            logger.warning("DELETE requires at least preference_type or preference_key")
            return {
                "status": "error",
                "message": "Must provide at least one of preference_type or preference_key"
            }
        
        # TRACE POINT 6: Database deletion
        logger.trace("DB_DELETE", f"Deleting preferences for type={preference_type}, key={preference_key}")
        success = self.dm.delete_user_preference(
            user_id=user_id,
            preference_type=preference_type,
            preference_key=preference_key
        )
        
        if success:
            logger.observe("delete_complete", success=True)
            return {
                "status": "success",
                "message": "Preferences deleted successfully"
            }
        else:
            logger.observe("delete_complete", success=False)
            return {
                "status": "error",
                "message": "No matching preferences found to delete"
            }
    
    def _is_sensitive_type(self, preference_type: str) -> bool:
        """
        Determine if a preference type contains sensitive data requiring encryption.
        
        Sensitive types include:
        - personal_info: Name, DOB, address
        - contact: Email, phone
        - financial: Payment info
        - medical: Health data
        - identification: ID numbers, SSN
        - private: Explicitly private data
        
        Args:
            preference_type: The type of preference
            
        Returns:
            bool: True if sensitive data requiring encryption
        """
        sensitive_types = {
            'personal_info',
            'contact',
            'financial',
            'medical',
            'identification',
            'private'
        }
        return preference_type.lower() in sensitive_types
    
    async def _arun(self, *args, **kwargs):
        """
        Async version of run.
        
        Note:
            Currently calls sync version. Can be optimized for async DB operations.
        """
        return self._run(*args, **kwargs)
