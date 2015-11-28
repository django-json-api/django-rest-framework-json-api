import json
from django.core.urlresolvers import reverse

import pytest
from example.tests.utils import dump_json, redump_json

pytestmark = pytest.mark.django_db


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
                "relationships":
                {
                    'allComments': {
                        'meta': {'count': 1},
                        'data': [{'id': '1','type': 'comments'}]
                    },
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
    content = json.loads(response.content.decode('utf-8'))

    assert content == expected
