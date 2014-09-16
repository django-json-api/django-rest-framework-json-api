import copy
import inflection

from rest_framework import renderers
from rest_framework_ember.utils import get_resource_name


class EmberJSONRenderer(renderers.JSONRenderer):
    """
    Render a JSON response the way Ember Data wants it. Such as:
    {
        "resource": {
            "id": 1,
            "field": "lorem ipsum",
            "pub_date": "2014-03-13 16:33:37"
        }
    }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        view = renderer_context.get('view')
        resource_name = get_resource_name(view)

        if isinstance(data, dict):
            for key, value in data.items():
                data[inflection.camelize(key, False)] = data.pop(key)

        elif isinstance(data, (list, tuple)):
            for obj in data:
                if hasattr(obj, 'items'):
                    for key, value in obj.items():
                        obj[inflection.camelize(key, False)] = obj.pop(key)
            resource_name = inflection.pluralize(resource_name)

        if resource_name == False:
            return super(JSONRenderer, self).render(
                data, accepted_media_type, renderer_context)

        try:
            data_copy = copy.copy(data)
            content = data_copy.pop('results')
            data = {resource_name : content, "meta" : data_copy}
        except (TypeError, KeyError, AttributeError) as e:
            data = {resource_name : data}
        return super(JSONRenderer, self).render(
            data, accepted_media_type, renderer_context)
