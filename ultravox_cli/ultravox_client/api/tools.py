from typing import Any, Dict, List, Optional, TypeVar, cast

T = TypeVar("T", bound="ToolsAPI")


class ToolsAPI:
    """
    API client for managing Ultravox tools.

    This class provides methods for creating, retrieving, and managing tools.
    """

    def __init__(self, client: Any) -> None:
        """
        Initialize the Tools API client.

        Args:
            client: The UltravoxClient instance
        """
        self.client = client

    async def list(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        List all tools.

        Args:
            limit: Maximum number of tools to return
            offset: Offset for pagination

        Returns:
            List of tools
        """
        result = await self.client.request(
            "GET", "tools", params={"limit": limit, "offset": offset}
        )
        return cast(Dict[str, Any], result)

    async def get(self, tool_id: str) -> Dict[str, Any]:
        """
        Get a specific tool by ID.

        Args:
            tool_id: The ID of the tool to retrieve

        Returns:
            Tool details
        """
        result = await self.client.request("GET", f"tools/{tool_id}")
        return cast(Dict[str, Any], result)

    async def create(
        self,
        name: str,
        description: str,
        schema: Dict[str, Any],
        function_url: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new tool.

        Args:
            name: The name of the tool
            description: Description of what the tool does
            schema: JSON schema for the tool parameters
            function_url: Optional URL for the tool function
            **kwargs: Additional parameters to include in the request

        Returns:
            Created tool details
        """
        body = {"name": name, "description": description, "schema": schema, **kwargs}

        if function_url:
            body["functionUrl"] = function_url

        result = await self.client.request("POST", "tools", json_data=body)
        return cast(Dict[str, Any], result)

    async def update(
        self,
        tool_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        function_url: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Update an existing tool.

        Args:
            tool_id: The ID of the tool to update
            name: Optional new name for the tool
            description: Optional new description
            schema: Optional new schema
            function_url: Optional new function URL
            **kwargs: Additional parameters to include in the request

        Returns:
            Updated tool details
        """
        body = {**kwargs}

        if name:
            body["name"] = name

        if description:
            body["description"] = description

        if schema:
            body["schema"] = schema

        if function_url:
            body["functionUrl"] = function_url

        result = await self.client.request("PUT", f"tools/{tool_id}", json_data=body)
        return cast(Dict[str, Any], result)

    async def delete(self, tool_id: str) -> Dict[str, Any]:
        """
        Delete a tool.

        Args:
            tool_id: The ID of the tool to delete

        Returns:
            Deletion confirmation
        """
        result = await self.client.request("DELETE", f"tools/{tool_id}")
        return cast(Dict[str, Any], result)
