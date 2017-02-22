try:
    import rest_framework_filters
    DjangoFilterBackend = rest_framework_filters.backends.DjangoFilterBackend
except ImportError:
    from rest_framework import filters
    DjangoFilterBackend = filters.DjangoFilterBackend

from rest_framework_json_api.utils import format_query_params

class JsonApiFilterBackend(DjangoFilterBackend):

    def filter_queryset(self, request, queryset, view):

        filter_class = self.get_filter_class(view, queryset)
        new_query_params = format_query_params(request.query_params)
        if filter_class:
            return filter_class(new_query_params, queryset=queryset).qs

        return queryset
