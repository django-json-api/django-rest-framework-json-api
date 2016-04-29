from django.core.urlresolvers import reverse
from django.conf import settings

import pytest

from example.views import EntryViewSet
from rest_framework_json_api.pagination import PageNumberPagination

from example.tests.utils import dump_json, redump_json

pytestmark = pytest.mark.django_db


# rf == request_factory
def test_multiple_entries_no_pagination(multiple_entries, rf):

    expected = {
        "data": [
            {
                "type": "posts",
                "id": "1",
                "attributes":
                {
                    "headline": multiple_entries[0].headline,
                    "bodyText": multiple_entries[0].body_text,
                    "pubDate": None,
                    "modDate": None
                },
                "meta": {
                    "bodyFormat": "text"
                },
                "relationships":
                {
                    "blog": {
                        "data": {"type": "blogs", "id": "1"}
                    },
                    "authors": {
                        "meta": {"count": 1},
                        "data": [{"type": "authors", "id": "1"}]
                    },
                    "comments": {
                        "meta": {"count": 1},
                        "data": [{"type": "comments", "id": "1"}]
                    },
                    "suggested": {
                        "data": [{"type": "entries", "id": "2"}]
                    }
                }
            },
            {
                "type": "posts",
                "id": "2",
                "attributes":
                {
                    "headline": multiple_entries[1].headline,
                    "bodyText": multiple_entries[1].body_text,
                    "pubDate": None,
                    "modDate": None
                },
                "meta": {
                    "bodyFormat": "text"
                },
                "relationships":
                {
                    "blog": {
                        "data": {"type": "blogs", "id": "2"}
                    },
                    "authors": {
                        "meta": {"count": 1},
                        "data": [{"type": "authors", "id": "2"}]
                    },
                    "comments": {
                        "meta": {"count": 1},
                        "data": [{"type": "comments", "id": "2"}]
                    },
                    "suggested": {
                        "data": [{"type": "entries", "id": "1"}]
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
