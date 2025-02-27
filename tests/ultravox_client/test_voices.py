import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict

from ultravox_cli.ultravox_client.api.voices import VoicesAPI


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.request = AsyncMock()
    return client


@pytest.fixture
def voices_api(mock_client: MagicMock) -> VoicesAPI:
    return VoicesAPI(mock_client)


@pytest.mark.asyncio
async def test_list_voices(voices_api: VoicesAPI, mock_client: MagicMock) -> None:
    """Test listing voices."""
    mock_response = {"voices": [{"id": "1"}, {"id": "2"}]}
    mock_client.request.return_value = mock_response

    result = await voices_api.list(limit=10, offset=0)

    mock_client.request.assert_called_once_with(
        "GET", "voices", params={"limit": 10, "offset": 0}
    )
    assert result == mock_response


@pytest.mark.asyncio
async def test_get_voice(voices_api: VoicesAPI, mock_client: MagicMock) -> None:
    """Test getting a specific voice."""
    voice_id = "test_voice_id"
    mock_response = {"id": voice_id, "name": "test_voice"}
    mock_client.request.return_value = mock_response

    result = await voices_api.get(voice_id)

    mock_client.request.assert_called_once_with("GET", f"voices/{voice_id}")
    assert result == mock_response


@pytest.mark.asyncio
async def test_create_clone(voices_api: VoicesAPI, mock_client: MagicMock) -> None:
    """Test creating a voice clone."""
    mock_response = {"id": "new_voice", "name": "test_voice"}
    mock_client.request.return_value = mock_response

    # Test with minimal parameters
    name = "test_voice"
    result = await voices_api.create_clone(name=name)

    expected_body = {"name": name}
    mock_client.request.assert_called_once_with(
        "POST", "voices", json_data=expected_body
    )
    assert result == mock_response

    # Test with all parameters
    mock_client.request.reset_mock()
    description = "A test voice"
    audio_url = "https://example.com/audio.mp3"
    extra_param = "value"

    result = await voices_api.create_clone(
        name=name, description=description, audio_url=audio_url, extra_param=extra_param
    )

    expected_body = {
        "name": name,
        "description": description,
        "audioUrl": audio_url,
        "extra_param": extra_param,
    }

    mock_client.request.assert_called_once_with(
        "POST", "voices", json_data=expected_body
    )
    assert result == mock_response


@pytest.mark.asyncio
async def test_delete_voice(voices_api: VoicesAPI, mock_client: MagicMock) -> None:
    """Test deleting a voice."""
    voice_id = "test_voice_id"
    mock_response = {"status": "deleted"}
    mock_client.request.return_value = mock_response

    result = await voices_api.delete(voice_id)

    mock_client.request.assert_called_once_with("DELETE", f"voices/{voice_id}")
    assert result == mock_response
