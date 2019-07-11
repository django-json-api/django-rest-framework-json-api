from unittest import mock

import pytest
from django.urls import reverse

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
                    "blogHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/1/blog",
                            "self": "http://testserver/entries/1/relationships/blog_hyperlinked"
                        }
                    },
                    "authors": {
                        "meta": {"count": 1},
                        "data": [{"type": "authors", "id": "1"}]
                    },
                    "comments": {
                        "meta": {"count": 1},
                        "data": [{"type": "comments", "id": "1"}]
                    },
                    "commentsHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/1/comments",
                            "self": "http://testserver/entries/1/relationships/comments_hyperlinked"
                        }
                    },
                    "suggested": {
                        "data": [{"type": "entries", "id": "2"}],
                        "links": {
                            "related": "http://testserver/entries/1/suggested/",
                            "self": "http://testserver/entries/1/relationships/suggested"
                        }
                    },
                    "suggestedHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/1/suggested/",
                            "self": "http://testserver/entries/1"
                                    "/relationships/suggested_hyperlinked"
                        }
                    },
                    "featuredHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/1/featured",
                            "self": "http://testserver/entries/1/relationships/featured_hyperlinked"
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
                    "blogHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/2/blog",
                            "self": "http://testserver/entries/2/relationships/blog_hyperlinked",
                        }
                    },
                    "authors": {
                        "meta": {"count": 1},
                        "data": [{"type": "authors", "id": "2"}]
                    },
                    "comments": {
                        "meta": {"count": 1},
                        "data": [{"type": "comments", "id": "2"}]
                    },
                    "commentsHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/2/comments",
                            "self": "http://testserver/entries/2/relationships/comments_hyperlinked"
                        }
                    },
                    "suggested": {
                        "data": [{"type": "entries", "id": "1"}],
                        "links": {
                            "related": "http://testserver/entries/2/suggested/",
                            "self": "http://testserver/entries/2/relationships/suggested"
                        }
                    },
                    "suggestedHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/2/suggested/",
                            "self": "http://testserver/entries/2"
                                    "/relationships/suggested_hyperlinked"
                        }
                    },
                    "featuredHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/2/featured",
                            "self": "http://testserver/entries/2/relationships/featured_hyperlinked"
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
