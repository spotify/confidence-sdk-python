import asyncio
import dataclasses
from datetime import datetime
from enum import Enum
import logging
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
)

import requests
from typing_extensions import TypeGuard

from confidence import __version__
from confidence.errors import (
    FlagNotFoundError,
    ParseError,
    TypeMismatchError,
)
from .flag_types import FlagResolutionDetails, Reason
from .names import FlagName, VariantName

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


class Confidence:
    context: Dict[str, FieldType] = {}

    def put_context(self, key: str, value: FieldType) -> None:
        self.context[key] = value

    def with_context(self, context: Dict[str, FieldType]) -> "Confidence":
        new_confidence = Confidence(
            self._client_secret,
            self._region,
            self._apply_on_resolve,
            self._custom_resolve_url,
        )
        new_confidence.context = {**self.context, **context}
        return new_confidence

    def __init__(
        self,
        client_secret: str,
        region: Region = Region.GLOBAL,
        apply_on_resolve: bool = True,
        custom_resolve_url: Optional[str] = None,
        logger: logging.Logger = logging.getLogger("confidence_logger"),
    ):
        self._client_secret = client_secret
        self._region = region
        self._api_endpoint = region.endpoint()
        self._apply_on_resolve = apply_on_resolve
        self.logger = logger
        self._setup_logger(logger)
        self._custom_resolve_url = custom_resolve_url

    def resolve_boolean_details(
        self, flag_key: str, default_value: bool
    ) -> FlagResolutionDetails[bool]:
        return self._evaluate(flag_key, bool, default_value, self.context)

    def resolve_float_details(
        self, flag_key: str, default_value: float
    ) -> FlagResolutionDetails[float]:
        return self._evaluate(flag_key, float, default_value, self.context)

    def resolve_integer_details(
        self, flag_key: str, default_value: int
    ) -> FlagResolutionDetails[int]:
        return self._evaluate(flag_key, int, default_value, self.context)

    def resolve_string_details(
        self, flag_key: str, default_value: str
    ) -> FlagResolutionDetails[str]:
        return self._evaluate(flag_key, str, default_value, self.context)

    def resolve_object_details(
        self, flag_key: str, default_value: Union[Object, List[Primitive]]
    ) -> FlagResolutionDetails[Union[Object, List[Primitive]]]:
        return self._evaluate(flag_key, Object, default_value, self.context)

    def _setup_logger(self, logger: logging.Logger) -> None:
        if logger is not None:
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            if not logger.hasHandlers():
                ch = logging.StreamHandler()
                ch.setFormatter(formatter)
                logger.addHandler(ch)

    #
    # --- internals
    #

    def _evaluate(
        self,
        flag_key: str,
        value_type: Type[FieldType],
        default_value: FieldType,
        context: Dict[str, FieldType],
    ) -> FlagResolutionDetails[Any]:
        if "." in flag_key:
            flag_id, value_path = flag_key.split(".", 1)
        else:
            flag_id = flag_key
            value_path = None
        result = self._resolve(FlagName(flag_id), context)
        if result.variant is None or len(str(result.value)) == 0:
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.DEFAULT,
                flag_metadata={"flag_key": flag_key},
            )

        variant_name = VariantName.parse(result.variant)

        value = self._select(result, value_path, value_type, self.logger)
        if value is None:
            self.logger.debug(
                f"Flag {flag_key} resolved to None. Returning default value."
            )
            value = default_value

        return FlagResolutionDetails(
            value=value,
            variant=variant_name.variant,
            reason=Reason.TARGETING_MATCH,
            flag_metadata={"flag_key": flag_key},
        )

    # type-arg: ignore
    def track(self, event_name: str, data: Dict[str, FieldType]) -> None:
        self._send_event_internal(event_name, data)

    def track_async(self, event_name: str, data: Dict[str, FieldType]) -> None:
        asyncio.create_task(self._send_event(event_name, data))

    async def _send_event(self, event_name: str, data: Dict[str, FieldType]) -> None:
        self._send_event_internal(event_name, data)

    def _send_event_internal(self, event_name: str, data: Dict[str, FieldType]) -> None:
        current_time = datetime.utcnow().isoformat() + "Z"
        request_body = {
            "clientSecret": self._client_secret,
            "sendTime": current_time,
            "events": [
                {
                    "eventDefinition": f"eventDefinitions/{event_name}",
                    "payload": {"context": {**self.context}, **data},
                    "eventTime": current_time,
                }
            ],
            "sdk": {"id": "SDK_ID_PYTHON_CONFIDENCE", "version": __version__},
        }

        event_url = "https://events.confidence.dev/v1/events:publish"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.post(event_url, json=request_body, headers=headers)
        if response.status_code == 200:
            json = response.json()

            json_errors = json.get("errors")
            if json_errors:
                self.logger.warn("events emitted with errors:")
                for error in json_errors:
                    self.logger.warn(error)
        else:
            self.logger.warn(
                f"Track event {event_name} failed with status code"
                + f" {response.status_code} and reason: {response.reason}"
            )

    def _resolve(
        self, flag_name: FlagName, context: Dict[str, FieldType]
    ) -> ResolveResult:
        request_body = {
            "clientSecret": self._client_secret,
            "evaluationContext": context,
            "apply": self._apply_on_resolve,
            "flags": [str(flag_name)],
            "sdk": {"id": "SDK_ID_PYTHON_CONFIDENCE", "version": __version__},
        }
        resolve_url = f"{self._api_endpoint}/flags:resolve"
        if self._custom_resolve_url is not None:
            resolve_url = self._custom_resolve_url

        response = requests.post(resolve_url, json=request_body)
        if response.status_code == 404:
            self.logger.error(f"Flag {flag_name} not found")
            raise FlagNotFoundError()

        response.raise_for_status()

        response_body = response.json()

        resolved_flags = response_body["resolvedFlags"]
        token = response_body["resolveToken"]

        if len(resolved_flags) == 0:
            self.logger.info(f"Flag {flag_name} not found")
            return ResolveResult(None, None, token)

        resolved_flag = resolved_flags[0]
        variant = resolved_flag.get("variant")
        return ResolveResult(
            resolved_flag.get("value"), None if variant == "" else variant, token
        )

    @staticmethod
    def _select(
        result: ResolveResult,
        value_path: Optional[str],
        value_type: Type[FieldType],
        logger: logging.Logger,
    ) -> FieldType:
        value: FieldType = result.value

        if value_path is not None:
            keys = value_path.split(".")
            for key in keys:
                if not isinstance(value, dict):
                    logger.debug(f"Value {value} is not a dict. Returning None.")
                    raise ParseError()

                if key not in value:
                    logger.debug(
                        f"Key {key} not found in value {value}. Returning None."
                    )
                    raise ParseError()

                value = value.get(key)

        # skip type checking if the value was not specified
        if value is None:
            return None

        if not Confidence.type_matches(value, value_type):
            logger.debug(
                f"Type of value {value} did not match expected type {value_type}."
            )
            raise TypeMismatchError("type of value did not match excepted type")

        return value

    @staticmethod
    def type_matches(value: FieldType, value_type: Type[FieldType]) -> bool:
        origin = get_origin(value_type)

        if is_primitive(value_type):
            return primitive_matches(value, value_type)
        elif origin is list:
            return isinstance(value, list)
        elif origin is dict:
            return isinstance(value, dict)

        return False
