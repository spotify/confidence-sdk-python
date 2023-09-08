import json

SUCCESSFUL_STRING_FLAG_RESOLVE = json.loads(
    """{
 "resolvedFlags": [
  {
   "flag": "flags/test-flag",
   "variant": "flags/test-flag/variants/control",
   "value": {
    "color": "red"
   },
   "flagSchema": {
    "schema": {
     "color": {
      "stringSchema": {}
     }
    }
   },
   "reason": "RESOLVE_REASON_MATCH"
  }
 ],
 "resolveToken": ""
}"""
)

NO_MATCH_STRING_FLAG_RESOLVE = json.loads(
    """{"resolvedFlags": [], "resolveToken": ""}"""
)

EXPECTED_REQUEST_PAYLOAD = json.loads(
    """{
  "clientSecret": "test",
  "evaluationContext": {
    "targeting_key": "boop",
    "user": { "country": "US" },
    "connection": "wifi"
  },
  "apply": true,
  "flags": ["test-flag"]
}"""
)
