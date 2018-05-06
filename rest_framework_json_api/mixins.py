"""
Class Mixins.
"""


class MultipleIDMixin(object):
    """
    Override get_queryset for multiple id support
    """

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
