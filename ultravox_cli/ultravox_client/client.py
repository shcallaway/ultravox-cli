import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

import aiohttp

from ultravox_cli.ultravox_client.api.calls import CallsAPI
from ultravox_cli.ultravox_client.api.tools import ToolsAPI
from ultravox_cli.ultravox_client.api.voices import VoicesAPI
from ultravox_cli.ultravox_client.session.websocket_session import WebsocketSession


class UltravoxClient:
    """
    Main client for interacting with the Ultravox API.

    This client provides access to all Ultravox API endpoints and functionality,
    including creating and managing calls, tools, and voices.

    Example:
        ```python
        client = UltravoxClient(api_key="your_api_key")

        # Create a call
        call = await client.calls.create(
            system_prompt="You are a helpful assistant.",
            voice="default"
        )

        # Join the call using WebSocket
        session = await client.join_call(call["joinUrl"])

        # Listen for events
        @session.on("state")
        async def on_state(state):
            print(f"State changed: {state}")

        @session.on("output")
        async def on_output(text, final):
            print(f"Output: {text}")

        # Start the session
        await session.start()

        # Stop the session when done
        await session.stop()
        ```
    """

    BASE_URL = "https://api.ultravox.ai/api"

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize the Ultravox client.

        Args:
            api_key: Your Ultravox API key
            base_url: Optional custom base URL for the Ultravox API
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.headers = {"X-API-Key": api_key}

        # Initialize API components
        self.calls = CallsAPI(self)
        self.tools = ToolsAPI(self)
        self.voices = VoicesAPI(self)

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Make a request to the Ultravox API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            params: Query parameters
            json_data: JSON body data

        Returns:
            Response data as JSON

        Raises:
            aiohttp.ClientError: If the request fails
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        logging.debug(f"Making request to {url} with method {method}")
        if json_data:
            logging.debug(f"Request body: {json_data}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=self.headers,
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"Request failed: {error_text}",
                        )
                    return await response.json()
        except aiohttp.ClientError as e:
            logging.error(f"Request failed: {e}")
            raise

    async def join_call(self, join_url: str) -> WebsocketSession:
        """
        Join a call using WebSocket.

        Args:
            join_url: The join URL for the call

        Returns:
            A WebsocketSession instance for interacting with the call
        """
        session = WebsocketSession(join_url)
        return session
