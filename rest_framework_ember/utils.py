"""
Resource name utilities.
"""

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

    return resource_name

