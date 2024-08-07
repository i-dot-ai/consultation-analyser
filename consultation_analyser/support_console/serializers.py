from drf_jsonschema_serializer.fields import JSONSchemaField
from rest_framework import serializers


# Very basic serializer for testing
class ExampleSerializer(serializers.Serializer):
    json_data = JSONSchemaField(schema={"type": "object"})
