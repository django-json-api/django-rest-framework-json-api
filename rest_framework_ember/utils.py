import inflection

from django.conf import settings


def get_resource_name(view):
    """
    Return the name of a resource.
    """
    try:
        # Check the view
        resource_name = getattr(view, 'resource_name')
    except AttributeError:
        try:
            # Check the meta class
            resource_name = getattr(view, 'serializer_class')\
                .Meta.resource_name
        except AttributeError:
            # Use the model
            try:
                name = resource_name = getattr(view, 'serializer_class')\
                    .Meta.model.__name__
            except AttributeError:
                try:
                    name = view.model.__name__
                except AttributeError:
                    name = view.__class__.__name__

            name = format_keys(name)
            resource_name = name[:1].lower() + name[1:]

    return resource_name


def format_keys(obj, format_type=None):
    """
    Takes either a dict or list and returns it with camelized keys only if
    REST_EMBER_FORMAT_KEYS is set.

    :format_type: Either 'camelize' or 'underscore'
    """
    if getattr(settings, 'REST_EMBER_FORMAT_KEYS', False)\
        and format_type in ('camelize', 'underscore'):
        
        if isinstance(obj, dict):
            formatted = {}
            for key, value in obj.items():
                if format_type == 'camelize':
                    formatted[inflection.camelize(key, False)]\
                        = format_keys(value, format_type)
                elif format_type == 'underscore':
                    formatted[inflection.underscore(key)]\
                        = format_keys(value, format_type)
            return formatted
        if isinstance(obj, list):
            return [format_keys(item, format_type) for item in obj]
        else:
            return obj
    else:
        return obj


def format_resource_name(obj, name):
    """
    Pluralize the resource name if more than one object in results.
    """
    if getattr(settings, 'REST_EMBER_PLURALIZE_KEYS', False) and isinstance(obj, list):
        return inflection.pluralize(name) if len(obj) > 1 else name
    else:
        return name
