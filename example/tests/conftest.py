import pytest
from pytest_factoryboy import register

from example.factories import BlogFactory, AuthorFactory, EntryFactory

register(BlogFactory)
register(AuthorFactory)
register(EntryFactory)


@pytest.fixture
def single_entry(blog, author, entry_factory):

    return entry_factory(blog=blog, authors=(author,))


@pytest.fixture
def multiple_entries(blog_factory, author_factory, entry_factory):

    return [
        entry_factory(blog=blog_factory(), authors=(author_factory(),)),
        entry_factory(blog=blog_factory(), authors=(author_factory(),)),
    ]

