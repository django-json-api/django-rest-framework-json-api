# Generated by Django 4.2.5 on 2023-09-12 07:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("example", "0013_questionnaire"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionnaire",
            name="metadata",
            field=models.JSONField(default={}),
            preserve_default=False,
        ),
    ]
