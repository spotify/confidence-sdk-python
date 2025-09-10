# Python Confidence SDK

This repo contains the [Confidence](https://confidence.spotify.com/) Python SDK and the Confidence OpenFeature provider. We recommend using the [OpenFeature Python SDK](https://github.com/open-feature/python-sdk) to access Confidence feature flags.


To learn more about the basic concepts (flags, targeting key, evaluation contexts),
the [OpenFeature reference documentation](https://openfeature.dev/docs/reference/intro) or the [getting started guide](https://openfeature.dev/docs/tutorials/getting-started/python) can be useful.

## Install

### pip install
<!---x-release-please-start-version-->
```python
pip install spotify-confidence-sdk==2.0.1
```

#### requirements.txt
```python
spotify-confidence-sdk==2.0.1

pip install -r requirements.txt
```
<!---x-release-please-end-->

## Usage

### Creating the SDK

The OpenFeature provider is created by using the SDK. More details on how to setup the SDK can be found [here](#configuration-options).

```python
from confidence.confidence import Confidence
from openfeature import api
from confidence.openfeature_provider import ConfidenceOpenFeatureProvider

provider = ConfidenceOpenFeatureProvider(Confidence(api_client, timeout_ms=500))
api.set_provider(provider)
```

### Resolving flags

Flag values are evaluated remotely and returned to the application by using the OpenFeature `client`:

```python
from openfeature import api

client = api.get_client()
user_identifier = "" # your identifier for a specific user

flag_value = client.get_string_value("flag-name.property-name", "my-default-value", api.EvaluationContext(attributes={"user_id": user_identifier}))
print(f"Flag value: {flag_value}")
```

### Configuration options

The SDK can be configured with several options:

```python
from confidence.confidence import Confidence, Region

confidence = Confidence(
    client_secret="CLIENT_TOKEN",
    region=Region.EU,  # Optional: defaults to GLOBAL
    timeout_ms=5000,  # Optional: specify timeout in milliseconds for network requests (default: 10000ms)
    custom_resolve_base_url="https://my-custom-endpoint.org" # we will append /v1/flags:resolve to this for the resolve endpoint.
)
```

## Logging

The SDK includes built-in logging functionality to help with debugging and monitoring. By default, the SDK creates a logger named `confidence_logger` that outputs to the console with DEBUG level logging enabled.

### Default logging behavior

When you create a Confidence client without specifying a logger, debug-level logging is automatically enabled:

```python
from confidence.confidence import Confidence

# Debug logging is enabled by default
confidence = Confidence("CLIENT_TOKEN")
```

This will output log messages such as flag resolution details, error messages, and debug information to help troubleshoot issues.

### Using a custom logger

You can provide your own logger instance to customize the logging behavior:

```python
import logging
from confidence.confidence import Confidence

# Create a custom logger with INFO level (less verbose)
custom_logger = logging.getLogger("my_confidence_logger")
custom_logger.setLevel(logging.INFO)

confidence = Confidence("CLIENT_TOKEN", logger=custom_logger)
```

### Disabling debug logging

To reduce log verbosity, you can configure a logger with a higher log level:

```python
import logging
from confidence.confidence import Confidence

# Create a logger that only shows warnings and errors
quiet_logger = logging.getLogger("quiet_confidence_logger")
quiet_logger.setLevel(logging.WARNING)

confidence = Confidence("CLIENT_TOKEN", logger=quiet_logger)
```

## Telemetry

The SDK includes telemetry functionality that helps monitor SDK performance and usage. By default, telemetry is enabled and collects metrics (anonymously) such as resolve latency and request status. This data is used by the Confidence team to improve the product, and in certain cases it is also available to the SDK adopters.

You can disable telemetry by setting `disable_telemetry=True` when initializing the Confidence client:

```python
confidence = Confidence("CLIENT_TOKEN",
    disable_telemetry=True
)
```
