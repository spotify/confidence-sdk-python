import dataclasses
import typing
from enum import Enum

import requests
from open_feature.evaluation_context.evaluation_context import EvaluationContext
from open_feature.exception.exceptions import (
    FlagNotFoundError,
    ParseError,
    TargetingKeyMissingError,
    TypeMismatchError,
)
from open_feature.flag_evaluation.flag_evaluation_details import FlagEvaluationDetails
from open_feature.flag_evaluation.reason import Reason
from open_feature.hooks.hook import Hook
from open_feature.provider.metadata import Metadata
from open_feature.provider.provider import AbstractProvider

from .names import FlagName, VariantName


EU_RESOLVE_API_ENDPOINT = "https://resolver.eu.confidence.dev/v1"
US_RESOLVE_API_ENDPOINT = "https://resolver.us.confidence.dev/v1"


class Region(Enum):
    def endpoint(self):
        return self.value

    EU = EU_RESOLVE_API_ENDPOINT
    US = US_RESOLVE_API_ENDPOINT


@dataclasses.dataclass
class ResolveResult(object):
    value: dict
    variant: str
    token: str


class ConfidenceOpenFeatureProvider(AbstractProvider):
    def __init__(self, client_secret: str, region: Region = Region.EU):
        self._client_secret = client_secret
        self._api_endpoint = region.endpoint()

    #
    # --- Provider API ---
    #

    def get_metadata(self) -> Metadata:
        return Metadata("confidence")

    def get_provider_hooks(self) -> typing.List[Hook]:
        return []

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[bool]:
        return self._evaluate(flag_key, bool, default_value, evaluation_context)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[float]:
        return self._evaluate(flag_key, float, default_value, evaluation_context)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[int]:
        return self._evaluate(flag_key, int, default_value, evaluation_context)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[str]:
        return self._evaluate(flag_key, str, default_value, evaluation_context)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: dict,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[dict]:
        return self._evaluate(flag_key, dict, default_value, evaluation_context)

    #
    # --- internals
    #

    def _evaluate(
        self,
        flag_key: str,
        value_type: typing.Type,
        default_value: typing.Any,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagEvaluationDetails[typing.Any]:
        if evaluation_context is None:
            evaluation_context = EvaluationContext()

        if "." in flag_key:
            flag_id, value_path = flag_key.split(".", 1)
        else:
            flag_id = flag_key
            value_path = None

        if evaluation_context.targeting_key is None:
            raise TargetingKeyMissingError("context is missing targeting key")

        context = {
            "targeting_key": evaluation_context.targeting_key,
            **(evaluation_context.attributes or {}),
        }

        result = self._resolve(FlagName(flag_id), context)
        if result.variant is None or len(result.value) == 0:
            return FlagEvaluationDetails(flag_key, default_value, reason=Reason.DEFAULT)

        variant_name = VariantName.parse(result.variant)

        value = self._select(result, value_path, value_type)
        if value is None:
            value = default_value

        return FlagEvaluationDetails(
            flag_key, value, variant_name.variant, reason=Reason.TARGETING_MATCH
        )

    def _resolve(self, flag_name: FlagName, context: dict) -> ResolveResult:
        request_body = {
            "clientSecret": self._client_secret,
            "evaluationContext": context,
            "apply": True,
            "flags": [flag_name.flag],
        }

        resolve_url = f"{self._api_endpoint}/flags:resolve"
        response = requests.post(resolve_url, json=request_body)

        if response.status_code == 404:
            raise FlagNotFoundError()

        response.raise_for_status()

        response_body = response.json()

        resolved_flags = response_body["resolvedFlags"]
        token = response_body["resolveToken"]
        resolved_flag = resolved_flags[0]
        return ResolveResult(resolved_flag["value"], resolved_flag["variant"], token)

    def _select(
        self,
        result: ResolveResult,
        value_path: str,
        value_type: typing.Type[bool | int | str | dict],
    ):
        value = result.value

        if value_path:
            keys = value_path.split(".")
            for key in keys:
                if not isinstance(value, dict):
                    raise ParseError()
                if key not in value:
                    raise ParseError()
                value = value.get(key)

        # skip type checking if the value was not specified
        if value is None:
            return None

        if not isinstance(value, value_type):
            raise TypeMismatchError("type of value did not match excepted type")

        return value
