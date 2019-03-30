from .models import Input, Output, InputToOutput
from rest_framework import serializers
from taggit_serializer.serializers import (TagListSerializerField, TaggitSerializer)
from taggit.models import Tag


class InputSerializer(TaggitSerializer, serializers.HyperlinkedModelSerializer):
    #url = serializers.HyperlinkedIdentityField(view_name="input:id")
    pk = serializers.ReadOnlyField()
    tags = TagListSerializerField()
    type = serializers.SerializerMethodField()

    #highlight = serializers.HyperlinkedIdentityField(view_name='set_down', format='html')

    class Meta:
        model = Input
        #fields = ('url', 'ph_sn', 'ph_index', 'input_type', 'deleted', 'description', 'outputs')
        #fields = ('url', 'url2', 'ph_sn', 'ph_index', 'input_type', 'deleted', 'description', 'outputs', 'tags',)
        fields = '__all__'

    def get_type(self, obj):
        try:
            return Input.INPUT_TYPES[obj.input_type-1][1]
        except Exception as ex:
            return 'UNKNOWN'


class InputSimpleSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = Input
        fields = 'pk', 'description', 'type', 'tags', 'state'

    def get_type(self, obj):
        try:
            return Input.INPUT_TYPES[obj.input_type-1][1]
        except Exception as ex:
            return 'UNKNOWN'


class InputAdminSerializer(InputSimpleSerializer):
    class Meta(InputSimpleSerializer.Meta):
        model = Input
        fields = 'pk', 'description', 'type', 'tags', 'state', 'ph_sn', 'ph_index'

#
# class OutputSerializer_base(TaggitSerializer, serializers.HyperlinkedModelSerializer):
#     def get_type(self, obj):
#         try:
#             import logging
#             logger = logging.getLogger('ios.views.IOsView')
#             logger.debug('??????????????????????????????????????????????????')
#
#             return Output.OUTPUT_TYPES[obj.output_type-1][1]
#         except Exception as ex:
#             return 'UNKNOWN'
#
#     def get_permissions(self, obj):
#         try:
#             return obj.permissions
#         except Exception as ex:
#             return 'UNKNOWN'
#
#
# class OutputSerializer(OutputSerializer_base):
#     #url = serializers.HyperlinkedIdentityField(view_name="input:id")
#     pk = serializers.ReadOnlyField()
#     type = serializers.SerializerMethodField()
#     tags = TagListSerializerField()
#     permissions = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Output
#         fields = '__all__'
#         extra_fields = ['permissions']
#         #fields = ('pk', 'url', 'ph_sn', 'ph_index', 'output_type', 'deleted', 'description', 'total_progress', '_my_state',)
#
#     def get_field_names(self, declared_fields, info):
#         """
#         Adds the 'extra_fields' to '_all_'
#         https://stackoverflow.com/questions/38245414/django-rest-framework-how-to-include-all-fields-and-a-related-field-in-mo
#         :param declared_fields:
#         :param info:
#         :return:
#         """
#         import logging
#         logger = logging.getLogger('ios.views.IOsView')
#         logger.debug('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
#         expanded_fields = super(OutputSerializer, self).get_field_names(declared_fields, info)
#         logger.debug('*************************************')
#         logger.debug(expanded_fields)
#
#         if getattr(self.Meta, 'extra_fields', None):
#             logger.debug('++++++++++++++++++++++++++++++++++++++')
#             logger.debug(expanded_fields)
#             return expanded_fields + self.Meta.extra_fields
#         else:
#             logger.debug('--------------------------------------')
#             logger.debug(expanded_fields)
#             return expanded_fields
#
#
#
# class OutputSimpleSerializer(OutputSerializer_base):
#     type = serializers.SerializerMethodField()
#     tags = TagListSerializerField()
#     permissions = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Output
#         fields = 'pk', 'description', 'state', 'type', 'tags', 'execution_limit', 'started_time', 'current_position', 'permissions'
#
#
# class OutputAdminSerializer(OutputSimpleSerializer):
#     class Meta(OutputSimpleSerializer.Meta):
#         model = Output
#         fields = 'pk', 'description', 'state', 'type', 'tags', 'execution_limit', 'started_time', 'current_position', 'ph_sn', 'ph_index'
#









class OutputSerializer(TaggitSerializer, serializers.HyperlinkedModelSerializer):
    #url = serializers.HyperlinkedIdentityField(view_name="input:id")
    pk = serializers.ReadOnlyField()
    type = serializers.SerializerMethodField()
    tags = TagListSerializerField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Output
        fields = '__all__'
        #fields = ('pk', 'url', 'ph_sn', 'ph_index', 'output_type', 'deleted', 'description', 'total_progress', '_my_state',)

    def get_type(self, obj):
        try:
            return Output.OUTPUT_TYPES[obj.output_type-1][1]
        except Exception as ex:
            return 'UNKNOWN'

    def get_permissions(self, obj):
        try:
            return obj.permissions
        except Exception as ex:
            return 'UNKNOWN'


class OutputSimpleSerializer(OutputSerializer):
    #type = serializers.SerializerMethodField()
    #tags = TagListSerializerField()

    class Meta(OutputSerializer.Meta):
        #model = Output
        fields = 'pk', 'description', 'state', 'type', 'tags', 'execution_limit', 'started_time', 'current_position', 'permissions', 'supports_schedules'

    #def get_type(self, obj):
    #    try:
    #        return Output.OUTPUT_TYPES[obj.output_type-1][1]
    #    except Exception as ex:
    #        return 'UNKNOWN'


class OutputAdminSerializer(OutputSimpleSerializer):
    class Meta(OutputSimpleSerializer.Meta):
        #model = Output
        fields = 'pk', 'description', 'state', 'type', 'tags', 'execution_limit', 'started_time', 'current_position', 'permissions', 'supports_schedules', 'ph_sn', 'ph_index'











#class IOsSerializer(serializers.Serializer):
#    inputs = InputSerializer(many=True, read_only=True)
#    outputs = OutputSerializer(many=True, read_only=True)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'
