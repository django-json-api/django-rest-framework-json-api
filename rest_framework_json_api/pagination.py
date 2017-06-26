"""
Pagination fields
"""
from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.views import Response


class PageNumberPagination(PageNumberPagination):
    """
    A json-api compatible pagination format
    """

    page_size_query_param = 'page_size'
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


class LimitOffsetPagination(LimitOffsetPagination):
    """
    A limit/offset based style. For example:
    http://api.example.org/accounts/?page[limit]=100
    http://api.example.org/accounts/?page[offset]=400&page[limit]=100
    """
    limit_query_param = 'page[limit]'
    offset_query_param = 'page[offset]'

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
