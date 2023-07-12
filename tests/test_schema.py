from rest_framework_json_api.schemas.openapi import AutoSchema
from tests.serializers import CallableDefaultSerializer


def test_schema_callable_default():
    inspector = AutoSchema()
    result = inspector.map_serializer(CallableDefaultSerializer())
    assert result["properties"]["attributes"]["properties"]["field"] == {
        "type": "string",
    }
