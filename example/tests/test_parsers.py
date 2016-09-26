import json

from django.test import TestCase
from io import BytesIO
from rest_framework_json_api.parsers import JSONParser


class TestJSONParser(TestCase):

    @staticmethod
    def _data_to_json_stream(data):
        string = json.dumps(data)
        return BytesIO(string.encode('utf-8'))

    def test_parse_include_metadata(self):
        class MockRequest(object):
            def __init__(self):
                self.method = 'GET'

        parser = JSONParser()
        parser_context = {'request': MockRequest(), 'kwargs': {}, 'view': 'BlogViewSet'}
        request_data = {
            'data': {
                'id': 123,
                'type': 'Blog'
            },
            'meta': {
                'random_key': 'random_value'
            }
        }
        result_data = parser.parse(self._data_to_json_stream(request_data), None, parser_context)
        self.assertEqual(result_data['_meta'], {'random_key': 'random_value'})

    def test_parse_with_included(self):
        """ test parsing of incoming JSON which includes referenced entities """
        class ViewMock(object):
            resource_name = 'author-bios'

        parser = JSONParser()
        request_data = {
            "data": {
                "type": "author-bios",
                "id": "author-bio-1",
                "attributes": {
                    "body": "This author is cool",
                },
                "relationships": {
                    "author": {
                        "data": {
                            "type": "authors",
                            "id": "author-1"
                        }
                    },
                }
            },
            "included": [{
                "type": "authors",
                "id": "author-1",
                "attributes": {
                    "name": "Homer Simpson",
                    "email": "homer@simpson.com"
                },
            }]
        }
        result_data = parser.parse(self._data_to_json_stream(request_data), parser_context={'view': ViewMock()})

        expected_data = {
            'id': 'author-bio-1',
            'body': 'This author is cool',
            'author': {
                'type': 'authors',
                'id': 'author-1'
            },
            '_included': {
                'authors': [{
                    'id': 'author-1',
                    'name': 'Homer Simpson',
                    'email': 'homer@simpson.com',
                }]
            },
        }
        self.assertEqual(result_data, expected_data)
