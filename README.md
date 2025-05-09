# Python Confidence SDK

Python library for [Confidence](https://confidence.spotify.com/).

## Install

### pip install
<!---x-release-please-start-version-->
```python
pip install spotify-confidence-sdk==2.0.0
```

#### requirements.txt
```python
spotify-confidence-sdk==2.0.0

pip install -r requirements.txt
```
<!---x-release-please-end-->

## Usage

### Resolving flags

Flag values are evaluated remotely and returned to the application:

```python
from confidence.confidence import Confidence

root_confidence = Confidence("CLIENT_TOKEN")
confidence = root_confidence.with_context({"user_id": "some-user-id"})
default_value = False
flag_details = confidence.resolve_boolean_details("flag-name.property-name", default_value)
print(flag_details)
```

### Configuration options

The SDK can be configured with several options:

```python
from confidence.confidence import Confidence, Region

# Configure timeout for network requests
confidence = Confidence(
    client_secret="CLIENT_TOKEN",
    region=Region.EU,  # Optional: defaults to GLOBAL
    timeout_ms=5000  # Optional: specify timeout in milliseconds for network requests (default: 10000ms)
)
```

### Tracking events

Events are emitted to the Confidence backend:

```python
confidence.track("event_name", {
	"field_1": False
})
```

## Telemetry

The SDK includes telemetry functionality that helps monitor SDK performance and usage. By default, telemetry is enabled and collects metrics (anonymously) such as resolve latency and request status. This data is used by the Confidence team to improve the product, and in certain cases it is also available to the SDK adopters.

You can disable telemetry by setting `disable_telemetry=True` when initializing the Confidence client:

```python
confidence = Confidence("CLIENT_TOKEN",
    disable_telemetry=True
)
```

## OpenFeature

The library includes a `Provider` for
the [OpenFeature Python SDK](https://openfeature.dev/docs/tutorials/getting-started/python), that can be
used to resolve feature flag values from the Confidence platform.

To learn more about the basic concepts (flags, targeting key, evaluation contexts),
the [OpenFeature reference documentation](https://openfeature.dev/docs/reference/intro) can be
useful.
