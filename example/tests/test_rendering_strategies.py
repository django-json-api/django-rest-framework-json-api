from __future__ import absolute_import

from django.utils import timezone
from rest_framework.reverse import reverse

from . import TestBase
from example.models import Author, Blog, Comment, Entry
from django.test import override_settings


class TestResourceRelatedField(TestBase):
    list_url = reverse('authors-nested-list')

    def setUp(self):
        super(TestResourceRelatedField, self).setUp()
        self.blog = Blog.objects.create(name='Some Blog', tagline="It's a blog")
        self.entry = Entry.objects.create(
            blog=self.blog,
            headline='headline',
            body_text='body_text',
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=3
        )
        for i in range(1, 6):
            name = 'some_author{}'.format(i)
            self.entry.authors.add(
                Author.objects.create(name=name, email='{}@example.org'.format(name))
            )

        self.comment = Comment.objects.create(
            entry=self.entry,
            body='testing one two three',
            author=Author.objects.first()
        )

    def test_attribute_rendering_strategy(self):
        with override_settings(JSON_API_NESTED_SERIALIZERS_RENDERING_STRATEGY='ATTRIBUTE'):
            response = self.client.get(self.list_url)

        expected = {
            "links": {
                "first": "http://testserver/authors-nested?page%5Bnumber%5D=1",
                "last": "http://testserver/authors-nested?page%5Bnumber%5D=5",
                "next": "http://testserver/authors-nested?page%5Bnumber%5D=2",
                "prev": None
            },
            "data": [
                {
                    "type": "authors",
                    "id": "1",
                    "attributes": {
                        "name": "some_author1",
                        "email": "some_author1@example.org",
                        "comments": [
                            {
                                "id": 1,
                                "entry": {
                                    "tags": [],
                                    "url": "http://testserver/drf-blogs/1"
                                },
                                "body": "testing one two three"
                            }
                        ]
                    }
                }
            ],
            "meta": {
                "pagination": {
                    "page": 1,
                    "pages": 5,
                    "count": 5
                }
            }
        }
        assert expected == response.json()
