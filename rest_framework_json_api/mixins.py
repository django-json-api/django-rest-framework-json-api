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
        if hasattr(self.request, 'query_params'):
            ids = dict(self.request.query_params).get('ids[]')
        else:
            ids = dict(self.request.QUERY_PARAMS).get('ids[]')

        if 'filter[id]' in self.request.query_params:
            ids = self.request.query_params.get('filter[id]').split(',')

        if ids:
            self.queryset = self.queryset.filter(id__in=ids)

        return self.queryset

