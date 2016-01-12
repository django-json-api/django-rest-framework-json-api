"""
Parsers
"""
from rest_framework import parsers
from rest_framework.exceptions import ParseError

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

    @staticmethod
    def parse_attributes(data):
        return utils.format_keys(data.get('attributes'), 'underscore') if data.get('attributes') else dict()

    @staticmethod
    def parse_relationships(data):
        relationships = (utils.format_keys(data.get('relationships'), 'underscore')
                         if data.get('relationships') else dict())

        # Parse the relationships
        parsed_relationships = dict()
        for field_name, field_data in relationships.items():
            field_data = field_data.get('data')
            if isinstance(field_data, dict) or field_data is None:
                parsed_relationships[field_name] = field_data
            elif isinstance(field_data, list):
                parsed_relationships[field_name] = list(relation for relation in field_data)
        return parsed_relationships

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data
        """
        result = super(JSONParser, self).parse(stream, media_type=media_type, parser_context=parser_context)
        data = result.get('data')

        if data:
            from rest_framework_json_api.views import RelationshipView
            if isinstance(parser_context['view'], RelationshipView):
                # We skip parsing the object as JSONAPI Resource Identifier Object and not a regular Resource Object
                if isinstance(data, list):
                    for resource_identifier_object in data:
                        if not (resource_identifier_object.get('id') and resource_identifier_object.get('type')):
                            raise ParseError(
                                'Received data contains one or more malformed JSONAPI Resource Identifier Object(s)'
                            )
                elif not (data.get('id') and data.get('type')):
                    raise ParseError('Received data is not a valid JSONAPI Resource Identifier Object')

                return data

            request = parser_context.get('request')

            # Check for inconsistencies
            resource_name = utils.get_resource_name(parser_context)
            if data.get('type') != resource_name and request.method in ('PUT', 'POST', 'PATCH'):
                raise exceptions.Conflict(
                    "The resource object's type ({data_type}) is not the type "
                    "that constitute the collection represented by the endpoint ({resource_type}).".format(
                        data_type=data.get('type'),
                        resource_type=resource_name
                    )
                )

            # Construct the return data
            parsed_data = {'id': data.get('id')}
            parsed_data.update(self.parse_attributes(data))
            parsed_data.update(self.parse_relationships(data))
            return parsed_data

        else:
            raise ParseError('Received document does not contain primary data')
