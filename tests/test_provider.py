import requests_mock
import unittest
from provider.provider import ConfidenceOpenFeatureProvider
from open_feature.evaluation_context.evaluation_context import EvaluationContext
from provider.provider import Region
from open_feature.open_feature_client import Reason
import test_resources


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
                json=test_resources.SUCCESSFUL_STRING_FLAG_RESOLVE,
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
                json=test_resources.NO_MATCH_STRING_FLAG_RESOLVE,
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
                json=test_resources.SUCCESSFUL_STRING_FLAG_RESOLVE,
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
                test_resources.EXPECTED_REQUEST_PAYLOAD,
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
                json=test_resources.SUCCESSFUL_STRING_FLAG_RESOLVE,
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
