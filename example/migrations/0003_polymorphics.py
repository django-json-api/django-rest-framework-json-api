import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("example", "0002_taggeditem"),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("topic", models.CharField(max_length=30)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AlterField(
            model_name="comment",
            name="entry",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comments",
                to="example.Entry",
            ),
        ),
        migrations.CreateModel(
            name="ArtProject",
            fields=[
                (
                    "project_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="example.Project",
                    ),
                ),
                ("artist", models.CharField(max_length=30)),
            ],
            options={
                "abstract": False,
            },
            bases=("example.project",),
        ),
        migrations.CreateModel(
            name="ResearchProject",
            fields=[
                (
                    "project_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="example.Project",
                    ),
                ),
                ("supervisor", models.CharField(max_length=30)),
            ],
            options={
                "abstract": False,
            },
            bases=("example.project",),
        ),
        migrations.AddField(
            model_name="project",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_example.project_set+",
                to="contenttypes.ContentType",
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="current_project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="companies",
                to="example.Project",
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="future_projects",
            field=models.ManyToManyField(to="example.Project"),
        ),
    ]
