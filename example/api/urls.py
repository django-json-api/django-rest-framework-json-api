"""
Example app URLs
"""
from django.conf.urls import patterns, include, url
from .api import (
    User, UserEmber, EmberUserModelViewSet, MultipleIDMixinUserModelViewSet,
    UserCarResource)

from rest_framework import routers

urlpatterns = patterns('',
    url(r'^user-default/(?P<pk>\d+)/$', User.as_view(), name='user-default'),
    url(r'^user-ember/(?P<pk>\d+)/$', UserEmber.as_view(), name='user-ember'),
    url(r'^user-mixin-viewset/$',
        MultipleIDMixinUserModelViewSet.as_view({'get': 'list'}),
        name='mixin-user-list'),
    url(r'^user-viewset/$', EmberUserModelViewSet.as_view({'get': 'list'}),
        name='user-list'),
    url(r'^user-viewset/(?P<pk>\d+)/$',
        EmberUserModelViewSet.as_view(
            {'get': 'retrieve', 'post': 'create', 'put': 'update'}),
        name='user-detail'),
    url(r'users-cars/$', UserCarResource.as_view(),
        name='users-cars'),
)

