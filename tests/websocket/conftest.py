"""Pytest configuration and fixtures for WebSocket tests."""
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket

# Enable asyncio mode for all tests in this directory
pytest_plugins = ('pytest_asyncio',)

# Configure asyncio event loop policy for Windows
if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture
def mock_websocket() -> AsyncMock:
    """Create a mock WebSocket for testing."""
    websocket = AsyncMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.receive_json = AsyncMock()
    websocket.close = AsyncMock()
    return websocket

@pytest.fixture
def connection_manager():
    """Fixture that provides a clean ConnectionManager instance for each test."""
    from app.websocket.chat_endpoint import ConnectionManager
    return ConnectionManager()

@pytest.fixture
def test_message() -> Dict[str, Any]:
    """Fixture that provides a test message."""
    return {
        "type": "chat_message",
        "content": "Hello, World!",
        "sender": "test_user",
        "timestamp": "2023-01-01T00:00:00.000000"
    }
