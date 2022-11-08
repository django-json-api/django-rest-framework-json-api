"""
Parsers
"""
from rest_framework import parsers
from rest_framework.exceptions import ParseError

from rest_framework_json_api import exceptions, renderers
from rest_framework_json_api.utils import get_resource_name, undo_format_field_names


class JSONParser(parsers.JSONParser):
    """
    Similar to `JSONRenderer`, the `JSONParser` you may override the following methods if you
    need highly custom parsing control.

    A JSON:API client will send a payload that looks like this:

    .. code:: json


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

    media_type = "application/vnd.api+json"
    renderer_class = renderers.JSONRenderer

    @staticmethod
    def parse_attributes(data):
        attributes = data.get("attributes") or dict()
        return undo_format_field_names(attributes)

    @staticmethod
    def parse_relationships(data):
        relationships = data.get("relationships") or dict()
        relationships = undo_format_field_names(relationships)

        # Parse the relationships
        parsed_relationships = dict()
        for field_name, field_data in relationships.items():
            field_data = field_data.get("data")
            if isinstance(field_data, dict) or field_data is None:
                parsed_relationships[field_name] = field_data
            elif isinstance(field_data, list):
                parsed_relationships[field_name] = list(
                    relation for relation in field_data
                )
        return parsed_relationships

    @staticmethod
    def parse_metadata(result):
        """
        Returns a dictionary which will be merged into parsed data of the request. By default,
        it reads the `meta` content in the request body and returns it in a dictionary with
        a `_meta` top level key.
        """
        metadata = result.get("meta")
        if metadata:
            return {"_meta": metadata}
        else:
            return {}

    def parse_data(self, result, parser_context):
        """
        Formats the output of calling JSONParser to match the JSON:API specification
        and returns the result.
        """
        if not isinstance(result, dict) or "data" not in result:
            raise ParseError("Received document does not contain primary data")

        data = result.get("data")
        parser_context = parser_context or {}
        view = parser_context.get("view")

        from rest_framework_json_api.views import RelationshipView

        if isinstance(view, RelationshipView):
            # We skip parsing the object as JSON:API Resource Identifier Object and not
            # a regular Resource Object
            if isinstance(data, list):
                for resource_identifier_object in data:
                    if not (
                        resource_identifier_object.get("id")
                        and resource_identifier_object.get("type")
                    ):
                        raise ParseError(
                            "Received data contains one or more malformed JSON:API "
                            "Resource Identifier Object(s)"
                        )
            elif not (data.get("id") and data.get("type")):
                raise ParseError(
                    "Received data is not a valid JSON:API Resource Identifier Object"
                )

            return data

        request = parser_context.get("request")
        method = request and request.method

        # Sanity check
        if not isinstance(data, dict):
            raise ParseError(
                "Received data is not a valid JSON:API Resource Identifier Object"
            )

        # Check for inconsistencies
        if method in ("PUT", "POST", "PATCH"):
            resource_name = get_resource_name(
                parser_context, expand_polymorphic_types=True
            )
            if isinstance(resource_name, str):
                if data.get("type") != resource_name:
                    raise exceptions.Conflict(
                        "The resource object's type ({data_type}) is not the type that "
                        "constitute the collection represented by the endpoint "
                        "({resource_type}).".format(
                            data_type=data.get("type"), resource_type=resource_name
                        )
                    )
            else:
                if data.get("type") not in resource_name:
                    raise exceptions.Conflict(
                        "The resource object's type ({data_type}) is not the type that "
                        "constitute the collection represented by the endpoint "
                        "(one of [{resource_types}]).".format(
                            data_type=data.get("type"),
                            resource_types=", ".join(resource_name),
                        )
                    )
        if not data.get("id") and method in ("PATCH", "PUT"):
            raise ParseError(
                "The resource identifier object must contain an 'id' member"
            )

        if method in ("PATCH", "PUT"):
            lookup_url_kwarg = getattr(view, "lookup_url_kwarg", None) or getattr(
                view, "lookup_field", None
            )
            if lookup_url_kwarg and str(data.get("id")) != str(
                view.kwargs[lookup_url_kwarg]
            ):
                raise exceptions.Conflict(
                    "The resource object's id ({data_id}) does not match url's "
                    "lookup id ({url_id})".format(
                        data_id=data.get("id"), url_id=view.kwargs[lookup_url_kwarg]
                    )
                )

        # Construct the return data
        parsed_data = {"id": data.get("id")} if "id" in data else {}
        parsed_data["type"] = data.get("type")
        parsed_data.update(self.parse_attributes(data))
        parsed_data.update(self.parse_relationships(data))
        parsed_data.update(self.parse_metadata(result))
        return parsed_data

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data
        """
        result = super().parse(
            stream, media_type=media_type, parser_context=parser_context
        )

        return self.parse_data(result, parser_context)
