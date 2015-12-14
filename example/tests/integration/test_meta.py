from datetime import datetime
from django.core.urlresolvers import reverse

import pytest
from example.tests.utils import dump_json, redump_json

pytestmark = pytest.mark.django_db


def test_top_level_meta(blog, client):

    expected = {
        "data": {
            "type": "blogs",
            "id": "1",
            "attributes": {
                "name": blog.name
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
