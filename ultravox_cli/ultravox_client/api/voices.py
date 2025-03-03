"""
API client for Ultravox Voices service.

This module provides the VoicesAPI class for interacting with the Voices endpoints
of the Ultravox API. It enables listing, retrieving, creating, and deleting voice
profiles that can be used for text-to-speech in calls.

The Voices API allows you to:
- List available voices
- Get details about specific voices
- Create custom voice clones from audio samples
- Delete custom voices

Example:
    ```python
    from ultravox_cli.ultravox_client import UltravoxClient

    async def example():
        client = UltravoxClient(api_key="your_api_key")

        # List available voices
        voices = await client.voices.list()
        print(f"Available voices: {[v['name'] for v in voices['voices']]}")

        # Create a new voice clone
        new_voice = await client.voices.create_clone(
            name="My Custom Voice",
            description="A custom voice for my application",
            audio_url="https://example.com/my_audio_sample.mp3"
        )
        print(f"Created voice with ID: {new_voice['id']}")

        # Get details about a specific voice
        voice_id = new_voice["id"]
        voice_details = await client.voices.get(voice_id)
        print(f"Voice details: {voice_details}")
    ```
"""

from typing import Any, Dict, Optional, TypeVar, cast

T = TypeVar("T", bound="VoicesAPI")


class VoicesAPI:
    """
    API client for managing Ultravox voices.

    This class provides methods for listing, retrieving, and managing voices.
    """

    def __init__(self, client: Any) -> None:
        """
        Initialize the Voices API client.

        Args:
            client: The UltravoxClient instance
        """
        self.client = client

    async def list(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        List all available voices.

        Args:
            limit: Maximum number of voices to return
            offset: Offset for pagination

        Returns:
            List of voices
        """
        result = await self.client.request(
            "GET", "voices", params={"limit": limit, "offset": offset}
        )
        return cast(Dict[str, Any], result)

    async def get(self, voice_id: str) -> Dict[str, Any]:
        """
        Get a specific voice by ID.

        Args:
            voice_id: The ID of the voice to retrieve

        Returns:
            Voice details
        """
        result = await self.client.request("GET", f"voices/{voice_id}")
        return cast(Dict[str, Any], result)

    async def create_clone(
        self,
        name: str,
        description: Optional[str] = None,
        audio_url: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create (clone) a new voice.

        Args:
            name: The name of the voice
            description: Optional description of the voice
            audio_url: Optional URL to audio sample for cloning
            **kwargs: Additional parameters to include in the request

        Returns:
            Created voice details
        """
        body = {"name": name, **kwargs}

        if description:
            body["description"] = description

        if audio_url:
            body["audioUrl"] = audio_url

        result = await self.client.request("POST", "voices", json_data=body)
        return cast(Dict[str, Any], result)

    async def delete(self, voice_id: str) -> Dict[str, Any]:
        """
        Delete a voice.

        Args:
            voice_id: The ID of the voice to delete

        Returns:
            Deletion confirmation
        """
        result = await self.client.request("DELETE", f"voices/{voice_id}")
        return cast(Dict[str, Any], result)
