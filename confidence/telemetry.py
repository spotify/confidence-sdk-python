import time
from typing import List
import base64
from queue import Queue
from confidence.telemetry_pb2 import (
    ProtoMonitoring,
    ProtoLibraryTraces,
    ProtoPlatform,
)

# Get the nested classes from ProtoLibraryTraces
ProtoTrace = ProtoLibraryTraces.ProtoTrace
ProtoLibrary = ProtoLibraryTraces.ProtoLibrary
ProtoTraceId = ProtoLibraryTraces.ProtoTraceId
ProtoStatus = ProtoLibraryTraces.ProtoTrace.ProtoRequestTrace.ProtoStatus

class Telemetry:
    _instance = None
    _initialized = False

    def __new__(cls, version: str):
        if cls._instance is None:
            cls._instance = super(Telemetry, cls).__new__(cls)
        return cls._instance

    def __init__(self, version: str):
        if not self._initialized:
            self.version = version
            self._traces_queue = Queue()
            self._initialized = True

    def add_trace(self, trace_id: ProtoTraceId, duration_ms: int, status: ProtoStatus) -> None:
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
            except:
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