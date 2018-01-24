import pytest
from django.urls import reverse

try:
    from unittest import mock
except ImportError:
    import mock

pytestmark = pytest.mark.django_db


@mock.patch(
    'rest_framework_json_api.utils'
    '.get_default_included_resources_from_serializer',
    new=lambda s: [])
def test_multiple_entries_no_pagination(multiple_entries, client):

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
                        "data": [{"type": "entries", "id": "2"}],
                        "links": {
                            "related": "http://testserver/entries/1/suggested/",
                            "self": "http://testserver/entries/1/relationships/suggested"
                        }
                    },
                    "tags": {
                        "data": []
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
                        "data": [{"type": "entries", "id": "1"}],
                        "links": {
                            "related": "http://testserver/entries/2/suggested/",
                            "self": "http://testserver/entries/2/relationships/suggested"
                        }
                    },
                    "tags": {
                        "data": []
                    }
                }
            },
        ]
    }

    response = client.get(reverse("nopage-entry-list"))

    assert expected == response.json()
