import factory
from faker import Factory as FakerFactory

from example.models import (
    ArtProject,
    Author,
    AuthorBio,
    AuthorBioMetadata,
    AuthorType,
    Blog,
    Comment,
    Company,
    Entry,
    ProjectType,
    ResearchProject,
    TaggedItem,
)

faker = FakerFactory.create()
faker.seed(983843)


class BlogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Blog

    name = factory.LazyAttribute(lambda x: faker.name())


class AuthorTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuthorType

    name = factory.LazyAttribute(lambda x: faker.name())


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author

    name = factory.LazyAttribute(lambda x: faker.name())
    email = factory.LazyAttribute(lambda x: faker.email())

    bio = factory.RelatedFactory("example.factories.AuthorBioFactory", "author")
    author_type = factory.SubFactory(AuthorTypeFactory)


class AuthorBioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuthorBio

    author = factory.SubFactory(AuthorFactory)
    body = factory.LazyAttribute(lambda x: faker.text())

    metadata = factory.RelatedFactory(
        "example.factories.AuthorBioMetadataFactory", "bio"
    )


class AuthorBioMetadataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuthorBioMetadata

    bio = factory.SubFactory(AuthorBioFactory)
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


class TaggedItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaggedItem

    content_object = factory.SubFactory(EntryFactory)
    tag = factory.LazyAttribute(lambda x: faker.word())


class ProjectTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectType

    name = factory.LazyAttribute(lambda x: faker.name())


class ArtProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ArtProject

    topic = factory.LazyAttribute(lambda x: faker.catch_phrase())
    artist = factory.LazyAttribute(lambda x: faker.name())
    project_type = factory.SubFactory(ProjectTypeFactory)


class ResearchProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResearchProject

    topic = factory.LazyAttribute(lambda x: faker.catch_phrase())
    supervisor = factory.LazyAttribute(lambda x: faker.name())
    project_type = factory.SubFactory(ProjectTypeFactory)


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.LazyAttribute(lambda x: faker.company())
    current_project = factory.SubFactory(ArtProjectFactory)

    @factory.post_generation
    def future_projects(self, create, extracted, **kwargs):
        if not create:  # pragma: no cover
            return
        if extracted:
            for project in extracted:
                self.future_projects.add(project)
