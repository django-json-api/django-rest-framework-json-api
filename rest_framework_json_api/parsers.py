"""
Parsers
"""
from django.conf import settings
from django.utils import six
from rest_framework import parsers
from rest_framework.exceptions import ParseError

from . import exceptions, renderers, utils
from .serializers import PolymorphicModelSerializer, ResourceIdentifierObjectSerializer


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
        attributes = data.get('attributes')
        uses_format_translation = getattr(settings, 'JSON_API_FORMAT_KEYS', False)

        if not attributes:
            return dict()
        elif uses_format_translation:
            # convert back to python/rest_framework's preferred underscore format
            return utils.format_keys(attributes, 'underscore')
        else:
            return attributes

    @staticmethod
    def parse_relationships(data):
        uses_format_translation = getattr(settings, 'JSON_API_FORMAT_KEYS', False)
        relationships = data.get('relationships')

        if not relationships:
            relationships = dict()
        elif uses_format_translation:
            # convert back to python/rest_framework's preferred underscore format
            relationships = utils.format_keys(relationships, 'underscore')

        # Parse the relationships
        parsed_relationships = dict()
        for field_name, field_data in relationships.items():
            field_data = field_data.get('data')
            if isinstance(field_data, dict) or field_data is None:
                parsed_relationships[field_name] = field_data
            elif isinstance(field_data, list):
                parsed_relationships[field_name] = list(relation for relation in field_data)
        return parsed_relationships

    @staticmethod
    def parse_metadata(result):
        metadata = result.get('meta')
        if metadata:
            return {'_meta': metadata}
        else:
            return {}

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data

        There are two basic object types in JSON-API.

        1. Resource Identifier Object

        They only have 'id' and 'type' keys (optionally also 'meta'). The 'type'
        should be passed to the views for processing. These objects are used in
        'relationships' keys and also as the actual 'data' in Relationship URLs.

        2. Resource Objects

        They use the keys as above plus optional 'attributes' and
        'relationships'. Attributes and relationships should be flattened before
        sending to views and the 'type' key should be removed.

        We support requests with list data. In JSON-API list data can be found
        in Relationship URLs where we would expect Resource Identifier Objects,
        but we will also allow lists of Resource Objects as the users might want
        to implement bulk operations in their custom views.

        In addition True, False and None will be accepted as data and passed to
        views. In JSON-API None is a valid data for 1-to-1 Relationship URLs and
        indicates that the relationship should be cleared.
        """
        result = super(JSONParser, self).parse(
            stream, media_type=media_type, parser_context=parser_context
        )

        if not isinstance(result, dict) or 'data' not in result:
            raise ParseError('Received document does not contain primary data')

        data = result.get('data')
        view = parser_context['view']
        resource_name = utils.get_resource_name(parser_context, expand_polymorphic_types=True)
        method = parser_context.get('request').method
        serializer_class = getattr(view, 'serializer_class', None)
        in_relationship_view = serializer_class == ResourceIdentifierObjectSerializer

        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    err = "Items in data array must be objects with 'id' and 'type' members."
                    raise ParseError(err)

            if in_relationship_view:
                for identifier in data:
                    self.verify_resource_identifier(identifier)
                return data
            else:
                return list(
                    self.parse_resource(d, d, resource_name, method, serializer_class)
                    for d in data
                )
        elif isinstance(data, dict):
            if in_relationship_view:
                self.verify_resource_identifier(data)
                return data
            else:
                return self.parse_resource(data, result, resource_name, method, serializer_class)
        else:
            # None, True, False, numbers and strings
            return data

    def parse_resource(self, data, meta_source, resource_name, method, serializer_class):
        # Check for inconsistencies
        if method in ('PUT', 'POST', 'PATCH'):
            if isinstance(resource_name, six.string_types):
                if data.get('type') != resource_name:
                    raise exceptions.Conflict(
                        "The resource object's type ({data_type}) is not the type that "
                        "constitute the collection represented by the endpoint "
                        "({resource_type}).".format(
                            data_type=data.get('type'),
                            resource_type=resource_name))
            else:
                if data.get('type') not in resource_name:
                    raise exceptions.Conflict(
                        "The resource object's type ({data_type}) is not the type that "
                        "constitute the collection represented by the endpoint "
                        "(one of [{resource_types}]).".format(
                            data_type=data.get('type'),
                            resource_types=", ".join(resource_name)))
        if not data.get('id') and method in ('PATCH', 'PUT'):
            raise ParseError("The resource object must contain an 'id' member.")

        # Construct the return data
        parsed_data = {'id': data.get('id')} if 'id' in data else {}
        # `type` field needs to be allowed in none polymorphic serializers
        if serializer_class is not None:
            if issubclass(serializer_class, PolymorphicModelSerializer):
                parsed_data['type'] = data.get('type')
        parsed_data.update(self.parse_attributes(data))
        parsed_data.update(self.parse_relationships(data))
        parsed_data.update(self.parse_metadata(meta_source))
        return parsed_data

    def verify_resource_identifier(self, data):
        if not data.get('id') or not data.get('type'):
            raise ParseError('Received data is not a valid JSONAPI Resource Identifier Object(s).')
