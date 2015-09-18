from django.conf.urls import include, url
from rest_framework import routers

from example.views import BlogViewSet, EntryViewSet, AuthorViewSet, EntryRelationshipView, BlogRelationshipView


router = routers.DefaultRouter(trailing_slash=False)

router.register(r'blogs', BlogViewSet)
router.register(r'entries', EntryViewSet)
router.register(r'authors', AuthorViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),

    url(r'^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)', EntryRelationshipView.as_view()),
    url(r'^blogs/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)', BlogRelationshipView.as_view())

]
