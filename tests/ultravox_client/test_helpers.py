import json
import logging
import pytest
from unittest.mock import patch, MagicMock

from ultravox_cli.ultravox_client.helpers import (
    format_query_params,
    setup_logger,
    validate_api_key,
)


class TestFormatQueryParams:
    """Tests for the format_query_params function."""

    def test_empty_params(self):
        """Test with empty or None parameters."""
        assert format_query_params(None) == ""
        assert format_query_params({}) == ""

    def test_none_values(self):
        """Test that None values are filtered out."""
        params = {"param1": "value1", "param2": None, "param3": "value3"}
        result = format_query_params(params)
        assert "param1=value1" in result
        assert "param3=value3" in result
        assert "param2" not in result

    def test_boolean_values(self):
        """Test that boolean values are properly formatted."""
        params = {"param1": True, "param2": False}
        result = format_query_params(params)
        assert "param1=true" in result
        assert "param2=false" in result

    def test_complex_values(self):
        """Test that lists and dictionaries are JSON serialized."""
        params = {"list_param": [1, 2, 3], "dict_param": {"key": "value"}}
        result = format_query_params(params)
        assert f"list_param={json.dumps([1, 2, 3])}" in result
        assert f"dict_param={json.dumps({'key': 'value'})}" in result

    def test_multiple_params(self):
        """Test with multiple parameters of different types."""
        params = {
            "string": "value",
            "number": 123,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
        }
        result = format_query_params(params)

        # Check that the result starts with a question mark
        assert result.startswith("?")

        # Check that all parameters are included
        assert "string=value" in result
        assert "number=123" in result
        assert "boolean=true" in result
        assert f"list={json.dumps([1, 2, 3])}" in result
        assert f"dict={json.dumps({'key': 'value'})}" in result

        # Check that parameters are separated by ampersands
        assert "&" in result


class TestSetupLogger:
    """Tests for the setup_logger function."""

    def test_logger_creation(self):
        """Test creating a new logger."""
        with patch("logging.getLogger") as mock_get_logger:
            # Setup mock logger
            mock_logger = MagicMock()
            mock_logger.handlers = []
            mock_get_logger.return_value = mock_logger

            # Call the function
            result = setup_logger("test_logger")

            # Verify the logger was configured correctly
            mock_get_logger.assert_called_once_with("test_logger")
            assert result == mock_logger
            assert mock_logger.setLevel.called
            assert len(mock_logger.addHandler.mock_calls) == 1

    def test_logger_with_existing_handlers(self):
        """Test that no new handlers are added if handlers already exist."""
        with patch("logging.getLogger") as mock_get_logger:
            # Setup mock logger with existing handlers
            mock_logger = MagicMock()
            mock_logger.handlers = [MagicMock()]  # Existing handler
            mock_get_logger.return_value = mock_logger

            # Call the function
            result = setup_logger("test_logger")

            # Verify no new handlers were added
            assert result == mock_logger
            assert not mock_logger.addHandler.called

    def test_custom_log_level(self):
        """Test setting a custom log level."""
        with patch("logging.getLogger") as mock_get_logger:
            # Setup mock logger
            mock_logger = MagicMock()
            mock_logger.handlers = []
            mock_get_logger.return_value = mock_logger

            # Call the function with custom log level
            setup_logger("test_logger", level=logging.DEBUG)

            # Verify the logger was configured with the custom level
            mock_logger.setLevel.assert_called_once_with(logging.DEBUG)


class TestValidateApiKey:
    """Tests for the validate_api_key function."""

    def test_valid_api_key(self):
        """Test with a valid API key."""
        # Should not raise an exception
        validate_api_key("valid_api_key")

    def test_none_api_key(self):
        """Test with None API key."""
        with pytest.raises(ValueError) as excinfo:
            validate_api_key(None)
        assert "API key is required" in str(excinfo.value)

    def test_empty_api_key(self):
        """Test with empty string API key."""
        with pytest.raises(ValueError) as excinfo:
            validate_api_key("")
        assert "API key is required" in str(excinfo.value)
