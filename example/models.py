# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


class BaseModel(models.Model):
    """
    I hear RoR has this by default, who doesn't need these two fields!
    """
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class Blog(BaseModel):
    name = models.CharField(max_length=100)
    tagline = models.TextField()

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Author(BaseModel):
    name = models.CharField(max_length=50)
    email = models.EmailField()

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class AuthorBio(BaseModel):
    author = models.OneToOneField(Author, related_name='bio')
    body = models.TextField()

    def __str__(self):
        return self.author.name


@python_2_unicode_compatible
class Entry(BaseModel):
    blog = models.ForeignKey(Blog)
    headline = models.CharField(max_length=255)
    body_text = models.TextField(null=True)
    pub_date = models.DateField(null=True)
    mod_date = models.DateField(null=True)
    authors = models.ManyToManyField(Author)
    n_comments = models.IntegerField(default=0)
    n_pingbacks = models.IntegerField(default=0)
    rating = models.IntegerField(default=0)

    def __str__(self):
        return self.headline


@python_2_unicode_compatible
class Comment(BaseModel):
    entry = models.ForeignKey(Entry)
    body = models.TextField()
    author = models.ForeignKey(
        Author,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.body

