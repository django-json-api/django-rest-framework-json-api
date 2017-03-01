import pytest
from pytest_factoryboy import register

from example.factories import BlogFactory, AuthorFactory, AuthorBioFactory, EntryFactory, CommentFactory, \
    TaggedItemFactory

register(BlogFactory)
register(AuthorFactory)
register(AuthorBioFactory)
register(EntryFactory)
register(CommentFactory)
register(TaggedItemFactory)


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

