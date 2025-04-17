import requests_mock
import unittest
from unittest.mock import patch, AsyncMock
import json
import httpx
from requests.exceptions import Timeout as RequestsTimeout


import confidence.confidence
from confidence.confidence import Confidence, DEFAULT_TIMEOUT_MS
from confidence.errors import ErrorCode
from confidence.flag_types import Reason


class TestConfidence(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.confidence = Confidence(client_secret="test")

    def test_resolve_string_with_dot_notation(self):
        with requests_mock.Mocker() as mock:
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
            self.assertEqual(result.value, "outer-string")
            self.assertEqual(result.variant, "enabled")
            self.assertEqual(result.reason, Reason.TARGETING_MATCH)

    def test_resolve_failed(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=NO_MATCH_STRING_FLAG_RESOLVE,
            )
            result = self.confidence.resolve_string_details(
                flag_key="some-flag-that-doesnt-exist",
                default_value="yellow",
            )

            self.assertEqual(result.reason, Reason.DEFAULT)
            self.assertEqual(
                result.flag_metadata["flag_key"], "some-flag-that-doesnt-exist"
            )
            self.assertEqual(result.value, "yellow")
            self.assertIsNone(result.variant)
            self.assertEqual(result.error_code, ErrorCode.FLAG_NOT_FOUND)
            self.assertEqual(
                result.error_message, "Flag some-flag-that-doesnt-exist not found"
            )

    def test_resolve_string_with_dot_notation_request_payload(self):
        with requests_mock.Mocker() as mock:
            confidence.confidence.__version__ = "v0.0.0"
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            self.confidence.with_context(
                {
                    "targeting_key": "boop",
                    "user": {"country": "US"},
                    "connection": "wifi",
                }
            ).resolve_string_details(
                flag_key="python-flag-1.string-key",
                default_value="yellow",
            )

            last_request = mock.request_history[-1]
            self.assertEqual(last_request.method, "POST")
            self.assertEqual(
                last_request.url, "https://resolver.confidence.dev/v1/flags:resolve"
            )
            self.assertEqual(
                last_request.json(),
                EXPECTED_REQUEST_PAYLOAD,
            )

    def test_resolve_successful_custom_url(self):
        self.confidence = Confidence(
            client_secret="test", custom_resolve_base_url="https://custom_url"
        )

        with requests_mock.Mocker() as mock:
            mock.post(
                "https://custom_url/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.confidence.resolve_object_details(
                flag_key="python-flag-1.struct-key",
                default_value={"key": "value"},
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.struct-key"
            )
            self.assertEqual(result.value, {"string-key": "inner-string"})

    def test_resolve_response_object_details(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.confidence.resolve_object_details(
                flag_key="python-flag-1",
                default_value={"key": "value"},
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(result.flag_metadata["flag_key"], "python-flag-1")
            self.assertEqual(
                result.value,
                {
                    "double-key": 42.42,
                    "enabled": True,
                    "int-key": 42,
                    "string-key": "outer-string",
                    "struct-key": {"string-key": "inner-string"},
                },
            )

    async def test_resolve_response_object_details_async(self):
        mock_response = httpx.Response(
            status_code=200,
            json=SUCCESSFUL_FLAG_RESOLVE,
            request=httpx.Request(
                "POST", "https://resolver.confidence.dev/v1/flags:resolve"
            ),
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await self.confidence.resolve_object_details_async(
                flag_key="python-flag-1", default_value={"key": "value"}
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(result.flag_metadata["flag_key"], "python-flag-1")
            self.assertEqual(
                result.value,
                {
                    "double-key": 42.42,
                    "enabled": True,
                    "int-key": 42,
                    "string-key": "outer-string",
                    "struct-key": {"string-key": "inner-string"},
                },
            )

    def test_resolve_struct_details(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.confidence.resolve_object_details(
                flag_key="python-flag-1.struct-key",
                default_value={"key": "value"},
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.struct-key"
            )
            self.assertEqual(result.value, {"string-key": "inner-string"})

    async def test_resolve_struct_details_async(self):
        mock_response = httpx.Response(
            status_code=200,
            json=SUCCESSFUL_FLAG_RESOLVE,
            request=httpx.Request(
                "POST", "https://resolver.confidence.dev/v1/flags:resolve"
            ),
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await self.confidence.resolve_object_details_async(
                flag_key="python-flag-1.struct-key", default_value={"key": "value"}
            )

            assert result.reason == Reason.TARGETING_MATCH
            assert result.flag_metadata["flag_key"] == "python-flag-1.struct-key"
            assert result.value == {"string-key": "inner-string"}

    def test_resolve_integer_details(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.confidence.resolve_integer_details(
                flag_key="python-flag-1.int-key",
                default_value=-1,
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(result.flag_metadata["flag_key"], "python-flag-1.int-key")
            self.assertEqual(result.value, 42)

    async def test_resolve_integer_details_async(self):
        mock_response = httpx.Response(
            status_code=200,
            json=SUCCESSFUL_FLAG_RESOLVE,
            request=httpx.Request(
                "POST", "https://resolver.confidence.dev/v1/flags:resolve"
            ),
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await self.confidence.resolve_integer_details_async(
                flag_key="python-flag-1.int-key", default_value=-1
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(result.flag_metadata["flag_key"], "python-flag-1.int-key")
            self.assertEqual(result.value, 42)

    def test_resolve_boolean_details(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.confidence.resolve_boolean_details(
                flag_key="python-flag-1.enabled",
                default_value=False,
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(result.flag_metadata["flag_key"], "python-flag-1.enabled")
            self.assertEqual(result.value, True)

    async def test_resolve_boolean_details_async(self):
        mock_response = httpx.Response(
            status_code=200,
            json=SUCCESSFUL_FLAG_RESOLVE,
            request=httpx.Request(
                "POST", "https://resolver.confidence.dev/v1/flags:resolve"
            ),
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await self.confidence.resolve_boolean_details_async(
                flag_key="python-flag-1.enabled", default_value=False
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(result.flag_metadata["flag_key"], "python-flag-1.enabled")
            self.assertEqual(result.value, True)

    def test_resolve_float_details(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.confidence.resolve_float_details(
                flag_key="python-flag-1.double-key",
                default_value=0.01,
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.double-key"
            )
            self.assertEqual(result.value, 42.42)

    async def test_resolve_float_details_async(self):
        mock_response = httpx.Response(
            status_code=200,
            json=SUCCESSFUL_FLAG_RESOLVE,
            request=httpx.Request(
                "POST", "https://resolver.confidence.dev/v1/flags:resolve"
            ),
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await self.confidence.resolve_float_details_async(
                flag_key="python-flag-1.double-key", default_value=0.01
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.double-key"
            )
            self.assertEqual(result.value, 42.42)

    def test_resolve_without_targeting_key(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.confidence.with_context(
                {"connection": "wifi"}
            ).resolve_string_details(
                flag_key="python-flag-1.string-key",
                default_value="brown",
            )
            self.assertIsNotNone(result.value)

            last_request = mock.request_history[-1]
            self.assertIsNone(
                last_request.json()["evaluationContext"].get("targeting_key"),
            )
            self.assertEqual(
                last_request.json()["evaluationContext"].get("connection"), "wifi"
            )

    def test_no_segment_match(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=NO_SEGMENT_MATCH_STRING_FLAG_RESOLVE,
            )
            result = self.confidence.with_context(
                {"connection": "wifi"}
            ).resolve_string_details(
                flag_key="test-flag.color",
                default_value="brown",
            )
            self.assertEqual(result.value, "brown")
            self.assertEqual(result.reason, Reason.DEFAULT)

    def test_resolve_with_timeout(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )

            with patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = SUCCESSFUL_FLAG_RESOLVE

                confidence_with_timeout = Confidence(
                    client_secret="test", timeout_ms=5500
                )
                confidence_with_timeout.resolve_string_details(
                    flag_key="python-flag-1.string-key",
                    default_value="yellow",
                )

                # Verify that timeout was passed to requests.post
                mock_post.assert_called_once()
                _, kwargs = mock_post.call_args
                self.assertEqual(kwargs["timeout"], 5.5)

    async def test_resolve_with_timeout_async(self):
        mock_response = httpx.Response(
            status_code=200,
            json=SUCCESSFUL_FLAG_RESOLVE,
            request=httpx.Request(
                "POST", "https://resolver.confidence.dev/v1/flags:resolve"
            ),
        )

        # Create an AsyncMock that returns an awaitable that resolves to mock_response
        mock_post = AsyncMock()
        mock_post.return_value = mock_response

        with patch("httpx.AsyncClient.post", mock_post):
            confidence_with_timeout = Confidence(client_secret="test", timeout_ms=3500)
            await confidence_with_timeout.resolve_string_details_async(
                flag_key="python-flag-1.string-key",
                default_value="yellow",
            )

            # Verify that timeout was passed to httpx.AsyncClient.post
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            self.assertEqual(kwargs["timeout"], 3.5)

    def test_resolve_with_default_timeout(self):
        """Test that the default timeout is used when timeout_ms is not provided."""
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )

            with patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = SUCCESSFUL_FLAG_RESOLVE

                # Create client without specifying timeout_ms
                confidence_default_timeout = Confidence(client_secret="test")
                confidence_default_timeout.resolve_string_details(
                    flag_key="python-flag-1.string-key",
                    default_value="yellow",
                )

                # Verify that default timeout (10 seconds) was passed to requests.post
                mock_post.assert_called_once()
                _, kwargs = mock_post.call_args
                self.assertEqual(kwargs["timeout"], DEFAULT_TIMEOUT_MS / 1000.0)

    async def test_resolve_with_default_timeout_async(self):
        mock_response = httpx.Response(
            status_code=200,
            json=SUCCESSFUL_FLAG_RESOLVE,
            request=httpx.Request(
                "POST", "https://resolver.confidence.dev/v1/flags:resolve"
            ),
        )

        # Create an AsyncMock that returns an awaitable that resolves to mock_response
        mock_post = AsyncMock()
        mock_post.return_value = mock_response

        with patch("httpx.AsyncClient.post", mock_post):
            # Create client without specifying timeout_ms
            confidence_default_timeout = Confidence(client_secret="test")
            await confidence_default_timeout.resolve_string_details_async(
                flag_key="python-flag-1.string-key",
                default_value="yellow",
            )

            # Verify that default timeout (10 seconds) was passed to
            # httpx.AsyncClient.post
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            self.assertEqual(kwargs["timeout"], DEFAULT_TIMEOUT_MS / 1000.0)

    def test_handle_actual_timeout(self):
        with patch("requests.post") as mock_post:
            # Simulate a timeout by raising the Timeout exception
            mock_post.side_effect = RequestsTimeout("Connection timed out")

            confidence_with_timeout = Confidence(client_secret="test", timeout_ms=100)

            # The operation should NOT raise an exception, but return default value
            result = confidence_with_timeout.resolve_string_details(
                flag_key="python-flag-1.string-key",
                default_value="yellow",
            )

            # Verify that default value was returned
            self.assertEqual(result.value, "yellow")
            self.assertEqual(result.reason, Reason.DEFAULT)
            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.string-key"
            )
            self.assertIsNone(result.variant)
            self.assertEqual(result.error_code, ErrorCode.TIMEOUT)

    async def test_handle_actual_timeout_async(self):
        # Create an AsyncMock that raises a timeout exception
        mock_post = AsyncMock()
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")

        with patch("httpx.AsyncClient.post", mock_post):
            confidence_with_timeout = Confidence(client_secret="test", timeout_ms=100)

            # The operation should NOT raise an exception, but return default value
            result = await confidence_with_timeout.resolve_string_details_async(
                flag_key="python-flag-1.string-key",
                default_value="yellow",
            )

            # Verify that default value was returned
            self.assertEqual(result.value, "yellow")
            self.assertEqual(result.reason, Reason.DEFAULT)
            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.string-key"
            )
            self.assertIsNone(result.variant)
            self.assertEqual(result.error_code, ErrorCode.TIMEOUT)

    if __name__ == "__main__":
        unittest.main()


NO_MATCH_STRING_FLAG_RESOLVE = json.loads(
    """{"resolvedFlags": [], "resolveToken": ""}"""
)

NO_SEGMENT_MATCH_STRING_FLAG_RESOLVE = json.loads(
    """{
  "resolveToken": "",
  "resolvedFlags": [
    {
      "flag": "flags/test-flag-2",
      "reason": "RESOLVE_REASON_NO_SEGMENT_MATCH",
      "variant": ""
    }
  ]
}"""
)

EXPECTED_REQUEST_PAYLOAD = json.loads(
    """{
  "clientSecret": "test",
  "evaluationContext": {
    "targeting_key": "boop",
    "user": { "country": "US" },
    "connection": "wifi"
  },
  "apply": true,
  "flags": ["flags/python-flag-1"],
  "sdk": {
    "id": "SDK_ID_PYTHON_CONFIDENCE",
    "version": "v0.0.0"
   }
}"""
)

SUCCESSFUL_FLAG_RESOLVE = json.loads(
    """{
     "resolvedFlags": [
    {
      "flag": "flags/python-flag-1",
      "variant": "flags/python-flag-1/variants/enabled",
      "value": {
        "struct-key": {
          "string-key": "inner-string"
        },
        "string-key": "outer-string",
        "double-key": 42.42,
        "int-key": 42,
        "enabled": true
      },
      "flagSchema": {
        "schema": {
          "struct-key": {
            "structSchema": {
              "schema": {
                "string-key": {
                  "stringSchema": {}
                }
              }
            }
          },
          "string-key": {
            "stringSchema": {}
          },
          "double-key": {
            "doubleSchema": {}
          },
          "int-key": {
            "intSchema": {}
          },
          "enabled": {
            "boolSchema": {}
          }
        }
      },
      "reason": "RESOLVE_REASON_MATCH"
    }
  ],
  "resolveToken": ""
    }"""
)
