import copy
import inflection

from django.conf import settings

from rest_framework import renderers
from rest_framework_ember.utils import get_resource_name, get_key


class JSONRenderer(renderers.JSONRenderer):
    """
    Render a JSON response the way Ember Data wants it. Such as:
    {
        "company": {
            "id": 1,
            "name": "nGen Works",
            "slug": "ngen-works",
            "date_created": "2014-03-13 16:33:37"
        }
    }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):

        view = renderer_context.get('view')
        resource_name = get_resource_name(view)

        if resource_name == False:
            return super(JSONRenderer, self).render(
                data, accepted_media_type, renderer_context)

        try:
            data_copy = copy.copy(data)
            content = data_copy.pop('results')

            # Handle meta
            for key, value in data_copy.items():
                data_copy[get_key(key)] = data_copy.pop(key)

            if isinstance(content, dict):
                for key, value in content.items():
                    content[get_key(key)] = content.pop(key)

            elif isinstance(content, (list, tuple)):
                for obj in content:
                    if hasattr(obj, 'items'):
                        for key, value in obj.items():
                            obj[get_key(key)] = obj.pop(key)

                if len(content) > 1:
                    resource_name = inflection.pluralize(resource_name)

            data = {resource_name : content, "meta" : data_copy}
        except (TypeError, KeyError, AttributeError) as e:

            # Default behavior
            if not resource_name == 'data':
                if isinstance(data, dict):
                    for key, value in data.items():
                        data[get_key(key)] = data.pop(key)
                else:
                    data = {resource_name: data}

            data = {resource_name : data}
        return super(JSONRenderer, self).render(
            data, accepted_media_type, renderer_context)

