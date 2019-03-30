from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from schedules.models import Schedule, OnetimeSchedule
from schedules.serializers import ScheduleSerializer, OnetimeScheduleSerializer
from datetime import datetime
from dateutil.tz import tzlocal

from common.jewish_dates.jtimes import get_day_times


@api_view(['GET'])
@permission_classes((AllowAny,))
def times(request):
    import time
    """
    Return sunrise/sunset times
    """
    today = datetime.now(tzlocal()).date()
    #today = datetime(2017, 9, 9)
    sunrise, sunset, shaa_zmanit, day_hours, night_hours, tz_offset = get_day_times(today)
    sunrise = "%02d:%02d" % (sunrise[0], sunrise[1])
    sunset = "%02d:%02d" % (sunset[0], sunset[1])
    tz_offset1 = -time.altzone // 60 // 60

    #print('sunrise: %s, sunset: %s, shaa-zmanit: %s, day-hours: %s, night-hours: %s' % (sunrise, sunset, shaa, day, night))
    #return sunrise, sunset, shaa, day, night

    return Response({'sunrise': sunrise, 'sunset': sunset, 'tz_offset': tz_offset, 'tz_offset1': tz_offset1, 'shaa-zmanit': shaa_zmanit, 'day-hours': day_hours, 'night-hours': night_hours})


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Schedule.objects.all().order_by('-pk')
    serializer_class = ScheduleSerializer


class OnetimeScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    #queryset = OnetimeSchedule.objects.all().order_by('-start')
    queryset = OnetimeSchedule.objects.all()
    serializer_class = OnetimeScheduleSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """ allow rest api to filter by submissions """
        queryset = OnetimeSchedule.objects.all().order_by('date')
        output_id = self.request.query_params.get('output', None)
        if output_id:
            queryset = queryset.filter(output__pk=output_id)
        only_applicable = self.request.query_params.get('only_applicable', True)
        if only_applicable not in ['false', 'False', '0', 0, False]:
            queryset = queryset.filter(date__gte=datetime.today())

        return queryset

    def perform_create(self, serializer):
        print(serializer)
        serializer.save()
        #serializer.save(owner=self.request.user)