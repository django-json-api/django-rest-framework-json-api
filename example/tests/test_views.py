from django.utils import timezone
from rest_framework.test import APITestCase

from rest_framework_json_api.utils import format_relation_name

from example.models import Blog, Entry
from example.views import EntryRelationshipView, BlogRelationshipView


class TestRelationshipView(APITestCase):

    def setUp(self):
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

    def test_get_entry_relationship_blog(self):
        response = self.client.get('/entries/{}/relationships/blog'.format(self.entry.id))
        expected_data = {'type': format_relation_name('Blog'), 'id': str(self.entry.blog.id)}

        assert response.data == expected_data

    def test_get_entry_relationship_invalid_field(self):
        response = self.client.get('/entries/{}/relationships/invalid_field'.format(self.entry.id))

        assert response.status_code == 404

    def test_get_blog_relationship_entry_set(self):
        response = self.client.get('/blogs/{}/relationships/entry_set'.format(self.blog.id))
