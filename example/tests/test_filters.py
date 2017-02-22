from django.core.urlresolvers import reverse

from rest_framework.settings import api_settings

import pytest

from example.tests.utils import dump_json, redump_json

pytestmark = pytest.mark.django_db


class TestJsonApiFilter(object):

    def test_request_without_filter(self, client, comment_factory):
        comment = comment_factory()
        comment2 = comment_factory()

        expected = {
            "links": {
                "first": "http://testserver/comments?page=1",
                "last": "http://testserver/comments?page=2",
                "next": "http://testserver/comments?page=2",
                "prev": None
            },
            "data": [
                {
                    "type": "comments",
                    "id": str(comment.pk),
                    "attributes": {
                        "body": comment.body
                    },
                    "relationships": {
                        "entry": {
                            "data": {
                                "type": "entries",
                                "id": str(comment.entry.pk)
                            }
                        },
                        "author": {
                            "data": {
                                "type": "authors",
                                "id": str(comment.author.pk)
                            }
                        },
                    }
                }
            ],
            "meta": {
                "pagination": {
                    "page": 1,
                    "pages": 2,
                    "count": 2
                }
            }
        }

        response = client.get('/comments')
        # assert 0

        assert response.status_code == 200
        actual = redump_json(response.content)
        expected_json = dump_json(expected)
        assert actual == expected_json

    def test_request_with_filter(self, client, comment_factory):
        comment = comment_factory(body='Body for comment 1')
        comment2 = comment_factory()

        expected = {
            "links": {
                "first": "http://testserver/comments?filter%5Bbody%5D=Body+for+comment+1&page=1",
                "last": "http://testserver/comments?filter%5Bbody%5D=Body+for+comment+1&page=1",
                "next": None,
                "prev": None
            },
            "data": [
                {
                    "type": "comments",
                    "id": str(comment.pk),
                    "attributes": {
                        "body": comment.body
                    },
                    "relationships": {
                        "entry": {
                            "data": {
                                "type": "entries",
                                "id": str(comment.entry.pk)
                            }
                        },
                        "author": {
                            "data": {
                                "type": "authors",
                                "id": str(comment.author.pk)
                            }
                        },
                    }
                }
            ],
            "meta": {
                "pagination": {
                    "page": 1,
                    "pages": 1,
                    "count": 1
                }
            }
        }

        response = client.get('/comments?filter[body]=Body for comment 1')

        assert response.status_code == 200
        actual = redump_json(response.content)
        expected_json = dump_json(expected)
        assert actual == expected_json

    def test_failed_request_with_filter(self, client, comment_factory):
        comment = comment_factory(body='Body for comment 1')
        comment2 = comment_factory()

        expected = {
            "links": {
                "first": "http://testserver/comments?filter%5Bbody%5D=random+comment&page=1",
                "last": "http://testserver/comments?filter%5Bbody%5D=random+comment&page=1",
                "next": None,
                "prev": None
            },
            "data": [],
            "meta": {
                "pagination": {
                    "page": 1,
                    "pages": 1,
                    "count": 0
                }
            }
        }

        response = client.get('/comments?filter[body]=random comment')
        assert response.status_code == 200
        actual = redump_json(response.content)
        expected_json = dump_json(expected)
        assert actual == expected_json
