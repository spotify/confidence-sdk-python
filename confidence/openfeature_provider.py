import dataclasses
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_args,
)

import openfeature.exception as open_feature_exception

import openfeature.exception
from openfeature.api import EvaluationContext
from openfeature.api import Hook
from openfeature.flag_evaluation import FlagResolutionDetails
from openfeature.provider.metadata import Metadata
from openfeature.provider.provider import AbstractProvider
from typing_extensions import TypeGuard

import confidence.confidence
from confidence.errors import ErrorCode

EU_RESOLVE_API_ENDPOINT = "https://resolver.eu.confidence.dev/v1"
US_RESOLVE_API_ENDPOINT = "https://resolver.us.confidence.dev/v1"
GLOBAL_RESOLVE_API_ENDPOINT = "https://resolver.confidence.dev/v1"


Primitive = Union[str, int, float, bool, None]
FieldType = Union[Primitive, List[Primitive], List["Object"], "Object"]
Object = Dict[str, FieldType]


def is_primitive(field_type: Type[Any]) -> TypeGuard[Type[Primitive]]:
    return field_type in get_args(Primitive)


def primitive_matches(value: FieldType, value_type: Type[Primitive]) -> bool:
    return (
        value_type is None
        or (value_type is int and isinstance(value, int))
        or (value_type is float and isinstance(value, float))
        or (value_type is str and isinstance(value, str))
        or (value_type is bool and isinstance(value, bool))
    )


class Region(Enum):
    def endpoint(self) -> str:
        return self.value

    EU = EU_RESOLVE_API_ENDPOINT
    US = US_RESOLVE_API_ENDPOINT
    GLOBAL = GLOBAL_RESOLVE_API_ENDPOINT


@dataclasses.dataclass
class ResolveResult(object):
    value: Optional[Object]
    variant: Optional[str]
    token: str


def _to_openfeature_error_code(
    error_code: Optional[ErrorCode],
) -> Optional[open_feature_exception.ErrorCode]:
    """
    Convert a confidence error code to an openfeature error code
    :param error_code:
    :return:
    """
    if error_code is None:
        return None
    if error_code is ErrorCode.FLAG_NOT_FOUND:
        return openfeature.exception.ErrorCode.FLAG_NOT_FOUND
    if error_code is ErrorCode.TYPE_MISMATCH:
        return openfeature.exception.ErrorCode.TYPE_MISMATCH
    if error_code is ErrorCode.TARGETING_KEY_MISSING:
        return openfeature.exception.ErrorCode.TARGETING_KEY_MISSING
    if error_code is ErrorCode.INVALID_CONTEXT:
        return openfeature.exception.ErrorCode.INVALID_CONTEXT
    if error_code is ErrorCode.GENERAL:
        return openfeature.exception.ErrorCode.GENERAL
    if error_code is ErrorCode.PARSE_ERROR:
        return openfeature.exception.ErrorCode.PARSE_ERROR
    if error_code is ErrorCode.TIMEOUT:
        return openfeature.exception.ErrorCode.GENERAL
    if error_code is ErrorCode.NOT_READY:
        return openfeature.exception.ErrorCode.PROVIDER_NOT_READY


class ConfidenceOpenFeatureProvider(AbstractProvider):  # type: ignore[misc]
    def __init__(self, confidence_sdk: confidence.confidence.Confidence):
        self.confidence_sdk = confidence_sdk

    #
    # --- Provider API ---
    #

    def get_metadata(self) -> Metadata:
        return Metadata("Confidence")

    def get_provider_hooks(self) -> List[Hook]:
        return []

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        details = self._confidence_with_context(
            evaluation_context
        ).resolve_boolean_details(flag_key, default_value)
        return FlagResolutionDetails[bool](
            value=details.value,
            variant=details.variant,
            reason=details.reason,
            error_code=_to_openfeature_error_code(details.error_code),
            error_message=details.error_message,
            flag_metadata=details.flag_metadata,
        )

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        details = self._confidence_with_context(
            evaluation_context
        ).resolve_float_details(flag_key, default_value)
        return FlagResolutionDetails[float](
            value=details.value,
            variant=details.variant,
            reason=details.reason,
            error_code=_to_openfeature_error_code(details.error_code),
            error_message=details.error_message,
            flag_metadata=details.flag_metadata,
        )

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        details = self._confidence_with_context(
            evaluation_context
        ).resolve_integer_details(flag_key, default_value)
        return FlagResolutionDetails[int](
            value=details.value,
            variant=details.variant,
            reason=details.reason,
            error_code=_to_openfeature_error_code(details.error_code),
            error_message=details.error_message,
            flag_metadata=details.flag_metadata,
        )

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        details = self._confidence_with_context(
            evaluation_context
        ).resolve_string_details(flag_key, default_value)
        return FlagResolutionDetails[str](
            value=details.value,
            variant=details.variant,
            reason=details.reason,
            error_code=_to_openfeature_error_code(details.error_code),
            error_message=details.error_message,
            flag_metadata=details.flag_metadata,
        )

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Union[Object, List[Primitive]],
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[Union[Object, List[Primitive]]]:
        details = self._confidence_with_context(
            evaluation_context
        ).resolve_object_details(flag_key, default_value)
        return FlagResolutionDetails[Union[Object, List[Primitive]]](
            value=details.value,
            variant=details.variant,
            reason=details.reason,
            error_code=_to_openfeature_error_code(details.error_code),
            error_message=details.error_message,
            flag_metadata=details.flag_metadata,
        )

    def _confidence_with_context(
        self, evaluation_context: Optional[EvaluationContext]
    ) -> confidence.confidence.Confidence:
        eval_context: Dict[str, FieldType] = {}
        if evaluation_context:
            if evaluation_context.targeting_key:
                eval_context["targeting_key"] = evaluation_context.targeting_key
            # add other fields to eval_context from evaluationContext
            for key, value in evaluation_context.attributes.items():
                eval_context[key] = value
        return self.confidence_sdk.with_context(eval_context)
