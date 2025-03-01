import asyncio
import unittest
from typing import Any, Optional, TypeVar, Generic, AsyncContextManager
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import aiohttp

from ultravox_cli.ultravox_client.client import UltravoxClient
from ultravox_cli.ultravox_client.session.websocket_session import WebsocketSession


class TestUltravoxClient(unittest.TestCase):
    """Test cases for the UltravoxClient class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.client = UltravoxClient(api_key=self.api_key)

    def test_init(self) -> None:
        """Test client initialization."""
        # Access attributes using their public names or through __dict__
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.base_url, "https://api.ultravox.ai/api")
        self.assertEqual(self.client.headers["X-API-Key"], self.api_key)
        self.assertIsNotNone(self.client.calls)
        self.assertIsNotNone(self.client.tools)
        self.assertIsNotNone(self.client.voices)

    @patch("aiohttp.ClientSession.request")
    def test_request(self, mock_request: MagicMock) -> None:
        """Test the request method."""
        # Set up the mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"key": "value"})
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value.__aenter__.return_value = mock_response

        # Run the test
        result = asyncio.run(self.client.request("GET", "/test"))

        # Check the result
        self.assertEqual(result, {"key": "value"})
        mock_request.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @patch("aiohttp.ClientSession.request")
    def test_request_error(self, mock_request: MagicMock) -> None:
        """Test the request method with an error response."""
        # Set up the mock
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.raise_for_status = MagicMock(
            side_effect=aiohttp.ClientError("Test error")
        )
        mock_response.json = AsyncMock(return_value={"error": "Test error"})
        mock_request.return_value.__aenter__.return_value = mock_response

        # Run the test
        with self.assertRaises(aiohttp.ClientError):
            asyncio.run(self.client.request("GET", "/test"))

        mock_request.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @patch("ultravox_cli.ultravox_client.session.websocket_session.ws_client.connect")
    def test_join_call(self, mock_connect: MagicMock) -> None:
        """Test the join_call method."""
        # Set up the mocks
        join_url = "ws://test.com/join"
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket

        # Run the test
        session = asyncio.run(self.client.join_call(join_url))

        # Check the result
        self.assertIsNotNone(session)
        self.assertEqual(session._url, join_url)


@pytest.fixture
def client() -> UltravoxClient:
    return UltravoxClient(api_key="test_key")


def test_client_init() -> None:
    """Test client initialization with default and custom base URLs."""
    # Test with default base URL
    client = UltravoxClient(api_key="test_key")
    assert client.api_key == "test_key"
    assert client.base_url == UltravoxClient.BASE_URL
    assert client.headers == {"X-API-Key": "test_key"}
    assert client.calls is not None
    assert client.tools is not None
    assert client.voices is not None

    # Test with custom base URL
    custom_url = "https://custom.api.example.com"
    client = UltravoxClient(api_key="test_key", base_url=custom_url)
    assert client.base_url == custom_url


T = TypeVar("T")


class AsyncContextManagerMock(Generic[T], AsyncContextManager[T]):
    """A mock that can be used as an async context manager."""

    def __init__(self, return_value: T) -> None:
        self.return_value = return_value

    async def __aenter__(self) -> T:
        return self.return_value

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        pass


class MockSession:
    def __init__(self, response: AsyncMock) -> None:
        self.response = response

    def request(self, *args: Any, **kwargs: Any) -> AsyncContextManagerMock:
        return AsyncContextManagerMock(self.response)

    async def __aenter__(self) -> "MockSession":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


@pytest.mark.asyncio
async def test_request_success():
    mock_response = AsyncMock()
    mock_response.json.return_value = {"data": "test"}
    mock_response.raise_for_status = MagicMock()

    mock_session = MockSession(mock_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        client = UltravoxClient("test_token")
        response = await client.request("GET", "/test")
        assert response == {"data": "test"}
        mock_response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_request_error():
    client = UltravoxClient("test_key")

    # Create a synchronous error-raising function
    def raise_error():
        raise aiohttp.ClientError()

    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock(side_effect=raise_error)
    mock_response.json = AsyncMock()

    mock_session = MockSession(mock_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(aiohttp.ClientError):
            await client.request("GET", "/test")

    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_not_called()


@pytest.mark.asyncio
async def test_join_call() -> None:
    """Test joining a call."""
    client = UltravoxClient(api_key="test_key")
    join_url = "wss://example.com/join"

    session = await client.join_call(join_url)
    assert isinstance(session, WebsocketSession)
    assert session._url == join_url


if __name__ == "__main__":
    unittest.main()
