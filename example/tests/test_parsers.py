import json
from io import BytesIO

from django.test import TestCase, override_settings
from rest_framework.exceptions import ParseError

from rest_framework_json_api.parsers import JSONParser


class TestJSONParser(TestCase):

    def setUp(self):
        class MockRequest(object):

            def __init__(self):
                self.method = 'GET'

        request = MockRequest()

        self.parser_context = {'request': request, 'kwargs': {}, 'view': 'BlogViewSet'}

        data = {
            'data': {
                'id': 123,
                'type': 'Blog',
                'attributes': {
                    'json-value': {'JsonKey': 'JsonValue'}
                },
            },
            'meta': {
                'random_key': 'random_value'
            }
        }

        self.string = json.dumps(data)

    @override_settings(JSON_API_FORMAT_FIELD_NAMES='dasherize')
    def test_parse_include_metadata_format_field_names(self):
        parser = JSONParser()

        stream = BytesIO(self.string.encode('utf-8'))
        data = parser.parse(stream, None, self.parser_context)

        self.assertEqual(data['_meta'], {'random_key': 'random_value'})
        self.assertEqual(data['json_value'], {'JsonKey': 'JsonValue'})

    def test_parse_invalid_data(self):
        parser = JSONParser()

        string = json.dumps([])
        stream = BytesIO(string.encode('utf-8'))

        with self.assertRaises(ParseError):
            parser.parse(stream, None, self.parser_context)

    def test_parse_invalid_data_key(self):
        parser = JSONParser()

        string = json.dumps({
            'data': [{
                'id': 123,
                'type': 'Blog',
                'attributes': {
                    'json-value': {'JsonKey': 'JsonValue'}
                },
            }]
        })
        stream = BytesIO(string.encode('utf-8'))

        with self.assertRaises(ParseError):
            parser.parse(stream, None, self.parser_context)
