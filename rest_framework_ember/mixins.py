"""
Class Mixins.
"""

class MultipleIDMixin(object):
    """
    Override get_queryset for multiple id support
    """
    def get_queryset(self):
        ids = dict(self.request.QUERY_PARAMS).get('ids[]')
        if ids:
            self.queryset = self.queryset.filter(id__in=ids)
        return self.queryset


class SparseFieldsetMixin(object):
    """
    For use with a :class:``ModelViewSet`` and its corresponding
    :class:``ModelSerializer``.

    :class:``SparseFieldsetMixin`` allows for fields to be removed
    from the response so the entire payload is not returned.

    Read more: http://jsonapi.org/format/#fetching-sparse-fieldsets

    Example::

        resp = requests.get('http://example.com/api/users')

    Could return the following::

        [{
            "id": 1,
            "name": "John Coltrane",
            "bio": "some long bio"

        },{
            "id": 2,
            "name": "Miles Davis",
            "bio": "some long bio"
        }]

    However, if only ``id`` and ``name`` are required, it can be wasteful
    to pull down ``bio`` as well.

    Example::

        resp = requests.get('http://example.com/api/users?fields=id,name')

    Would return the following::

        [{
            "id": 1,
            "name": "John Coltrane"
        },{
            "id": 2,
            "name": "Miles Davis"
        }]

    """
    def get_serializer_class(self):
        """
        Override DRF :class:``GenericAPIView`` :meth:``get_serializer_class``

        Change fields on the serializer IF ``fields`` is included
        in the GET query params
        """
        fields = self.request.GET.get('fields')
        allowed_methods = ('GET', 'OPTIONS', 'HEAD', )

        if fields and self.request.method in allowed_methods:
            fields = fields.split(',')

            self.serializer_class.Meta.fields = \
                list(set(fields).intersection(
                    self.serializer_class.Meta.fields))

        return super(SparseFieldsetMixin, self).get_serializer_class()

