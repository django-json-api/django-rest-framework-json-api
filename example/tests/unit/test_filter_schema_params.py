from rest_framework import filters as drf_filters

from rest_framework_json_api import filters as dja_filters
from rest_framework_json_api.django_filters import backends

from example.views import EntryViewSet


class DummyEntryViewSet(EntryViewSet):
    filter_backends = (
        dja_filters.QueryParameterValidationFilter,
        dja_filters.OrderingFilter,
        backends.DjangoFilterBackend,
        drf_filters.SearchFilter,
    )
    filterset_fields = {
        "id": ("exact",),
        "headline": ("exact", "contains"),
        "blog__name": ("contains",),
    }

    def __init__(self, **kwargs):
        # dummy up self.request since PreloadIncludesMixin expects it to be defined
        self.request = None
        super().__init__(**kwargs)


def test_filters_get_schema_params():
    """
    test all my filters for `get_schema_operation_parameters()`
    """
    # list of tuples: (filter, expected result)
    filters = [
        (dja_filters.QueryParameterValidationFilter, []),
        (
            backends.DjangoFilterBackend,
            [
                {
                    "name": "filter[id]",
                    "required": False,
                    "in": "query",
                    "description": "id",
                    "schema": {"type": "string"},
                },
                {
                    "name": "filter[headline]",
                    "required": False,
                    "in": "query",
                    "description": "headline",
                    "schema": {"type": "string"},
                },
                {
                    "name": "filter[headline.contains]",
                    "required": False,
                    "in": "query",
                    "description": "headline__contains",
                    "schema": {"type": "string"},
                },
                {
                    "name": "filter[blog.name.contains]",
                    "required": False,
                    "in": "query",
                    "description": "blog__name__contains",
                    "schema": {"type": "string"},
                },
            ],
        ),
        (
            dja_filters.OrderingFilter,
            [
                {
                    "name": "sort",
                    "required": False,
                    "in": "query",
                    "description": "Which field to use when ordering the results.",
                    "schema": {"type": "string"},
                }
            ],
        ),
        (
            drf_filters.SearchFilter,
            [
                {
                    "name": "filter[search]",
                    "required": False,
                    "in": "query",
                    "description": "A search term.",
                    "schema": {"type": "string"},
                }
            ],
        ),
    ]
    view = DummyEntryViewSet()

    for c, expected in filters:
        f = c()
        result = f.get_schema_operation_parameters(view)
        assert len(result) == len(expected)
        if len(result) == 0:
            continue
        # py35: the result list/dict ordering isn't guaranteed
        for res_item in result:
            assert "name" in res_item
            for exp_item in expected:
                if res_item["name"] == exp_item["name"]:
                    assert res_item == exp_item
