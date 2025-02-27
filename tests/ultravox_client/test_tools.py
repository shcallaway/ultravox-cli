import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict

from ultravox_cli.ultravox_client.api.tools import ToolsAPI


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.request = AsyncMock()
    return client


@pytest.fixture
def tools_api(mock_client: MagicMock) -> ToolsAPI:
    return ToolsAPI(mock_client)


@pytest.mark.asyncio
async def test_list_tools(tools_api: ToolsAPI, mock_client: MagicMock) -> None:
    """Test listing tools."""
    mock_response = {"tools": [{"id": "1"}, {"id": "2"}]}
    mock_client.request.return_value = mock_response

    result = await tools_api.list(limit=10, offset=0)

    mock_client.request.assert_called_once_with(
        "GET", "tools", params={"limit": 10, "offset": 0}
    )
    assert result == mock_response


@pytest.mark.asyncio
async def test_get_tool(tools_api: ToolsAPI, mock_client: MagicMock) -> None:
    """Test getting a specific tool."""
    tool_id = "test_tool_id"
    mock_response = {"id": tool_id, "name": "test_tool"}
    mock_client.request.return_value = mock_response

    result = await tools_api.get(tool_id)

    mock_client.request.assert_called_once_with("GET", f"tools/{tool_id}")
    assert result == mock_response


@pytest.mark.asyncio
async def test_create_tool(tools_api: ToolsAPI, mock_client: MagicMock) -> None:
    """Test creating a new tool."""
    mock_response = {"id": "new_tool", "name": "test_tool"}
    mock_client.request.return_value = mock_response

    # Test with minimal parameters
    name = "test_tool"
    description = "A test tool"
    schema = {"type": "object", "properties": {}}

    result = await tools_api.create(name=name, description=description, schema=schema)

    expected_body = {"name": name, "description": description, "schema": schema}

    mock_client.request.assert_called_once_with(
        "POST", "tools", json_data=expected_body
    )
    assert result == mock_response

    # Test with function URL and additional parameters
    mock_client.request.reset_mock()
    function_url = "https://example.com/function"
    extra_param = "value"

    result = await tools_api.create(
        name=name,
        description=description,
        schema=schema,
        function_url=function_url,
        extra_param=extra_param,
    )

    expected_body = {
        "name": name,
        "description": description,
        "schema": schema,
        "functionUrl": function_url,
        "extra_param": extra_param,
    }

    mock_client.request.assert_called_once_with(
        "POST", "tools", json_data=expected_body
    )
    assert result == mock_response


@pytest.mark.asyncio
async def test_update_tool(tools_api: ToolsAPI, mock_client: MagicMock) -> None:
    """Test updating a tool."""
    tool_id = "test_tool_id"
    mock_response = {"id": tool_id, "name": "updated_tool"}
    mock_client.request.return_value = mock_response

    # Test with minimal parameters
    result = await tools_api.update(tool_id)
    mock_client.request.assert_called_once_with("PUT", f"tools/{tool_id}", json_data={})
    assert result == mock_response

    # Test with all parameters
    mock_client.request.reset_mock()
    name = "updated_tool"
    description = "Updated description"
    schema = {"type": "object", "properties": {"new": "property"}}
    function_url = "https://example.com/new-function"
    extra_param = "new_value"

    result = await tools_api.update(
        tool_id,
        name=name,
        description=description,
        schema=schema,
        function_url=function_url,
        extra_param=extra_param,
    )

    expected_body = {
        "name": name,
        "description": description,
        "schema": schema,
        "functionUrl": function_url,
        "extra_param": extra_param,
    }

    mock_client.request.assert_called_once_with(
        "PUT", f"tools/{tool_id}", json_data=expected_body
    )
    assert result == mock_response


@pytest.mark.asyncio
async def test_delete_tool(tools_api: ToolsAPI, mock_client: MagicMock) -> None:
    """Test deleting a tool."""
    tool_id = "test_tool_id"
    mock_response = {"status": "deleted"}
    mock_client.request.return_value = mock_response

    result = await tools_api.delete(tool_id)

    mock_client.request.assert_called_once_with("DELETE", f"tools/{tool_id}")
    assert result == mock_response
