import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from example.factories import (
    AuthorBioFactory,
    AuthorBioMetadataFactory,
    AuthorFactory,
    AuthorTypeFactory,
    BlogFactory,
    CommentFactory,
    EntryFactory,
    QuestionnaireFactory,
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
register(QuestionnaireFactory)


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
def client():
    return APIClient()
