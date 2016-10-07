import django_filters

from example.models import Comment


class CommentFilter(django_filters.FilterSet):

    class Meta:
        model = Comment
        fileds = {'body': ['exact', 'in', 'icontains', 'contains'],
                  'author': ['exact', 'gte', 'lte'],
                  }
