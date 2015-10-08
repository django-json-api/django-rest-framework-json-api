from django.core.urlresolvers import reverse
from django.conf import settings

import pytest

from ..views import EntryViewSet
from rest_framework_json_api.pagination import PageNumberPagination

from example.tests.utils import dump_json, redump_json

pytestmark = pytest.mark.django_db


def test_multiple_entries_no_pagination(rf, multiple_entries):

    expected = {
        "data": [
            {
                "type": "posts",
                "id": "1",
                "attributes":
                {
                    "headline": "The Absolute Minimum Every Software DeveloperAbsolutely, Positively Must Know About Unicode and Character Sets (No Excuses!)",
                    "bodyText": "Here goes the body text",
                    "pubDate": None,
                    "modDate": None
                },
                "relationships":
                {
                    "blog": {
                        "data": {"type": "blogs", "id": "1"}
                    },
                    "authors": {
                        "meta": {"count": 1},
                        "data": [{"type": "authors", "id": "1"}]
                    }
                }
            },
            {
                "type": "posts",
                "id": "2",
                "attributes":
                {
                    "headline": "Pragmatic Unicode",
                    "bodyText": "Here goes the body text",
                    "pubDate": None,
                    "modDate": None
                },
                "relationships":
                {
                    "blog": {
                        "data": {"type": "blogs", "id": "2"}
                    },
                    "authors": {
                        "meta": {"count": 1},
                        "data": [{"type": "authors", "id": "2"}]
                    }
                }
            },
        ]
    }

    class NoPagination(PageNumberPagination):
        page_size = None

    class NonPaginatedEntryViewSet(EntryViewSet):
        pagination_class = NoPagination

    request = rf.get(
        reverse("entry-list"))
    view = NonPaginatedEntryViewSet.as_view({'get': 'list'})
    response = view(request)
    response.render()

    content_dump = redump_json(response.content)
    expected_dump = dump_json(expected)

    assert content_dump == expected_dump
