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

