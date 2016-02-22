# -*- encoding: utf-8 -*-

import factory
from faker import Factory as FakerFactory
from example.models import Blog, Author, AuthorBio, Entry, Comment

faker = FakerFactory.create()
faker.seed(983843)

class BlogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Blog

    name = factory.LazyAttribute(lambda x: faker.name())


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author

    name = factory.LazyAttribute(lambda x: faker.name())
    email = factory.LazyAttribute(lambda x: faker.email())

    bio = factory.RelatedFactory('example.factories.AuthorBioFactory', 'author')

class AuthorBioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuthorBio

    author = factory.SubFactory(AuthorFactory)
    body = factory.LazyAttribute(lambda x: faker.text())


class EntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Entry

    headline = factory.LazyAttribute(lambda x: faker.sentence(nb_words=4))
    body_text = factory.LazyAttribute(lambda x: faker.text())

    blog = factory.SubFactory(BlogFactory)

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        if extracted:
            if isinstance(extracted, (list, tuple)):
                for author in extracted:
                    self.authors.add(author)
            else:
                self.authors.add(extracted)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    entry = factory.SubFactory(EntryFactory)
    body = factory.LazyAttribute(lambda x: faker.text())
    author = factory.SubFactory(AuthorFactory)

