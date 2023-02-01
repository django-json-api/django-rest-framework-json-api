import re

from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend, OrderingFilter

from rest_framework_json_api.utils import undo_format_field_name


class OrderingFilter(OrderingFilter):
    """
    A backend filter that implements https://jsonapi.org/format/#fetching-sorting and
    raises a 400 error if any sort field is invalid.

    If you prefer *not* to report 400 errors for invalid sort fields, just use
    :py:class:`rest_framework.filters.OrderingFilter` with
    :py:attr:`~rest_framework.filters.OrderingFilter.ordering_param` = "sort"

    Also supports undo of field name formatting
    (See JSON_API_FORMAT_FIELD_NAMES in docs/usage.md)
    """

    #: override :py:attr:`rest_framework.filters.OrderingFilter.ordering_param`
    #: with JSON:API-compliant query parameter name.
    ordering_param = "sort"
    ordering_description = (
        "[list of fields to sort by]" "(https://jsonapi.org/format/#fetching-sorting)"
    )

    def remove_invalid_fields(self, queryset, fields, view, request):
        """
        Extend :py:meth:`rest_framework.filters.OrderingFilter.remove_invalid_fields` to
        validate that all provided sort fields exist (as contrasted with the super's behavior
        which is to silently remove invalid fields).

        :raises ValidationError: if a sort field is invalid.
        """
        valid_fields = [
            item[0]
            for item in self.get_valid_fields(queryset, view, {"request": request})
        ]
        bad_terms = [
            term
            for term in fields
            if undo_format_field_name(term.replace(".", "__").lstrip("-"))
            not in valid_fields
        ]
        if bad_terms:
            raise ValidationError(
                "invalid sort parameter{}: {}".format(
                    ("s" if len(bad_terms) > 1 else ""), ",".join(bad_terms)
                )
            )
        # this looks like it duplicates code above, but we want the ValidationError to report
        # the actual parameter supplied while we want the fields passed to the super() to
        # be correctly rewritten.
        # The leading `-` has to be stripped to prevent format_value from turning it into `_`.
        underscore_fields = []
        for item in fields:
            item_rewritten = item.replace(".", "__")
            if item_rewritten.startswith("-"):
                underscore_fields.append(
                    "-" + undo_format_field_name(item_rewritten.lstrip("-"))
                )
            else:
                underscore_fields.append(undo_format_field_name(item_rewritten))

        return super().remove_invalid_fields(queryset, underscore_fields, view, request)


class QueryParameterValidationFilter(BaseFilterBackend):
    """
    A backend filter that performs strict validation of query parameters for
    JSON:API spec conformance and raises a 400 error if non-conforming usage is
    found.

    If you want to add some additional non-standard query parameters,
    override :py:attr:`query_regex` adding the new parameters. Make sure to comply with
    the rules at https://jsonapi.org/format/#query-parameters.
    """

    #: compiled regex that matches the allowed https://jsonapi.org/format/#query-parameters:
    #: `sort` and `include` stand alone; `filter`, `fields`, and `page` have []'s
    query_regex = re.compile(
        r"^(sort|include)$|^(?P<type>filter|fields|page)(\[[\w\.\-]+\])?$"
    )

    def validate_query_params(self, request):
        """
        Validate that query params are in the list of valid query keywords in
        :py:attr:`query_regex`

        :raises ValidationError: if not.
        """
        # TODO: For JSON:API error object conformance, must set JSON:API errors "parameter" for
        # the ValidationError. This requires extending DRF/DJA Exceptions.
        for qp in request.query_params.keys():
            m = self.query_regex.match(qp)
            if not m:
                raise ValidationError(f"invalid query parameter: {qp}")
            if (
                not m.group("type") == "filter"
                and len(request.query_params.getlist(qp)) > 1
            ):
                raise ValidationError(f"repeated query parameter not allowed: {qp}")

    def filter_queryset(self, request, queryset, view):
        """
        Overrides :py:meth:`BaseFilterBackend.filter_queryset` by first validating the
        query params with :py:meth:`validate_query_params`
        """
        self.validate_query_params(request)
        return queryset
