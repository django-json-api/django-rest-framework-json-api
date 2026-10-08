from collections.abc import Mapping

from django.core.exceptions import ObjectDoesNotExist
from django.utils.module_loading import import_string as import_class_from_dotted_path
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ParseError
from rest_framework.relations import HyperlinkedIdentityField

# star import defined so `rest_framework_json_api.serializers` can be
# a simple drop in for `rest_framework.serializers`
from rest_framework.serializers import *  # noqa: F401, F403
from rest_framework.serializers import (
    BaseSerializer,
    HyperlinkedModelSerializer,
    ModelSerializer,
    Serializer,
    SerializerMetaclass,
)
from rest_framework.settings import api_settings

from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.utils import (
    get_included_resources,
    get_resource_type_from_instance,
    get_resource_type_from_model,
    get_resource_type_from_serializer,
    undo_format_field_name,
)


class ResourceIdentifierObjectSerializer(BaseSerializer):
    default_error_messages = {
        "incorrect_model_type": _(
            "Incorrect model type. Expected {model_type}, received {received_type}."
        ),
        "does_not_exist": _('Invalid pk "{pk_value}" - object does not exist.'),
        "incorrect_type": _("Incorrect type. Expected pk value, received {data_type}."),
    }

    model_class = None

    def __init__(self, *args, **kwargs):
        self.model_class = kwargs.pop("model_class", self.model_class)
        # this has no fields but assumptions are made elsewhere that self.fields exists.
        self.fields = {}
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        return {
            "type": get_resource_type_from_instance(instance),
            "id": str(instance.pk),
        }

    def to_internal_value(self, data):
        if data["type"] != get_resource_type_from_model(self.model_class):
            self.fail(
                "incorrect_model_type",
                model_type=self.model_class,
                received_type=data["type"],
            )
        pk = data["id"]
        try:
            return self.model_class.objects.get(pk=pk)
        except ObjectDoesNotExist:
            self.fail("does_not_exist", pk_value=pk)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data["pk"]).__name__)


class SparseFieldsetsMixin:
    """
    A serializer mixin that adds support for sparse fieldsets through `fields` query parameter.

    Specification: https://jsonapi.org/format/#fetching-sparse-fieldsets
    """

    @property
    def _readable_fields(self):
        request = self.context.get("request") if self.context else None
        readable_fields = super()._readable_fields

        if request:
            try:
                resource_type = get_resource_type_from_serializer(self)
                sparse_fieldset_query_param = f"fields[{resource_type}]"

                sparse_fieldset_value = request.query_params.get(
                    sparse_fieldset_query_param
                )
                if sparse_fieldset_value is not None:
                    sparse_fields = [
                        undo_format_field_name(sparse_field)
                        for sparse_field in sparse_fieldset_value.split(",")
                    ]
                    return (
                        field
                        for field in readable_fields
                        if field.field_name in sparse_fields
                        # URL_FIELD_NAME is the field used as self-link to resource
                        # however only when it is a HyperlinkedIdentityField
                        or (
                            field.field_name == api_settings.URL_FIELD_NAME
                            and isinstance(field, HyperlinkedIdentityField)
                        )
                        # ID is a required field which might have been overwritten
                        # so need to keep it
                        or field.field_name == "id"
                    )
            except AttributeError:
                # no type on serializer, may only be used nested
                pass

        return readable_fields


class IncludedResourcesValidationMixin:
    """
    A serializer mixin that adds validation of `include` query parameter to
    support compound documents.

    Specification: https://jsonapi.org/format/#document-compound-documents)
    """

    def __init__(self, *args, **kwargs):
        context = kwargs.get("context")
        request = context.get("request") if context else None
        view = context.get("view") if context else None

        def validate_path(serializer_class, field_path, path):
            serializers = getattr(serializer_class, "included_serializers", None)
            if serializers is None:
                raise ParseError("This endpoint does not support the include parameter")
            this_field_name = field_path[0]
            this_included_serializer = serializers.get(this_field_name)
            if this_included_serializer is None:
                raise ParseError(
                    "This endpoint does not support the include parameter for path {}".format(
                        path
                    )
                )
            if len(field_path) > 1:
                new_included_field_path = field_path[1:]
                # We go down one level in the path
                validate_path(this_included_serializer, new_included_field_path, path)

        if request and view:
            included_resources = get_included_resources(request)
            for included_field_name in included_resources:
                included_field_path = included_field_name.split(".")
                if "related_field" in view.kwargs:
                    this_serializer_class = view.get_related_serializer_class()
                else:
                    this_serializer_class = view.get_serializer_class()
                # lets validate the current path
                validate_path(
                    this_serializer_class, included_field_path, included_field_name
                )

        super().__init__(*args, **kwargs)


