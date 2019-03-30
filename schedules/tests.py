from django.contrib.auth.models import User
from django.test import TestCase
from dateutil.tz import tzlocal
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from schedules.views import OnetimeScheduleViewSet
from .models import Schedule, OnetimeSchedule
from ios.models import Output
import datetime


class SchedulesTestCase(TestCase):
    def setUp(self):
        self.su = User.objects.create_superuser(username='admin', password='test', email='admin@mail.com')
        #self.user1 = User.objects.create_user(username='user1', password='test')
        #self.user2 = User.objects.create_user(username='user2', password='test')
        #self.user3 = User.objects.create_user(username='user3', password='test')

        #self.sched0 = Schedule.objects.create(ph_sn=1, ph_index=0, input_type=Input.INPUT_TYPE_MAGNET, deleted=False, description='in 0')
        #self.obj0.tags.add('Door')
        #self.obj0.save()

        #Schedule.objects.create(sun=True, mon=False, tue=False, wed=False, thu=False, fri=False, but_only_secular_fri=False, sha=False, but_not_sukkot=False, time=datetime.time(1, 1, 0)).save()
        self.output = Output.objects.create(ph_sn=1, ph_index=3, output_type=Output.OUTPUT_TYPE_BLIND_DOWN, deleted=False, description='out 3')
        self.output.save()
        self.output2 = Output.objects.create(ph_sn=2, ph_index=3, output_type=Output.OUTPUT_TYPE_BLIND_DOWN, deleted=False, description='out 2')
        self.output2.save()
        return

        self.sun = self.create_schedule(sun=True, mon=False, tue=False, wed=False, thu=False, fri=False, but_only_secular_fri=False, sha=False, but_not_sukkot=False, time='1:01', turn_on=True, output=self.output)
        self.mon = self.create_schedule(sun=False, mon=True, tue=False, wed=False, thu=False, fri=False, but_only_secular_fri=False, sha=False, but_not_sukkot=False, time='1:02', turn_on=True, output=self.output)
        self.tue = self.create_schedule(sun=False, mon=False, tue=True, wed=False, thu=False, fri=False, but_only_secular_fri=False, sha=False, but_not_sukkot=False, time='1:03', turn_on=True, output=self.output)
        self.wed = self.create_schedule(sun=False, mon=False, tue=False, wed=True, thu=False, fri=False, but_only_secular_fri=False, sha=False, but_not_sukkot=False, time='1:04', turn_on=True, output=self.output)
        self.thu = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=True, fri=False, but_only_secular_fri=False, sha=False, but_not_sukkot=False, time='1:05', turn_on=True, output=self.output)
        self.fri = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=False, fri=True, but_only_secular_fri=False, sha=False, but_not_sukkot=False, time='1:06', turn_on=True, output=self.output)
        self.fri_no_sukkot = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=False, fri=True, but_only_secular_fri=False, sha=False, but_not_sukkot=True, time='1:07', turn_on=True, output=self.output)
        self.sec_fri = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=False, fri=True, but_only_secular_fri=True, sha=False, but_not_sukkot=False, time='1:08', turn_on=True, output=self.output)
        self.sha = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=False, fri=False, but_only_secular_fri=False, sha=True, but_not_sukkot=False, time='1:09', turn_on=True, output=self.output)
        self.sha_no_sukkot = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=False, fri=False, but_only_secular_fri=False, sha=True, but_not_sukkot=True, time='1:10', turn_on=True, output=self.output)

    def x_test_none(self):
        none = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=False, fri=False, but_only_secular_fri=False, sha=False, but_not_sukkot=False, time='1:11', turn_on=True, output=self.output)
        self.assertEqual(none._prepare_next(), None)
        none = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=False, fri=False, but_only_secular_fri=True, sha=False, but_not_sukkot=False, time='1:12', turn_on=True, output=self.output)
        self.assertEqual(none._prepare_next(), None)
        none = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=False, fri=False, but_only_secular_fri=False, sha=False, but_not_sukkot=True, time='1:13', turn_on=True, output=self.output)
        self.assertEqual(none._prepare_next(), None)
        none = self.create_schedule(sun=False, mon=False, tue=False, wed=False, thu=False, fri=False, but_only_secular_fri=True, sha=False, but_not_sukkot=True, time='1:14', turn_on=True, output=self.output)
        self.assertEqual(none._prepare_next(), None)

    def create_schedule(self, *args, **kwargs):
        obj = Schedule(*args, **kwargs)
        obj.save(just_testing=True)
        return obj

    def test_onetime_schedule_simple(self):
        one = OnetimeSchedule(date=datetime.date(2017, 9, 19), start=datetime.time(0, 0, tzinfo=tzlocal()), end=datetime.time(23, 59, tzinfo=tzlocal()), segments='111111111111111111111111111111111111100001111111111111111111111111111111111111111111111111111111', output=self.output, active=True, deleted=False)
        print('===========================================================================================================')
        print('2017-09-18 0:00')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 18, 0, 0, tzinfo=tzlocal()), for_next_time=False, just_testing=True), (datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), True))
        print('2017-09-18 0:00 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 18, 0, 0, tzinfo=tzlocal()), for_next_time=True, just_testing=True), (datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), True))
        print('2017-09-19 0:00')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), for_next_time=False, just_testing=True), (datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), True))
        print('2017-09-19 0:00 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), for_next_time=True, just_testing=True), (datetime.datetime(2017, 9, 19, 9, 15, tzinfo=tzlocal()), False))
        print('2017-09-19 9:15 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 9, 15, tzinfo=tzlocal()), for_next_time=True, just_testing=True), (datetime.datetime(2017, 9, 19, 10, 15, tzinfo=tzlocal()), True))
        print('2017-09-19 10:15 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 10, 15, tzinfo=tzlocal()), for_next_time=True, just_testing=True), None)

        one = OnetimeSchedule(date=datetime.date(2017, 9, 19), start=datetime.time(0, 0, tzinfo=tzlocal()), end=datetime.time(23, 59, tzinfo=tzlocal()), segments='000000000000000000000000000000000000011110000000000000000000000000000000000000000000000000000000', output=self.output, active=True, deleted=False)
        print('===========================================================================================================')
        print('2017-09-18 0:00')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 18, 0, 0, tzinfo=tzlocal()), for_next_time=False, just_testing=True), (datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), False))
        print('2017-09-18 0:00 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 18, 0, 0, tzinfo=tzlocal()), for_next_time=True, just_testing=True), (datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), False))
        print('2017-09-19 0:00')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), for_next_time=False, just_testing=True), (datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), False))
        print('2017-09-19 0:00 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), for_next_time=True, just_testing=True), (datetime.datetime(2017, 9, 19, 9, 15, tzinfo=tzlocal()), True))
        print('2017-09-19 9:15 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 9, 15, tzinfo=tzlocal()), for_next_time=True, just_testing=True), (datetime.datetime(2017, 9, 19, 10, 15, tzinfo=tzlocal()), False))
        print('2017-09-19 10:15 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 10, 15, tzinfo=tzlocal()), for_next_time=True, just_testing=True), None)

    def x_test_onetime_schedule_startend_times(self):
        one = OnetimeSchedule(date=datetime.date(2017, 9, 19), start=datetime.time(2, 14, tzinfo=tzlocal()), end=datetime.time(20, 44, tzinfo=tzlocal()), segments='', output=self.output, active=True, deleted=False)
        print('===========================================================================================================')
        print('2017-09-18 0:00')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 18, 0, 0, tzinfo=tzlocal()), for_next_time=False, just_testing=True), datetime.datetime(2017, 9, 19, 2, 14, tzinfo=tzlocal()))
        print('2017-09-18 0:00 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 18, 0, 0, tzinfo=tzlocal()), for_next_time=True, just_testing=True), datetime.datetime(2017, 9, 19, 2, 14, tzinfo=tzlocal()))
        print('2017-09-19 0:00 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 0, 0, tzinfo=tzlocal()), for_next_time=True, just_testing=True), datetime.datetime(2017, 9, 19, 2, 14, tzinfo=tzlocal()))
        print('2017-09-19 2:00')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 2, 0, tzinfo=tzlocal()), for_next_time=False, just_testing=True), datetime.datetime(2017, 9, 19, 2, 14, tzinfo=tzlocal()))
        print('2017-09-19 2:00 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 2, 0, tzinfo=tzlocal()), for_next_time=True, just_testing=True), datetime.datetime(2017, 9, 19, 2, 15, tzinfo=tzlocal()))
        print('2017-09-19 2:15 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 2, 15, tzinfo=tzlocal()), for_next_time=True, just_testing=True), datetime.datetime(2017, 9, 19, 2, 30, tzinfo=tzlocal()))

        print('2017-09-19 20:30')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 20, 30, tzinfo=tzlocal()), for_next_time=False, just_testing=False), datetime.datetime(2017, 9, 19, 20, 30, tzinfo=tzlocal()))
        print('2017-09-19 20:30 next')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 19, 20, 30, tzinfo=tzlocal()), for_next_time=True, just_testing=True), None)

        print('2017-09-20 1:00')
        self.assertEqual(one._prepare_next(now=datetime.datetime(2017, 9, 20, 1, 0, tzinfo=tzlocal()), for_next_time=False, just_testing=True), None)
        print('===========================================================================================================')
        #OneSched.save(just_testing=True)

    def X_test_onetimeschedule_and_yearlyschedule_overlap(self):
        one = OnetimeSchedule(date=datetime.date(2017, 9, 19), start=datetime.time(0, 50, tzinfo=tzlocal()), end=datetime.time(0, 59, tzinfo=tzlocal()), segments='111111111011111111101111111110111111111011111111101111111110111111111011111111101111111110111110', output=self.output, active=True, deleted=False)
        one.save(just_testing=True)

        two = OnetimeSchedule(date=datetime.date(2017, 9, 19), start=datetime.time(0, 55, tzinfo=tzlocal()), end=datetime.time(1, 1, tzinfo=tzlocal()), segments='111111111011111111101111111110111111111011111111101111111110111111111011111111101111111110111110', output=self.output2, active=True, deleted=False)
        two.save(just_testing=True)

        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output, datetime.datetime(2017, 9, 19, 0, 49, tzinfo=tzlocal())))
        self.assertTrue(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output, datetime.datetime(2017, 9, 19, 0, 50, tzinfo=tzlocal())))
        self.assertTrue(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output, datetime.datetime(2017, 9, 19, 0, 51, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output, datetime.datetime(2017, 9, 19, 0, 59, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output, datetime.datetime(2017, 9, 19, 1, 0, tzinfo=tzlocal())))

        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 19, 0, 49, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 19, 0, 50, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 19, 0, 51, tzinfo=tzlocal())))
        self.assertTrue(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 19, 0, 59, tzinfo=tzlocal())))
        self.assertTrue(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 19, 1, 0, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 19, 1, 1, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 19, 1, 2, tzinfo=tzlocal())))

        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 20, 0, 49, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 20, 0, 50, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 20, 0, 51, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 20, 0, 59, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 20, 1, 0, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 20, 1, 1, tzinfo=tzlocal())))
        self.assertFalse(OnetimeSchedule.objects.is_onetime_active_for_datatime(self.output2, datetime.datetime(2017, 9, 20, 1, 2, tzinfo=tzlocal())))

    def X_test_api(self):
        one = OnetimeSchedule(start=datetime.datetime(2017, 9, 19, 0, 50, tzinfo=tzlocal()), end=datetime.datetime(2017, 9, 19, 0, 59, tzinfo=tzlocal()), segments='111111111011111111101111111110111111111011111111101111111110111111111011111111101111111110111110', output=self.output, active=True, deleted=False)
        one.save(just_testing=True)

        # Using the standard RequestFactory API to create a form POST request
        factory = APIRequestFactory()
        view = OnetimeScheduleViewSet.as_view({'get': 'list',
                                               #'get': 'retrieve',
                                               'post': 'create',
                                               'put': 'update',
                                               'patch': 'partial_update',
                                               'delete': 'destroy'})

        #request = factory.get('/api/onetimeschedules/?output='+str(self.output.pk))
        request = factory.get('onetimeschedules', {'output': self.output.pk})
        force_authenticate(request, user=self.su)
        response = view(request)
        response.render()
        print(response)
        import json
        json = json.loads(response.content)
        json[0]['segments'] = '011111111001111111101111111110111111111011111111101111111110111111111011111111101111111110111101'
        print(json)

        print(json[0])
        print(json[0]['start'])
        #request = factory.post('onetimeschedules', data=json[0])


        #from django.test.client import encode_multipart
        #content = encode_multipart('BoUnDaRyStRiNg', json[0])
        #content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
        #request = factory.put('/notes/547/', content, content_type=content_type)

        #request = factory.put('onetimeschedules/' + str(json[0]['pk']) + '/', content, content_type=content_type)
        #request = factory.put('onetimeschedules', content, content_type=content_type)
        request = factory.put('onetimeschedules', data=json[0])


        force_authenticate(request, user=self.su)
        response = view(request, pk=json[0]['pk'])
        response.render()
        print(response)

        request = factory.get('onetimeschedules', {'output': self.output.pk})
        force_authenticate(request, user=self.su)
        response = view(request)
        response.render()
        print(response)


    def x_test_schedules(self):
        self.validate_schedule(datetime.datetime (2017, 9, 19, 1, 0, tzinfo=tzlocal()), {        #Tue, Day before Erev Rosh Hashana
            self.sun: datetime.datetime          (2017, 9, 24, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 19, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 20, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 20, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 20, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 21, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 21, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 20, 1, 0, tzinfo=tzlocal()), {        #Erev Rosh Hashana
            self.sun: datetime.datetime          (2017, 9, 24, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 26, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 20, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 20, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 20, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 21, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 21, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 21, 1, 0, tzinfo=tzlocal()), {        #Rosh Hashana 1 - 1:00
            self.sun: datetime.datetime          (2017, 9, 24, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 26, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 21, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 21, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 21, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 21, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 21, 2, 0, tzinfo=tzlocal()), {        #Rosh Hashana 1 - 2:00
            self.sun: datetime.datetime          (2017, 9, 24, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 26, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 22, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 22, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 22, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 22, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 22, 1, 0, tzinfo=tzlocal()), {        #Rosh Hashana 2 - 1:00
            self.sun: datetime.datetime          (2017, 9, 24, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 26, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 22, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 22, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 22, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 22, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 22, 2, 0, tzinfo=tzlocal()), {        #Rosh Hashana 2 - 2:00
            self.sun: datetime.datetime          (2017, 9, 24, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 26, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 29, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 29, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 23, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 23, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 23, 1, 0, tzinfo=tzlocal()), {        #Sha - Day after Rosh Hashana 2 - 1:00
            self.sun: datetime.datetime          (2017, 9, 24, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 26, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 29, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 29, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 23, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 23, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 23, 2, 0, tzinfo=tzlocal()), {        #Sha - Day after Rosh Hashana 2 - 2:00
            self.sun: datetime.datetime          (2017, 9, 24, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 26, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 29, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 29, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 30, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 30, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 24, 1, 0, tzinfo=tzlocal()), {        #Sun - 1:00
            self.sun: datetime.datetime          (2017, 9, 24, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 26, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 29, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 29, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 30, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 30, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 24, 2, 0, tzinfo=tzlocal()), {        #Sun - 2:00
            self.sun: datetime.datetime          (2017, 10, 1, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 9, 25, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 9, 26, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 9, 27, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 29, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 29, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 30, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 30, 1, 10, tzinfo=tzlocal())})


        self.validate_schedule(datetime.datetime (2017, 9, 28, 1, 0, tzinfo=tzlocal()), {        #Thur - Day before Erev Sha/YomKippur - 1:00
            self.sun: datetime.datetime          (2017, 10, 1, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 2, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 9, 28, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 29, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 29, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 30, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 30, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 28, 2, 0, tzinfo=tzlocal()), {        #Thur - Day before Erev Sha/YomKippur - 2:00
            self.sun: datetime.datetime          (2017, 10, 1, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 2, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),     #delayed due to Sukkot
            self.fri: datetime.datetime          (2017, 9, 29, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 29, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 30, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 30, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 29, 1, 0, tzinfo=tzlocal()), {        #Fri - Erev Sha/YomKippur - 1:00
            self.sun: datetime.datetime          (2017, 10, 1, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 2, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 9, 29, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 9, 29, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 9, 29, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 30, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 30, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 29, 2, 0, tzinfo=tzlocal()), {        #Fri - Erev Sha/YomKippur - 2:00
            self.sun: datetime.datetime          (2017, 10, 1, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 2, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 4, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 4, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 30, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 30, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 30, 1, 0, tzinfo=tzlocal()), {        #Sha/YomKippur - 1:00
            self.sun: datetime.datetime          (2017, 10, 1, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 2, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 4, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 4, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 9, 30, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 9, 30, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 9, 30, 2, 0, tzinfo=tzlocal()), {        #Sha/YomKippur - 2:00
            self.sun: datetime.datetime          (2017, 10, 1, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 2, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 4, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 4, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 5, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 1, 1, 0, tzinfo=tzlocal()), {        #Sun - 1:00
            self.sun: datetime.datetime          (2017, 10, 1, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 2, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 4, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 4, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 5, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 1, 2, 0, tzinfo=tzlocal()), {        #Sun - 2:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 2, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 4, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 4, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 5, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})


        self.validate_schedule(datetime.datetime (2017, 10, 3, 1, 0, tzinfo=tzlocal()), {        #Tue - Day before Erev Sukkot - 1:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 4, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 4, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 5, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 3, 2, 0, tzinfo=tzlocal()), {        #Tue - Day before Erev Sukkot - 2:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 4, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 4, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 5, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 4, 1, 0, tzinfo=tzlocal()), {        #Wed - Erev Sukkot - 1:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 4, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 4, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 5, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 4, 2, 0, tzinfo=tzlocal()), {        #Wed - Erev Sukkot - 2:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 6, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 6, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 5, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 5, 1, 0, tzinfo=tzlocal()), {        #Thur - Sukkot - 1:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 6, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 6, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 5, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 5, 2, 0, tzinfo=tzlocal()), {        #Thur - Sukkot - 2:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 6, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 6, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 7, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 6, 1, 0, tzinfo=tzlocal()), {        #Fri - Sukkot - 1:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 6, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 6, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 7, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 6, 2, 0, tzinfo=tzlocal()), {        #Fri - Sukkot - 2:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 11, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 11, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 7, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 7, 1, 0, tzinfo=tzlocal()), {        #Sha- Sukkot - 1:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 11, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 11, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 7, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 7, 2, 0, tzinfo=tzlocal()), {        #Sha- Sukkot - 2:00
            self.sun: datetime.datetime          (2017, 10, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),     #delayed due to Erev Sukkot
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 11, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 11, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 12, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})


        self.validate_schedule(datetime.datetime (2017, 10, 11, 1, 0, tzinfo=tzlocal()), {        #Wed- Erev Simchat Torah - 1:00
            self.sun: datetime.datetime          (2017, 10, 15, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 16, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 17, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 11, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 11, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 11, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 12, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 11, 2, 0, tzinfo=tzlocal()), {        #Wed- Erev Simchat Torah - 2:00
            self.sun: datetime.datetime          (2017, 10, 15, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 16, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 17, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 13, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 13, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 13, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 12, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 12, 1, 0, tzinfo=tzlocal()), {        #Thu- Simchat Torah - 1:00
            self.sun: datetime.datetime          (2017, 10, 15, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 16, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 17, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 13, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 13, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 13, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 12, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 12, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2017, 10, 12, 2, 0, tzinfo=tzlocal()), {        #Thu- Simchat Torah - 2:00
            self.sun: datetime.datetime          (2017, 10, 15, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2017, 10, 16, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2017, 10, 17, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2017, 10, 18, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2017, 10, 19, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2017, 10, 13, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2017, 10, 13, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2017, 10, 13, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2017, 10, 14, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2017, 10, 14, 1, 10, tzinfo=tzlocal())})


        self.validate_schedule(datetime.datetime (2018, 3, 29, 1, 0, tzinfo=tzlocal()), {        #Thu- Day before Erev Pesach - 1:00
            self.sun: datetime.datetime          (2018, 4, 1, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2018, 4, 2, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2018, 4, 3, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2018, 4, 4, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2018, 3, 29, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2018, 3, 30, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2018, 3, 30, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2018, 3, 30, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2018, 3, 31, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2018, 3, 31, 1, 10, tzinfo=tzlocal())})


        self.validate_schedule(datetime.datetime (2018, 4, 4, 1, 0, tzinfo=tzlocal()), {        #Wed- Day before Erev Pesach II - 1:00
            self.sun: datetime.datetime          (2018, 4, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2018, 4, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2018, 4, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2018, 4, 4, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2018, 4, 12, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2018, 4, 5, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2018, 4, 5, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2018, 4, 5, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2018, 4, 6, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2018, 4, 6, 1, 10, tzinfo=tzlocal())})


        self.validate_schedule(datetime.datetime (2018, 4, 6, 1, 0, tzinfo=tzlocal()), {        #Fri- Pesach II - 1:00
            self.sun: datetime.datetime          (2018, 4, 8, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2018, 4, 9, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2018, 4, 10, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2018, 4, 11, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2018, 4, 12, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2018, 4, 6, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2018, 4, 6, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2018, 4, 13, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2018, 4, 6, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2018, 4, 6, 1, 10, tzinfo=tzlocal())})


        self.validate_schedule(datetime.datetime (2018, 5, 19, 1, 0, tzinfo=tzlocal()), {        #Sha- Erev Shavuot - 1:00
            self.sun: datetime.datetime          (2018, 5, 27, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2018, 5, 21, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2018, 5, 22, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2018, 5, 23, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2018, 5, 24, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2018, 5, 19, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2018, 5, 19, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2018, 5, 25, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2018, 5, 19, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2018, 5, 19, 1, 10, tzinfo=tzlocal())})

        self.validate_schedule(datetime.datetime (2018, 5, 19, 2, 0, tzinfo=tzlocal()), {        #Sha- Erev Shavuot - 2:00
            self.sun: datetime.datetime          (2018, 5, 27, 1, 1, tzinfo=tzlocal()),
            self.mon: datetime.datetime          (2018, 5, 21, 1, 2, tzinfo=tzlocal()),
            self.tue: datetime.datetime          (2018, 5, 22, 1, 3, tzinfo=tzlocal()),
            self.wed: datetime.datetime          (2018, 5, 23, 1, 4, tzinfo=tzlocal()),
            self.thu: datetime.datetime          (2018, 5, 24, 1, 5, tzinfo=tzlocal()),
            self.fri: datetime.datetime          (2018, 5, 25, 1, 6, tzinfo=tzlocal()),
            self.fri_no_sukkot: datetime.datetime(2018, 5, 25, 1, 7, tzinfo=tzlocal()),
            self.sec_fri: datetime.datetime      (2018, 5, 25, 1, 8, tzinfo=tzlocal()),
            self.sha: datetime.datetime          (2018, 5, 20, 1, 9, tzinfo=tzlocal()),
            self.sha_no_sukkot: datetime.datetime(2018, 5, 20, 1, 10, tzinfo=tzlocal())})

    def validate_schedule(self, date, expected_schedule_dates):
        count = 0
        for schedule in Schedule.objects.all():
            count += 1
            schedule_time = schedule._prepare_next(date)
            print('schedule for date: %s, schedule: %s, schedule_time: %s, expected_date: %s' % (date, schedule, schedule_time, expected_schedule_dates[schedule]))
            self.assertEqual(schedule_time, expected_schedule_dates[schedule])
        self.assertEqual(count, len(expected_schedule_dates))

    def Xtest_bitmask_char(self):

        def test_chars_bitmasks():
            from common.utils import chars_to_bitmask, bitmask_to_chars
            i = 0
            while True:
                binary1 = bin(i)[2:]
                chars_of_4 = (len(binary1) // 32 + 1)
                binary = binary1.zfill(chars_of_4 * 32)
                if i % 10000 == 0:
                    print(i, chars_of_4, '"' + binary + '"')
                if chars_to_bitmask(bitmask_to_chars(binary)) != binary:
                    print('ERROR')
                    print('"' + bitmask_to_chars(binary) + '"')
                    print('"' + chars_to_bitmask(bitmask_to_chars(binary)) + '"')
                    print(binary, i)
                    return
                i += 1

        test_chars_bitmasks()

    def Xtest_bitmask_int(self):

        def test_chars_bitmasks():
            #from common.utils import bitmask_to_int
            #i = pow(2,64)-1000
            #i = pow(2,32)-1000
            #i = pow(2,16)-1000
            i = 0
            while True:
                binary1 = bin(i)[2:]
                chars_of_4 = (len(binary1) // 32 + 1)
                binary = binary1.zfill(chars_of_4 * 32)
                if i % 10000 == 0:
                    print(i, chars_of_4, len(binary.lstrip('0')), '"' + binary + '"')
                if bitmask_to_int(binary) != i:
                    print('ERROR')
                    print('ERROR', binary, i)
                    print('ERROR', bitmask_to_int(binary))
                    return
                i += 1
                #if i > 158456325028528675187087900672:
                if i > 79228162514264337593543950336+1000:
                    print('END!!!')
                    return

        test_chars_bitmasks()


    # def old_test_schedule_runs(self):
    #     self.validate_schedule(datetime.date(2017, 9, 19), [self.tue])  #Day before Erev Rosh Hashana
    #     self.validate_schedule(datetime.date(2017, 9, 20), [self.sec_fri, self.fri, self.fri_no_sukkot])  #Erev Rosh Hashana
    #
    #     self.validate_schedule(datetime.date(2017, 9, 21), [self.sha, self.sha_no_sukkot, self.fri, self.fri_no_sukkot])  #Rosh Hashana
    #     self.validate_schedule(datetime.date(2017, 9, 22), [self.sha, self.sha_no_sukkot, self.fri, self.fri_no_sukkot])  #Rosh Hashana
    #     self.validate_schedule(datetime.date(2017, 9, 23), [self.sha, self.sha_no_sukkot])  #Shabbat after Hag
    #     self.validate_schedule(datetime.date(2017, 9, 24), [self.sun])  #Sunday
    #
    #     self.validate_schedule(datetime.date(2017, 9, 28), [self.thu]) #Thur
    #     self.validate_schedule(datetime.date(2017, 9, 29), [self.sec_fri, self.fri, self.fri_no_sukkot])  #Erev Shabbat/Kippur
    #     self.validate_schedule(datetime.date(2017, 9, 30), [self.sha, self.sha_no_sukkot])  #YomKippur & Shabbat
    #     self.validate_schedule(datetime.date(2017, 10, 1), [self.sun])  #Sunday
    #
    #     self.validate_schedule(datetime.date(2017, 10, 3), [self.tue])  #Tue
    #     self.validate_schedule(datetime.date(2017, 10, 4), [self.sec_fri, self.fri])  #Erev Sukkot
    #     self.validate_schedule(datetime.date(2017, 10, 5), [self.sha])  #Sukkot
    #     self.validate_schedule(datetime.date(2017, 10, 6), [self.sec_fri, self.fri])  #Fri Sukkot
    #     self.validate_schedule(datetime.date(2017, 10, 7), [self.sha])  #Sha Sukkot
    #     self.validate_schedule(datetime.date(2017, 10, 8), [self.sun])  #Sun
    #     self.validate_schedule(datetime.date(2017, 10, 9), [self.mon])  #Mon
    #     self.validate_schedule(datetime.date(2017, 10, 10), [self.tue])  #Tue
    #     self.validate_schedule(datetime.date(2017, 10, 11), [self.sec_fri, self.fri, self.fri_no_sukkot])  #Erev SimchatTorah
    #     self.validate_schedule(datetime.date(2017, 10, 12), [self.sha, self.sha_no_sukkot])  #SimchatTorah
    #     self.validate_schedule(datetime.date(2017, 10, 13), [self.sec_fri, self.fri, self.fri_no_sukkot])  #Fri
    #     self.validate_schedule(datetime.date(2017, 10, 14), [self.sha, self.sha_no_sukkot])  #Sha
    #     self.validate_schedule(datetime.date(2017, 10, 15), [self.sun])  #Sun
    #
    #     self.validate_schedule(datetime.date(2018, 3, 29), [self.thu])  #Thu
    #     self.validate_schedule(datetime.date(2018, 3, 30), [self.sec_fri, self.fri, self.fri_no_sukkot])  #Fri Erev Pesach
    #     self.validate_schedule(datetime.date(2018, 3, 31), [self.sha, self.sha_no_sukkot])  #Sha/Pesach
    #     self.validate_schedule(datetime.date(2018, 4, 1), [self.sun])   #Sun
    #     self.validate_schedule(datetime.date(2018, 4, 2), [self.mon])   #Mon
    #     self.validate_schedule(datetime.date(2018, 4, 3), [self.tue])   #Tue
    #     self.validate_schedule(datetime.date(2018, 4, 4), [self.wed])   #Wed
    #     self.validate_schedule(datetime.date(2018, 4, 5), [self.sec_fri, self.fri, self.fri_no_sukkot])   #Erev Hag
    #     self.validate_schedule(datetime.date(2018, 4, 6), [self.sha, self.sha_no_sukkot, self.fri, self.fri_no_sukkot])   #Hag Sheini
    #     self.validate_schedule(datetime.date(2018, 4, 7), [self.sha, self.sha_no_sukkot])   #Sha
    #     self.validate_schedule(datetime.date(2018, 4, 8), [self.sun])   #Sun
    #
    #     self.validate_schedule(datetime.date(2018, 5, 17), [self.thu])   #Thu
    #     self.validate_schedule(datetime.date(2018, 5, 18), [self.sec_fri, self.fri, self.fri_no_sukkot])   #Fri
    #     self.validate_schedule(datetime.date(2018, 5, 19), [self.sha, self.sha_no_sukkot, self.fri, self.fri_no_sukkot])   #Sha
    #     self.validate_schedule(datetime.date(2018, 5, 20), [self.sha, self.sha_no_sukkot])   #Shavuot
    #     self.validate_schedule(datetime.date(2018, 5, 21), [self.mon])   #Mon
    #
    #     self.validate_schedule(datetime.date(2018, 9, 6), [self.thu])    #Thu
    #     self.validate_schedule(datetime.date(2018, 9, 7), [self.sec_fri, self.fri, self.fri_no_sukkot])    #Fri
    #     self.validate_schedule(datetime.date(2018, 9, 8), [self.sha, self.sha_no_sukkot])    #Sha
    #     self.validate_schedule(datetime.date(2018, 9, 9), [self.sec_fri, self.fri, self.fri_no_sukkot])    #Erev RoshHashana
    #     self.validate_schedule(datetime.date(2018, 9, 10), [self.sha, self.sha_no_sukkot, self.fri, self.fri_no_sukkot])   #RoshHashana
    #     self.validate_schedule(datetime.date(2018, 9, 11), [self.sha, self.sha_no_sukkot])   #RoshHashana
    #     self.validate_schedule(datetime.date(2018, 9, 12), [self.wed])   #Wed
    #
    #     self.validate_schedule(datetime.date(2018, 9, 17), [self.mon])   #Mon
    #     self.validate_schedule(datetime.date(2018, 9, 18), [self.sec_fri, self.fri, self.fri_no_sukkot])   #Erev YomKippur
    #     self.validate_schedule(datetime.date(2018, 9, 19), [self.sha, self.sha_no_sukkot])   #YomKippur
    #     self.validate_schedule(datetime.date(2018, 9, 20), [self.thu])   #Thur
    #     self.validate_schedule(datetime.date(2018, 9, 21), [self.sec_fri, self.fri, self.fri_no_sukkot])   #Fri
    #     self.validate_schedule(datetime.date(2018, 9, 22), [self.sha, self.sha_no_sukkot])   #Sat
    #     self.validate_schedule(datetime.date(2018, 9, 23), [self.sec_fri, self.fri])   #Erev Sukkot
    #     self.validate_schedule(datetime.date(2018, 9, 24), [self.sha])   #Sukkot
    #     self.validate_schedule(datetime.date(2018, 9, 25), [self.tue])   #Tue
    #     self.validate_schedule(datetime.date(2018, 9, 26), [self.wed])   #Wed
    #     self.validate_schedule(datetime.date(2018, 9, 27), [self.thu])   #Thu
    #     self.validate_schedule(datetime.date(2018, 9, 28), [self.sec_fri, self.fri])   #Fri
    #     self.validate_schedule(datetime.date(2018, 9, 29), [self.sha])   #Sha Sukkot
    #     self.validate_schedule(datetime.date(2018, 9, 30), [self.sec_fri, self.fri, self.fri_no_sukkot])   #Erev SimchatTorah
    #     self.validate_schedule(datetime.date(2018, 10, 1), [self.sha, self.sha_no_sukkot])   #SimchatTorah
    #     self.validate_schedule(datetime.date(2018, 10, 2), [self.tue])   #Tue
    #
    # def validate_schedule_runs_old(self, date, expected_schedules):
    #     ScheduleRun.objects.prepare_runs_for_date(date)
    #     actual_ids = []
    #     for run in ScheduleRun.objects.all():
    #         actual_ids = actual_ids + [run.schedule.id]
    #         print(run)
    #     if len(expected_schedules) == 1:
    #         expected_schedules = [expected_schedules[0],]
    #     self.assertEqual(sorted(actual_ids), sorted(list(map(lambda x: x.id, expected_schedules))))       #extract the expected ids and sort them
    #     ScheduleRun.objects.all().delete()
    #
