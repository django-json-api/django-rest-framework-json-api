# -*- encoding: utf-8 -*-

import factory
from faker import Factory as FakerFactory
from example import models


faker = FakerFactory.create()
faker.seed(983843)


class BlogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Blog

    name = factory.LazyAttribute(lambda x: faker.name())


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Author

    name = factory.LazyAttribute(lambda x: faker.name())
    email = factory.LazyAttribute(lambda x: faker.email())

    bio = factory.RelatedFactory('example.factories.AuthorBioFactory', 'author')

class AuthorBioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.AuthorBio

    author = factory.SubFactory(AuthorFactory)
    body = factory.LazyAttribute(lambda x: faker.text())


class EntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Entry

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
        model = models.Comment

    entry = factory.SubFactory(EntryFactory)
    body = factory.LazyAttribute(lambda x: faker.text())
    author = factory.SubFactory(AuthorFactory)


class ArtProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ArtProject

    topic = factory.LazyAttribute(lambda x: faker.catch_phrase())
    artist = factory.LazyAttribute(lambda x: faker.name())


class ResearchProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ResearchProject

    topic = factory.LazyAttribute(lambda x: faker.catch_phrase())
    supervisor = factory.LazyAttribute(lambda x: faker.name())


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Company

    name = factory.LazyAttribute(lambda x: faker.company())
    current_project = factory.SubFactory(ArtProjectFactory)

    @factory.post_generation
    def future_projects(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for project in extracted:
                self.future_projects.add(project)
