from datetime import datetime

import pytest
from django.core.urlresolvers import reverse

from example.tests.utils import load_json

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
            "relationships": {
                "tags": {
                    "data": []
                }
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
    parsed_content = load_json(response.content)

    assert expected == parsed_content


def test_top_level_meta_for_detail_view(blog, client):

    expected = {
        "data": {
            "type": "blogs",
            "id": "1",
            "attributes": {
                "name": blog.name
            },
            "relationships": {
                "tags": {
                    "data": []
                }
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
    parsed_content = load_json(response.content)

    assert expected == parsed_content
