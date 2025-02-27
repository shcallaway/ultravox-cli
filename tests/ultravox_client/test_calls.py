import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict

from ultravox_cli.ultravox_client.api.calls import CallsAPI


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.request = AsyncMock()
    return client


@pytest.fixture
def calls_api(mock_client: MagicMock) -> CallsAPI:
    return CallsAPI(mock_client)


@pytest.mark.asyncio
async def test_list_calls(calls_api: CallsAPI, mock_client: MagicMock) -> None:
    """Test listing calls."""
    mock_response = {"calls": [{"id": "1"}, {"id": "2"}]}
    mock_client.request.return_value = mock_response

    result = await calls_api.list(limit=10, offset=0)
    
    mock_client.request.assert_called_once_with(
        "GET", "calls", params={"limit": 10, "offset": 0}
    )
    assert result == mock_response


@pytest.mark.asyncio
async def test_get_call(calls_api: CallsAPI, mock_client: MagicMock) -> None:
    """Test getting a specific call."""
    call_id = "test_call_id"
    mock_response = {"id": call_id, "status": "active"}
    mock_client.request.return_value = mock_response

    result = await calls_api.get(call_id)
    
    mock_client.request.assert_called_once_with("GET", f"calls/{call_id}")
    assert result == mock_response


@pytest.mark.asyncio
async def test_create_call(calls_api: CallsAPI, mock_client: MagicMock) -> None:
    """Test creating a new call."""
    mock_response = {"id": "new_call", "joinUrl": "wss://example.com/join"}
    mock_client.request.return_value = mock_response

    # Test with minimal parameters
    result = await calls_api.create(system_prompt="Test prompt")
    
    expected_body = {
        "systemPrompt": "Test prompt",
        "temperature": 0.8,
        "medium": {
            "serverWebSocket": {
                "inputSampleRate": 48000,
                "outputSampleRate": 48000,
                "clientBufferSizeMs": 30000,
            }
        },
        "initialOutputMedium": "MESSAGE_MEDIUM_TEXT",
    }
    
    mock_client.request.assert_called_once_with("POST", "calls", json_data=expected_body)
    assert result == mock_response

    # Test with all parameters
    mock_client.request.reset_mock()
    voice = "test_voice"
    tools = [{"name": "test_tool"}]
    messages = [{"role": "user", "content": "Hello"}]
    medium = {"custom": "config"}

    result = await calls_api.create(
        system_prompt="Test prompt",
        temperature=0.5,
        voice=voice,
        selected_tools=tools,
        initial_messages=messages,
        medium=medium,
        extra_param="value"
    )

    expected_body = {
        "systemPrompt": "Test prompt",
        "temperature": 0.5,
        "medium": medium,
        "initialOutputMedium": "MESSAGE_MEDIUM_TEXT",
        "voice": voice,
        "selectedTools": tools,
        "initialMessages": messages,
        "extra_param": "value"
    }

    mock_client.request.assert_called_once_with("POST", "calls", json_data=expected_body)
    assert result == mock_response


@pytest.mark.asyncio
async def test_get_messages(calls_api: CallsAPI, mock_client: MagicMock) -> None:
    """Test getting messages for a call."""
    call_id = "test_call_id"
    mock_response = {"messages": [{"role": "user", "content": "Hello"}]}
    mock_client.request.return_value = mock_response

    result = await calls_api.get_messages(call_id)
    
    mock_client.request.assert_called_once_with("GET", f"calls/{call_id}/messages")
    assert result == mock_response


@pytest.mark.asyncio
async def test_get_tools(calls_api: CallsAPI, mock_client: MagicMock) -> None:
    """Test getting tools for a call."""
    call_id = "test_call_id"
    mock_response = {"tools": [{"name": "test_tool"}]}
    mock_client.request.return_value = mock_response

    result = await calls_api.get_tools(call_id)
    
    mock_client.request.assert_called_once_with("GET", f"calls/{call_id}/tools")
    assert result == mock_response


@pytest.mark.asyncio
async def test_get_recording(calls_api: CallsAPI, mock_client: MagicMock) -> None:
    """Test getting recording for a call."""
    call_id = "test_call_id"
    mock_response = {"url": "https://example.com/recording.mp3"}
    mock_client.request.return_value = mock_response

    result = await calls_api.get_recording(call_id)
    
    mock_client.request.assert_called_once_with("GET", f"calls/{call_id}/recording")
    assert result == mock_response


def test_add_query_param(calls_api: CallsAPI) -> None:
    """Test adding query parameters to URLs."""
    url = "https://example.com/path?existing=value"
    result = calls_api.add_query_param(url, "new", "param")
    assert "existing=value" in result
    assert "new=param" in result

    # Test with no existing query parameters
    url = "https://example.com/path"
    result = calls_api.add_query_param(url, "key", "value")
    assert result == "https://example.com/path?key=value" 
