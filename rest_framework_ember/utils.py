import inflection
from django.conf import settings

def get_key(key):
    """
    https://github.com/ngenworks/rest_framework_ember/pull/10

    Introduces camelizing of key names in the JSON response.
    Unfortunately, this breaks backwards compatibility. In the event
    one would like that functionality, they can use the
    ``REST_FRAMEWORK_CAMELIZE_KEYS`` setting.
    """
    camelize = getattr(settings, 'REST_FRAMEWORK_CAMELIZE_KEYS', False)
    if camelize:
        return inflection.camelize(key, False)
    return key


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

            name = get_key(name)
            resource_name = name[:1].lower() + name[1:]

    return resource_name

