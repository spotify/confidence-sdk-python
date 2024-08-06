# Python Confidence SDK

Python library for [Confidence](https://confidence.spotify.com/).

## Install

### pip install
<!---x-release-please-start-version-->
```python
pip install spotify-confidence-sdk==0.2.4

#### requirements.txt
```python
spotify-confidence-sdk==0.2.4

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

### Tracking events

Events are emitted to the Confidence backend:

```python
confidence.track("event_name", {
	"field_1": False
})
```

## OpenFeature

The library includes a `Provider` for
the [OpenFeature Python SDK](https://openfeature.dev/docs/tutorials/getting-started/python), that can be
used to resolve feature flag values from the Confidence platform.

To learn more about the basic concepts (flags, targeting key, evaluation contexts),
the [OpenFeature reference documentation](https://openfeature.dev/docs/reference/intro) can be
useful.
