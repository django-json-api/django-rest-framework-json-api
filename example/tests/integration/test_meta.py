from datetime import datetime
from django.core.urlresolvers import reverse

import pytest
from example.tests.utils import dump_json, redump_json

pytestmark = pytest.mark.django_db


def test_top_level_meta_for_list_view(blog, client):

    expected = {
        "data": [{
            "type": "blogs",
            "id": "1",
            "attributes": {
                "name": blog.name
            },
            "links": {
                "self": 'http://testserver/blogs/1'
            },
            "meta": {
                "copyright": datetime.now().year
            },
        }],
        'links': {
            'first': 'http://testserver/blogs?page=1',
            'last': 'http://testserver/blogs?page=1',
            'next': None,
            'prev': None
        },
        'meta': {
            'pagination': {'count': 1, 'page': 1, 'pages': 1},
            'apiDocs': '/docs/api/blogs'
        }
    }

    response = client.get(reverse("blog-list"))
    content_dump = redump_json(response.content)
    expected_dump = dump_json(expected)

    assert content_dump == expected_dump


def test_top_level_meta_for_detail_view(blog, client):

    expected = {
        "data": {
            "type": "blogs",
            "id": "1",
            "attributes": {
                "name": blog.name
            },
            "links": {
                "self": "http://testserver/blogs/1"
            },
            "meta": {
                "copyright": datetime.now().year
            },
        },
        "meta": {
            "apiDocs": "/docs/api/blogs"
        },
    }

    response = client.get(reverse("blog-detail", kwargs={'pk': blog.pk}))
    content_dump = redump_json(response.content)
    expected_dump = dump_json(expected)

    assert content_dump == expected_dump
