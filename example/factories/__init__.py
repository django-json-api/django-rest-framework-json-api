# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import factory

from example.models import Blog


class BlogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Blog

    name = "Blog 1"
