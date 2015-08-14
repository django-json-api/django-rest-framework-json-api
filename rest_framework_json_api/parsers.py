"""
Parsers
"""
from rest_framework import parsers

from . import utils, renderers, exceptions


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
    media_type = 'application/vnd.api+json'
    renderer_class = renderers.JSONRenderer

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data
        """
        result = super(JSONParser, self).parse(stream, media_type=media_type, parser_context=parser_context)
        data = result.get('data', {})

        if data:
            # Check for inconsistencies
            resource_name = utils.get_resource_name(parser_context)
            if data.get('type') != resource_name:
                raise exceptions.Conflict(
                    "The resource object's type ({data_type}) is not the type "
                    "that constitute the collection represented by the endpoint ({resource_type}).".format(
                        data_type=data.get('type'),
                        resource_type=resource_name
                    )
                )
            # Get the ID
            data_id = data.get('id')
            # Get the attributes
            attributes = utils.format_keys(data.get('attributes'), 'underscore') if data.get(
                'attributes') else dict()
            # Get the relationships
            relationships = utils.format_keys(data.get('relationships'), 'underscore') if data.get(
                'relationships') else dict()

            # Parse the relationships
            parsed_relationships = dict()
            for field_name, field_data in relationships.items():
                field_data = field_data.get('data')
                if isinstance(field_data, dict):
                    parsed_relationships[field_name] = field_data.get('id')
                elif isinstance(field_data, list):
                    parsed_relationships[field_name] = list(relation.get('id') for relation in field_data)

            # Construct the return data
            parsed_data = {'id': data_id}
            parsed_data.update(attributes)
            parsed_data.update(parsed_relationships)
            return parsed_data
