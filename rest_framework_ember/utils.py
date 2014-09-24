"""
Resource name utilities.
"""
from collections import OrderedDict
from functools import partial
import re

import inflection


camelize = partial(inflection.camelize, uppercase_first_letter=False)
underscore = inflection.underscore


def get_resource_name(view):
    """
    Return the name of a resource
    """
    try:
        # is the resource name set directly on the view?
        resource_name = getattr(view, 'resource_name')
    except AttributeError:
        try:
            # was it set in the serializer Meta class?
            resource_name = getattr(view, 'serializer_class')\
                .Meta.resource_name
        except AttributeError:
            # camelCase the name of the model if it hasn't been set
            # in either of the other places
            try:
                name = resource_name = getattr(view, 'serializer_class')\
                    .Meta.model.__name__
            except AttributeError:
                try:
                    name = view.model.__name__
                except AttributeError:
                    name = view.__class__.__name__

            resource_name = name[:1].lower() + name[1:]

    if hasattr(view, 'action') and view.action == 'list':
        resource_name = inflection.pluralize(resource_name)
    return inflection.underscore(resource_name)


def recursive_key_map(function, obj):
    if isinstance(obj, dict):
        new_dict = OrderedDict()
        for key, value in obj.items():
            key = function(key)
            new_dict[key] = recursive_key_map(function, value)
        return new_dict
    if isinstance(obj, (list, tuple)):
        return [recursive_key_map(function, value) for value in obj]
    return obj
