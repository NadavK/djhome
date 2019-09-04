from redis import Redis
from rq_scheduler import Scheduler

from common.jewish_dates.holidays import get_hag_and_shabbat
from common.jewish_dates.jtimes import sunrise_sunset
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import datetime, time, timedelta
from dateutil.tz import tzlocal
from ios.models import Output
import schedules.managers as managers
from struct import *            # for pack
import pytz
import logging

#class time_validator = models.CharField(
#    max_length=6,
#    # required=True,
#    validators=[
#        RegexValidator(
#            regex='-?\d{1,2}:\d{1,2}',
#            message='Comply to +/-HH:MM',
#        ),
#    ]
#)
from ios.tasks import set_output_state_from_schedule


def time_validator(value):
    if value != '123':
        raise ValidationError(
            '%(value)s must be 123',
            params={'value': value},
        )


class HappyDays:
    '''
    Helper class that holds date data for yesterday and today
    '''

    def __init__(self, date):
        #self.logger = logging.getLogger(self.__class__.__name__)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self.today = get_hag_and_shabbat(date)
        self.tomorrow = get_hag_and_shabbat(date + timedelta(days=1))
        # self.yesterday = get_hag_and_shabbat(now - datetime.timedelta(days=1))

        self.friday = self.tomorrow  # tomorrow is hag/shabbat. this can occur together with shabbat/hag
        self.secular_friday = self.tomorrow and not self.today  # tomorrow=hag/shabbat and today is not
        self.shabbat = self.today  # today=hag/shabbat. this can occur together with fri/erev
        self.sukkot = 'Sukkot' in (self.today, self.tomorrow)  # today or tomorrow=hag/shabbat of Sukkot

        self.logger.debug(
            "date: %s, today='%s', tomorrow='%s', friday='%s', secular_friday='%s', shabbat='%s', sukkot='%s'" % (
            date, self.today, self.tomorrow, self.friday, self.secular_friday, self.shabbat, self.sukkot))


