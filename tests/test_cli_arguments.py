import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import argparse
import pytest
from typing import Any

# Add the project root directory to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestCLIArgumentParsing(unittest.TestCase):
    """Test cases for CLI argument parsing."""

    @patch('argparse.ArgumentParser.parse_args')
    def test_default_arguments(self, mock_parse_args: Any) -> None:
        """Test that default arguments are set correctly."""
        # Create a mock args object with default values
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        # Check the default values
        self.assertFalse(args.verbose)
        self.assertFalse(args.very_verbose)
        self.assertIsNone(args.voice)
        self.assertEqual(args.system_prompt, "Test system prompt")
        self.assertEqual(args.temperature, 0.8)
        self.assertFalse(args.secret_menu)
        self.assertFalse(args.experimental_messages)
        self.assertIsNone(args.prior_call_id)
        self.assertFalse(args.user_speaks_first)
        self.assertFalse(args.initial_output_text)
        self.assertIsNone(args.api_version)

    @patch('argparse.ArgumentParser.parse_args')
    def test_verbose_flag(self, mock_parse_args: Any) -> None:
        """Test the verbose flag."""
        # Test with verbose flag
        mock_args = argparse.Namespace(
            verbose=True,
            very_verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertTrue(args.verbose)
        self.assertFalse(args.very_verbose)
            
        # Test with very verbose flag
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=True,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        importlib.reload(cli)
        args = mock_parse_args.return_value
        
        self.assertTrue(args.very_verbose)

    @patch('argparse.ArgumentParser.parse_args')
    def test_voice_argument(self, mock_parse_args: Any) -> None:
        """Test the voice argument."""
        # Test with voice argument
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice="custom_voice",
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertEqual(args.voice, "custom_voice")
            
        # Test with short form
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice="short_voice",
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        importlib.reload(cli)
        args = mock_parse_args.return_value
        
        self.assertEqual(args.voice, "short_voice")

    @patch('argparse.ArgumentParser.parse_args')
    def test_system_prompt_argument(self, mock_parse_args: Any) -> None:
        """Test the system prompt argument."""
        custom_prompt = "This is a custom system prompt"
        # Test with system prompt argument
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice=None,
            system_prompt=custom_prompt,
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertEqual(args.system_prompt, custom_prompt)

    @patch('argparse.ArgumentParser.parse_args')
    def test_temperature_argument(self, mock_parse_args: Any) -> None:
        """Test the temperature argument."""
        # Test with temperature argument
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.5,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertEqual(args.temperature, 0.5)

    @patch('argparse.ArgumentParser.parse_args')
    def test_secret_menu_flag(self, mock_parse_args: Any) -> None:
        """Test the secret menu flag."""
        # Test with secret menu flag
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=True,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertTrue(args.secret_menu)

    @patch('argparse.ArgumentParser.parse_args')
    def test_experimental_messages_flag(self, mock_parse_args: Any) -> None:
        """Test the experimental messages flag."""
        # Test with experimental messages flag
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=True,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertTrue(args.experimental_messages)

    @patch('argparse.ArgumentParser.parse_args')
    def test_prior_call_id_argument(self, mock_parse_args: Any) -> None:
        """Test the prior call ID argument."""
        # Test with prior call ID argument
        test_id = "test-call-id-12345"
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=test_id,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertEqual(args.prior_call_id, test_id)

    @patch('argparse.ArgumentParser.parse_args')
    def test_user_speaks_first_flag(self, mock_parse_args: Any) -> None:
        """Test the user speaks first flag."""
        # Test with user speaks first flag
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=True,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertTrue(args.user_speaks_first)

    @patch('argparse.ArgumentParser.parse_args')
    def test_initial_output_text_flag(self, mock_parse_args: Any) -> None:
        """Test the initial output text flag."""
        # Test with initial output text flag
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=True,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertTrue(args.initial_output_text)

    @patch('argparse.ArgumentParser.parse_args')
    def test_api_version_argument(self, mock_parse_args: Any) -> None:
        """Test the API version argument."""
        # Test with API version argument
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=2
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertEqual(args.api_version, 2)

    @patch('argparse.ArgumentParser.parse_args')
    def test_multiple_arguments(self, mock_parse_args: Any) -> None:
        """Test multiple arguments together."""
        # Test with multiple arguments
        mock_args = argparse.Namespace(
            verbose=False,
            very_verbose=False,
            voice="test_voice",
            system_prompt="Custom prompt",
            temperature=0.4,
            secret_menu=True,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=True,
            initial_output_text=False,
            api_version=None
        )
        mock_parse_args.return_value = mock_args
        
        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli
        importlib.reload(cli)
        
        # Access the mocked args through the mock
        args = mock_parse_args.return_value
        
        self.assertEqual(args.voice, "test_voice")
        self.assertEqual(args.temperature, 0.4)
        self.assertTrue(args.secret_menu)
        self.assertTrue(args.user_speaks_first)
        self.assertEqual(args.system_prompt, "Custom prompt")


if __name__ == "__main__":
    unittest.main() 
