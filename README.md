# Confidence SDK

This repo contains the [Confidence](https://confidence.spotify.com/) SDK for python and the Confidence OpenFeature flag provider.

## Adding the dependency

#### pip install
<!---x-release-please-start-version-->
```python
pip install spotify-confidence-sdk==0.2.4

#### requirements.txt
```python
spotify-confidence-sdk==0.2.4

pip install -r requirements.txt
```
<!---x-release-please-end-->

### Creating and using the flag provider

Below is an example for how to initialize the Confidence SDK, and then resolve
a flag with a boolean attribute. The SDK is configured with an api key, which will authorize the resolving requests. 

The flag will be applied immediately, meaning that Confidence will count the targeted user as having received the treatment. 

You can retrieve attributes on the flag variant using property dot notation, meaning `test-flag.boolean-key` will retrieve
the attribute `boolean-key` on the flag `test-flag`. 

You can also use only the flag name `test-flag` and retrieve all values as a map with `resolve_object_details()`. 

The flag's schema is validated against the requested data type, and if it doesn't match it will fall back to the default value.

```python

from confidence.confidence import Confidence
from confidence.confidence import Region

confidence = Confidence("API_KEY")
# to send an event
confidence.with_context({"app": "python"}).track("event_name", {})
#to resolve a flag
default_value = False
flag_value = confidence.resolve_boolean_details("test-flag.boolean-key", default_value)
print(flag_value)

```
