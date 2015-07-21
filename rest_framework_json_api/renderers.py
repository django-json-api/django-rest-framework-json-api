"""
Renderers
"""
from rest_framework import renderers

from . import utils


class JSONRenderer(renderers.JSONRenderer):
    """
    Render a JSON response the JSON API v1.0 (jsonapi.org) way. Such as:
    {
      "links": {
        "self": "http://example.com/posts",
        "next": "http://example.com/posts?page[offset]=2",
        "last": "http://example.com/posts?page[offset]=10"
      },
      "data": [{
        "type": "posts",
        "id": "1",
        "attributes": {
          "title": "JSON API paints my bikeshed!"
        },
        "relationships": {
          "author": {
            "links": {
              "self": "http://example.com/posts/1/relationships/author",
              "related": "http://example.com/posts/1/author"
            },
            "data": { "type": "people", "id": "9" }
          },
          "comments": {
            "links": {
              "self": "http://example.com/posts/1/relationships/comments",
              "related": "http://example.com/posts/1/comments"
            },
            "data": [
              { "type": "comments", "id": "5" },
              { "type": "comments", "id": "12" }
            ]
          }
        },
        "links": {
          "self": "http://example.com/posts/1"
        }
      }],
      "included": [{
        "type": "people",
        "id": "9",
        "attributes": {
          "first-name": "Dan",
          "last-name": "Gebhardt",
          "twitter": "dgeb"
        },
        "links": {
          "self": "http://example.com/people/9"
        }
      }, {
        "type": "comments",
        "id": "5",
        "attributes": {
          "body": "First!"
        },
        "links": {
          "self": "http://example.com/comments/5"
        }
      }, {
        "type": "comments",
        "id": "12",
        "attributes": {
          "body": "I like XML better"
        },
        "links": {
          "self": "http://example.com/comments/12"
        }
      }]
    }
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Get the resource name.
        resource_type = utils.get_resource_type(renderer_context)

        # If no `resource_type` is found, render the default response.
        if not resource_type:
            return super(JSONRenderer, self).render(
                data, accepted_media_type, renderer_context
            )

        # If this is an error response, skip the rest.
        if 'errors' in resource_type or resource_type == 'data':
            return super(JSONRenderer, self).render(
                {resource_type: data}, accepted_media_type, renderer_context
            )

        # Camelize the keynames.
        formatted_data = utils.format_keys(data, 'camelize')

        # Check if it's paginated data and contains a `results` key.
        results = (formatted_data.get('results')
                   if isinstance(formatted_data, dict) else None)

        # Pluralize the resource_type.
        resource_type = utils.format_resource_name(
            results or formatted_data, resource_type
        )

        resource_data = []

        if results:
            for result in results:
                resource_data.append(utils.format_resource_data(resource_type, result))
            formatted_data.pop('results')

            rendered_data = ({'links': formatted_data.pop('links')} if formatted_data.get('links', False) else {})
            rendered_data.update({
                'data': resource_data,
                'meta': formatted_data
            })
        else:
            rendered_data = {
                resource_type: formatted_data
            }

        return super(JSONRenderer, self).render(
            rendered_data, accepted_media_type, renderer_context
        )
