"""
Helper utilities for the Ultravox client library.

This module provides various utility functions used throughout the Ultravox client
library. These include:

- URL and query parameter formatting
- Logging configuration
- Validation utilities

These utilities are primarily used internally by the Ultravox client, but may also
be useful for applications that build on top of the client library.

Example:
    ```python
    from ultravox_cli.ultravox_client.helpers import format_query_params, setup_logger

    # Format query parameters for a URL
    params = {"limit": 10, "filter": "active", "include": ["user", "profile"]}
    query_string = format_query_params(params)
    # Returns "?limit=10&filter=active&include=[\"user\",\"profile\"]"

    # Set up a logger
    logger = setup_logger("my_app", logging.DEBUG)
    logger.debug("Debugging information")
    ```
"""

import json
import logging
from typing import Any, Dict, Optional


def format_query_params(params: Optional[Dict[str, Any]] = None) -> str:
    """
    Format query parameters for URL.

    Args:
        params: Dictionary of query parameters

    Returns:
        Formatted query string
    """
    if not params:
        return ""

    # Filter out None values
    filtered_params = {k: v for k, v in params.items() if v is not None}

    if not filtered_params:
        return ""

    # Convert values to strings
    param_strings = []
    for key, value in filtered_params.items():
        if isinstance(value, bool):
            param_strings.append(f"{key}={'true' if value else 'false'}")
        elif isinstance(value, (list, dict)):
            param_strings.append(f"{key}={json.dumps(value)}")
        else:
            param_strings.append(f"{key}={value}")

    return "?" + "&".join(param_strings)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and level.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create console handler if no handlers exist
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def validate_api_key(api_key: Optional[str]) -> None:
    """
    Validate that an API key is provided.

    Args:
        api_key: API key to validate

    Raises:
        ValueError: If API key is missing
    """
    if not api_key:
        raise ValueError(
            "API key is required. Set it when creating the client or "
            "via the ULTRAVOX_API_KEY environment variable."
        )
