"""
Class Mixins.
"""
import warnings


class MultipleIDMixin(object):
    """
    Override get_queryset for multiple id support

    .. warning::

        MultipleIDMixin is deprecated because it does not comply with http://jsonapi.org/format.
        Instead add :py:class:`django_filters.DjangoFilterBackend` to your
        list of `filter_backends` and change client usage from:
        ``?ids[]=id1,id2,...,idN`` to ``'?filter[id.in]=id1,id2,...,idN``

    """
    def __init__(self, *args, **kwargs):
        warnings.warn("MultipleIDMixin is deprecated. "
                      "Instead add django_filters.DjangoFilterBackend to your "
                      "list of 'filter_backends' and change client usage from: "
                      "'?ids[]=id1,id2,...,idN' to '?filter[id.in]=id1,id2,...,idN'",
                      DeprecationWarning)
        super(MultipleIDMixin, self).__init__(*args, **kwargs)

    def get_queryset(self):
        """
        Override :meth:``get_queryset``
        """
        queryset = super(MultipleIDMixin, self).get_queryset()
        if hasattr(self.request, 'query_params'):
            ids = dict(self.request.query_params).get('ids[]')
        else:
            ids = dict(self.request.QUERY_PARAMS).get('ids[]')
        if ids:
            queryset = queryset.filter(id__in=ids)
        return queryset
