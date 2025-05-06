import asyncio
import base64
import dataclasses
from datetime import datetime
from enum import Enum
import json
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
import httpx
from typing_extensions import TypeGuard
import time

from confidence import __version__
from confidence.errors import (
    FlagNotFoundError,
    GeneralError,
    ParseError,
    TypeMismatchError,
    TimeoutError,
)
from .flag_types import FlagResolutionDetails, Reason, ErrorCode
from .names import FlagName, VariantName
from .telemetry import Telemetry, ProtoTraceId, ProtoStatus

EU_RESOLVE_API_ENDPOINT = "https://resolver.eu.confidence.dev"
US_RESOLVE_API_ENDPOINT = "https://resolver.us.confidence.dev"
GLOBAL_RESOLVE_API_ENDPOINT = "https://resolver.confidence.dev"

# Default timeout in milliseconds (10 seconds)
DEFAULT_TIMEOUT_MS = 10000

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
            self._custom_resolve_base_url,
            timeout_ms=self._timeout_ms,
            logger=self.logger,
            async_client=self.async_client,
        )
        new_confidence.context = {**self.context, **context}
        return new_confidence

    def __init__(
        self,
        client_secret: str,
        region: Region = Region.GLOBAL,
        apply_on_resolve: bool = True,
        custom_resolve_base_url: Optional[str] = None,
        timeout_ms: Optional[int] = DEFAULT_TIMEOUT_MS,
        logger: logging.Logger = logging.getLogger("confidence_logger"),
        async_client: httpx.AsyncClient = httpx.AsyncClient(),
        disable_telemetry: bool = False,
    ):
        self._client_secret = client_secret
        self._region = region
        self._api_endpoint = region.endpoint()
        self._apply_on_resolve = apply_on_resolve
        self._timeout_ms = timeout_ms
        self.logger = logger
        self.async_client = async_client
        self._setup_logger(logger)
        self._custom_resolve_base_url = custom_resolve_base_url
        self._telemetry = Telemetry(__version__, disabled=disable_telemetry)

    def _get_resolve_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        telemetry_header = self._telemetry.get_monitoring_header()
        if telemetry_header:
            headers["X-CONFIDENCE-TELEMETRY"] = telemetry_header
        return headers

    def resolve_boolean_details(
        self, flag_key: str, default_value: bool
    ) -> FlagResolutionDetails[bool]:
        return self._evaluate(flag_key, bool, default_value, self.context)

    async def resolve_boolean_details_async(
        self, flag_key: str, default_value: bool
    ) -> FlagResolutionDetails[bool]:
        return await self._evaluate_async(flag_key, bool, default_value, self.context)

    def resolve_float_details(
        self, flag_key: str, default_value: float
    ) -> FlagResolutionDetails[float]:
        return self._evaluate(flag_key, float, default_value, self.context)

    async def resolve_float_details_async(
        self, flag_key: str, default_value: float
    ) -> FlagResolutionDetails[float]:
        return await self._evaluate_async(flag_key, float, default_value, self.context)

    def resolve_integer_details(
        self, flag_key: str, default_value: int
    ) -> FlagResolutionDetails[int]:
        return self._evaluate(flag_key, int, default_value, self.context)

    async def resolve_integer_details_async(
        self, flag_key: str, default_value: int
    ) -> FlagResolutionDetails[int]:
        return await self._evaluate_async(flag_key, int, default_value, self.context)

    def resolve_string_details(
        self, flag_key: str, default_value: str
    ) -> FlagResolutionDetails[str]:
        return self._evaluate(flag_key, str, default_value, self.context)

    async def resolve_string_details_async(
        self, flag_key: str, default_value: str
    ) -> FlagResolutionDetails[str]:
        return await self._evaluate_async(flag_key, str, default_value, self.context)

    def resolve_object_details(
        self, flag_key: str, default_value: Union[Object, List[Primitive]]
    ) -> FlagResolutionDetails[Union[Object, List[Primitive]]]:
        return self._evaluate(flag_key, Object, default_value, self.context)

    async def resolve_object_details_async(
        self, flag_key: str, default_value: Union[Object, List[Primitive]]
    ) -> FlagResolutionDetails[Union[Object, List[Primitive]]]:
        return await self._evaluate_async(flag_key, Object, default_value, self.context)

    #
    # --- internals
    #

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

    def _logResolveTester(self, flag_id: str, context: Dict[str, FieldType]) -> None:
        json_payload = json.dumps(
            {
                "flag": f"flags/{flag_id}",
                "context": context,
                "clientKey": self._client_secret,
            }
        )
        base64_payload = base64.b64encode(json_payload.encode("utf-8")).decode("utf-8")
        self.logger.debug(
            f"Check your flag evaluation for '{flag_id}' by copy-pasting the payload to the Resolve tester: {base64_payload}"  # noqa: E501
        )

    def _handle_evaluation_result(
        self,
        result: ResolveResult,
        flag_id: str,
        flag_key: str,
        value_type: Type[FieldType],
        default_value: FieldType,
        value_path: Optional[str],
        context: Dict[str, FieldType],
    ) -> FlagResolutionDetails[Any]:
        self._logResolveTester(flag_id, context)

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
        try:
            result = self._resolve(FlagName(flag_id), context)
            return self._handle_evaluation_result(
                result,
                flag_id,
                flag_key,
                value_type,
                default_value,
                value_path,
                context,
            )
        except FlagNotFoundError:
            self.logger.info(f"Flag {flag_key} not found")
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.DEFAULT,
                error_code=ErrorCode.FLAG_NOT_FOUND,
                error_message=f"Flag {flag_key} not found",
                flag_metadata={"flag_key": flag_key},
            )
        except TimeoutError as e:
            self.logger.warning(
                f"Request timed out after {self._timeout_ms} ms"
                f" when resolving flag {flag_key}"
            )
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.DEFAULT,
                error_code=ErrorCode.TIMEOUT,
                error_message=str(e),
                flag_metadata={"flag_key": flag_key},
            )
        except Exception as e:
            self.logger.error(f"Error resolving flag {flag_key}: {str(e)}")
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.GENERAL,
                error_message=str(e),
                flag_metadata={"flag_key": flag_key},
            )

    async def _evaluate_async(
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
        try:
            result = await self._resolve_async(FlagName(flag_id), context)
            return self._handle_evaluation_result(
                result,
                flag_id,
                flag_key,
                value_type,
                default_value,
                value_path,
                context,
            )
        except FlagNotFoundError:
            self.logger.info(f"Flag {flag_key} not found")
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.DEFAULT,
                error_code=ErrorCode.FLAG_NOT_FOUND,
                error_message=f"Flag {flag_key} not found",
                flag_metadata={"flag_key": flag_key},
            )
        except TimeoutError as e:
            self.logger.warning(
                f"Request timed out after {self._timeout_ms} ms"
                f" when resolving flag {flag_key}"
            )
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.DEFAULT,
                error_code=ErrorCode.TIMEOUT,
                error_message=str(e),
                flag_metadata={"flag_key": flag_key},
            )
        except Exception as e:
            self.logger.error(f"Error resolving flag {flag_key}: {str(e)}")
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.DEFAULT,
                error_code=ErrorCode.GENERAL,
                error_message=str(e),
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
        timeout_sec = None if self._timeout_ms is None else self._timeout_ms / 1000.0
        try:
            response = requests.post(
                event_url, json=request_body, headers=headers, timeout=timeout_sec
            )
            if response.status_code == 200:
                json = response.json()
                json_errors = json.get("errors")
                if json_errors:
                    self.logger.warning("events emitted with errors:")
                    for error in json_errors:
                        self.logger.warning(error)
            else:
                self.logger.warning(
                    f"Track event {event_name} failed with status code"
                    + f" {response.status_code} and reason: {response.reason}"
                )
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Failed to track event {event_name}: {str(e)}")

    def _handle_resolve_response(
        self, response: requests.Response, flag_name: FlagName
    ) -> ResolveResult:
        if response.status_code == 404:
            self.logger.error(f"Flag {flag_name} not found")
            raise FlagNotFoundError()

        response.raise_for_status()

        response_body = response.json()

        resolved_flags = response_body["resolvedFlags"]
        token = response_body["resolveToken"]

        if len(resolved_flags) == 0:
            raise FlagNotFoundError()

        resolved_flag = resolved_flags[0]
        variant = resolved_flag.get("variant")
        return ResolveResult(
            resolved_flag.get("value"), None if variant == "" else variant, token
        )

    def _resolve(
        self, flag_name: FlagName, context: Dict[str, FieldType]
    ) -> ResolveResult:
        start_time = time.perf_counter()
        request_body = {
            "clientSecret": self._client_secret,
            "evaluationContext": context,
            "apply": self._apply_on_resolve,
            "flags": [str(flag_name)],
            "sdk": {"id": "SDK_ID_PYTHON_CONFIDENCE", "version": __version__},
        }
        base_url = self._api_endpoint
        if self._custom_resolve_base_url is not None:
            base_url = self._custom_resolve_base_url

        resolve_url = f"{base_url}/v1/flags:resolve"
        timeout_sec = None if self._timeout_ms is None else self._timeout_ms / 1000.0

        try:
            response = requests.post(
                resolve_url,
                json=request_body,
                headers=self._get_resolve_headers(),
                timeout=timeout_sec,
            )

            result = self._handle_resolve_response(response, flag_name)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._telemetry.add_trace(
                ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
                duration_ms,
                ProtoStatus.PROTO_STATUS_SUCCESS,
            )
            return result
        except requests.exceptions.Timeout:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._telemetry.add_trace(
                ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
                duration_ms,
                ProtoStatus.PROTO_STATUS_TIMEOUT,
            )
            self.logger.warning(
                f"Request timed out after {timeout_sec}s"
                f" when resolving flag {flag_name}"
            )
            raise TimeoutError()
        except requests.exceptions.RequestException as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._telemetry.add_trace(
                ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
                duration_ms,
                ProtoStatus.PROTO_STATUS_ERROR,
            )
            self.logger.warning(f"Error resolving flag {flag_name}: {str(e)}")
            raise GeneralError(str(e))

    async def _resolve_async(
        self, flag_name: FlagName, context: Dict[str, FieldType]
    ) -> ResolveResult:
        start_time = time.perf_counter()
        request_body = {
            "clientSecret": self._client_secret,
            "evaluationContext": context,
            "apply": self._apply_on_resolve,
            "flags": [str(flag_name)],
            "sdk": {"id": "SDK_ID_PYTHON_CONFIDENCE", "version": __version__},
        }
        base_url = self._api_endpoint
        if self._custom_resolve_base_url is not None:
            base_url = self._custom_resolve_base_url

        resolve_url = f"{base_url}/v1/flags:resolve"
        timeout_sec = None if self._timeout_ms is None else self._timeout_ms / 1000.0
        try:
            response = await self.async_client.post(
                resolve_url,
                json=request_body,
                headers=self._get_resolve_headers(),
                timeout=timeout_sec,
            )
            result = self._handle_resolve_response(response, flag_name)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._telemetry.add_trace(
                ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
                duration_ms,
                ProtoStatus.PROTO_STATUS_SUCCESS,
            )
            return result
        except httpx.TimeoutException:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._telemetry.add_trace(
                ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
                duration_ms,
                ProtoStatus.PROTO_STATUS_TIMEOUT,
            )
            self.logger.warning(
                f"Request timed out after {timeout_sec}s"
                f" when resolving flag {flag_name}"
            )
            raise TimeoutError()
        except httpx.HTTPError as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._telemetry.add_trace(
                ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
                duration_ms,
                ProtoStatus.PROTO_STATUS_ERROR,
            )
            self.logger.warning(f"Error resolving flag {flag_name}: {str(e)}")
            raise GeneralError(str(e))

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
