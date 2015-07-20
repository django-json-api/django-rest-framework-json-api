"""
Parsers
"""
from rest_framework import parsers

from . import utils


class JSONParser(parsers.JSONParser):
    """
    A JSON API client will send a payload that looks like this:

        {
            "data": {
                "type": "identities",
                "id": 1,
                "attributes": {
                    "first_name": "John",
                    "last_name": "Coltrane"
                }
            }
        }

    We extract the attributes so that DRF serializers can work as normal.
    """
    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data
        """
        result = super(JSONParser, self).parse(stream, media_type=media_type,
                                               parser_context=parser_context)
        data = result.get('data', {})
        attributes = data.get('attributes')
        if attributes:
            attributes['id'] = data.get('id')
        return utils.format_keys(attributes, 'underscore')
