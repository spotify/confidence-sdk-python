from __future__ import annotations

import typing
import sys
from dataclasses import dataclass, field

from confidence.errors import ErrorCode

if sys.version_info >= (3, 11):
    # re-export needed for type checking
    from enum import StrEnum as StrEnum  # noqa: PLC0414
else:
    from enum import Enum


    class StrEnum(str, Enum):
        """
        Backport StrEnum for Python <3.11
        """

        pass


class FlagType(StrEnum):
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    OBJECT = "OBJECT"
    FLOAT = "FLOAT"
    INTEGER = "INTEGER"


class Reason(StrEnum):
    CACHED = "CACHED"
    DEFAULT = "DEFAULT"
    DISABLED = "DISABLED"
    ERROR = "ERROR"
    STATIC = "STATIC"
    SPLIT = "SPLIT"
    TARGETING_MATCH = "TARGETING_MATCH"
    UNKNOWN = "UNKNOWN"


FlagMetadata = typing.Mapping[str, typing.Any]

T_co = typing.TypeVar("T_co", covariant=True)


@dataclass
class FlagEvaluationDetails(typing.Generic[T_co]):
    flag_key: str
    value: T_co
    variant: typing.Optional[str] = None
    flag_metadata: FlagMetadata = field(default_factory=dict)
    reason: typing.Optional[typing.Union[str, Reason]] = None
    error_code: typing.Optional[ErrorCode] = None
    error_message: typing.Optional[str] = None


@dataclass
class FlagEvaluationOptions:
    hooks: typing.List[Hook] = field(default_factory=list)
    hook_hints: dict = field(default_factory=dict)


U_co = typing.TypeVar("U_co", covariant=True)


@dataclass
class FlagResolutionDetails(typing.Generic[U_co]):
    value: U_co
    error_code: typing.Optional[ErrorCode] = None
    error_message: typing.Optional[str] = None
    reason: typing.Optional[typing.Union[str, Reason]] = None
    variant: typing.Optional[str] = None
    flag_metadata: FlagMetadata = field(default_factory=dict)
