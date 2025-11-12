"""
Secure Memory System for Socializer.

This package provides user-specific encrypted memory storage
for conversation history and context management.

Key Components:
- UserMemoryEncryptor: Handles user-specific encryption/decryption
- SecureMemoryManager: Manages encrypted conversation storage
- UserAgent: User-specific AI agent with isolated memory access

Author: Socializer Development Team
Date: 2024-11-12
"""

from memory.memory_encryptor import UserMemoryEncryptor
from memory.secure_memory_manager import SecureMemoryManager
from memory.user_agent import UserAgent

__all__ = [
    'UserMemoryEncryptor',
    'SecureMemoryManager', 
    'UserAgent'
]

__version__ = '1.0.0'
