from .models import Schedule, OnetimeSchedule
from rest_framework import serializers


class ScheduleSerializer(serializers.ModelSerializer):
    time_reference = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = '__all__'

    def get_time_reference(self, obj):
        try:
            return Schedule.RELATIVE_TYPES[obj.time_reference-1][1]
        except Exception as ex:
            return 'UNKNOWN'


class OnetimeScheduleSerializer(serializers.ModelSerializer):
    pk = serializers.ReadOnlyField()

    class Meta:
        model = OnetimeSchedule
        fields = '__all__'
        #fields = 'pk', 'description', 'state', 'type', 'tags', 'execution_limit', 'started_time', 'current_position', 'ph_sn', 'ph_index'

