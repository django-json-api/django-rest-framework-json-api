# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from polymorphic.models import PolymorphicModel


class BaseModel(models.Model):
    """
    I hear RoR has this by default, who doesn't need these two fields!
    """
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TaggedItem(BaseModel):
    tag = models.SlugField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.tag

    class Meta:
        ordering = ('id',)


@python_2_unicode_compatible
class Blog(BaseModel):
    name = models.CharField(max_length=100)
    tagline = models.TextField()
    tags = GenericRelation(TaggedItem)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)


@python_2_unicode_compatible
class AuthorType(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)


@python_2_unicode_compatible
class Author(BaseModel):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    type = models.ForeignKey(AuthorType, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)


@python_2_unicode_compatible
class AuthorBio(BaseModel):
    author = models.OneToOneField(Author, related_name='bio')
    body = models.TextField()

    def __str__(self):
        return self.author.name

    class Meta:
        ordering = ('id',)


@python_2_unicode_compatible
class Entry(BaseModel):
    blog = models.ForeignKey(Blog)
    headline = models.CharField(max_length=255)
    body_text = models.TextField(null=True)
    pub_date = models.DateField(null=True)
    mod_date = models.DateField(null=True)
    authors = models.ManyToManyField(Author, related_name='entries')
    n_comments = models.IntegerField(default=0)
    n_pingbacks = models.IntegerField(default=0)
    rating = models.IntegerField(default=0)
    tags = GenericRelation(TaggedItem)

    def __str__(self):
        return self.headline

    class Meta:
        ordering = ('id',)


@python_2_unicode_compatible
class Comment(BaseModel):
    entry = models.ForeignKey(Entry, related_name='comments')
    body = models.TextField()
    author = models.ForeignKey(
        Author,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.body

    class Meta:
        ordering = ('id',)


class Project(PolymorphicModel):
    topic = models.CharField(max_length=30)


class ArtProject(Project):
    artist = models.CharField(max_length=30)


class ResearchProject(Project):
    supervisor = models.CharField(max_length=30)


@python_2_unicode_compatible
class Company(models.Model):
    name = models.CharField(max_length=100)
    current_project = models.ForeignKey(Project, related_name='companies')
    future_projects = models.ManyToManyField(Project)

    def __str__(self):
        return self.name
