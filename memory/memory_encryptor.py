"""
User-specific memory encryption module.

Provides encryption/decryption functionality for user conversation memory
using unique per-user encryption keys.

Author: Socializer Development Team
Date: 2024-11-12
"""

import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet, InvalidToken


class UserMemoryEncryptor:
    """
    Handles encryption and decryption of user-specific conversation memory.
    
    Each user has their own unique encryption key, ensuring that memories
    are completely isolated and secure.
    
    Attributes:
        _user_id (int): The ID of the user this encryptor belongs to
        _key (bytes): The user's unique encryption key
        _fernet (Fernet): The Fernet cipher instance for this user
    """
    
    def __init__(self, user):
        """
        Initialize the encryptor with a user-specific key.
        
        Args:
            user: User object with id and encryption_key attributes
            
        Raises:
            ValueError: If user doesn't have a valid encryption key
        """
        self._user_id = user.id
        
        # Get or generate encryption key for this user
        if not hasattr(user, 'encryption_key') or not user.encryption_key:
            raise ValueError(f"User {user.id} does not have an encryption key")
        
        # Ensure key is in bytes format
        if isinstance(user.encryption_key, str):
            self._key = user.encryption_key.encode()
        else:
            self._key = user.encryption_key
        
        # Validate key format
        try:
            self._fernet = Fernet(self._key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key for user {user.id}: {str(e)}")
    
    def encrypt_memory(self, memory_data: Dict[str, Any]) -> str:
        """
        Encrypt user's conversation memory.
        
        Args:
            memory_data: Dictionary containing conversation memory
            
        Returns:
            str: Base64-encoded encrypted string
            
        Example:
            >>> memory = {"messages": [{"role": "user", "content": "Hello"}]}
            >>> encrypted = encryptor.encrypt_memory(memory)
            >>> print(encrypted[:10])
            'gAAAAABh...'
        """
        if not memory_data:
            memory_data = {}
        
        try:
            # Convert to JSON string
            json_data = json.dumps(memory_data)
            
            # Encrypt the JSON string
            encrypted_bytes = self._fernet.encrypt(json_data.encode())
            
            # Return as base64 string for storage
            return encrypted_bytes.decode()
            
        except Exception as e:
            raise RuntimeError(f"Failed to encrypt memory for user {self._user_id}: {str(e)}")
    
    def decrypt_memory(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt user's conversation memory.
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            Dict containing decrypted conversation memory
            
        Raises:
            InvalidToken: If decryption fails (wrong key or corrupted data)
            
        Example:
            >>> encrypted = 'gAAAAABh...'
            >>> memory = encryptor.decrypt_memory(encrypted)
            >>> print(memory)
            {"messages": [{"role": "user", "content": "Hello"}]}
        """
        if not encrypted_data:
            return {}
        
        try:
            # Decode from base64 string
            encrypted_bytes = encrypted_data.encode()
            
            # Decrypt the data
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            
            # Parse JSON
            json_str = decrypted_bytes.decode()
            return json.loads(json_str)
            
        except InvalidToken:
            raise ValueError(f"Cannot decrypt memory for user {self._user_id}: Invalid key or corrupted data")
        except json.JSONDecodeError as e:
            raise ValueError(f"Decrypted data is not valid JSON for user {self._user_id}: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt memory for user {self._user_id}: {str(e)}")
    
    def is_encrypted(self, data: str) -> bool:
        """
        Check if data appears to be encrypted.
        
        Args:
            data: String to check
            
        Returns:
            bool: True if data looks like Fernet-encrypted data
        """
        if not data or len(data) < 20:
            return False
        
        # Fernet tokens start with 'gAAAAA'
        return data.startswith('gAAAAA')
    
    def rotate_key(self, new_key: str, old_encrypted_data: str) -> tuple[str, str]:
        """
        Rotate encryption key while preserving existing data.
        
        Args:
            new_key: New encryption key to use
            old_encrypted_data: Data encrypted with the old key
            
        Returns:
            tuple: (new_key, newly_encrypted_data)
            
        Note:
            This method is useful for key rotation security practices
        """
        # Decrypt with old key
        decrypted_data = self.decrypt_memory(old_encrypted_data)
        
        # Create new Fernet with new key
        if isinstance(new_key, str):
            new_key_bytes = new_key.encode()
        else:
            new_key_bytes = new_key
        
        new_fernet = Fernet(new_key_bytes)
        
        # Encrypt with new key
        json_data = json.dumps(decrypted_data)
        new_encrypted = new_fernet.encrypt(json_data.encode())
        
        # Update this instance to use new key
        self._key = new_key_bytes
        self._fernet = new_fernet
        
        return new_key, new_encrypted.decode()
    
    @staticmethod
    def generate_user_key() -> str:
        """
        Generate a new unique encryption key for a user.
        
        Returns:
            str: Base64-encoded encryption key
            
        Example:
            >>> key = UserMemoryEncryptor.generate_user_key()
            >>> print(len(key))
            44
        """
        return Fernet.generate_key().decode()
    
    def __repr__(self) -> str:
        """String representation of the encryptor."""
        return f"<UserMemoryEncryptor(user_id={self._user_id})>"
