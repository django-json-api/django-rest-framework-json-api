import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from example.factories import (
    ArtProjectFactory,
    AuthorBioFactory,
    AuthorBioMetadataFactory,
    AuthorFactory,
    AuthorTypeFactory,
    BlogFactory,
    CommentFactory,
    CompanyFactory,
    EntryFactory,
    ResearchProjectFactory,
    TaggedItemFactory,
)

register(BlogFactory)
register(AuthorFactory)
register(AuthorBioFactory)
register(AuthorBioMetadataFactory)
register(AuthorTypeFactory)
register(EntryFactory)
register(CommentFactory)
register(TaggedItemFactory)
register(ArtProjectFactory)
register(ResearchProjectFactory)
register(CompanyFactory)


@pytest.fixture
def single_entry(blog, author, entry_factory, comment_factory, tagged_item_factory):

    entry = entry_factory(blog=blog, authors=(author,))
    comment_factory(entry=entry)
    tagged_item_factory(content_object=entry)
    return entry


@pytest.fixture
def multiple_entries(blog_factory, author_factory, entry_factory, comment_factory):

    entries = [
        entry_factory(blog=blog_factory(), authors=(author_factory(),)),
        entry_factory(blog=blog_factory(), authors=(author_factory(),)),
    ]
    comment_factory(entry=entries[0])
    comment_factory(entry=entries[1])
    return entries


@pytest.fixture
def single_comment(blog, author, entry_factory, comment_factory):
    entry = entry_factory(blog=blog, authors=(author,))
    comment_factory(entry=entry)
    return comment_factory(entry=entry)


@pytest.fixture
def single_company(art_project_factory, research_project_factory, company_factory):
    company = company_factory(
        future_projects=(research_project_factory(), art_project_factory())
    )
    return company


@pytest.fixture
def single_art_project(art_project_factory):
    return art_project_factory()


@pytest.fixture
def client():
    return APIClient()
