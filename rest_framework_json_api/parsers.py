"""
Parsers
"""
from rest_framework import parsers

from . import utils


class JSONParser(parsers.JSONParser):
    """
    By default, EmberJS sends a payload that looks like the following::

        {
            "identity": {
                "id": 1,
                "first_name": "John",
                "last_name": "Coltrane"
            }
        }

    So we can work with the grain on both Ember and RestFramework,
    Do some tweaks to the payload so DRF gets what it expects.
    """
    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data
        """
        result = super(JSONParser, self).parse(stream, media_type=media_type,
                                               parser_context=parser_context)
        resource = result.get(utils.get_resource_name(parser_context))
        return utils.format_keys(resource, 'underscore')
