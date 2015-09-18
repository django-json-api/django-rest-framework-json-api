import pytest
from pytest_factoryboy import register

from example.factories import BlogFactory, AuthorFactory, EntryFactory

register(BlogFactory)
register(AuthorFactory)
register(EntryFactory)
