"""
Renderers
"""
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

        # @TODO format errors correctly
        # If this is an error response, skip the rest.
        if resource_name == 'errors':
            return super(JSONRenderer, self).render(
                {resource_name: data}, accepted_media_type, renderer_context
            )

        # If detail view then json api spec expects dict, otherwise a list
        # - http://jsonapi.org/format/#document-top-level
        if view and view.action == 'list':
            # Check for paginated results
            results = (data["results"] if isinstance(data, dict) else data)

            json_api_data = []
            for result in results:
                result_id = result.pop('id', None)
                json_api_data.append({
                    'type': resource_name,
                    'id': result_id,
                    'attributes': utils.format_keys(result),
                    'meta': utils.convert_resource(result, results, request)
                })
        else:
            result_id = data.pop('id', None)
            json_api_data = {
                'type': resource_name,
                'id': result_id,
                'attributes': utils.format_keys(data),
            }

        # remove results from the dict
        data.pop('results', None)
        if renderer_context.get('view').action == 'list':
            # allow top level data to be added from list views
            rendered_data = data
        else:
            # on detail views we don't render anything but serializer data
            rendered_data = {}
        rendered_data['data'] = json_api_data

        return super(JSONRenderer, self).render(
            rendered_data, accepted_media_type, renderer_context
        )
