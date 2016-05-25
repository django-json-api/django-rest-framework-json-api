# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-13 08:57
from __future__ import unicode_literals
from distutils.version import LooseVersion

from django.db import migrations, models
import django.db.models.deletion
import django


class Migration(migrations.Migration):

    # TODO: Must be removed as soon as Django 1.7 support is dropped
    if django.get_version() < LooseVersion('1.8'):
        dependencies = [
            ('contenttypes', '0001_initial'),
            ('example', '0001_initial'),
        ]
    else:
        dependencies = [
            ('contenttypes', '0002_remove_content_type_name'),
            ('example', '0001_initial'),
        ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=30)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ArtProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='example.Project')),
                ('artist', models.CharField(max_length=30)),
            ],
            options={
                'abstract': False,
            },
            bases=('example.project',),
        ),
        migrations.CreateModel(
            name='ResearchProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='example.Project')),
                ('supervisor', models.CharField(max_length=30)),
            ],
            options={
                'abstract': False,
            },
            bases=('example.project',),
        ),
        migrations.AddField(
            model_name='project',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_example.project_set+', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='company',
            name='current_project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='companies', to='example.Project'),
        ),
        migrations.AddField(
            model_name='company',
            name='future_projects',
            field=models.ManyToManyField(to='example.Project'),
        ),
    ]
