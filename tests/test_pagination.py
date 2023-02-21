from rest_framework.request import Request

from rest_framework_json_api.pagination import JsonApiLimitOffsetPagination


class TestLimitOffsetPagination:
    def test_get_paginated_response(self, rf):
        pagination = JsonApiLimitOffsetPagination()
        queryset = range(1, 101)
        offset = 10
        limit = 5
        count = len(queryset)

        request = Request(
            rf.get(
                "/",
                {
                    pagination.limit_query_param: limit,
                    pagination.offset_query_param: offset,
                },
            )
        )
        queryset = list(pagination.paginate_queryset(queryset, request))
        content = pagination.get_paginated_response(queryset).data

        expected_content = {
            "results": list(range(11, 16)),
            "links": {
                "first": "http://testserver/?page%5Blimit%5D=5",
                "last": "http://testserver/?page%5Blimit%5D=5&page%5Boffset%5D=100",
                "next": "http://testserver/?page%5Blimit%5D=5&page%5Boffset%5D=15",
                "prev": "http://testserver/?page%5Blimit%5D=5&page%5Boffset%5D=5",
            },
            "meta": {
                "pagination": {
                    "count": count,
                    "limit": limit,
                    "offset": offset,
                }
            },
        }

        assert content == expected_content
