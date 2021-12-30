from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
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
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.tag

    class Meta:
        ordering = ("id",)


class Blog(BaseModel):
    name = models.CharField(max_length=100)
    tagline = models.TextField()
    tags = GenericRelation(TaggedItem)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("id",)


class AuthorType(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("id",)


class Author(BaseModel):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    author_type = models.ForeignKey(AuthorType, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("id",)


class AuthorBio(BaseModel):
    author = models.OneToOneField(Author, related_name="bio", on_delete=models.CASCADE)
    body = models.TextField()

    def __str__(self):
        return self.author.name

    class Meta:
        ordering = ("id",)


class AuthorBioMetadata(BaseModel):
    """
    Just a class to have a relation with author bio
    """

    bio = models.OneToOneField(
        AuthorBio, related_name="metadata", on_delete=models.CASCADE
    )
    body = models.TextField()

    def __str__(self):
        return self.bio.author.name

    class Meta:
        ordering = ("id",)


class Entry(BaseModel):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    headline = models.CharField(max_length=255)
    body_text = models.TextField(null=True)
    pub_date = models.DateField(null=True)
    mod_date = models.DateField(null=True)
    authors = models.ManyToManyField(Author, related_name="entries")
    n_comments = models.IntegerField(default=0)
    n_pingbacks = models.IntegerField(default=0)
    rating = models.IntegerField(default=0)
    tags = GenericRelation(TaggedItem)

    def __str__(self):
        return self.headline

    class Meta:
        ordering = ("id",)


class Comment(BaseModel):
    entry = models.ForeignKey(Entry, related_name="comments", on_delete=models.CASCADE)
    body = models.TextField()
    author = models.ForeignKey(
        Author,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    def __str__(self):
        return self.body

    class Meta:
        ordering = ("id",)


class ProjectType(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("id",)


class Project(PolymorphicModel):
    topic = models.CharField(max_length=30)
    project_type = models.ForeignKey(ProjectType, null=True, on_delete=models.CASCADE)


class ArtProject(Project):
    artist = models.CharField(max_length=30)
    description = models.CharField(max_length=100, null=True)


class ResearchProject(Project):
    supervisor = models.CharField(max_length=30)


class LabResults(models.Model):
    research_project = models.ForeignKey(
        ResearchProject, related_name="lab_results", on_delete=models.CASCADE
    )
    date = models.DateField()
    measurements = models.TextField()
    author = models.ForeignKey(
        Author,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="lab_results",
    )

    class Meta:
        ordering = ("id",)


class Company(models.Model):
    name = models.CharField(max_length=100)
    current_project = models.ForeignKey(
        Project, related_name="companies", on_delete=models.CASCADE
    )
    future_projects = models.ManyToManyField(Project)

    def __str__(self):
        return self.name
