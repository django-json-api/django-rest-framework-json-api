from rest_framework import viewsets
from example.models import Blog
from example.serializers import BlogSerializer


class BlogViewSet(viewsets.ModelViewSet):

    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
