import pytest
from django.core.urlresolvers import reverse

from example.tests.utils import load_json

try:
    from unittest import mock
except ImportError:
    import mock


pytestmark = pytest.mark.django_db


@mock.patch(
    'rest_framework_json_api.utils'
    '.get_default_included_resources_from_serializer',
    new=lambda s: [])
def test_pagination_with_single_entry(single_entry, client):

    expected = {
        "data": [
            {
                "type": "posts",
                "id": "1",
                "attributes":
                {
                    "headline": single_entry.headline,
                    "bodyText": single_entry.body_text,
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
                        "data": [],
                        "links": {
                            "related": "http://testserver/entries/1/suggested/",
                            "self": "http://testserver/entries/1/relationships/suggested"
                        }
                    },
                    "tags": {
                        "data": [
                            {
                                "id": "1",
                                "type": "taggedItems"
                            }
                        ]
                    }
                }
            }],
        "links": {
            "first": "http://testserver/entries?page=1",
            "last": "http://testserver/entries?page=1",
            "next": None,
            "prev": None,
        },
        "meta":
        {
            "pagination":
            {
                "page": 1,
                "pages": 1,
                "count": 1
            }
        }
    }

    response = client.get(reverse("entry-list"))
    parsed_content = load_json(response.content)

    assert expected == parsed_content
