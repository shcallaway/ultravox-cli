import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict

from ultravox_cli.ultravox_client.client import UltravoxClient


@pytest.fixture
def mock_response() -> Dict[str, Any]:
    """Fixture for a mock API response."""
    return {"data": "test"}


@pytest.fixture
def mock_client() -> MagicMock:
    """Fixture for a mock client with async request method."""
    client = MagicMock()
    client.request = AsyncMock()
    return client


@pytest.fixture
def client() -> UltravoxClient:
    """Fixture for a real UltravoxClient instance."""
    return UltravoxClient(api_key="test_key")


@pytest.fixture
def mock_websocket() -> MagicMock:
    """Fixture for a mock WebSocket connection."""
    socket = MagicMock()
    socket.close = AsyncMock()
    socket.send = AsyncMock()
    socket.__aiter__ = AsyncMock()
    return socket
