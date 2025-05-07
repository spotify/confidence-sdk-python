import base64
from queue import Queue
from typing import Optional
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


class Telemetry:
    _instance: Optional["Telemetry"] = None
    _initialized: bool = False
    version: str
    _traces_queue: Queue[ProtoTrace]
    _disabled: bool

    def __new__(cls, version: str, disabled: bool = False) -> "Telemetry":
        if cls._instance is None:
            cls._instance = super(Telemetry, cls).__new__(cls)
            cls._initialized = False
            cls._disabled = disabled
        return cls._instance

    def __init__(self, version: str, disabled: bool = False) -> None:
        if not self._initialized:
            self.version = version
            self._traces_queue = Queue()
            self._disabled = disabled
            self._initialized = True

    def add_trace(
        self, trace_id: ProtoTraceId, duration_ms: int, status: ProtoStatus
    ) -> None:
        if self._disabled:
            return
        trace = ProtoTrace()
        trace.id = trace_id
        request_trace = ProtoTrace.ProtoRequestTrace()
        request_trace.millisecond_duration = duration_ms
        request_trace.status = status
        trace.request_trace.CopyFrom(request_trace)
        self._traces_queue.put(trace)

    def get_monitoring_header(self) -> str:
        if self._disabled:
            return ""
        current_traces = []
        while not self._traces_queue.empty():
            try:
                current_traces.append(self._traces_queue.get_nowait())
            except Exception:
                break

        monitoring = ProtoMonitoring()
        library_traces = monitoring.library_traces.add()
        library_traces.library = ProtoLibrary.PROTO_LIBRARY_CONFIDENCE
        library_traces.library_version = self.version
        library_traces.traces.extend(current_traces)
        monitoring.platform = ProtoPlatform.PROTO_PLATFORM_PYTHON
        serialized = monitoring.SerializeToString()
        encoded = base64.b64encode(serialized).decode()
        return encoded
