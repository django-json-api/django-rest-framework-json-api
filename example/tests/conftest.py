import pytest
from pytest_factoryboy import register

from example import factories

register(factories.BlogFactory)
register(factories.AuthorFactory)
register(factories.AuthorBioFactory)
register(factories.EntryFactory)
register(factories.CommentFactory)
register(factories.ArtProjectFactory)
register(factories.ResearchProjectFactory)
register(factories.CompanyFactory)


@pytest.fixture
def single_entry(blog, author, entry_factory, comment_factory):

    entry = entry_factory(blog=blog, authors=(author,))
    comment_factory(entry=entry)
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
def single_company(art_project_factory, research_project_factory, company_factory):
    company = company_factory(future_projects=(research_project_factory(), art_project_factory()))
    return company


@pytest.fixture
def single_art_project(art_project_factory):
    return art_project_factory()
