from typing import Any, Dict, List, Optional
import urllib.parse


class CallsAPI:
    """
    API client for managing Ultravox calls.

    This class provides methods for creating, retrieving, and managing calls.
    """

    def __init__(self, client):
        """
        Initialize the Calls API client.

        Args:
            client: The UltravoxClient instance
        """
        self.client = client

    async def list(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        List all calls.

        Args:
            limit: Maximum number of calls to return
            offset: Offset for pagination

        Returns:
            List of calls
        """
        return await self.client.request(
            "GET", "calls", params={"limit": limit, "offset": offset}
        )

    async def get(self, call_id: str) -> Dict[str, Any]:
        """
        Get a specific call by ID.

        Args:
            call_id: The ID of the call to retrieve

        Returns:
            Call details
        """
        return await self.client.request("GET", f"calls/{call_id}")

    async def create(
        self,
        system_prompt: str,
        temperature: float = 0.8,
        voice: Optional[str] = None,
        selected_tools: Optional[List[Dict[str, Any]]] = None,
        initial_messages: Optional[List[Dict[str, Any]]] = None,
        initial_output_medium: str = "MESSAGE_MEDIUM_TEXT",
        medium: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new call.

        Args:
            system_prompt: The system prompt for the call
            temperature: Temperature for the model (0.0 to 1.0)
            voice: Optional voice ID or name
            selected_tools: Optional list of tools to enable for the call
            initial_messages: Optional list of initial messages
            initial_output_medium: Initial output medium (default: TEXT)
            medium: Optional medium configuration
            **kwargs: Additional parameters to include in the request

        Returns:
            Created call details including joinUrl
        """
        # Default medium configuration for websocket
        if medium is None:
            medium = {
                "serverWebSocket": {
                    "inputSampleRate": 48000,
                    "outputSampleRate": 48000,
                    "clientBufferSizeMs": 30000,
                }
            }

        body = {
            "systemPrompt": system_prompt,
            "temperature": temperature,
            "medium": medium,
            "initialOutputMedium": initial_output_medium,
            **kwargs,
        }

        if voice:
            body["voice"] = voice

        if selected_tools:
            body["selectedTools"] = selected_tools

        if initial_messages:
            body["initialMessages"] = initial_messages

        return await self.client.request("POST", "calls", json_data=body)

    async def get_messages(self, call_id: str) -> Dict[str, Any]:
        """
        Get messages for a specific call.

        Args:
            call_id: The ID of the call

        Returns:
            List of messages for the call
        """
        return await self.client.request("GET", f"calls/{call_id}/messages")

    async def get_tools(self, call_id: str) -> Dict[str, Any]:
        """
        Get tools used in a specific call.

        Args:
            call_id: The ID of the call

        Returns:
            List of tools used in the call
        """
        return await self.client.request("GET", f"calls/{call_id}/tools")

    async def get_recording(self, call_id: str) -> Dict[str, Any]:
        """
        Get recording for a specific call.

        Args:
            call_id: The ID of the call

        Returns:
            Recording details for the call
        """
        return await self.client.request("GET", f"calls/{call_id}/recording")

    def add_query_param(self, url: str, key: str, value: str) -> str:
        """
        Add a query parameter to a URL.

        Args:
            url: The URL to modify
            key: The parameter key
            value: The parameter value

        Returns:
            Modified URL with the added parameter
        """
        url_parts = list(urllib.parse.urlparse(url))
        query = dict(urllib.parse.parse_qsl(url_parts[4]))
        query.update({key: value})
        url_parts[4] = urllib.parse.urlencode(query)
        return urllib.parse.urlunparse(url_parts)
