# Django REST framework 3.14 removed NullBooleanField
# can be removed once support for DRF 3.13 is dropped.
try:
    from rest_framework.serializers import NullBooleanField
except ImportError:  # pragma: no cover
    NullBooleanField = object()


# Django REST framework 3.14 deprecates usage of `_get_reference`.
# can be removed once support for DRF 3.13 is dropped.
def get_reference(schema, serializer):
    try:
        return schema.get_reference(serializer)
    except AttributeError:  # pragma: no cover
        return schema._get_reference(serializer)
