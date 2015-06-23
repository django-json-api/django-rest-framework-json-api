"""
Example app URLs
"""
from django.conf.urls import patterns, include, url
from rest_framework import routers
from .resources.identity import Identity, GenericIdentity

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'identities', Identity)

urlpatterns = router.urls

urlpatterns += patterns('',
    url(r'identities/default/(?P<pk>\d+)',
        GenericIdentity.as_view(), name='user-default'),
)

