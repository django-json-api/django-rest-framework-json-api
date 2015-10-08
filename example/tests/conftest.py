import pytest
from pytest_factoryboy import register

from example.factories import BlogFactory, AuthorFactory, EntryFactory

register(BlogFactory)
register(AuthorFactory)
register(EntryFactory)


@pytest.fixture
def single_entry(author_factory, entry_factory):

    author = author_factory(name="Joel Spolsky")
    entry = entry_factory(
        headline=("The Absolute Minimum Every Software Developer"
                  "Absolutely, Positively Must Know About Unicode "
                  "and Character Sets (No Excuses!)"),
        blog__name='Joel on Software',
        authors=(author, )
    )


@pytest.fixture
def multiple_entries(single_entry, author_factory, entry_factory):

    author = author_factory(name="Ned Batchelder")
    entry = entry_factory(
        headline=("Pragmatic Unicode"),
        blog__name='Ned Batchelder Blog',
        authors=(author, )
    )
