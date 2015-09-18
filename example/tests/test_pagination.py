from django.core.urlresolvers import reverse

import pytest
from example.tests.utils import dump_json, redump_json

pytestmark = pytest.mark.django_db


@pytest.fixture
def single_entry(author_factory, entry_factory):

    author = author_factory(name="Joel Spolsky")
    entry = entry_factory(
        headline=("The Absolute Minimum Every Software Developer"
                  "Absolutely, Positively Must Know About Unicode "
                  "and Character Sets (No Excuses!)"),
        blog__name='Joel on Software',
        authors=(author, )
    )


def test_pagination_with_single_entry(single_entry, client):

    expected = {
        "data": [
            {
                "type": "posts",
                "id": "1",
                "attributes":
                {
                    "headline": "The Absolute Minimum Every Software DeveloperAbsolutely, Positively Must Know About Unicode and Character Sets (No Excuses!)",
                    "body-text": "Here goes the body text",
                    "pub-date": None,
                    "mod-date": None
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
    content_dump = redump_json(response.content)
    expected_dump = dump_json(expected)

    assert content_dump == expected_dump
