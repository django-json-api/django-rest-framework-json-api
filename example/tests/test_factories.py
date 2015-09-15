import pytest

from example.models import Blog
from example.factories import BlogFactory

pytestmark = pytest.mark.django_db


def test_factory_instance(blog_factory):

    assert blog_factory == BlogFactory


def test_model_instance(blog):

    assert isinstance(blog, Blog)


def test_blog_name(blog):
    assert blog.name == 'Blog 1'


def test_multiple_blog(blog_factory):
    another_blog = blog_factory(name='Cool Blog')
    new_blog = blog_factory(name='Awesome Blog')

    assert another_blog.name == 'Cool Blog'
    assert new_blog.name == 'Awesome Blog'
