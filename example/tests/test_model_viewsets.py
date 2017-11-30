import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import encoding

from example.tests import TestBase
from example.tests.utils import dump_json, load_json


class ModelViewSetTests(TestBase):
    """
    Test usage with ModelViewSets, also tests pluralization, camelization,
    and underscore.

    [<RegexURLPattern user-list ^identities/$>,
    <RegexURLPattern user-detail ^identities/(?P<pk>[^/]+)/$>]
    """
    list_url = reverse('user-list')

    def setUp(self):
        super(ModelViewSetTests, self).setUp()
        self.detail_url = reverse('user-detail', kwargs={'pk': self.miles.pk})

        setattr(settings, 'JSON_API_FORMAT_KEYS', 'dasherize')

    def tearDown(self):

        setattr(settings, 'JSON_API_FORMAT_KEYS', 'camelize')

    def test_key_in_list_result(self):
        """
        Ensure the result has a 'user' key since that is the name of the model
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[0]
        expected = {
            'data': [
                {
                    'type': 'users',
                    'id': encoding.force_text(user.pk),
                    'attributes': {
                        'first-name': user.first_name,
                        'last-name': user.last_name,
                        'email': user.email
                    },
                }
            ],
            'links': {
                'first': 'http://testserver/identities?page=1',
                'last': 'http://testserver/identities?page=2',
                'next': 'http://testserver/identities?page=2',
                'prev': None
            },
            'meta': {
                'pagination': {
                    'page': 1,
                    'pages': 2,
                    'count': 2
                }
            }
        }

        parsed_content = load_json(response.content)

        assert expected == parsed_content

    def test_page_two_in_list_result(self):
        """
        Ensure that the second page is reachable and is the correct data.
        """
        response = self.client.get(self.list_url, {'page': 2})
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[1]
        expected = {
            'data': [
                {
                    'type': 'users',
                    'id': encoding.force_text(user.pk),
                    'attributes': {
                        'first-name': user.first_name,
                        'last-name': user.last_name,
                        'email': user.email
                    },
                }
            ],
            'links': {
                'first': 'http://testserver/identities?page=1',
                'last': 'http://testserver/identities?page=2',
                'next': None,
                'prev': 'http://testserver/identities?page=1',
            },
            'meta': {
                'pagination': {
                    'page': 2,
                    'pages': 2,
                    'count': 2
                }
            }
        }

        parsed_content = load_json(response.content)

        assert expected == parsed_content

    def test_page_range_in_list_result(self):
        """
        Ensure that the range of a page can be changed from the client,
        tests pluralization as two objects means it converts ``user`` to
        ``users``.
        """
        response = self.client.get(self.list_url, {'page_size': 2})
        self.assertEqual(response.status_code, 200)

        users = get_user_model().objects.all()
        expected = {
            'data': [
                {
                    'type': 'users',
                    'id': encoding.force_text(users[0].pk),
                    'attributes': {
                        'first-name': users[0].first_name,
                        'last-name': users[0].last_name,
                        'email': users[0].email
                    },
                },
                {
                    'type': 'users',
                    'id': encoding.force_text(users[1].pk),
                    'attributes': {
                        'first-name': users[1].first_name,
                        'last-name': users[1].last_name,
                        'email': users[1].email
                    },
                }
            ],
            'links': {
                'first': 'http://testserver/identities?page=1&page_size=2',
                'last': 'http://testserver/identities?page=1&page_size=2',
                'next': None,
                'prev': None
            },
            'meta': {
                'pagination': {
                    'page': 1,
                    'pages': 1,
                    'count': 2
                }
            }
        }

        parsed_content = load_json(response.content)

        assert expected == parsed_content

    def test_key_in_detail_result(self):
        """
        Ensure the result has a 'user' key.
        """
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'data': {
                'type': 'users',
                'id': encoding.force_text(self.miles.pk),
                'attributes': {
                    'first-name': self.miles.first_name,
                    'last-name': self.miles.last_name,
                    'email': self.miles.email
                },
            }
        }

        parsed_content = load_json(response.content)

        assert expected == parsed_content

    def test_patch_requires_id(self):
        """
        Verify that 'id' is required to be passed in an update request.
        """
        data = {
            'data': {
                'type': 'users',
                'attributes': {
                    'first-name': 'DifferentName'
                }
            }
        }

        response = self.client.patch(self.detail_url,
                                     content_type='application/vnd.api+json',
                                     data=dump_json(data))

        self.assertEqual(response.status_code, 400)

    def test_key_in_post(self):
        """
        Ensure a key is in the post.
        """
        self.client.login(username='miles', password='pw')
        data = {
            'data': {
                'type': 'users',
                'id': encoding.force_text(self.miles.pk),
                'attributes': {
                    'first-name': self.miles.first_name,
                    'last-name': self.miles.last_name,
                    'email': 'miles@trumpet.org'
                },
            }
        }

        response = self.client.put(self.detail_url,
                                   content_type='application/vnd.api+json',
                                   data=dump_json(data))

        parsed_content = load_json(response.content)

        assert data == parsed_content

        # is it updated?
        self.assertEqual(
            get_user_model().objects.get(pk=self.miles.pk).email,
            'miles@trumpet.org')


@pytest.mark.django_db
def test_patch_allow_field_type(author, author_type_factory, client):
    """
    Verify that type field may be updated.
    """
    author_type = author_type_factory()
    url = reverse('author-detail', args=[author.id])

    data = {
        'data': {
            'id': author.id,
            'type': 'authors',
            'relationships': {
                'data': {
                    'id': author_type.id,
                    'type': 'author-type'
                }
            }
        }
    }

    response = client.patch(url,
                            content_type='application/vnd.api+json',
                            data=dump_json(data))

    assert response.status_code == 200
