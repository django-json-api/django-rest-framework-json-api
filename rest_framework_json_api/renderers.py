"""
Renderers
"""
from collections import OrderedDict
from rest_framework import renderers

from . import utils
from rest_framework.relations import RelatedField
from rest_framework.settings import api_settings


class JSONRenderer(renderers.JSONRenderer):
    """
    Render a JSON response per the JSON API spec:
    {
        "data": [{
            "type": "companies",
            "id": 1,
            "attributes": {
                "name": "Mozilla",
                "slug": "mozilla",
                "date-created": "2014-03-13 16:33:37"
            }
        }, {
            "type": "companies",
            "id": 2,
            ...
        }]
    }
    """

    media_type = 'application/vnd.api+json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Get the resource name.
        resource_name = utils.get_resource_name(renderer_context)

        view = renderer_context.get("view", None)
        request = renderer_context.get("request", None)

        # If `resource_name` is set to None then render default as the dev
        # wants to build the output format manually.
        if resource_name is None or resource_name is False:
            return super(JSONRenderer, self).render(
                data, accepted_media_type, renderer_context
            )

        # If this is an error response, skip the rest.
        if resource_name == 'errors':
            if len(data) > 1:
                data.sort(key=lambda x: x.get('source', {}).get('pointer', ''))
            return super(JSONRenderer, self).render(
                {resource_name: data}, accepted_media_type, renderer_context
            )

        json_api_included = list()

        # If detail view then json api spec expects dict, otherwise a list
        # - http://jsonapi.org/format/#document-top-level
        if view and hasattr(view, 'action') and view.action == 'list':
            # Check for paginated results
            results = (data["results"] if isinstance(data, dict) else data)

            resource_serializer = results.serializer

            # Get the serializer fields
            fields = utils.get_serializer_fields(resource_serializer)

            json_api_data = list()
            for resource in results:
                json_api_data.append(
                    utils.build_json_resource_obj(fields, resource, resource_name))
                included = utils.extract_included(fields, resource)
                if included:
                    json_api_included.extend(included)
        else:
            # Check if data contains a serializer
            if hasattr(data, 'serializer'):
                fields = utils.get_serializer_fields(data.serializer)
                json_api_data = utils.build_json_resource_obj(fields, data, resource_name)
                included = utils.extract_included(fields, data)
                if included:
                    json_api_included.extend(included)
            else:
                json_api_data = data

        # Make sure we render data in a specific order
        render_data = OrderedDict()

        if isinstance(data, dict) and data.get('links'):
            render_data['links'] = data.get('links')

        render_data['data'] = json_api_data

        if len(json_api_included) > 0:
            # Iterate through compound documents to remove duplicates
            seen = set()
            unique_compound_documents = list()
            for included_dict in json_api_included:
                type_tuple = tuple((included_dict['type'], included_dict['id']))
                if type_tuple not in seen:
                    seen.add(type_tuple)
                    unique_compound_documents.append(included_dict)

            # Sort the items by type then by id
            render_data['included'] = sorted(unique_compound_documents, key=lambda item: (item['type'], item['id']))

        if isinstance(data, dict) and data.get('meta'):
            render_data['meta'] = data.get('meta')

        return super(JSONRenderer, self).render(
            render_data, accepted_media_type, renderer_context
        )
