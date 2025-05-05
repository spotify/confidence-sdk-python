import base64
import sys
from queue import Queue
from typing import Optional, TypeVar, Generic, cast
from typing_extensions import TypeAlias

from confidence.telemetry_pb2 import (
    ProtoMonitoring,
    ProtoLibraryTraces,
    ProtoPlatform,
)

# Define type aliases for the protobuf classes
ProtoTrace: TypeAlias = ProtoLibraryTraces.ProtoTrace
ProtoLibrary: TypeAlias = ProtoLibraryTraces.ProtoLibrary
ProtoTraceId: TypeAlias = ProtoLibraryTraces.ProtoTraceId
ProtoStatus: TypeAlias = ProtoLibraryTraces.ProtoTrace.ProtoRequestTrace.ProtoStatus

T = TypeVar("T")

if sys.version_info >= (3, 9):
    QueueType = Queue
else:

    class QueueType(Queue, Generic[T]):
        pass


class Telemetry:
    _instance: Optional["Telemetry"] = None
    _initialized: bool = False
    version: str
    _traces_queue: "QueueType[ProtoTrace]"

    def __new__(cls, version: str) -> "Telemetry":
        if cls._instance is None:
            cls._instance = super(Telemetry, cls).__new__(cls)
        return cls._instance

    def __init__(self, version: str) -> None:
        if not self._initialized:
            self.version = version
            self._traces_queue = cast("QueueType[ProtoTrace]", Queue())
            self._initialized = True

    def add_trace(
        self, trace_id: ProtoTraceId, duration_ms: int, status: ProtoStatus
    ) -> None:
        trace = ProtoTrace()
        trace.id = trace_id
        request_trace = ProtoTrace.ProtoRequestTrace()
        request_trace.millisecond_duration = duration_ms
        request_trace.status = status
        trace.request_trace.CopyFrom(request_trace)
        self._traces_queue.put(trace)

    def get_monitoring_header(self) -> str:
        # Get all current traces atomically
        current_traces = []
        while not self._traces_queue.empty():
            try:
                current_traces.append(self._traces_queue.get_nowait())
            except Exception:  # Specify the exception type
                break

        # Create monitoring data with the captured traces
        monitoring = ProtoMonitoring()
        library_traces = monitoring.library_traces.add()
        library_traces.library = ProtoLibrary.PROTO_LIBRARY_CONFIDENCE
        library_traces.library_version = self.version
        library_traces.traces.extend(current_traces)
        monitoring.platform = ProtoPlatform.PROTO_PLATFORM_PYTHON

        # Serialize to protobuf and base64 encode
        serialized = monitoring.SerializeToString()
        encoded = base64.b64encode(serialized).decode()
        return encoded
