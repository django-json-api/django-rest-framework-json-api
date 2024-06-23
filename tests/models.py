from django.db import models


class DJAModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """

    class Meta:
        app_label = "tests"
        abstract = True


class BasicModel(DJAModel):
    text = models.CharField(max_length=100)

    class Meta:
        ordering = ("id",)


class URLModel(DJAModel):
    url = models.URLField()
    text = models.CharField(max_length=100)

    class Meta:
        ordering = ("id",)


# Models for relations tests
# ManyToMany
class ManyToManyTarget(DJAModel):
    name = models.CharField(max_length=100)


class ManyToManySource(DJAModel):
    name = models.CharField(max_length=100)
    targets = models.ManyToManyField(ManyToManyTarget, related_name="sources")


# ForeignKey
class ForeignKeyTarget(DJAModel):
    name = models.CharField(max_length=100)


class ForeignKeySource(DJAModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(
        ForeignKeyTarget, related_name="sources", on_delete=models.CASCADE
    )


class NestedRelatedSource(DJAModel):
    m2m_sources = models.ManyToManyField(ManyToManySource, related_name="nested_source")
    fk_source = models.ForeignKey(
        ForeignKeySource, related_name="nested_source", on_delete=models.CASCADE
    )
    m2m_targets = models.ManyToManyField(ManyToManyTarget, related_name="nested_target")
    fk_target = models.ForeignKey(
        ForeignKeyTarget, related_name="nested_target", on_delete=models.CASCADE
    )
