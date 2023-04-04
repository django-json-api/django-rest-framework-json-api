import re

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings

from rest_framework_json_api.utils import format_field_name, undo_format_field_name


class DjangoFilterBackend(DjangoFilterBackend):
    """
    A Django-style ORM filter implementation, using `django-filter`.

    This is not part of the JSON:API standard per-se, other than the requirement
    to use the `filter` keyword: This is an optional implementation of style of
    filtering in which each filter is an ORM expression as implemented by
    DjangoFilterBackend and seems to be in alignment with an interpretation of
    https://jsonapi.org/recommendations/#filtering, including relationship
    chaining. It also returns a 400 error for invalid filters.

    Filters can be:

    - A resource field
      equality test:

      ``?filter[qty]=123``

    - Apply other
      https://docs.djangoproject.com/en/stable/ref/models/querysets/#field-lookups
      operators:

      ``?filter[name.icontains]=bar`` or ``?filter[name.isnull]=true...``

    - Membership in
      a list of values:

      ``?filter[name.in]=abc,123,zzz`` (name in ['abc','123','zzz'])

    - Filters can be combined
      for intersection (AND):

      ``?filter[qty]=123&filter[name.in]=abc,123,zzz&filter[...]``

    - A related resource path
      can be used:

      ``?filter[inventory.item.partNum]=123456``

      where `inventory.item` is the relationship path.

    If you are also using rest_framework.filters.SearchFilter you'll want to customize
    the name of the query parameter for searching to make sure it doesn't conflict
    with a field name defined in the filterset.
    The recommended value is: `search_param="filter[search]"` but just make sure it's
    `filter[<something>]` to comply with the JSON:API spec requirement to use the filter
    keyword. The default is "search" unless overriden but it's used here just to make sure
    we don't complain about it being an invalid filter.
    """

    search_param = api_settings.SEARCH_PARAM

    # Make this regex check for 'filter' as well as 'filter[...]'
    # See https://jsonapi.org/format/#document-member-names for allowed characters
    # and https://jsonapi.org/format/#document-member-names-reserved-characters for reserved
    # characters (for use in paths, lists or as delimiters).
    # regex `\w` matches [a-zA-Z0-9_].
    # TODO: U+0080 and above allowed but not recommended. Leave them out for now.e
    #       Also, ' ' (space) is allowed within a member name but not recommended.
    filter_regex = re.compile(
        r"^filter(?P<ldelim>\[?)(?P<assoc>[\w\.\-]*)(?P<rdelim>\]?$)"
    )

    def _validate_filter(self, keys, filterset_class):
        """
        Check that all the filter[key] are valid.

        :param keys: list of FilterSet keys
        :param filterset_class: :py:class:`django_filters.rest_framework.FilterSet`
        :raises ValidationError: if key not in FilterSet keys or no FilterSet.
        """
        for k in keys:
            if (not filterset_class) or (k not in filterset_class.base_filters):
                raise ValidationError(f"invalid filter[{k}]")

    def get_filterset(self, request, queryset, view):
        """
        Sometimes there's no `filterset_class` defined yet the client still
        requests a filter. Make sure they see an error too. This means
        we have to `get_filterset_kwargs()` even if there's no `filterset_class`.
        """
        # TODO: .base_filters vs. .filters attr (not always present)
        filterset_class = self.get_filterset_class(view, queryset)
        kwargs = self.get_filterset_kwargs(request, queryset, view)
        self._validate_filter(kwargs.pop("filter_keys"), filterset_class)
        if filterset_class is None:
            return None
        return filterset_class(**kwargs)

    def get_filterset_kwargs(self, request, queryset, view):
        """
        Turns filter[<field>]=<value> into <field>=<value> which is what
        DjangoFilterBackend expects

        :raises ValidationError: for bad filter syntax
        """
        filter_keys = []
        # rewrite filter[field] query params to make DjangoFilterBackend work.
        data = request.query_params.copy()
        for qp, val in request.query_params.lists():
            m = self.filter_regex.match(qp)
            if m and (
                not m.groupdict()["assoc"]
                or m.groupdict()["ldelim"] != "["
                or m.groupdict()["rdelim"] != "]"
            ):
                raise ValidationError(f"invalid query parameter: {qp}")
            if m and qp != self.search_param:
                if not all(val):
                    raise ValidationError(f"missing value for query parameter {qp}")
                # convert JSON:API relationship path to Django ORM's __ notation
                key = m.groupdict()["assoc"].replace(".", "__")
                key = undo_format_field_name(key)
                data.setlist(key, val)
                filter_keys.append(key)
                del data[qp]
        return {
            "data": data,
            "queryset": queryset,
            "request": request,
            "filter_keys": filter_keys,
        }

    def get_schema_operation_parameters(self, view):
        """
        Convert backend filter `name` to JSON:API-style `filter[name]`.
        For filters that are relationship paths, rewrite ORM-style `__` to our preferred `.`.
        For example: `blog__name__contains` becomes `filter[blog.name.contains]`.

        This is basically the reverse of `get_filterset_kwargs` above.
        """
        result = super().get_schema_operation_parameters(view)
        for res in result:
            if "name" in res:
                name = format_field_name(res["name"].replace("__", "."))
                res["name"] = f"filter[{name}]"
        return result
