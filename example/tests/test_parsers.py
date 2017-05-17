import json
from io import BytesIO

from django.test import TestCase
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
                'type': 'Blog'
            },
            'meta': {
                'random_key': 'random_value'
            }
        }

        self.string = json.dumps(data)

    def test_parse_include_metadata(self):
        parser = JSONParser()

        stream = BytesIO(self.string.encode('utf-8'))
        data = parser.parse(stream, None, self.parser_context)

        self.assertEqual(data['_meta'], {'random_key': 'random_value'})

    def test_parse_invalid_data(self):
        parser = JSONParser()

        string = json.dumps([])
        stream = BytesIO(string.encode('utf-8'))

        with self.assertRaises(ParseError):
            parser.parse(stream, None, self.parser_context)
