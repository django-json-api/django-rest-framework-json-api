"""
Pagination fields
"""
import warnings
from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.views import Response


class _JsonApiPageNumberPagination(PageNumberPagination):
    """
    A json-api compatible pagination format.
    Use a private name for the implementation because the public name is pending deprecation.
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


class JsonApiPageNumberPagination(_JsonApiPageNumberPagination):
    """
    current public name to be deprecated soon.
    """
    def __init__(self):
        if type(self) == JsonApiPageNumberPagination:
            warnings.warn(
                'JsonApiPageNumberPagination will be renamed to PageNumberPagination in'
                ' release 3.0. See '
                'https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html#pagination',  # noqa: E501
                PendingDeprecationWarning)
        super(_JsonApiPageNumberPagination, self).__init__()


class _JsonApiLimitOffsetPagination(LimitOffsetPagination):
    """
    A limit/offset based style. For example:
    http://api.example.org/accounts/?page[limit]=100
    http://api.example.org/accounts/?page[offset]=400&page[limit]=100

    Use a private name for the implementation because the public name is pending deprecation.
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


class JsonApiLimitOffsetPagination(_JsonApiLimitOffsetPagination):
    """
    current public name to be deprecated soon.
    """

    def __init__(self):
        warnings.warn(
            'JsonApiLimitOffsetPagination will be renamed to LimitOffsetPagination in release 3.0'
            ' See '
            'https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html#pagination',
            PendingDeprecationWarning)
        super(JsonApiLimitOffsetPagination, self).__init__()



class PageNumberPagination(_JsonApiPageNumberPagination):
    """
    A soon-to-be-changed paginator that uses non-JSON:API query parameters (default:
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
                'PageNumberPagination will change in release 3.0 to change default values to: '
                '`page_query_param = "page[number]"` and `page_size_query_param = "page[size]"`. '
                'If you want to retain the current defaults you will need to explicitly set '
                '`page_query_param = "page"` and `page_size_query_param = "page_size"`. '
                'See '
                'https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html#pagination',  # noqa: E501
                PendingDeprecationWarning)

        super(PageNumberPagination, self).__init__()


class LimitOffsetPagination(_JsonApiLimitOffsetPagination):
    """
    Deprecated paginator that uses a different max_limit
    """
    max_limit = None

    def __init__(self):
        if type(self) == LimitOffsetPagination:
            warn = self.max_limit is None
        else:
            warn = 'max_limit' not in type(self).__dict__
        if warn:
            warnings.warn(
                'LimitOffsetPagination will change in release 3.0 to default to `max_limit=100`. '
                'If you want to retain the current default you will need to explicitly set '
                '`max_limit = None`.'
                'See '
                'https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html#pagination',  # noqa: E501
                PendingDeprecationWarning)
        super(LimitOffsetPagination, self).__init__()
