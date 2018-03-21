"""
Class Mixins.
"""


class MultipleIDMixin(object):
    """
    A stackable Mixin that overides get_queryset for multiple id support
    """

    def get_queryset(self):
        """
        Override :meth:``get_queryset``
        """
        self.queryset = super(MultipleIDMixin, self).get_queryset()
        if hasattr(self.request, 'query_params'):
            ids = dict(self.request.query_params).get('ids[]')
        else:
            ids = dict(self.request.QUERY_PARAMS).get('ids[]')
        if ids:
            self.queryset = self.queryset.filter(id__in=ids)
        return self.queryset


class FilterMixin(object):
    """
    A stackable Mixin that overrides get_queryset for JSON API filter query parameter support
    per http://jsonapi.org/recommendations/#filtering.

    The `filter` syntax is `filter[name1]=list,of,alternative,values&filter[name2]=more,alternatives...`
    which can be interpreted as `(name1 in [list,of,alternative,values]) and (name2 in [more,alternatives])`
    `name` can be `id` or attributes field.

    @example
    GET /widgets/?filter[name1]=can+opener,tap&filter[name2]=foo

    TODO: decide if we want to allow multiple instances of the *same* filter[field]
      e.g. Is "&filter[id]==123&filter[id]=345" the same as "&filter[id]=123,345"?
      For now additional instances of the same filter[field] are ignored.
    """

    def get_queryset(self):
        """
        Override :meth:``get_queryset``
        """
        self.queryset = super(FilterMixin, self).get_queryset()
        qp = dict(self.request.query_params if hasattr(self.request, 'query_params') else self.request.QUERY_PARAMS)
        if not qp:
            return self.queryset
        FILTER = 'filter['
        flen = len(FILTER)
        filters = {}
        for k in qp:
            if k[:flen] == FILTER and k[-1] == ']':
                attr = k[flen:-1]
                filters[attr+"__in"] = qp.get(k)[0].split(',')

        self.queryset = self.queryset.filter(**filters)
        return self.queryset


class SortMixin(object):
    """
    A stackable Mixin that overrides get_queryset for JSON API sort query parameter support
    per http://jsonapi.org/format/#fetching-sorting.

    The `sort` syntax is `sort=-field1,field2,...`
    The `sort` parameter is allowed to be given more than once and the lists are combined.
    e.g. "&sort=field1&sort=field2" is the same as "&sort=field1,field2".
    TODO: Decide if allowing repeats of the sort parameter is correct.
    TODO: Add dot-separated type.field to enable sorting by relationship attributes.

    @example
    GET /widgets/?sort=-name1,name2&sort=name3,name4
    """

    def get_queryset(self):
        """
        Override :meth:``get_queryset``
        """
        self.queryset = super(SortMixin, self).get_queryset()
        qp = dict(self.request.query_params if hasattr(self.request, 'query_params') else self.request.QUERY_PARAMS)
        if not qp:
            return self.queryset
        sorts = []
        if 'sort' in qp:
            for s in qp.get('sort'):
                sorts += s.split(',')

        self.queryset = self.queryset.order_by(*sorts)
        return self.queryset
