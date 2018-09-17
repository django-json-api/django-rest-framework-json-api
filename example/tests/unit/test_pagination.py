import sys
from collections import OrderedDict

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.utils.urls import replace_query_param

from rest_framework_json_api import pagination

factory = APIRequestFactory()


class TestLimitOffset:
    """
    Unit tests for `pagination.JsonApiLimitOffsetPagination`.
    """

    def setup(self):
        class ExamplePagination(pagination.JsonApiLimitOffsetPagination):
            default_limit = 10
            max_limit = 15

        self.pagination = ExamplePagination()
        self.queryset = range(1, 101)
        self.base_url = 'http://testserver/'

    def paginate_queryset(self, request):
        return list(self.pagination.paginate_queryset(self.queryset, request))

    def get_paginated_content(self, queryset):
        response = self.pagination.get_paginated_response(queryset)
        return response.data

    def get_test_request(self, arguments):
        return Request(factory.get('/', arguments))

    def test_valid_offset_limit(self):
        """
        Basic test, assumes offset and limit are given.
        """
        offset = 10
        limit = 5
        count = len(self.queryset)
        last_offset = (count // limit) * limit
        next_offset = 15
        prev_offset = 5

        request = self.get_test_request({
            self.pagination.limit_query_param: limit,
            self.pagination.offset_query_param: offset
        })
        base_url = replace_query_param(self.base_url, self.pagination.limit_query_param, limit)
        last_url = replace_query_param(base_url, self.pagination.offset_query_param, last_offset)
        first_url = base_url
        next_url = replace_query_param(base_url, self.pagination.offset_query_param, next_offset)
        prev_url = replace_query_param(base_url, self.pagination.offset_query_param, prev_offset)
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        next_offset = offset + limit

        expected_content = {
            'results': list(range(offset + 1, next_offset + 1)),
            'links': OrderedDict([
                ('first', first_url),
                ('last', last_url),
                ('next', next_url),
                ('prev', prev_url),
            ]),
            'meta': {
                'pagination': OrderedDict([
                    ('count', count),
                    ('limit', limit),
                    ('offset', offset),
                ])
            }
        }

        assert queryset == list(range(offset + 1, next_offset + 1))
        assert content == expected_content

    @pytest.mark.xfail((sys.version_info.major, sys.version_info.minor) == (2, 7),
                       reason="python2.7 fails to generate DeprecationWarrning for unknown reason")
    def test_limit_offset_deprecation(self):
        with pytest.warns(DeprecationWarning) as record:
            pagination.LimitOffsetPagination()
        assert len(record) == 1
        assert 'LimitOffsetPagination is deprecated' in str(record[0].message)

    class MyInheritedLimitOffsetPagination(pagination.LimitOffsetPagination):
        """
        Inherit the default values
        """
        pass

    class MyOverridenLimitOffsetPagination(pagination.LimitOffsetPagination):
        """
        Explicitly set max_limit to the "old" values.
        """
        max_limit = None

    def test_my_limit_offset_deprecation(self):
        with pytest.warns(DeprecationWarning) as record:
            self.MyInheritedLimitOffsetPagination()
        assert len(record) == 1
        assert 'LimitOffsetPagination is deprecated' in str(record[0].message)

        with pytest.warns(None) as record:
            self.MyOverridenLimitOffsetPagination()
        assert len(record) == 0


class TestPageNumber:
    """
    Unit tests for `pagination.JsonApiPageNumberPagination`.
    """

    @pytest.mark.xfail((sys.version_info.major, sys.version_info.minor) == (2, 7),
                       reason="python2.7 fails to generate DeprecationWarrning for unknown reason")
    def test_page_number_deprecation(self):
        with pytest.warns(DeprecationWarning) as record:
            pagination.PageNumberPagination()
        assert len(record) == 1
        assert 'PageNumberPagination is deprecated' in str(record[0].message)

    class MyInheritedPageNumberPagination(pagination.PageNumberPagination):
        """
        Inherit the default values
        """
        pass

    class MyOverridenPageNumberPagination(pagination.PageNumberPagination):
        """
        Explicitly set page_query_param and page_size_query_param to the "old" values.
        """
        page_query_param = "page"
        page_size_query_param = "page_size"

    @pytest.mark.xfail((sys.version_info.major, sys.version_info.minor) == (2, 7),
                       reason="python2.7 fails to generate DeprecationWarrning for unknown reason")
    def test_my_page_number_deprecation(self):
        with pytest.warns(DeprecationWarning) as record:
            self.MyInheritedPageNumberPagination()
        assert len(record) == 1
        assert 'PageNumberPagination is deprecated' in str(record[0].message)

        with pytest.warns(None) as record:
            self.MyOverridenPageNumberPagination()
        assert len(record) == 0
