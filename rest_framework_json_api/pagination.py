"""
Pagination fields
"""
import warnings
from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.views import Response


class JsonApiPageNumberPagination(PageNumberPagination):
    """
    A json-api compatible pagination format.
    """
    page_query_param = 'page[number]'
    page_size_query_param = 'page[size]'
    max_page_size = 100

    def build_link(self, index):
        if not index:
            return None
        url = self.request and self.request.build_absolute_uri() or ''
        return replace_query_param(url, self.page_query_param, index)

    def get_paginated_response(self, data):
        next = None
        previous = None

        if self.page.has_next():
            next = self.page.next_page_number()
        if self.page.has_previous():
            previous = self.page.previous_page_number()

        return Response({
            'results': data,
            'meta': {
                'pagination': OrderedDict([
                    ('page', self.page.number),
                    ('pages', self.page.paginator.num_pages),
                    ('count', self.page.paginator.count),
                ])
            },
            'links': OrderedDict([
                ('first', self.build_link(1)),
                ('last', self.build_link(self.page.paginator.num_pages)),
                ('next', self.build_link(next)),
                ('prev', self.build_link(previous))
            ])
        })


class JsonApiLimitOffsetPagination(LimitOffsetPagination):
    """
    A limit/offset based style. For example:

    .. code::

        http://api.example.org/accounts/?page[limit]=100
        http://api.example.org/accounts/?page[offset]=400&page[limit]=100

    """
    limit_query_param = 'page[limit]'
    offset_query_param = 'page[offset]'
    max_limit = 100

    def get_last_link(self):
        if self.count == 0:
            return None

        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        offset = (self.count // self.limit) * self.limit

        if offset <= 0:
            return remove_query_param(url, self.offset_query_param)

        return replace_query_param(url, self.offset_query_param, offset)

    def get_first_link(self):
        if self.count == 0:
            return None

        url = self.request.build_absolute_uri()
        return remove_query_param(url, self.offset_query_param)

    def get_paginated_response(self, data):
        return Response({
            'results': data,
            'meta': {
                'pagination': OrderedDict([
                    ('count', self.count),
                    ('limit', self.limit),
                    ('offset', self.offset),
                ])
            },
            'links': OrderedDict([
                ('first', self.get_first_link()),
                ('last', self.get_last_link()),
                ('next', self.get_next_link()),
                ('prev', self.get_previous_link())
            ])
        })


class PageNumberPagination(JsonApiPageNumberPagination):
    """
    .. warning::

        PageNumberPagination is deprecated. Use JsonApiPageNumberPagination instead.
        If you want to retain current defaults you will need to implement custom
        pagination class explicitly setting `page_query_param = "page"` and
        `page_size_query_param = "page_size"`.
        See changelog for more details.

    A paginator that uses non-JSON:API query parameters (default:
    'page' and 'page_size' instead of 'page[number]' and 'page[size]').
    """
    page_query_param = 'page'
    page_size_query_param = 'page_size'

    def __init__(self):
        if type(self) == PageNumberPagination:
            warn = self.page_query_param == 'page' or self.page_size_query_param == 'page_size'
        else:  # inherited class doesn't override the attributes?
            warn = ('page_query_param' not in type(self).__dict__ or
                    'page_size_query_param' not in type(self).__dict__)
        if warn:
            warnings.warn(
                'PageNumberPagination is deprecated. Use JsonApiPageNumberPagination instead. '
                'If you want to retain current defaults you will need to implement custom '
                'pagination class explicitly setting `page_query_param = "page"` and '
                '`page_size_query_param = "page_size"`. '
                'See changelog for more details.',
                DeprecationWarning)

        super(PageNumberPagination, self).__init__()


class LimitOffsetPagination(JsonApiLimitOffsetPagination):
    """
    .. warning::

        LimitOffsetPagination is deprecated. Use JsonApiLimitOffsetPagination instead.
        If you want to retain current defaults you will need to implement custom
        pagination class explicitly setting `max_limit = None`.
        See changelog for more details.

    A paginator that uses a different max_limit from `JsonApiLimitOffsetPagination`.
    """
    max_limit = None

    def __init__(self):
        if type(self) == LimitOffsetPagination:
            warn = self.max_limit is None
        else:
            warn = 'max_limit' not in type(self).__dict__
        if warn:
            warnings.warn(
                'LimitOffsetPagination is deprecated. Use JsonApiLimitOffsetPagination instead. '
                'If you want to retain current defaults you will need to implement custom '
                'pagination class explicitly setting `max_limit = None`. '
                'See changelog for more details.',
                DeprecationWarning)
        super(LimitOffsetPagination, self).__init__()
