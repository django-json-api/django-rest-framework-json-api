from rest_framework.exceptions import ValidationError
from rest_framework.relations import *
from rest_framework_json_api.utils import format_relation_name, get_related_resource_type, \
    get_resource_type_from_queryset, get_resource_type_from_instance
from django.utils.translation import ugettext_lazy as _


class HyperlinkedRelatedField(HyperlinkedRelatedField):
    """
    This field exists for the sole purpose of accepting PKs as well as URLs
    when data is submitted back to the serializer
    """
    default_error_messages = {
        'required': _('This field is required.'),
        'no_match': _('Invalid hyperlink - No URL match.'),
        'incorrect_match': _('Invalid hyperlink - Incorrect URL match.'),
        'does_not_exist': _('Invalid hyperlink - Object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected URL string, received {data_type}.'),
        'pk_does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_pk_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def __init__(self, **kwargs):
        self.pk_field = kwargs.pop('pk_field', None)
        super(HyperlinkedRelatedField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            # Try parsing links first for the browseable API
            return super(HyperlinkedRelatedField, self).to_internal_value(data)
        except ValidationError:
            if self.pk_field is not None:
                data = self.pk_field.to_internal_value(data)
            try:
                return self.get_queryset().get(pk=data)
            except ObjectDoesNotExist:
                self.fail('pk_does_not_exist', pk_value=data)
            except (TypeError, ValueError):
                self.fail('incorrect_pk_type', data_type=type(data).__name__)


class ResourceRelatedField(PrimaryKeyRelatedField):
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
        'incorrect_relation_type': _('Incorrect relation type. Expected {relation_type}, received {received_type}.'),
    }

    def to_internal_value(self, data):
        expected_relation_type = get_resource_type_from_queryset(self.queryset)
        if data['type'] != expected_relation_type:
            self.fail('incorrect_relation_type', relation_type=expected_relation_type, received_type=data['type'])
        return super(ResourceRelatedField, self).to_internal_value(data['id'])

    def to_representation(self, value):
        return {
            'type': format_relation_name(get_resource_type_from_instance(value)),
            'id': str(value.pk)
        }

