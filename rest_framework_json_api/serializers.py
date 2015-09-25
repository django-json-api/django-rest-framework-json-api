from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import *

from rest_framework_json_api.utils import format_relation_name, get_resource_type_from_instance, \
    get_resource_type_from_serializer


class ResourceIdentifierObjectSerializer(BaseSerializer):
    default_error_messages = {
        'incorrect_model_type': _('Incorrect model type. Expected {model_type}, received {received_type}.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def __init__(self, *args, **kwargs):
        self.model_class = kwargs.pop('model_class', None)
        if 'instance' not in kwargs and not self.model_class:
            raise RuntimeError('ResourceIdentifierObjectsSerializer must be initialized with a model class.')
        super(ResourceIdentifierObjectSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        return {
            'type': format_relation_name(get_resource_type_from_instance(instance)),
            'id': str(instance.pk)
        }

    def to_internal_value(self, data):
        if data['type'] != format_relation_name(self.model_class.__name__):
            self.fail('incorrect_model_type', model_type=self.model_class, received_type=data['type'])
        pk = data['id']
        try:
            return self.model_class.objects.get(pk=pk)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=pk)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data['pk']).__name__)


class SparseFieldsetsMixin(object):
    def __init__(self, *args, **kwargs):
        context = kwargs.get('context')
        request = context.get('request') if context else None

        if request:
            sparse_fieldset_query_param = 'fields[{}]'.format(get_resource_type_from_serializer(self))
            try:
                param_name = next(key for key in request.query_params if sparse_fieldset_query_param in key)
            except StopIteration:
                pass
            else:
                fieldset = request.query_params.get(param_name).split(',')
                for field_name, field in self.fields.items():
                    if field_name == api_settings.URL_FIELD_NAME:  # leave self link there
                        continue
                    if field_name not in fieldset:
                        self.fields.pop(field_name)

        super(SparseFieldsetsMixin, self).__init__(*args, **kwargs)


class HyperlinkedModelSerializer(SparseFieldsetsMixin, HyperlinkedModelSerializer):
    """
    A type of `ModelSerializer` that uses hyperlinked relationships instead
    of primary key relationships. Specifically:

    * A 'url' field is included instead of the 'id' field.
    * Relationships to other instances are hyperlinks, instead of primary keys.

    * A mixin class to enable sparse fieldsets is included
    """
