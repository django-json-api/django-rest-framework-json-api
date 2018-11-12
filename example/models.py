# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import uuid

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
    type = models.ForeignKey(AuthorType, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)


@python_2_unicode_compatible
class AuthorBio(BaseModel):
    author = models.OneToOneField(Author, related_name='bio', on_delete=models.CASCADE)
    body = models.TextField()

    def __str__(self):
        return self.author.name

    class Meta:
        ordering = ('id',)


@python_2_unicode_compatible
class Entry(BaseModel):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
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
    entry = models.ForeignKey(Entry, related_name='comments', on_delete=models.CASCADE)
    body = models.TextField()
    author = models.ForeignKey(
        Author,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.body

    class Meta:
        ordering = ('id',)


@python_2_unicode_compatible
class ProjectType(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)


class Project(PolymorphicModel):
    topic = models.CharField(max_length=30)
    project_type = models.ForeignKey(ProjectType, null=True, on_delete=models.CASCADE)


class ArtProject(Project):
    artist = models.CharField(max_length=30)


class ResearchProject(Project):
    supervisor = models.CharField(max_length=30)


@python_2_unicode_compatible
class Company(models.Model):
    name = models.CharField(max_length=100)
    current_project = models.ForeignKey(
        Project, related_name='companies', on_delete=models.CASCADE)
    future_projects = models.ManyToManyField(Project)

    def __str__(self):
        return self.name


# the following serializers are to reproduce/confirm fix for this bug:
# https://github.com/django-json-api/django-rest-framework-json-api/issues/489
class CommonModel(models.Model):
    """
    Abstract model with common fields for all "real" Models:
    - id: globally unique UUID version 4
    - effective dates
    - last modified dates
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    effective_start_date = models.DateField(default=None, blank=True, null=True)
    effective_end_date = models.DateField(default=None, blank=True, null=True)
    last_mod_user_name = models.CharField(max_length=80)
    last_mod_date = models.DateField(auto_now=True)

    class Meta:
        abstract = True


class Course(CommonModel):
    """
    A course of instruction. e.g. COMSW1002 Computing in Context
    """
    school_bulletin_prefix_code = models.CharField(max_length=10)
    suffix_two = models.CharField(max_length=2)
    subject_area_code = models.CharField(max_length=10)
    course_number = models.CharField(max_length=10)
    course_identifier = models.CharField(max_length=10, unique=True)
    course_name = models.CharField(max_length=80)
    course_description = models.TextField()

    class Meta:
        # verbose_name = "Course"
        # verbose_name_plural = "Courses"
        ordering = ["course_number"]


class Term(CommonModel):
    """
    A specific course term (year+semester) instance.
    e.g. 20183COMSW1002
    """
    term_identifier = models.TextField(max_length=10)
    audit_permitted_code = models.PositiveIntegerField(blank=True, default=0)
    exam_credit_flag = models.BooleanField(default=True)
    course = models.ForeignKey('example.Course', related_name='terms',
                               on_delete=models.CASCADE, null=True,
                               default=None)

    class Meta:
        ordering = ["term_identifier"]
