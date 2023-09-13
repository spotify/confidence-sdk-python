import pytest
import requests_mock
from open_feature.evaluation_context import EvaluationContext

from provider.provider import ConfidenceOpenFeatureProvider
from tests.test_provider import SUCCESSFUL_FLAG_RESOLVE


@pytest.mark.parametrize(
    "apply_on_resolve",
    (
            (True, False)
    )
)
def test_apply_configurable(apply_on_resolve):
    ctx = EvaluationContext(targeting_key="meh")
    apply_provider = ConfidenceOpenFeatureProvider(
        client_secret="test", apply_on_resolve=apply_on_resolve
    )
    with requests_mock.Mocker() as mock:
        mock.post(
            "https://resolver.eu.confidence.dev/v1/flags:resolve",
            json=SUCCESSFUL_FLAG_RESOLVE,
        )

        apply_provider.resolve_string_details(
            flag_key="flags/python-flag-1.string-key",
            default_value="yellow",
            evaluation_context=ctx,
        )

        last_request = mock.request_history[-1]
        assert last_request.json()["apply"] == apply_on_resolve