# Create your models here.
class Schedule(models.Model):
    objects = managers.ScheduleManager()
    type = 'Schedule'

    RELATIVE_TYPE_ABSOLUTE = 0
    RELATIVE_TYPE_SUNRISE = 1
    RELATIVE_TYPE_SUNSET = 2
    RELATIVE_TYPES = (
        (RELATIVE_TYPE_ABSOLUTE, 'Absolute'),
        (RELATIVE_TYPE_SUNRISE, 'Sunrise'),
        (RELATIVE_TYPE_SUNSET, 'Sunset'),
    )
    #XXX_INPUT_TYPES = (
    #    (INPUT_TYPE_TOGGLE, 'Toggle', 'Toggle (click) on/off switch for A/C & lights'),
    #    (INPUT_TYPE_PUSH, 'Push', 'Push button (on when held) for blinds, door, water-drips & dimmer'),
    #    (INPUT_TYPE_MAGNET, 'Magnet', 'Alarm Magnet'),
    #    (INPUT_TYPE_SONIC, 'Sonic', 'Sonic movement detector'),
    #)


    sun = models.BooleanField()
    mon = models.BooleanField()
    tue = models.BooleanField()
    wed = models.BooleanField()
    thu = models.BooleanField()
    fri = models.BooleanField(help_text='Erev-Shabbat/Hag, also if it falls on Hag/Shabbat itself (erev 2nd day)')
    sha = models.BooleanField(help_text='Shabbat/Hag')
    but_only_secular_fri = models.BooleanField(verbose_name='secular', help_text='Fri/Erev-Hag, but not on Shabbat/Hag itself (not on erev 2nd day)')
    but_not_sukkot = models.BooleanField(help_text='Will not be enabled on Sukkot Fri/Shabbat/Hag')


    #first_erev = models.BooleanField(help_text='Will be enabled on Fri/Erev-Hag but not on Shabbat/Hag itself')
    #any_erev = models.BooleanField(help_text='Will be enabled on Fri/Erev-Hag and also on Shabbat/Hag itself')


    # think of the a/c in the bedrooms: we want it to come on fri-night, but not sat-night, unless sat-night itself is erev hag
    # also, we want the kitchen light to turn off Fri morning at 1:00, but on first-day-hag (which is also Fri since there is a second hag) it should stay on all day
    # OTOH, we want the windows to come up early Fri morning, but later on Sha/Hag


    time_reference = models.IntegerField(choices=RELATIVE_TYPES, default=RELATIVE_TYPE_ABSOLUTE)
    #time = models.CharField(max_length=6, validators=[time_validator])
    time = models.CharField(max_length=6, validators=[
        RegexValidator(regex='^[-+]?\d{1,2}:\d{1,2}$', message='Comply to +/-HH:MM',)
    ])

    output = models.ForeignKey(Output, on_delete=models.CASCADE, related_name='schedules')

    turn_on = models.BooleanField(help_text='Turn on the output (leave blank to turn off)')
    target_position = models.IntegerField(blank=True, null=True, help_text='For blinds, what position the blinds should reach, where 0 is full-down and 100 is full-up')
    active = models.BooleanField(default=True, help_text='Disable temporarily')
    deleted = models.BooleanField(default=False, help_text='Delete permanently')
    description = models.TextField(blank=True)
    updated = models.DateTimeField(auto_now=True)
    task_id = models.CharField(blank=True, max_length=36)

    # class Meta:
    #    index_together = [["ph_sn", "ph_index"], ]
    #    permissions = (
    #        ('view_output', 'View Output'),
    #    )

    def __str__(self):
        return "Schedule (#%s): Output %s at %s (%s) - %s" % (self.id, self.output, self.time, self.get_time_reference_display(), self.turn_on_display())

    def __init__(self, *args, **kwargs):
        super(Schedule, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def turn_on_display(self):
        return 'On' if self.turn_on else 'Off'
    turn_on_display.short_description = 'Action'
    turn_on_display.admin_order_field = 'turn_on'  # Allows column order sorting

    def output_desc(self):
        return self.output.description
    output_desc.short_description = 'Output'
    output_desc.admin_order_field = 'pk'  # Allows column order sorting


    #def clean(self):
    #    if len(self.time) < 4:
    #        raise ValidationError('invalid time')

    @property
    def valid(self):
        return self.active and not self.deleted

    '''Finds next schedule time - should only be called by save() [does not call save()]'''
    def next_datetime(self, now=0, info_only=False, for_next_time=False):
        '''
        if self.task_id and not info_only:
            try:
                #Note: Revoke doesn't actually delete the task...
                self.logger.info('Revoking schedule [task_id=%s] - %s', self.task_id, self)
                from djhome.celery import app
                from celery.bin.control import inspect
                print(inspect.query_task([self.task_id]))
                app.control.revoke(self.task_id)
                self.task_id = ''
            except:
                pass
        '''

        #set the next schedule run
        #if not self.valid:        #     The next run should be set even if the schedule is invalid, so that when the schedule becomes valid it will have a next-run (valid can be set via admin bulk update which does not call save)
        #    return

        if not self.sha and not self.fri and not self.thu and not self.wed and not self.tue and not self.mon and not self.sun:
            return

        if not now:
            now = datetime.now(tzlocal())
        today = now.date()

        for days in range(1 if for_next_time else 0, 99):                   # Not sure can-happen/what-happens if cannot find schedule for next 99 days...
            date = today + timedelta(days=days)
            suntimes = sunrise_sunset(date)  # [0] for sunrise, [1] for sunset
            days_data = HappyDays(date)
            dow = date.weekday()
            if days_data.shabbat and self.sha or days_data.friday and self.fri or \
                not days_data.shabbat and not days_data.friday and (
                        dow == 3 and self.thu or
                        dow == 2 and self.wed or
                        dow == 1 and self.tue or
                        dow == 0 and self.mon or
                        dow == 6 and self.sun):
                    if days_data.friday and not days_data.secular_friday and self.but_only_secular_fri:
                        self.logger.info('Schedule not enabled on secular_fri: %s -  %s', date, self)
                    elif days_data.sukkot and self.but_not_sukkot:
                        self.logger.info('Schedule %s not enabled on Sukkot', self)
                    else:
                        time_str = self.time.split(':')
                        hour = int(time_str[0])
                        minute = int(time_str[1])
                        minutes = hour * 60 + minute  # used for relative schedule
                        if self.time[0] == '-' and minutes >= 0:  # the hour can be 0 which negates the minus sign, so specifically check and set negative time
                            minutes = -abs(minutes)
                        if self.time_reference in [self.RELATIVE_TYPE_SUNRISE, self.RELATIVE_TYPE_SUNSET]:
                            suntime = suntimes[0] if self.time_reference == self.RELATIVE_TYPE_SUNRISE else suntimes[1]
                            schedule_datetime = datetime.combine(date, time(hour=suntime.hour, minute=suntime.minute, tzinfo=tzlocal())) + timedelta(minutes=minutes)
                        else:
                            schedule_datetime = datetime.combine(date, time(hour, minute, tzinfo=tzlocal()))

                        if schedule_datetime < now:
                            self.logger.info('Today\'s (%s) schedule is past (%s), looking for tomorrow\'s schedule - %s: ', schedule_datetime, now, self)
                        else:
                            if not info_only:
                                scheduler = Scheduler(connection=Redis())  # Get a scheduler for the "default" queue
                                job = scheduler.enqueue_at(func=set_output_state_from_schedule, args=(self.pk, Schedule.type, self.turn_on, self.target_position), scheduled_time=schedule_datetime.astimezone(pytz.utc))
                                self.task_id = job.id
                                self.logger.info('Defined schedule time %s [task_id=%s]: %s', schedule_datetime, self.task_id, self)
                            else:
                                self.logger.info('Next schedule time %s: %s', schedule_datetime, self)
                            return schedule_datetime


    '''wrapper function to prepare next schedule (instead of calling save)'''
    def prepare_next_schedule(self, **kwargs):
        self.save(**kwargs)

    '''Every save also prepares the next schedule'''
    def save(self, **kwargs):

        #import inspect
        #curframe = inspect.currentframe()
        #calframe = inspect.getouterframes(curframe, 2)
        #self.logger.debug('caller name: %s' % calframe[1][3])

        for_next_time = kwargs.pop('for_next_time', None)
        info_only = kwargs.pop('info_only', None)
        if for_next_time:
            self.logger.info('for_next_time: %s', for_next_time)
        if info_only:
            self.logger.info('info_only: %s', info_only)
        #self.clean()
        self.full_clean()           #I think this is needed to test RegexValidator
        self.logger.debug('Saving %s' % self)
        self.next_datetime(for_next_time=for_next_time, info_only=info_only)

        if info_only:
            return
        return super(Schedule, self).save(**kwargs)


# Create your models here.
class OnetimeSchedule(models.Model):
    """
    A Onetime Schedule is active for a specific day.
    Each 15 minute segment can be turned on/off (default off)
    """
    objects = managers.OneTimeScheduleManager()
    type = 'OnetimeSchedule'

    date = models.DateField()                                   # the date this schedule is valid from
    start = models.TimeField(help_text='Schedule will only be valid from this time')  # the start_time this schedule is valid from
    end = models.TimeField(help_text='Schedule will only be valid until this time')   # the end time this schedule is valid from. must be same date as start
    segments = models.CharField(max_length=96, validators=[RegexValidator(regex='^.{96}$', message='Length has to be 96', code='nomatch')], default='0'*96)   # 24 hours * 4 segments-per-hour = 96 bits = 12 * 8 bits

    output = models.ForeignKey(Output, on_delete=models.CASCADE, related_name='onetime_schedules', unique_for_date="date")

    active = models.BooleanField(default=True, help_text='Disable temporarily')
    deleted = models.BooleanField(default=False, help_text='Delete permanently')
    description = models.TextField(blank=True)
    updated = models.DateTimeField(auto_now=True)
    task_id = models.CharField(blank=True, max_length=36)

    # class Meta:
    #    index_together = [["ph_sn", "ph_index"], ]
    #    permissions = (
    #        ('view_output', 'View Output'),
    #    )

    def __str__(self):
        return "OnetimeSchedule (#%s): Output %s, from %s %s - %s: %s" % (self.id, self.output, self.date, self.start, self.end, self.get_segments_display())

    def __init__(self, *args, **kwargs):
        super(OnetimeSchedule, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def clean(self):
        if self.start > self.end:
            raise ValidationError('End time must be later than start time')

    '''returns a bitmask string of 96 chars: 0/1'''
    def get_segments_display(self):
        return self.segments
        #return chars_to_bitmask(self.segments)

    '''expects 12 characters (each char is 8 bits)'''
    def set_segments(self, bitmask):
        self.segments = bitmask
        #self.segments = bitmask_to_chars(bitmask)

    @property
    def valid(self):
        return self.active and not self.deleted

    @property
    def start_date(self):
        return datetime.combine(self.date, self.start.replace(tzinfo=tzlocal()))

    @property
    def end_date(self):
        return datetime.combine(self.date, self.end.replace(tzinfo=tzlocal()))

    def _prepare_next(self, now=0, info_only=False, for_next_time=False):
        '''
        Finds next schedule time - should only be called by save() [does not call save()]
        :param now:
        :param info_only:    does not create actual celery schedule
        :param for_next_time:   Will find the next schedule to create (based on next 15-minute segment from now)
        :return:    scheduled_date and scheduled_state (bool)
        '''
        if self.task_id:
            try:
                #from djhome.celery import app
                #app.control.revoke(self.task_id)
                self.task_id = ''
            except:
                pass

        def time_to_seg_index(t):
            return t.hour * 4 + t.minute // 15

        def get_seg(index):
            if index > 95:
                raise IndexError
            return self.segments[index:index+1] == '1'

        def hour_minute_to_seg(hour, minute):
            return hour * 4 + minute // 15

        def seg_index_to_time(seg):
            seg_hours = seg // 4
            seg_minutes = (seg - seg_hours * 4) * 15
            return seg_hours, seg_minutes

        #set the next schedule run
        if not self.valid:
            self.logger.warning('OnetimeSchedule is invalid (%s, %s) - %s', self.active, self.deleted, self)
            return

        #if all(c == '0' for c in self.segments):     # no schedule if segments is empty
        #    #UNLESS IT IS CURRENTLY ON AND NEEDS TO BE SHUT OFF
        #    return

        if not now:
            now = datetime.now(tzlocal())

        if now.date() != self.date:
            self.logger.error('OnetimeSchedule for_next_time has bad now.date (%s!=%s), re-scheduling - %s', now.date(), self.date, self)
        elif for_next_time:                                       # we assume that this is called after the initial OneTimeSchedule segment schedule, and we now look for the next time with a different on/off state
            try:
                current_state = get_seg(time_to_seg_index(now))
            except IndexError:
                return
            next_state = current_state
            while current_state == next_state:
                minutes_to_next_segment = 15 - now.time().minute % 15         # minutes to next segment
                now += timedelta(minutes=minutes_to_next_segment)
                if now.date() != self.date:
                    self.logger.info('OnetimeSchedule has no more scheduled changes for %s - %s', self.date, self)
                    return
                try:
                    next_state = get_seg(time_to_seg_index(now))
                except IndexError:
                    return

            self.logger.info('OnetimeSchedule next time has been adjusted to: %s - %s', now, self)

        if now <= self.start_date:
            schedule_datetime = self.start_date
        elif self.end_date >= now >= self.start_date:
            schedule_datetime = now
        else:   # now.time() > self.end which means schedule has finished
            self.logger.info('OnetimeSchedule time %s has passed - %s ', self.end_date, self)
            return

        seg_index = time_to_seg_index(schedule_datetime)               # this is the segment for the next schedule run
        on = get_seg(seg_index)

        if info_only:
            self.logger.info('Onetime Schedule for %s (seg_index %s) %s - %s ', schedule_datetime, seg_index, 'on' if on else 'off', self)
        else:
            scheduler = Scheduler(connection=Redis())  # Get a scheduler for the "default" queue
            job = scheduler.enqueue_at(func=set_output_state_from_schedule, args=(self.pk, OnetimeSchedule.type, on, None), scheduled_time=schedule_datetime.astimezone(pytz.utc))
            self.task_id = job.id
            self.logger.info('Defining schedule for %s (seg_index %s): %s [task_id=%s] - %s', schedule_datetime, seg_index, 'on' if on else 'off', self.task_id, self)
        return schedule_datetime, on

    '''wrapper function to prepare next schedule (instead of calling save)'''
    def prepare_next_schedule(self, **kwargs):
        self.save(**kwargs)

    '''Every save also prepares the next schedule'''
    def save(self, **kwargs):
        for_next_time = kwargs.pop('for_next_time', None)
        info_only = kwargs.pop('info_only', None)
        if for_next_time:
            self.logger.info('for_next_time: %s', for_next_time)
        if info_only:
            self.logger.info('info_only: %s', info_only)
        #self.clean()
        self.full_clean()           #I think this is needed to test RegexValidator

        if not self.pk:
            super(OnetimeSchedule, self).save(**kwargs)                               # _prepare_next requires self.pk
        self._prepare_next(for_next_time=for_next_time, info_only=info_only)
        #force_update = False,
        kwargs['force_insert'] = False
        super(OnetimeSchedule, self).save(**kwargs)                                   # And save again the new values from _prepate_next

    def output_desc(self):
        return self.output.description
    output_desc.short_description = 'Output'
    output_desc.admin_order_field = 'pk'  # Allows column order sorting
