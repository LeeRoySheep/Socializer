"""
Encryption utilities for secure user data storage.

Uses Fernet (symmetric encryption) from cryptography library.
Personal user data is encrypted at rest and only accessible to authenticated users.
"""
import os
from typing import Optional
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class DataEncryption:
    """
    Handles encryption and decryption of sensitive user data.
    
    Uses Fernet symmetric encryption with a key derived from environment variable.
    Thread-safe and production-ready.
    """
    
    def __init__(self):
        """Initialize encryption with key from environment or generate new one."""
        self._fernet = self._initialize_fernet()
    
    def _initialize_fernet(self) -> Fernet:
        """
        Initialize Fernet cipher with key from environment.
        
        Returns:
            Fernet: Initialized cipher
            
        Raises:
            ValueError: If encryption key is invalid
        """
        # Get encryption key from environment
        encryption_key = os.getenv("USER_DATA_ENCRYPTION_KEY")
        
        if not encryption_key:
            # Generate a new key and warn the user
            encryption_key = Fernet.generate_key().decode()
            print("⚠️  WARNING: No USER_DATA_ENCRYPTION_KEY found in .env!")
            print(f"⚠️  Generated temporary key: {encryption_key}")
            print(f"⚠️  Add this to your .env file for production:")
            print(f"USER_DATA_ENCRYPTION_KEY={encryption_key}")
        
        # Ensure key is bytes
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        return Fernet(encryption_key)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Plain text string to encrypt
            
        Returns:
            str: Base64-encoded encrypted string
            
        Example:
            >>> encryptor = DataEncryption()
            >>> encrypted = encryptor.encrypt("secret_data")
            >>> print(encrypted)
            'gAAAAABh...'
        """
        if not data:
            return ""
        
        # Convert to bytes, encrypt, then base64 encode for storage
        encrypted_bytes = self._fernet.encrypt(data.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            str: Decrypted plain text
            
        Raises:
            ValueError: If decryption fails (wrong key or corrupted data)
            
        Example:
            >>> encryptor = DataEncryption()
            >>> decrypted = encryptor.decrypt('gAAAAABh...')
            >>> print(decrypted)
            'secret_data'
        """
        if not encrypted_data:
            return ""
        
        try:
            # Decrypt and convert back to string
            decrypted_bytes = self._fernet.decrypt(encrypted_data.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
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


# Global instance for easy access
_encryptor = None

def get_encryptor() -> DataEncryption:
    """
    Get singleton encryptor instance.
    
    Returns:
        DataEncryption: Global encryptor instance
    """
    global _encryptor
    if _encryptor is None:
        _encryptor = DataEncryption()
    return _encryptor


# Convenience functions
def encrypt_user_data(data: str) -> str:
    """
    Encrypt user personal data.
    
    Args:
        data: Plain text to encrypt
        
    Returns:
        str: Encrypted string
    """
    return get_encryptor().encrypt(data)


def decrypt_user_data(encrypted_data: str) -> str:
    """
    Decrypt user personal data.
    
    Args:
        encrypted_data: Encrypted string
        
    Returns:
        str: Decrypted plain text
    """
    return get_encryptor().decrypt(encrypted_data)
