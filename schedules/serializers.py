from .models import Schedule, OnetimeSchedule
from rest_framework import serializers


class ScheduleSerializer(serializers.ModelSerializer):
    time_reference = serializers.SerializerMethodField()
    absolute_next_time = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = '__all__'

    def get_time_reference(self, obj):
        try:
            return Schedule.RELATIVE_TYPES[obj.time_reference][1]
        except Exception as ex:
            return 'UNKNOWN'

    def get_absolute_next_time(self, obj):
        return obj.next_datetime(for_next_time=False, info_only=True)


class OnetimeScheduleSerializer(serializers.ModelSerializer):
    pk = serializers.ReadOnlyField()

    class Meta:
        model = OnetimeSchedule
        fields = '__all__'
        #fields = 'pk', 'description', 'state', 'type', 'tags', 'execution_limit', 'started_time', 'current_position', 'ph_sn', 'index'


