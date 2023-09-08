import requests_mock
import unittest
import json
from provider.provider import ConfidenceOpenFeatureProvider
from provider.provider import EvaluationContext
from provider.provider import Region
from provider.provider import Reason


class TestMyProvider(unittest.TestCase):
    def setUp(self):
        self.provider = ConfidenceOpenFeatureProvider(client_secret="test")

    def test_region_has_endpoint(self):
        assert Region.EU.endpoint()

    def test_resolve_string_with_dot_notation(self):
        ctx = EvaluationContext(targeting_key="boop")
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.eu.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_STRING_FLAG_RESOLVE,
            )
            result = self.provider.resolve_string_details(
                flag_key="test-flag.color",
                default_value="yellow",
                evaluation_context=ctx,
            )

            self.assertEqual(result.flag_key, "test-flag.color")
            self.assertEqual(result.value, "red")
            self.assertEqual(result.variant, "control")
            self.assertEqual(result.reason, Reason.TARGETING_MATCH)

    def test_resolve_failed(self):
        ctx = EvaluationContext(targeting_key="boop")
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.eu.confidence.dev/v1/flags:resolve",
                json=NO_MATCH_STRING_FLAG_RESOLVE,
            )
            result = self.provider.resolve_string_details(
                flag_key="some-flag-that-doesnt-exist",
                default_value="yellow",
                evaluation_context=ctx,
            )

            self.assertEqual(result.reason, Reason.DEFAULT)
            self.assertEqual(result.flag_key, "some-flag-that-doesnt-exist")
            self.assertEqual(result.value, "yellow")
            self.assertIsNone(result.variant)

    def test_resolve_string_with_dot_notation_request_payload(self):
        ctx = EvaluationContext(
            targeting_key="boop",
            attributes={"user": {"country": "US"}, "connection": "wifi"},
        )
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.eu.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_STRING_FLAG_RESOLVE,
            )
            self.provider.resolve_string_details(
                flag_key="test-flag.color",
                default_value="yellow",
                evaluation_context=ctx,
            )

            last_request = mock.request_history[-1]
            self.assertEqual(last_request.method, "POST")
            self.assertEqual(
                last_request.url, "https://resolver.eu.confidence.dev/v1/flags:resolve"
            )
            self.assertEqual(
                last_request.json(),
                EXPECTED_REQUEST_PAYLOAD,
            )

    def test_apply_configurable(self):
        ctx = EvaluationContext(targeting_key="meh")
        apply_false_provider = ConfidenceOpenFeatureProvider(
            client_secret="test", apply_on_resolve=False
        )
        apply_true_provider = ConfidenceOpenFeatureProvider(
            client_secret="test", apply_on_resolve=True
        )
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://resolver.eu.confidence.dev/v1/flags:resolve",
                json=SUCCESSFUL_STRING_FLAG_RESOLVE,
            )

            apply_false_provider.resolve_string_details(
                flag_key="test-flag.color",
                default_value="yellow",
                evaluation_context=ctx,
            )

            last_request = mock.request_history[-1]
            self.assertEqual(last_request.json()["apply"], False)

            apply_true_provider.resolve_string_details(
                flag_key="test-flag.color",
                default_value="yellow",
                evaluation_context=ctx,
            )

            last_request = mock.request_history[-1]
            self.assertEqual(last_request.json()["apply"], True)

    if __name__ == "__main__":
        unittest.main()


SUCCESSFUL_STRING_FLAG_RESOLVE = json.loads(
    """{
 "resolvedFlags": [
  {
   "flag": "flags/test-flag",
   "variant": "flags/test-flag/variants/control",
   "value": {
    "color": "red"
   },
   "flagSchema": {
    "schema": {
     "color": {
      "stringSchema": {}
     }
    }
   },
   "reason": "RESOLVE_REASON_MATCH"
  }
 ],
 "resolveToken": ""
}"""
)

NO_MATCH_STRING_FLAG_RESOLVE = json.loads(
    """{"resolvedFlags": [], "resolveToken": ""}"""
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
  "flags": ["test-flag"]
}"""
)
