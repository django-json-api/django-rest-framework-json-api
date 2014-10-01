import inflection


def get_resource_name(view):
    """Return the name of a resource."""
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

            resource_name = inflection.camelize(name, False)

    return resource_name
