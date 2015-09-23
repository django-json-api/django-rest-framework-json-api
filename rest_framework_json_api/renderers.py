"""
Renderers
"""
from collections import OrderedDict

from rest_framework import renderers

from . import utils


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
    format = 'vnd.api+json'

    def render(self, data, accepted_media_type=None, renderer_context=None):

        view = renderer_context.get("view", None)
        request = renderer_context.get("request", None)

        from rest_framework_json_api.views import RelationshipView
        if isinstance(view, RelationshipView):
            # Special case for RelationshipView
            render_data = OrderedDict([
                ('data', data)
            ])
            links = view.get_links()
            if links:
                render_data.update({'links': links}),
            return super(JSONRenderer, self).render(
                render_data, accepted_media_type, renderer_context
            )

        # Get the resource name.
        resource_name = utils.get_resource_name(renderer_context)

        # If `resource_name` is set to None then render default as the dev
        # wants to build the output format manually.
        if resource_name is None or resource_name is False:
            return super(JSONRenderer, self).render(
                data, accepted_media_type, renderer_context
            )

        # If this is an error response, skip the rest.
        if resource_name == 'errors':
            if len(data) > 1 and isinstance(data, list):
                data.sort(key=lambda x: x.get('source', {}).get('pointer', ''))
            return super(JSONRenderer, self).render(
                {resource_name: data}, accepted_media_type, renderer_context
            )

        json_api_included = list()

        if view and hasattr(view, 'action') and view.action == 'list' and \
                isinstance(data, dict) and 'results' in data:
            # If detail view then json api spec expects dict, otherwise a list
            # - http://jsonapi.org/format/#document-top-level
            # The `results` key may be missing if unpaginated or an OPTIONS request

            results = data["results"]

            resource_serializer = results.serializer

            # Get the serializer fields
            fields = utils.get_serializer_fields(resource_serializer)

            json_api_data = list()
            for position in range(len(results)):
                resource = results[position]  # Get current resource
                resource_instance = resource_serializer.instance[position]  # Get current instance
                json_api_data.append(
                    utils.build_json_resource_obj(fields, resource, resource_instance, resource_name))
                included = utils.extract_included(fields, resource, resource_instance)
                if included:
                    json_api_included.extend(included)
        else:
            # Check if data contains a serializer
            if hasattr(data, 'serializer'):
                fields = utils.get_serializer_fields(data.serializer)
                resource_instance = data.serializer.instance
                json_api_data = utils.build_json_resource_obj(fields, data, resource_instance, resource_name)
                included = utils.extract_included(fields, data, resource_instance)
                if included:
                    json_api_included.extend(included)
            else:
                json_api_data = data

        # Make sure we render data in a specific order
        render_data = OrderedDict()

        if isinstance(data, dict) and data.get('links'):
            render_data['links'] = data.get('links')

        # format the api root link list
        if view.__class__ and view.__class__.__name__ == 'APIRoot':
            render_data['data'] = None
            render_data['links'] = json_api_data
        else:
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
