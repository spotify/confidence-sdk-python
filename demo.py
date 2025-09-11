import uuid
import os

from confidence.confidence import Confidence
from openfeature import api
from confidence.openfeature_provider import ConfidenceOpenFeatureProvider
from dotenv import load_dotenv

def get_flag():
    api_client = os.getenv("API_CLIENT")
    api.set_provider(ConfidenceOpenFeatureProvider(Confidence(api_client, timeout_ms=100)))

    random_uuid = str(uuid.uuid4())
    client = api.get_client()

    flag_value = client.get_string_value("hawkflag.color", "default", api.EvaluationContext(attributes={"visitor_id": random_uuid}))
    print(f"Flag value: {flag_value}")


if __name__ == "__main__":
    load_dotenv()
    get_flag()
