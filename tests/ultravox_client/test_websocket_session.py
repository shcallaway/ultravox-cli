import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import (
    Any,
    Dict,
    Generator,
    Literal,
    cast,
    List,
    AsyncIterator,
    Optional,
    TypeVar,
    Generic,
)

from websockets import exceptions as ws_exceptions
from websockets.asyncio import client as ws_client
from aiohttp import WSMsgType
from websockets.frames import Close

from ultravox_cli.ultravox_client.session.websocket_session import WebsocketSession

T = TypeVar("T")


class AsyncIteratorMock(Generic[T]):
    def __init__(self, items: List[T]) -> None:
        self.items = items.copy()

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        try:
            item = self.items.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        except IndexError:
            raise StopAsyncIteration


@pytest.fixture
def session() -> WebsocketSession:
    return WebsocketSession("wss://example.com/join")


@pytest.fixture
def mock_socket() -> MagicMock:
    socket = MagicMock()
    socket.close = AsyncMock()
    socket.send = AsyncMock()
    return socket


def test_init(session: WebsocketSession) -> None:
    """Test WebsocketSession initialization."""
    assert session._url == "wss://example.com/join"
    assert session._state == "idle"
    assert session._pending_output == ""
    assert session._socket is None
    assert session._receive_task is None
    assert session._tool_handlers == {}


@pytest.mark.asyncio
async def test_start(session: WebsocketSession) -> None:
    """Test starting a WebSocket session."""
    mock_socket = AsyncMock()

    with patch(
        "websockets.asyncio.client.connect", AsyncMock(return_value=mock_socket)
    ):
        await session.start()
        assert session._socket == mock_socket
        assert session._receive_task is not None


@pytest.mark.asyncio
async def test_stop(session: WebsocketSession, mock_socket: MagicMock) -> None:
    """Test stopping a WebSocket session."""
    session._socket = mock_socket
    session._receive_task = asyncio.create_task(asyncio.sleep(0))
    session._state = cast(
        Literal["idle", "listening", "thinking", "speaking"], "listening"
    )

    await session.stop()

    mock_socket.close.assert_called_once()
    assert session._state == "idle"


@pytest.mark.asyncio
async def test_socket_receive_normal_close(
    session: WebsocketSession, mock_socket: MagicMock
) -> None:
    """Test WebSocket receive with normal close."""
    mock_socket.__aiter__.return_value = AsyncMock(
        __anext__=AsyncMock(side_effect=ws_exceptions.ConnectionClosedOK(None, None))
    )

    # Create a list to store emitted events
    events = []
    session.on("ended", lambda: events.append("ended"))

    await session._socket_receive(mock_socket)
    assert "ended" in events


@pytest.mark.asyncio
async def test_socket_receive_error() -> None:
    mock_socket = AsyncMock()
    error = ws_exceptions.ConnectionClosedError(Close(1006, "test error"), None)
    mock_socket.__aiter__ = lambda self: AsyncIteratorMock[Exception]([error])

    session = WebsocketSession("ws://test.com")
    events: List[Any] = []
    session.on("error", lambda e: events.append(e))

    await session._socket_receive(mock_socket)
    assert len(events) == 1
    assert events[0] == error


@pytest.mark.asyncio
async def test_handle_state_message(session: WebsocketSession) -> None:
    """Test handling state messages."""
    events = []
    session.on("state", lambda state: events.append(("state", state)))

    await session._handle_data_message({"type": "state", "state": "listening"})
    assert session._state == "listening"
    assert events[0] == ("state", "listening")


@pytest.mark.asyncio
async def test_handle_transcript_message(session: WebsocketSession) -> None:
    """Test handling transcript messages."""
    events = []
    session.on("output", lambda text, final: events.append(("output", text, final)))

    # Test complete message
    await session._handle_data_message(
        {"type": "transcript", "role": "agent", "text": "Hello", "final": True}
    )
    assert events[0] == ("output", "Hello", True)
    assert session._pending_output == ""

    # Test incremental message
    await session._handle_data_message(
        {"type": "transcript", "role": "agent", "delta": "Hello ", "final": False}
    )
    await session._handle_data_message(
        {"type": "transcript", "role": "agent", "delta": "world", "final": True}
    )
    assert events[2] == ("output", "Hello world", True)
    assert session._pending_output == ""


@pytest.mark.asyncio
async def test_handle_client_tool_call(
    session: WebsocketSession, mock_socket: MagicMock
) -> None:
    """Test handling client tool calls."""
    session._socket = mock_socket

    # Test unknown tool
    await session._handle_client_tool_call("unknown_tool", "123", {"param": "value"})

    expected_response = {
        "type": "client_tool_result",
        "invocationId": "123",
        "errorType": "undefined",
        "errorMessage": "Unknown tool: unknown_tool",
    }
    mock_socket.send.assert_called_once_with(json.dumps(expected_response))

    # Test successful tool call
    mock_socket.send.reset_mock()

    async def tool_handler(params: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "success"}

    session.register_tool("test_tool", tool_handler)
    await session._handle_client_tool_call("test_tool", "456", {"param": "value"})

    expected_response = {
        "type": "client_tool_result",
        "invocationId": "456",
        "result": json.dumps({"result": "success"}),
    }
    mock_socket.send.assert_called_once_with(json.dumps(expected_response))

    # Test tool handler error
    mock_socket.send.reset_mock()

    async def error_handler(params: Dict[str, Any]) -> Dict[str, Any]:
        raise ValueError("Test error")

    session.register_tool("error_tool", error_handler)
    await session._handle_client_tool_call("error_tool", "789", {"param": "value"})

    expected_response = {
        "type": "client_tool_result",
        "invocationId": "789",
        "errorType": "ValueError",
        "errorMessage": "Test error",
    }
    mock_socket.send.assert_called_once_with(json.dumps(expected_response))


def test_register_tool(session: WebsocketSession) -> None:
    """Test registering tool handlers."""

    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "success"}

    session.register_tool("test_tool", handler)
    assert "test_tool" in session._tool_handlers
    assert session._tool_handlers["test_tool"] == handler
