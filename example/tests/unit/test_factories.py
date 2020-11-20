import pytest

from example.factories import BlogFactory
from example.models import Blog

pytestmark = pytest.mark.django_db


def test_factory_instance(blog_factory):

    assert blog_factory == BlogFactory


def test_model_instance(blog):

    assert isinstance(blog, Blog)


def test_multiple_blog(blog_factory):
    another_blog = blog_factory(name="Cool Blog")
    new_blog = blog_factory(name="Awesome Blog")

    assert another_blog.name == "Cool Blog"
    assert new_blog.name == "Awesome Blog"


def test_factories_with_relations(author_factory, entry_factory):

    author = author_factory(name="Joel Spolsky")
    entry = entry_factory(
        headline=(
            "The Absolute Minimum Every Software Developer"
            "Absolutely, Positively Must Know About Unicode "
            "and Character Sets (No Excuses!)"
        ),
        blog__name="Joel on Software",
        authors=(author,),
    )

    assert entry.blog.name == "Joel on Software"
    assert entry.headline == (
        "The Absolute Minimum Every Software Developer"
        "Absolutely, Positively Must Know About Unicode "
        "and Character Sets (No Excuses!)"
    )
    assert entry.authors.all().count() == 1
    assert entry.authors.all()[0].name == "Joel Spolsky"