class ReservedFieldNamesMixin:
    """Ensures that reserved field names are not used and an error raised instead."""

    _reserved_field_names = {
        "meta",
        "results",
        "type",
        api_settings.NON_FIELD_ERRORS_KEY,
    }

    def get_fields(self):
        fields = super().get_fields()

        found_reserved_field_names = self._reserved_field_names.intersection(
            fields.keys()
        )
        assert not found_reserved_field_names, (
            f"Serializer class {self.__class__.__module__}.{self.__class__.__qualname__} "
            f"uses following reserved field name(s) which is not allowed: "
            f"{', '.join(sorted(found_reserved_field_names))}"
        )

        return fields


class LazySerializersDict(Mapping):
    """
    A dictionary of serializers which lazily import dotted class path and self.
    """

    def __init__(self, parent, serializers):
        self.parent = parent
        self.serializers = serializers

    def __getitem__(self, key):
        value = self.serializers[key]
        if not isinstance(value, type):
            if value == "self":
                value = self.parent
            else:
                value = import_class_from_dotted_path(value)
            self.serializers[key] = value

        return value

    def __iter__(self):
        return iter(self.serializers)

    def __len__(self):
        return len(self.serializers)

    def __repr__(self):
        return dict.__repr__(self.serializers)


class SerializerMetaclass(SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        serializer = super().__new__(cls, name, bases, attrs)

        if attrs.get("included_serializers", None):
            serializer.included_serializers = LazySerializersDict(
                serializer, attrs["included_serializers"]
            )

        if attrs.get("related_serializers", None):
            serializer.related_serializers = LazySerializersDict(
                serializer, attrs["related_serializers"]
            )

        return serializer


# If user imports serializer from here we can catch class definition and check
# nested serializers for depricated use.
class Serializer(
    IncludedResourcesValidationMixin,
    SparseFieldsetsMixin,
    ReservedFieldNamesMixin,
    Serializer,
    metaclass=SerializerMetaclass,
):
    """
    A `Serializer` is a model-less serializer class with additional
    support for JSON:API spec features.

    As in JSON:API specification a type is always required you need to
    make sure that you define `resource_name` in your `Meta` class
    when deriving from this class.

    Included Mixins:

    * A mixin class to enable sparse fieldsets is included
    * A mixin class to enable validation of included resources is included
    """

    pass


class HyperlinkedModelSerializer(
    IncludedResourcesValidationMixin,
    SparseFieldsetsMixin,
    ReservedFieldNamesMixin,
    HyperlinkedModelSerializer,
    metaclass=SerializerMetaclass,
):
    """
    A type of `ModelSerializer` that uses hyperlinked relationships instead
    of primary key relationships. Specifically:

    * A 'url' field is included instead of the 'id' field.
    * Relationships to other instances are hyperlinks, instead of primary keys.

    Included Mixins:

    * A mixin class to enable sparse fieldsets is included
    * A mixin class to enable validation of included resources is included
    """


class ModelSerializer(
    IncludedResourcesValidationMixin,
    SparseFieldsetsMixin,
    ReservedFieldNamesMixin,
    ModelSerializer,
    metaclass=SerializerMetaclass,
):
    """
    A `ModelSerializer` is just a regular `Serializer`, except that:

    * A set of default fields are automatically populated.
    * A set of default validators are automatically populated.
    * Default `.create()` and `.update()` implementations are provided.

    The process of automatically determining a set of serializer fields
    based on the model fields is reasonably complex, but you almost certainly
    don't need to dig into the implementation.

    If the `ModelSerializer` class *doesn't* generate the set of fields that
    you need you should either declare the extra/differing fields explicitly on
    the serializer class, or simply use a `Serializer` class.


    Included Mixins:

    * A mixin class to enable sparse fieldsets is included
    * A mixin class to enable validation of included resources is included
    """

    serializer_related_field = ResourceRelatedField

    def get_field_names(self, declared_fields, info):
        """
        We override the parent to omit explicity defined meta fields (such
        as SerializerMethodFields) from the list of declared fields
        """
        meta_fields = getattr(self.Meta, "meta_fields", [])

        declared = {
            field_name: field
            for field_name, field in declared_fields.items()
            if field_name not in meta_fields
        }
        fields = super().get_field_names(declared, info)
        return list(fields) + list(getattr(self.Meta, "meta_fields", list()))
