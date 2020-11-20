import json
from io import BytesIO

from django.test import TestCase, override_settings
from django.urls import path, reverse
from rest_framework import status, views
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.test import APITestCase

from rest_framework_json_api import serializers
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.renderers import JSONRenderer


class TestJSONParser(TestCase):
    def setUp(self):
        class MockRequest(object):
            def __init__(self):
                self.method = "GET"

        request = MockRequest()

        self.parser_context = {"request": request, "kwargs": {}, "view": "BlogViewSet"}

        data = {
            "data": {
                "id": 123,
                "type": "Blog",
                "attributes": {"json-value": {"JsonKey": "JsonValue"}},
            },
            "meta": {"random_key": "random_value"},
        }

        self.string = json.dumps(data)

    @override_settings(JSON_API_FORMAT_FIELD_NAMES="dasherize")
    def test_parse_include_metadata_format_field_names(self):
        parser = JSONParser()

        stream = BytesIO(self.string.encode("utf-8"))
        data = parser.parse(stream, None, self.parser_context)

        self.assertEqual(data["_meta"], {"random_key": "random_value"})
        self.assertEqual(data["json_value"], {"JsonKey": "JsonValue"})

    def test_parse_invalid_data(self):
        parser = JSONParser()

        string = json.dumps([])
        stream = BytesIO(string.encode("utf-8"))

        with self.assertRaises(ParseError):
            parser.parse(stream, None, self.parser_context)

    def test_parse_invalid_data_key(self):
        parser = JSONParser()

        string = json.dumps(
            {
                "data": [
                    {
                        "id": 123,
                        "type": "Blog",
                        "attributes": {"json-value": {"JsonKey": "JsonValue"}},
                    }
                ]
            }
        )
        stream = BytesIO(string.encode("utf-8"))

        with self.assertRaises(ParseError):
            parser.parse(stream, None, self.parser_context)


class DummyDTO:
    def __init__(self, response_dict):
        for k, v in response_dict.items():
            setattr(self, k, v)

    @property
    def pk(self):
        return self.id if hasattr(self, "id") else None


class DummySerializer(serializers.Serializer):
    body = serializers.CharField()
    id = serializers.IntegerField()


class DummyAPIView(views.APIView):
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]
    resource_name = "dummy"

    def patch(self, request, *args, **kwargs):
        serializer = DummySerializer(DummyDTO(request.data))
        return Response(status=status.HTTP_200_OK, data=serializer.data)


urlpatterns = [
    path("repeater", DummyAPIView.as_view(), name="repeater"),
]


class TestParserOnAPIView(APITestCase):
    def setUp(self):
        class MockRequest(object):
            def __init__(self):
                self.method = "PATCH"

        request = MockRequest()
        # To be honest view string isn't resolved into actual view
        self.parser_context = {"request": request, "kwargs": {}, "view": "DummyAPIView"}

        self.data = {
            "data": {
                "id": 123,
                "type": "strs",
                "attributes": {"body": "hello"},
            }
        }

        self.string = json.dumps(self.data)

    def test_patch_doesnt_raise_attribute_error(self):
        parser = JSONParser()

        stream = BytesIO(self.string.encode("utf-8"))

        data = parser.parse(stream, None, self.parser_context)

        assert data["id"] == 123
        assert data["body"] == "hello"

    @override_settings(ROOT_URLCONF=__name__)
    def test_patch_request(self):
        url = reverse("repeater")
        data = self.data
        data["data"]["type"] = "dummy"
        response = self.client.patch(url, data=data)
        data = response.json()

        assert data["data"]["id"] == str(123)
        assert data["data"]["attributes"]["body"] == "hello"
