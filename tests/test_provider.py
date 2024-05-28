import requests_mock
import unittest
import json

from openfeature.flag_evaluation import Reason

import confidence.confidence
from confidence.confidence import Confidence
from confidence.provider.provider import ConfidenceOpenFeatureProvider
from confidence.provider.provider import EvaluationContext
from confidence.provider.provider import Region
from confidence.provider import provider


class TestMyProvider(unittest.TestCase):
    def setUp(self):
        self.provider = ConfidenceOpenFeatureProvider(Confidence(client_secret="test"))

    def test_region_has_endpoint(self):
        assert Region.GLOBAL.endpoint()

    def test_resolve_string_with_dot_notation(self):
        ctx = EvaluationContext(targeting_key="boop")
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.provider.resolve_string_details(
                flag_key="python-flag-1.string-key",
                default_value="yellow",
                evaluation_context=ctx,
            )

            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.string-key"
            )
            self.assertEqual(result.value, "outer-string")
            self.assertEqual(result.variant, "enabled")
            self.assertEqual(result.reason, Reason.TARGETING_MATCH)

    def test_resolve_failed(self):
        ctx = EvaluationContext(targeting_key="boop")
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=NO_MATCH_STRING_FLAG_RESOLVE,
            )
            result = self.provider.resolve_string_details(
                flag_key="some-flag-that-doesnt-exist",
                default_value="yellow",
                evaluation_context=ctx,
            )

            self.assertEqual(result.reason, Reason.DEFAULT)
            self.assertEqual(
                result.flag_metadata["flag_key"], "some-flag-that-doesnt-exist"
            )
            self.assertEqual(result.value, "yellow")
            self.assertIsNone(result.variant)

    def test_resolve_string_with_dot_notation_request_payload(self):
        ctx = EvaluationContext(
            targeting_key="boop",
            attributes={"user": {"country": "US"}, "connection": "wifi"},
        )
        with requests_mock.Mocker() as mock:
            confidence.confidence.__version__ = "v0.0.0"
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            self.provider.resolve_string_details(
                flag_key="python-flag-1.string-key",
                default_value="yellow",
                evaluation_context=ctx,
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

    def test_resolve_response_object_details(self):
        ctx = EvaluationContext(
            targeting_key="boop",
        )
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.provider.resolve_object_details(
                flag_key="python-flag-1",
                default_value={"key": "value"},
                evaluation_context=ctx,
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
        ctx = EvaluationContext(
            targeting_key="boop",
        )
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.provider.resolve_object_details(
                flag_key="python-flag-1.struct-key",
                default_value={"key": "value"},
                evaluation_context=ctx,
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.struct-key"
            )
            self.assertEqual(result.value, {"string-key": "inner-string"})

    def test_resolve_integer_details(self):
        ctx = EvaluationContext(
            targeting_key="boop",
        )
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.provider.resolve_integer_details(
                flag_key="python-flag-1.int-key",
                default_value=-1,
                evaluation_context=ctx,
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(result.flag_metadata["flag_key"], "python-flag-1.int-key")
            self.assertEqual(result.value, 42)

    def test_resolve_boolean_details(self):
        ctx = EvaluationContext(
            targeting_key="boop",
        )
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.provider.resolve_boolean_details(
                flag_key="python-flag-1.enabled",
                default_value=False,
                evaluation_context=ctx,
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(result.flag_metadata["flag_key"], "python-flag-1.enabled")
            self.assertEqual(result.value, True)

    def test_resolve_float_details(self):
        ctx = EvaluationContext(
            targeting_key="boop",
        )
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.provider.resolve_float_details(
                flag_key="python-flag-1.double-key",
                default_value=0.01,
                evaluation_context=ctx,
            )

            self.assertEqual(result.reason, Reason.TARGETING_MATCH)
            self.assertEqual(
                result.flag_metadata["flag_key"], "python-flag-1.double-key"
            )
            self.assertEqual(result.value, 42.42)

    def test_resolve_without_targeting_key(self):
        ctx = EvaluationContext(
            attributes={"user": {"country": "US"}, "connection": "wifi"}
        )
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_FLAG_RESOLVE,
            )
            result = self.provider.resolve_string_details(
                flag_key="python-flag-1.string-key",
                default_value="brown",
                evaluation_context=ctx,
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
        ctx = EvaluationContext(attributes={"connection": "wifi"})
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.confidence.dev/v1/flags:resolve",
                json=NO_SEGMENT_MATCH_STRING_FLAG_RESOLVE,
            )
            result = self.provider.resolve_string_details(
                flag_key="test-flag.color",
                default_value="brown",
                evaluation_context=ctx,
            )
            self.assertEqual(result.value, "brown")
            self.assertEqual(result.reason, Reason.DEFAULT)

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
