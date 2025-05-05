import unittest
import base64
import time
from unittest.mock import patch, MagicMock
from confidence.telemetry_pb2 import ProtoMonitoring, ProtoLibraryTraces, ProtoPlatform
from confidence.telemetry import Telemetry
from confidence.confidence import Confidence, Region
import requests

# Get the nested classes from ProtoLibraryTraces
ProtoTrace = ProtoLibraryTraces.ProtoTrace
ProtoRequestTrace = ProtoTrace.ProtoRequestTrace
ProtoStatus = ProtoRequestTrace.ProtoStatus
ProtoLibrary = ProtoLibraryTraces.ProtoLibrary
ProtoTraceId = ProtoLibraryTraces.ProtoTraceId


class TestTelemetry(unittest.TestCase):
    def setUp(self):
        Telemetry._instance = None
        Telemetry._initialized = False
        self.telemetry = Telemetry("1.0.0")

    def test_add_trace(self):
        self.telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            100,
            ProtoStatus.PROTO_STATUS_SUCCESS,
        )

        header = self.telemetry.get_monitoring_header()
        monitoring = ProtoMonitoring()
        monitoring.ParseFromString(base64.b64decode(header))

        self.assertEqual(monitoring.platform, ProtoPlatform.PROTO_PLATFORM_PYTHON)
        self.assertEqual(len(monitoring.library_traces), 1)

        library_trace = monitoring.library_traces[0]
        self.assertEqual(library_trace.library, ProtoLibrary.PROTO_LIBRARY_CONFIDENCE)
        self.assertEqual(library_trace.library_version, "1.0.0")

        self.assertEqual(len(library_trace.traces), 1)
        trace = library_trace.traces[0]
        self.assertEqual(trace.id, ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY)
        self.assertEqual(trace.request_trace.millisecond_duration, 100)
        self.assertEqual(trace.request_trace.status, ProtoStatus.PROTO_STATUS_SUCCESS)

    def test_traces_are_consumed(self):
        self.telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            100,
            ProtoStatus.PROTO_STATUS_SUCCESS,
        )
        self.telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            200,
            ProtoStatus.PROTO_STATUS_ERROR,
        )

        header1 = self.telemetry.get_monitoring_header()
        monitoring1 = ProtoMonitoring()
        monitoring1.ParseFromString(base64.b64decode(header1))
        self.assertEqual(len(monitoring1.library_traces[0].traces), 2)

        header2 = self.telemetry.get_monitoring_header()
        monitoring2 = ProtoMonitoring()
        monitoring2.ParseFromString(base64.b64decode(header2))
        self.assertEqual(len(monitoring2.library_traces[0].traces), 0)

    def test_multiple_traces(self):
        self.telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            100,
            ProtoStatus.PROTO_STATUS_SUCCESS,
        )
        self.telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            200,
            ProtoStatus.PROTO_STATUS_ERROR,
        )
        self.telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            300,
            ProtoStatus.PROTO_STATUS_TIMEOUT,
        )

        header = self.telemetry.get_monitoring_header()
        monitoring = ProtoMonitoring()
        monitoring.ParseFromString(base64.b64decode(header))
        traces = monitoring.library_traces[0].traces

        self.assertEqual(len(traces), 3)
        self.assertEqual(traces[0].request_trace.millisecond_duration, 100)
        self.assertEqual(
            traces[0].request_trace.status, ProtoStatus.PROTO_STATUS_SUCCESS
        )
        self.assertEqual(traces[1].request_trace.millisecond_duration, 200)
        self.assertEqual(traces[1].request_trace.status, ProtoStatus.PROTO_STATUS_ERROR)
        self.assertEqual(traces[2].request_trace.millisecond_duration, 300)
        self.assertEqual(
            traces[2].request_trace.status, ProtoStatus.PROTO_STATUS_TIMEOUT
        )

    def test_singleton_behavior(self):
        telemetry1 = Telemetry("1.0.0")
        telemetry2 = Telemetry("2.0.0")

        telemetry1.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            100,
            ProtoStatus.PROTO_STATUS_SUCCESS,
        )

        header = telemetry2.get_monitoring_header()
        monitoring = ProtoMonitoring()
        monitoring.ParseFromString(base64.b64decode(header))
        self.assertEqual(len(monitoring.library_traces[0].traces), 1)

        self.assertEqual(monitoring.library_traces[0].library_version, "1.0.0")

    @patch("requests.post")
    def test_telemetry_during_resolve(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resolvedFlags": [{"value": True, "variant": "on"}],
            "resolveToken": "test-token",
        }
        mock_response.raise_for_status.return_value = None

        def delayed_response(*args, **kwargs):
            time.sleep(0.01)
            return mock_response

        mock_post.side_effect = delayed_response

        confidence = Confidence(client_secret="test-secret", region=Region.GLOBAL)

        confidence.resolve_boolean_details("test-flag", False)

        final_header = confidence._telemetry.get_monitoring_header()
        monitoring = ProtoMonitoring()
        monitoring.ParseFromString(base64.b64decode(final_header))
        final_traces = monitoring.library_traces[0].traces
        self.assertEqual(len(final_traces), 1)
        trace = final_traces[0]
        self.assertEqual(trace.id, ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY)
        self.assertEqual(trace.request_trace.status, ProtoStatus.PROTO_STATUS_SUCCESS)
        self.assertGreaterEqual(trace.request_trace.millisecond_duration, 10)

    @patch("requests.post")
    def test_telemetry_during_resolve_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.RequestException("Test error")
        )
        mock_response.json.side_effect = requests.exceptions.RequestException(
            "Test error"
        )

        def delayed_error(*args, **kwargs):
            time.sleep(0.01)
            return mock_response

        mock_post.side_effect = delayed_error

        confidence = Confidence(client_secret="test-secret", region=Region.GLOBAL)

        confidence.resolve_boolean_details("test-flag", False)

        final_header = confidence._telemetry.get_monitoring_header()
        monitoring = ProtoMonitoring()
        monitoring.ParseFromString(base64.b64decode(final_header))
        final_traces = monitoring.library_traces[0].traces
        self.assertEqual(len(final_traces), 1)
        trace = final_traces[0]
        self.assertEqual(trace.id, ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY)
        self.assertEqual(trace.request_trace.status, ProtoStatus.PROTO_STATUS_ERROR)
        self.assertGreaterEqual(trace.request_trace.millisecond_duration, 10)

    def test_send_telemetry(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            self.telemetry.add_trace(
                ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
                100,
                ProtoStatus.PROTO_STATUS_SUCCESS
            )
            header = self.telemetry.get_monitoring_header()
            self.assertIsNotNone(header)
            mock_post.assert_not_called()  # No direct HTTP calls should be made


if __name__ == "__main__":
    unittest.main()
