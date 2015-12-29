import json

from django.utils import timezone
from rest_framework.reverse import reverse

from rest_framework.test import APITestCase

from rest_framework_json_api.utils import format_relation_name
from example.models import Blog, Entry, Comment, Author


class TestRelationshipView(APITestCase):
    def setUp(self):
        self.author = Author.objects.create(name='Super powerful superhero', email='i.am@lost.com')
        self.blog = Blog.objects.create(name='Some Blog', tagline="It's a blog")
        self.other_blog = Blog.objects.create(name='Other blog', tagline="It's another blog")
        self.first_entry = Entry.objects.create(
            blog=self.blog,
            headline='headline one',
            body_text='body_text two',
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=3
        )
        self.second_entry = Entry.objects.create(
            blog=self.blog,
            headline='headline two',
            body_text='body_text one',
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=1
        )
        self.first_comment = Comment.objects.create(entry=self.first_entry, body="This entry is cool", author=None)
        self.second_comment = Comment.objects.create(
            entry=self.second_entry,
            body="This entry is not cool",
            author=self.author
        )

    def test_get_entry_relationship_blog(self):
        url = reverse('entry-relationships', kwargs={'pk': self.first_entry.id, 'related_field': 'blog'})
        response = self.client.get(url)
        expected_data = {'type': format_relation_name('Blog'), 'id': str(self.first_entry.blog.id)}

        assert response.data == expected_data

    def test_get_entry_relationship_invalid_field(self):
        response = self.client.get('/entries/{}/relationships/invalid_field'.format(self.first_entry.id))

        assert response.status_code == 404

    def test_get_blog_relationship_entry_set(self):
        response = self.client.get('/blogs/{}/relationships/entry_set'.format(self.blog.id))
        expected_data = [{'type': format_relation_name('Entry'), 'id': str(self.first_entry.id)},
                         {'type': format_relation_name('Entry'), 'id': str(self.second_entry.id)}]

        assert response.data == expected_data

    def test_put_entry_relationship_blog_returns_405(self):
        url = '/entries/{}/relationships/blog'.format(self.first_entry.id)
        response = self.client.put(url, data={})
        assert response.status_code == 405

    def test_patch_invalid_entry_relationship_blog_returns_400(self):
        url = '/entries/{}/relationships/blog'.format(self.first_entry.id)
        response = self.client.patch(url,
                                     data=json.dumps({'data': {'invalid': ''}}),
                                     content_type='application/vnd.api+json')
        assert response.status_code == 400

    def test_get_empty_to_one_relationship(self):
        url = '/comments/{}/relationships/author'.format(self.first_entry.id)
        response = self.client.get(url)
        expected_data = None

        assert response.data == expected_data

    def test_get_to_many_relationship_self_link(self):
        url = '/authors/{}/relationships/comment_set'.format(self.author.id)

        response = self.client.get(url)
        expected_data = {
            'links': {'self': 'http://testserver/authors/1/relationships/comment_set'},
            'data': [{'id': str(self.second_comment.id), 'type': format_relation_name('Comment')}]
        }
        assert json.loads(response.content.decode('utf-8')) == expected_data

    def test_patch_to_one_relationship(self):
        url = '/entries/{}/relationships/blog'.format(self.first_entry.id)
        request_data = {
            'data': {'type': format_relation_name('Blog'), 'id': str(self.other_blog.id)}
        }
        response = self.client.patch(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 200, response.content.decode()

        response = self.client.get(url)
        assert response.data == request_data['data']

    def test_patch_to_many_relationship(self):
        url = '/blogs/{}/relationships/entry_set'.format(self.first_entry.id)
        request_data = {
            'data': [{'type': format_relation_name('Entry'), 'id': str(self.first_entry.id)}, ]
        }
        response = self.client.patch(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 200, response.content.decode()

        response = self.client.get(url)
        assert response.data == request_data['data']

    def test_post_to_one_relationship_should_fail(self):
        url = '/entries/{}/relationships/blog'.format(self.first_entry.id)
        request_data = {
            'data': {'type': format_relation_name('Blog'), 'id': str(self.other_blog.id)}
        }
        response = self.client.post(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 405, response.content.decode()

    def test_post_to_many_relationship_with_no_change(self):
        url = '/entries/{}/relationships/comment_set'.format(self.first_entry.id)
        request_data = {
            'data': [{'type': format_relation_name('Comment'), 'id': str(self.first_comment.id)}, ]
        }
        response = self.client.post(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 204, response.content.decode()

    def test_post_to_many_relationship_with_change(self):
        url = '/entries/{}/relationships/comment_set'.format(self.first_entry.id)
        request_data = {
            'data': [{'type': format_relation_name('Comment'), 'id': str(self.second_comment.id)}, ]
        }
        response = self.client.post(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 200, response.content.decode()

        assert request_data['data'][0] in response.data

    def test_delete_to_one_relationship_should_fail(self):
        url = '/entries/{}/relationships/blog'.format(self.first_entry.id)
        request_data = {
            'data': {'type': format_relation_name('Blog'), 'id': str(self.other_blog.id)}
        }
        response = self.client.delete(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 405, response.content.decode()

    def test_delete_relationship_overriding_with_none(self):
        url = '/comments/{}'.format(self.second_comment.id)
        request_data = {
            'data': {
                'type': 'comments',
                'relationships': {
                    'author': {
                        'data': None
                    }
                }
            }
        }
        response = self.client.patch(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 200, response.content.decode()
        assert response.data['author'] == None

    def test_delete_to_many_relationship_with_no_change(self):
        url = '/entries/{}/relationships/comment_set'.format(self.first_entry.id)
        request_data = {
            'data': [{'type': format_relation_name('Comment'), 'id': str(self.second_comment.id)}, ]
        }
        response = self.client.delete(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 204, response.content.decode()

    def test_delete_one_to_many_relationship_with_not_null_constraint(self):
        url = '/entries/{}/relationships/comment_set'.format(self.first_entry.id)
        request_data = {
            'data': [{'type': format_relation_name('Comment'), 'id': str(self.first_comment.id)}, ]
        }
        response = self.client.delete(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 409, response.content.decode()

    def test_delete_to_many_relationship_with_change(self):
        url = '/authors/{}/relationships/comment_set'.format(self.author.id)
        request_data = {
            'data': [{'type': format_relation_name('Comment'), 'id': str(self.second_comment.id)}, ]
        }
        response = self.client.delete(url, data=json.dumps(request_data), content_type='application/vnd.api+json')
        assert response.status_code == 200, response.content.decode()
