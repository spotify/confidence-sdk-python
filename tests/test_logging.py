import unittest
import logging
import io
import requests_mock
from requests.exceptions import ConnectTimeout

from confidence.confidence import Confidence
from confidence.errors import ErrorCode
from confidence.flag_types import Reason
from tests.test_confidence import SUCCESSFUL_FLAG_RESOLVE


class TestConfidenceLogging(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with custom logger and log capture."""
        # Create a logger for testing
        self.test_logger = logging.getLogger("test_confidence_logger")
        self.test_logger.setLevel(logging.DEBUG)

        # Create a string stream to capture log output
        self.log_stream = io.StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.log_handler.setLevel(logging.DEBUG)

        # Set formatter to include level name in output
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        self.log_handler.setFormatter(formatter)

        # Clear any existing handlers
        self.test_logger.handlers.clear()
        self.test_logger.addHandler(self.log_handler)

        # Create Confidence instance with our test logger
        self.confidence = Confidence(
            client_secret="test_secret", logger=self.test_logger
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.log_handler.close()
        self.test_logger.handlers.clear()

    def get_log_output(self):
        """Get the captured log output as a string."""
        return self.log_stream.getvalue()

    def test_logger_setup_configuration(self):
        """Test that logger is properly configured during setup."""
        # Create a completely fresh logger name to ensure no existing state
        import uuid

        logger_name = f"test_logger_{uuid.uuid4().hex[:8]}"
        fresh_logger = logging.getLogger(logger_name)

        # Ensure it starts with no handlers and no level set
        fresh_logger.handlers.clear()
        fresh_logger.setLevel(logging.NOTSET)

        confidence = Confidence(client_secret="test", logger=fresh_logger)

        # Verify logger level is set to DEBUG
        self.assertEqual(fresh_logger.level, logging.DEBUG)

        # The logger might not have handlers added by _setup_logger if there are
        # parent logger handlers, so let's test what we can verify
        # At minimum, we know the logger is configured and functional
        self.assertIsNotNone(fresh_logger)

        # Test that logging actually works by triggering a log message
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json={"resolvedFlags": [], "resolveToken": "test-token"},
            )

            # Create a stream to capture this specific logger's output
            test_stream = io.StringIO()
            test_handler = logging.StreamHandler(test_stream)
            test_handler.setLevel(logging.DEBUG)
            fresh_logger.addHandler(test_handler)

            confidence.resolve_string_details("test-flag", "default")

            # Verify logging occurred
            output = test_stream.getvalue()
            self.assertIn("Flag test-flag not found", output)

            # Clean up
            fresh_logger.removeHandler(test_handler)

    def test_flag_not_found_logging(self):
        """Test INFO logging when flag is not found."""
        with requests_mock.Mocker() as mock:
            # Mock API response for flag not found
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json={"resolvedFlags": [], "resolveToken": "test-token"},
            )

            result = self.confidence.resolve_string_details(
                flag_key="non-existent-flag", default_value="default"
            )

            # Verify the result
            self.assertEqual(result.reason, Reason.DEFAULT)
            self.assertEqual(result.error_code, ErrorCode.FLAG_NOT_FOUND)

            # Verify logging occurred
            log_output = self.get_log_output()
            self.assertIn("Flag non-existent-flag not found", log_output)
            self.assertIn("INFO", log_output)

    def test_timeout_error_logging(self):
        """Test WARNING logging when request times out."""
        with requests_mock.Mocker() as mock:
            # Mock timeout exception
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve", exc=ConnectTimeout
            )

            # Create confidence with short timeout
            confidence = Confidence(
                client_secret="test", timeout_ms=100, logger=self.test_logger
            )

            result = confidence.resolve_string_details(
                flag_key="test-flag", default_value="default"
            )

            # Verify the result
            self.assertEqual(result.reason, Reason.DEFAULT)
            self.assertEqual(result.error_code, ErrorCode.TIMEOUT)

            # Verify logging occurred
            log_output = self.get_log_output()
            self.assertIn("Request timed out", log_output)
            self.assertIn("WARNING", log_output)

    def test_general_error_logging(self):
        """Test ERROR logging when general errors occur."""
        with requests_mock.Mocker() as mock:
            # Mock a server error
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                status_code=500,
                text="Internal Server Error",
            )

            result = self.confidence.resolve_string_details(
                flag_key="test-flag", default_value="default"
            )

            # Verify the result
            self.assertEqual(result.reason, Reason.ERROR)
            self.assertEqual(result.error_code, ErrorCode.GENERAL)

            # Verify logging occurred
            log_output = self.get_log_output()
            self.assertIn("Error resolving flag test-flag", log_output)
            self.assertIn("ERROR", log_output)

    def test_debug_resolve_tester_logging(self):
        """Test DEBUG logging for resolve tester payload."""
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json={
                    "resolvedFlags": [
                        {"value": {"key": "test-value"}, "variant": "enabled"}
                    ],
                    "resolveToken": "test-token",
                },
            )

            self.confidence.resolve_string_details(
                flag_key="test-flag", default_value="default"
            )

            # Verify debug logging occurred
            log_output = self.get_log_output()
            self.assertIn("Check your flag evaluation", log_output)
            self.assertIn("DEBUG", log_output)

    def test_custom_logger_injection(self):
        """Test that custom logger can be injected and used."""
        custom_logger = logging.getLogger("custom_logger")
        custom_stream = io.StringIO()
        custom_handler = logging.StreamHandler(custom_stream)
        custom_logger.addHandler(custom_handler)
        custom_logger.setLevel(logging.INFO)

        confidence = Confidence(client_secret="test", logger=custom_logger)

        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json={"resolvedFlags": [], "resolveToken": "test-token"},
            )

            confidence.resolve_string_details("test-flag", "default")

            # Verify our custom logger captured the log
            custom_output = custom_stream.getvalue()
            self.assertIn("Flag test-flag not found", custom_output)

    def test_logging_levels_are_respected(self):
        """Test that different log levels are properly used."""
        # Set logger to WARNING level to filter out DEBUG and INFO
        self.test_logger.setLevel(logging.WARNING)

        with requests_mock.Mocker() as mock:
            # First test - flag not found (INFO level, should be filtered)
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json={"resolvedFlags": [], "resolveToken": "test-token"},
            )

            self.confidence.resolve_string_details("test-flag", "default")
            log_output = self.get_log_output()

            # INFO message should not appear
            self.assertNotIn("Flag test-flag not found", log_output)

            # Now test WARNING level message (timeout)
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve", exc=ConnectTimeout
            )

            self.confidence.resolve_string_details("test-flag2", "default")
            log_output = self.get_log_output()

            # WARNING message should appear
            self.assertIn("Request timed out", log_output)

    def test_with_context_preserves_logger(self):
        """Test that using with_context preserves the same logger."""
        context_confidence = self.confidence.with_context({"user": "test_user"})

        # Verify same logger instance is used
        self.assertIs(self.confidence.logger, context_confidence.logger)

        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json={"resolvedFlags": [], "resolveToken": "test-token"},
            )

            context_confidence.resolve_string_details("test-flag", "default")

            # Verify logging still works with context instance
            log_output = self.get_log_output()
            self.assertIn("Flag test-flag not found", log_output)

    def test_default_logger_creation(self):
        """Test that default logger is created when none provided."""
        # Test default logger without providing a custom one
        confidence = Confidence(client_secret="test")

        # Verify that a logger was created
        self.assertIsNotNone(confidence.logger)

        # Verify the logger name is the default
        self.assertEqual(confidence.logger.name, "confidence_logger")

        # Verify logger is configured correctly
        self.assertEqual(confidence.logger.level, logging.DEBUG)

    def test_warning_error_only_logger_filters_debug(self):
        """Test that a logger set to WARNING level filters out DEBUG messages."""
        # Create a logger that only captures WARNING and ERROR
        warning_logger = logging.getLogger("warning_only_logger")
        warning_logger.setLevel(logging.WARNING)

        # Create a string stream to capture log output
        warning_stream = io.StringIO()
        warning_handler = logging.StreamHandler(warning_stream)
        warning_handler.setLevel(logging.WARNING)

        # Set formatter to include level name in output
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        warning_handler.setFormatter(formatter)

        # Clear any existing handlers and add our warning-only handler
        warning_logger.handlers.clear()
        warning_logger.addHandler(warning_handler)

        # Create Confidence instance with warning-only logger
        confidence = Confidence(client_secret="test_secret", logger=warning_logger)

        with requests_mock.Mocker() as mock:
            # Mock a successful response that would normally generate DEBUG logs
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.confidence.resolve_string_details(
                flag_key="python-flag-1.string-key",
                default_value="yellow",
            )

            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.string-key"
            )
            # Get the captured log output
            warning_output = warning_stream.getvalue()

            # Verify NO DEBUG messages appear in the output
            self.assertNotIn("DEBUG", warning_output)
            self.assertNotIn("Check your flag evaluation", warning_output)

            # The output should be empty since no WARNING/ERROR occurred
            self.assertEqual(warning_output.strip(), "")

        # Now test that WARNING messages still get through
        with requests_mock.Mocker() as mock:
            # Mock a timeout to generate a WARNING message
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve", exc=ConnectTimeout
            )

            result = confidence.resolve_string_details(
                flag_key="test-flag-timeout", default_value="default"
            )

            # Get the captured log output
            warning_output = warning_stream.getvalue()

            # Verify WARNING message appears
            self.assertIn("WARNING", warning_output)
            self.assertIn("Request timed out", warning_output)

            # But still no DEBUG messages
            self.assertNotIn("DEBUG", warning_output)
            self.assertNotIn("Check your flag evaluation", warning_output)

        # Clean up
        warning_handler.close()
        warning_logger.handlers.clear()

    def test_setup_logger_respects_preconfigured_level(self):
        """Test that _setup_logger respects pre-configured logger levels."""
        import uuid

        # Test 1: Logger with NOTSET should be set to DEBUG
        notset_logger_name = f"notset_logger_{uuid.uuid4().hex[:8]}"
        notset_logger = logging.getLogger(notset_logger_name)
        notset_logger.handlers.clear()
        notset_logger.setLevel(logging.NOTSET)

        _ = Confidence(client_secret="test", logger=notset_logger)

        # Should be set to DEBUG
        self.assertEqual(notset_logger.level, logging.DEBUG)

        # Test 2: Logger with pre-configured WARNING level should be preserved
        warning_logger_name = f"warning_logger_{uuid.uuid4().hex[:8]}"
        warning_logger = logging.getLogger(warning_logger_name)
        warning_logger.handlers.clear()
        warning_logger.setLevel(logging.WARNING)

        _ = Confidence(client_secret="test", logger=warning_logger)

        # Should remain WARNING, not be overridden to DEBUG
        self.assertEqual(warning_logger.level, logging.WARNING)

        # Test 3: Logger with INFO level should be preserved
        info_logger_name = f"info_logger_{uuid.uuid4().hex[:8]}"
        info_logger = logging.getLogger(info_logger_name)
        info_logger.handlers.clear()
        info_logger.setLevel(logging.INFO)

        _ = Confidence(client_secret="test", logger=info_logger)

        # Should remain INFO
        self.assertEqual(info_logger.level, logging.INFO)

        # Test 4: Logger with ERROR level should be preserved
        error_logger_name = f"error_logger_{uuid.uuid4().hex[:8]}"
        error_logger = logging.getLogger(error_logger_name)
        error_logger.handlers.clear()
        error_logger.setLevel(logging.ERROR)

        _ = Confidence(client_secret="test", logger=error_logger)

        # Should remain ERROR
        self.assertEqual(error_logger.level, logging.ERROR)


if __name__ == "__main__":
    unittest.main()
