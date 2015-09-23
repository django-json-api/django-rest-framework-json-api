# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import factory

from example.models import Blog, Author, Entry


class BlogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Blog

    name = "Blog 1"


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author

    name = "Author 1"
    email = "author1@blog1.com"


class EntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Entry

    headline = "Headline 1"
    body_text = "Here goes the body text"

    blog = factory.SubFactory(BlogFactory)

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        if extracted:
            if isinstance(extracted, (list, tuple)):
                for author in extracted:
                    self.authors.add(author)
            else:
                self.authors.add(extracted)
