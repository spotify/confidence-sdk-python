import unittest
import base64
import time
from unittest.mock import patch, MagicMock
from confidence.telemetry import Telemetry, PROTOBUF_AVAILABLE
from confidence.confidence import Confidence, Region
import requests

# Import protobuf types if available, otherwise use fallback types
if PROTOBUF_AVAILABLE:
    from confidence.telemetry_pb2 import ProtoMonitoring, ProtoLibraryTraces, ProtoPlatform
    # Get the nested classes from ProtoLibraryTraces
    ProtoTrace = ProtoLibraryTraces.ProtoTrace
    ProtoRequestTrace = ProtoTrace.ProtoRequestTrace
    ProtoStatus = ProtoRequestTrace.ProtoStatus
    ProtoLibrary = ProtoLibraryTraces.ProtoLibrary
    ProtoTraceId = ProtoLibraryTraces.ProtoTraceId
else:
    from confidence.telemetry import (
        ProtoLibrary, ProtoTraceId, ProtoStatus, ProtoPlatform, ProtoTrace
    )


def requires_protobuf(test_func):
    """Decorator to skip tests that require protobuf when it's not available"""
    return unittest.skipUnless(PROTOBUF_AVAILABLE, "protobuf not available")(test_func)


class TestTelemetry(unittest.TestCase):
    def setUp(self):
        # Reset singleton state before each test
        Telemetry._instance = None
        Telemetry._initialized = False

    def test_add_trace(self):
        telemetry = Telemetry("1.0.0")
        telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            100,
            ProtoStatus.PROTO_STATUS_SUCCESS,
        )

        header = telemetry.get_monitoring_header()

        if PROTOBUF_AVAILABLE:
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
        else:
            # When protobuf is not available, telemetry should return empty header
            self.assertEqual(header, "")

    def test_traces_are_consumed(self):
        telemetry = Telemetry("1.0.0")
        telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            100,
            ProtoStatus.PROTO_STATUS_SUCCESS,
        )
        telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            200,
            ProtoStatus.PROTO_STATUS_ERROR,
        )

        header1 = telemetry.get_monitoring_header()
        monitoring1 = ProtoMonitoring()
        monitoring1.ParseFromString(base64.b64decode(header1))
        self.assertEqual(len(monitoring1.library_traces[0].traces), 2)

        header2 = telemetry.get_monitoring_header()
        monitoring2 = ProtoMonitoring()
        monitoring2.ParseFromString(base64.b64decode(header2))
        self.assertEqual(len(monitoring2.library_traces[0].traces), 0)

    def test_multiple_traces(self):
        telemetry = Telemetry("1.0.0")
        telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            100,
            ProtoStatus.PROTO_STATUS_SUCCESS,
        )
        telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            200,
            ProtoStatus.PROTO_STATUS_ERROR,
        )
        telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            300,
            ProtoStatus.PROTO_STATUS_TIMEOUT,
        )

        header = telemetry.get_monitoring_header()
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

    @patch("requests.post")
    def test_disabled_telemetry(self, mock_post):
        # Create a confidence instance with telemetry disabled
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resolvedFlags": [{"value": True, "variant": "on"}],
            "resolveToken": "test-token",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        confidence = Confidence(
            client_secret="test-secret", region=Region.GLOBAL, disable_telemetry=True
        )

        # Add a trace and verify it's not added
        confidence._telemetry.add_trace(
            ProtoTraceId.PROTO_TRACE_ID_RESOLVE_LATENCY,
            100,
            ProtoStatus.PROTO_STATUS_SUCCESS,
        )

        # Get the header and verify it's empty
        header = confidence._telemetry.get_monitoring_header()
        self.assertEqual(header, "")

        # Make a resolve call and verify no telemetry header is sent
        confidence.resolve_boolean_details("test-flag", False)
        headers = mock_post.call_args[1]["headers"]
        self.assertNotIn("X-CONFIDENCE-TELEMETRY", headers)

    @patch("requests.post")
    def test_telemetry_shared_across_confidence_instances(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resolvedFlags": [{"value": True, "variant": "on"}],
            "resolveToken": "test-token",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Create first confidence instance and resolve a flag
        confidence1 = Confidence(client_secret="test-secret", region=Region.GLOBAL)
        confidence1.resolve_boolean_details("test-flag", False)

        # Create second confidence instance using with_context and resolve another flag
        confidence2 = confidence1.with_context({"user_id": "test-user"})
        confidence2.resolve_boolean_details("test-flag", False)

        # Verify both instances share the same telemetry instance
        self.assertIs(confidence1._telemetry, confidence2._telemetry)

        self.assertEqual(mock_post.call_count, 2)

        # First request should have no trace
        headers1 = mock_post.call_args_list[0][1]["headers"]
        self.assertIn("X-CONFIDENCE-TELEMETRY", headers1)
        monitoring1 = ProtoMonitoring()
        print(f"Decoding telemetry header: {headers1['X-CONFIDENCE-TELEMETRY']}")
        monitoring1.ParseFromString(
            base64.b64decode(headers1["X-CONFIDENCE-TELEMETRY"])
        )
        traces1 = monitoring1.library_traces[0].traces
        print(f"First request traces: {traces1}")
        self.assertEqual(len(traces1), 0)

        # Second request should have the first traces
        headers2 = mock_post.call_args_list[1][1]["headers"]
        self.assertIn("X-CONFIDENCE-TELEMETRY", headers2)
        monitoring2 = ProtoMonitoring()
        print(f"Decoding telemetry header: {headers1['X-CONFIDENCE-TELEMETRY']}")
        monitoring2.ParseFromString(
            base64.b64decode(headers2["X-CONFIDENCE-TELEMETRY"])
        )
        traces2 = monitoring2.library_traces[0].traces
        self.assertEqual(len(traces2), 1)


if __name__ == "__main__":
    unittest.main()
