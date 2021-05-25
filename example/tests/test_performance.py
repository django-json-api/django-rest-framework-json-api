from datetime import date, timedelta
from random import randint

from django.utils import timezone
from rest_framework.test import APITestCase

from example.factories import CommentFactory, EntryFactory
from example.models import Author, Blog, Comment, Entry, LabResults, ResearchProject


class PerformanceTestCase(APITestCase):
    def setUp(self):
        self.author = Author.objects.create(
            name="Super powerful superhero", email="i.am@lost.com"
        )
        self.blog = Blog.objects.create(name="Some Blog", tagline="It's a blog")
        self.other_blog = Blog.objects.create(
            name="Other blog", tagline="It's another blog"
        )
        self.first_entry = Entry.objects.create(
            blog=self.blog,
            headline="headline one",
            body_text="body_text two",
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=3,
        )
        self.second_entry = Entry.objects.create(
            blog=self.blog,
            headline="headline two",
            body_text="body_text one",
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=1,
        )
        self.comment = Comment.objects.create(entry=self.first_entry)
        CommentFactory.create_batch(50)
        EntryFactory.create_batch(50)

    def test_query_count_no_includes(self):
        """We expect a simple list view to issue only two queries.

        1. The number of results in the set (e.g. a COUNT query),
           only necessary because we're using PageNumberPagination
        2. The SELECT query for the set
        """
        with self.assertNumQueries(2):
            response = self.client.get("/comments?page[size]=25")
            self.assertEqual(len(response.data["results"]), 25)

    def test_query_count_include_author(self):
        """We expect a list view with an include have five queries:

        1. Primary resource COUNT query
        2. Primary resource SELECT
        3. Authors prefetched
        4. Author types prefetched
        5. Entries prefetched
        """
        with self.assertNumQueries(5):
            response = self.client.get("/comments?include=author&page[size]=25")
            self.assertEqual(len(response.data["results"]), 25)

    def test_query_select_related_entry(self):
        """We expect a list view with an include have two queries:

        1. Primary resource COUNT query
        2. Primary resource SELECT + SELECT RELATED writer(author) and bio
        """
        with self.assertNumQueries(2):
            response = self.client.get("/comments?include=writer&page[size]=25")
            self.assertEqual(len(response.data["results"]), 25)

    def test_query_prefetch_uses_included_resources(self):
        """We expect a list view with `included_resources` to have three queries:

        1. Primary resource COUNT query
        2. Primary resource SELECT
        3. Comments prefetched
        """
        with self.assertNumQueries(3):
            response = self.client.get(
                "/entries?fields[entries]=comments&page[size]=25"
            )
            self.assertEqual(len(response.data["results"]), 25)

    def test_query_prefetch_read_only(self):
        """We expect a read only list view with an include have five queries:

        1. Primary resource COUNT query
        2. Primary resource SELECT
        3. Authors prefetched
        4. Author types prefetched
        5. Entries prefetched
        """
        project = ResearchProject.objects.create(
            topic="Mars Mission", supervisor="Elon Musk"
        )

        LabResults.objects.bulk_create(
            [
                LabResults(
                    research_project=project,
                    date=date.today() + timedelta(days=i),
                    measurements=randint(0, 10000),
                    author=self.author,
                )
                for i in range(20)
            ]
        )

        with self.assertNumQueries(5):
            response = self.client.get("/lab-results?include=author&page[size]=25")
            self.assertEqual(len(response.data["results"]), 20)
