"""
Example app URLs
"""
from django.conf.urls import patterns, include, url
from .api import User, UserEmber

urlpatterns = patterns('',
    url(r'^user-default/(?P<pk>\d+)/$', User.as_view(), name='user-default'),
    url(r'^user-ember/(?P<pk>\d+)/$', UserEmber.as_view(), name='user-ember'),

)

