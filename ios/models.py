from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
import json
from log_request_id import local
from log_request_id.middleware import RequestIDMiddleware
import logging
from pytz import utc
from redis import Redis
import requests
from requests import Session
from rq_scheduler import Scheduler
import subprocess
from taggit.managers import TaggableManager
from taggit.models import TaggedItem, TaggedItemBase, GenericTaggedItemBase, TagBase

import ios.managers as managers
from ios.tasks import set_output_state_from_delay
from .consumers import IOConsumer


class Device(models.Model):
    objects = managers.DeviceManager()

    SET_DEFAULT_OUTPUTS = '{host}/default_outputs/{sn}'     # Sets default state for all outputs
    SET_OUTPUT = '{host}/output/{sn}/{output}/{state}'      # Sets state for specific output
    GET_OUTPUTS_STATE = '{host}/states'                     # Trigger device to return all states (states are returned in separate responses)

    description = models.CharField(max_length=255)
    sn = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return "%s (#%s)" % (self.description, self.id)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def get_request_id(self, request_id=None, prefix=''):
        # prepare request_id
        if getattr(local, 'request_id', None):
            self.need_to_del_local_request_id = False
        else:
            self.need_to_del_local_request_id = True
            local.request_id = request_id or (prefix + RequestIDMiddleware()._generate_id())
        return local.request_id

    def clear_request_id(self):
        if self.need_to_del_local_request_id:
            delattr(local, 'request_id')

    def set_default_outputs(self, states, request_id=None):
        try:
            request_id = self.get_request_id(request_id, 'wsgi_setDefaultStates_')
            #TODO: Why using session? Is it kept open? should it be a member variable?

            url = self.SET_DEFAULT_OUTPUTS.format(host=self.host, sn=self.sn)
            self.logger.warning('Calling Device: POST %s, output mask: "%s"', url, states)
            Session().post(url, json={'states': states},
                           headers={settings.LOG_REQUEST_ID_HEADER: request_id}).raise_for_status()
        except Exception:
            self.logger.exception('Calling Device set_default_outputs')
            # TODO: Should retry
        finally:
            self.clear_request_id()

    def trigger_get_states(self, request_id=None):
        try:
            request_id = self.get_request_id(request_id, 'wsgi_get_states_')
            url = self.GET_OUTPUTS_STATE.format(host=self.host)          # this is a per-host call, no sn
            self.logger.warning('Calling Device: Trigger get states: %s"', url)
            Session().get(url, headers={settings.LOG_REQUEST_ID_HEADER: request_id}).raise_for_status()
            return True
        except requests.exceptions.RequestException as e:  # catch all requests exception
            self.logger.error(e)
        except Exception as ex:
            self.logger.exception('Calling Device trigger_get_states')
        finally:
            self.clear_request_id()
        return False

    def set_output_state(self, output_id, state):
        try:
            request_id = self.get_request_id()
            url = self.SET_OUTPUT.format(host=self.host, sn=self.sn, output=output_id, state=json.dumps(state))
            requests.post(url, json={}, headers={settings.LOG_REQUEST_ID_HEADER: request_id}).raise_for_status()
        finally:
            self.clear_request_id()
        return request_id


class Input(models.Model):
    objects = managers.InputManager()

    INPUT_TYPE_TOGGLE = 1
    INPUT_TYPE_PUSH = 2
    INPUT_TYPE_MAGNET = 3
    INPUT_TYPE_SONIC = 4
    INPUT_TYPES = (
        (INPUT_TYPE_TOGGLE, 'Toggle'),
        (INPUT_TYPE_PUSH, 'Push'),
        (INPUT_TYPE_MAGNET, 'Magnet'),
        (INPUT_TYPE_SONIC, 'Sonic'),
    )
    XXX_INPUT_TYPES = (
        (INPUT_TYPE_TOGGLE, 'Toggle', 'Toggle (click) on/off switch for A/C & lights'),
        (INPUT_TYPE_PUSH, 'Push', 'Push button (on when held) for blinds, door, water-drips & dimmer'),
        (INPUT_TYPE_MAGNET, 'Magnet', 'Alarm Magnet'),
        (INPUT_TYPE_SONIC, 'Sonic', 'Sonic movement detector'),
    )

    device = models.ForeignKey(Device, blank=True, null=True, on_delete=models.PROTECT)
    index = models.IntegerField(verbose_name='Index-ID on device')            # Input Index-ID on the device
    # input_type = models.ForeignKey(InputType, on_delete=models.PROTECT)
    input_type = models.IntegerField(choices=INPUT_TYPES)
    deleted = models.BooleanField(default=False)
    description = models.CharField(max_length=255)
    outputs = models.ManyToManyField('Output', through='InputToOutput', related_name='inputs')
    tags = TaggableManager(blank=True)
    # permissions = TaggableManager(through=TaggedInputPermissions)
    # permissions.rel.related_name = "+"
    # state = models.NullBooleanField(db_column='state', blank=True, null=True, default=None)         #We don't save state between sessions - it's used to save state within the session (are cleared on load)
    state = models.BooleanField(db_column='state', blank=True, null=True,
                                default=None)  # We don't save state between sessions - it's used to save state within the session (are cleared on load)

    class Meta:
        unique_together = (('device', 'index'),)
        index_together = [["device", "index"], ]
        # permissions = (
        #    ('view_input', 'View Input'),
        # )

    def __str__(self):
        return "Input: %s (#%s, %s [%s, %s])" % (
            self.description, self.id, self.get_input_type_display(), self.device.description, self.index)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def on_state_change(self, state, user):
        # from ios.consumers import ActionConsumer

        try:
            self.state = state = bool(state)
            self.save()

            self.logger.debug("OnInputChange %s, state: %s (%s)" % (self, state, user))
            trigger = TriggerAudit.objects.model.create_from_input(input=self)
            IOConsumer.send_io_changed(self)  # Update clients that input has changed

            # retrieve valid outputs (outputs that are not deleted)
            # I don't know how to get the valid output instance without the i2o instance
            for i2o in InputToOutput.valid_objects.filter(input=self):
                output = i2o.output
                if self.input_type == Input.INPUT_TYPE_TOGGLE:
                    if state:
                        self.logger.debug("%s is %s, setting to %s" % (output, output.state, not output.state))
                        output.state = not output.state
                    else:
                        self.logger.debug("Input state false - not changing output")
                elif self.input_type == Input.INPUT_TYPE_PUSH:
                    self.logger.debug("Setting %s to %s" % (output, state))
                    output.state = state
                elif self.input_type == Input.INPUT_TYPE_MAGNET:
                    if output.output_type == Output.OUTPUT_TYPE_ALARM:
                        output_state = not InputToOutput.valid_objects.filter(output=output, input__state=False).exists()
                        self.logger.debug("Setting %s to %s" % (output, output_state))
                        output.state = output_state
                elif self.input_type == Input.INPUT_TYPE_SONIC:
                    self.logger.debug("Setting %s to %s" % (output, state))
                    output.state = state
                else:
                    self.logger.error("Not supported self.input_type %s (%s)" % (self.input_type, output))

                OutputAudit.objects.model.create(trigger=trigger, output=output)

        except Exception:
            self.logger.exception('')


class Cue(TagBase):
    class Meta:
        verbose_name = "Cue"
        verbose_name_plural = "Cues"
        app_label = 'taggit'


class CuedItem(GenericTaggedItemBase, TaggedItemBase):
    class Meta:
        verbose_name = "Cued Item"
        verbose_name_plural = "Cued Items"
        app_label = "taggit"
        index_together = [["content_type", "object_id"]]
        unique_together = [["content_type", "object_id", "tag"]]

    tag = models.ForeignKey(
        Cue,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )


class Output(models.Model):
    objects = managers.OutputManager()

    OUTPUT_TYPE_REGULAR = 1
    OUTPUT_TYPE_ALARM = 2           # Difference to Regular is the color used in the GUI
    OUTPUT_TYPE_BLIND_UP = 3
    OUTPUT_TYPE_BLIND_DOWN = 4
    OUTPUT_TYPE_SCRIPT = 5          # Runs a bash script
    OUTPUT_TYPES = (
        (OUTPUT_TYPE_REGULAR, 'Relay'),
        (OUTPUT_TYPE_ALARM, 'Alarm'),
        (OUTPUT_TYPE_BLIND_UP, 'Blind Up'),
        (OUTPUT_TYPE_BLIND_DOWN, 'Blind Down'),
        (OUTPUT_TYPE_SCRIPT, 'Script'),
    )

    DEFAULT_STATE_TYPE_OFF = 0
    DEFAULT_STATE_TYPE_ON = 1  # TODO: NOT TESTED
    DEFAULT_STATE_TYPE_RESTORE_LAST = 2
    DEFAULT_STATE_TYPES = (
        (DEFAULT_STATE_TYPE_OFF, 'Off'),
        (DEFAULT_STATE_TYPE_ON, 'On'),
        (DEFAULT_STATE_TYPE_RESTORE_LAST, 'Restore last state'),
    )

    device = models.ForeignKey(Device, blank=True, null=True, on_delete=models.PROTECT)
    index = models.IntegerField(verbose_name='Index-ID on device')            # Output Index-ID on the device
    # output_type = models.ForeignKey(OutputType, on_delete=models.PROTECT)
    output_type = models.IntegerField(choices=OUTPUT_TYPES)
    nc = models.BooleanField(default=False, verbose_name="Normally-closed relay")  # Set true if output is connected to a normally-closed relay
    deleted = models.BooleanField(default=False)  # soft-delete
    description = models.CharField(max_length=255)

    execution_limit = models.IntegerField(blank=True, null=True)  # the total time this output should be on
    started_time = models.DateTimeField(blank=True, null=True)  # the time the output was turned on
    current_position = models.IntegerField(blank=True,
                                           default=0)  # the current progress state, in percent (updated when turned off)

    # total_progress = models.IntegerField(blank=True, null=True)                 #the total time this output should be on
    # progress_started = models.DateTimeField(blank=True, null=True)              #the time the output was turned on
    # current_progress = models.IntegerField(blank=True, null=True)               #the current progress state (updated when turned off)

    _my_state = models.BooleanField(db_column='state',
                                    default=False)  # True == switched-on            "_state" is an existing Django Model field
    default_state = models.IntegerField(choices=DEFAULT_STATE_TYPES, default=DEFAULT_STATE_TYPE_RESTORE_LAST)
    # off_delay_ms = models.IntegerField(default=0)                               #Set delay (milliseconds) until auto turn off
    # off_delay_initiated_time = models.IntegerField(default=0)                  #This is the time that the last auto-off was initiated. Used to filter out invalid async tasks (that have in the meantime been replaced with other tasks)
    task_id = models.CharField(blank=True, max_length=36)
    script = models.TextField(blank=True)  # Contains a bash script to execute
    toggle_off_output = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='+')  # toggle_off_output will be turned off when this output is turned on

    tags = TaggableManager(blank=True, through=TaggedItem)
    cues = TaggableManager(blank=True, through=CuedItem, verbose_name='Cues')

    supports_schedules = models.BooleanField(
        default=False)  # Helper flag for GUI, to know if this output supports schedules/onetimeschedules

    # permissions = TaggableManager(through=TaggedOutputPermissions)
    ##permissions.rel.related_name = "+"

    class Meta:
        unique_together = (('device', 'index'),)
        index_together = [["device", "index"], ]
        permissions = (
            # ('view_output', 'View Output'),
            ('add_onetimeschedule', 'Add OneTimeSchedule'),
        )

    def __str__(self):
        return "Output: %s (#%s, [%s, %s])" % (self.description, self.id, self.device.description if self.device else 'no device', self.index)

    def __init__(self, *args, **kwargs):
        super(Output, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    @property
    def state(self):
        return self._my_state

    @state.setter
    def state(self, state):
        return self.set_state(state)

    '''
    execution_limit can be set in ms or percentage
    '''
    def set_state(self, state, execution_limit_ms=0, target_position=None, user=None):
        # if delay_initiated_time and delay_initiated_time < self.off_delay_initiated_time:
        #    self.logger.debug("%s: Ignoring delay_initiated_time (%s) < self.off_delay_initiated_time (%s)" % (self, utils.ms_to_datetime(delay_initiated_time), utils.ms_to_datetime(self.off_delay_initiated_time)))
        #    return

        self.logger.debug("Setting %s, state: %s, execution_limit_ms: %s, target_position: %s" % (
            self, state, execution_limit_ms, target_position))

        if self.deleted:
            self.logger.warning('set_state - Output %s is deleted', self)

        try:
            if self.output_type == self.OUTPUT_TYPE_SCRIPT:
                if state:
                    self.logger.debug("Executing: %s" % (self.script))
                    p = subprocess.Popen(self.script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    if stdout:
                        self.logger.info(stdout)
                    if stderr:
                        self.logger.error(stderr)
                return

            if execution_limit_ms and target_position is not None:
                self.logger.error("execution_limit_ms and target_position cannot both be set: %s" % self)
                return
            elif target_position is not None:
                if self.output_type != Output.OUTPUT_TYPE_BLIND_UP:
                    self.logger.warning("target_position can only be set on Windows UP - ignoring: %s" % self)
                elif target_position == 100:
                    execution_limit_ms = self.execution_limit * 1.2  # Add 20% buffer
                elif target_position == 0:
                    execution_limit_ms = -self.execution_limit * 1.2  # Add 20% buffer
                else:
                    execution_limit_ms = (target_position - self.current_position) / 100 * self.execution_limit
            elif not execution_limit_ms and self.execution_limit:  # use self as the default execution_limit
                execution_limit_ms = self.execution_limit * 1.2  # Add 20% buffer

            if execution_limit_ms and state:  # TODO: consider moving this to set_state(). OTOH self is saved here and not in set_state()
                self.logger.debug("Setting execution_limit_ms %s: %s ms" % (self, execution_limit_ms))

                if execution_limit_ms < 0:  # Window should be lowered
                    self.toggle_off_output.set_state(True, execution_limit_ms=-execution_limit_ms)
                    return
                else:
                    scheduler = Scheduler(connection=Redis())  # Get a scheduler for the "default" queue
                    job = scheduler.enqueue_in(func=set_output_state_from_delay, args=(self.pk, False, None),
                                               time_delta=timedelta(milliseconds=execution_limit_ms))
                    self.task_id = job.id
                    self.started_time = datetime.now(utc)
                    self.save()
                    self.logger.debug("Set auto-off %s: %s ms (task_id=%s)" % (self, execution_limit_ms, self.task_id))
            elif not state:  # TODO: consider moving this to on_state_change().
                if self.output_type == Output.OUTPUT_TYPE_BLIND_UP:
                    output = self.toggle_off_output
                else:
                    output = self

                if self.execution_limit and self.started_time:
                    output.current_position = min(100, (
                                self.execution_limit / (datetime.now(utc) - self.started_time).total_seconds()) * 100)
                    output.save()
                    self.logger.debug("Updated current_position for %s: %s" % (self, self.current_position))

            if state and self.toggle_off_output:  # Turn of paired outputs (windows)
                self.toggle_off_output.set_state(False, user=None)

            # Call device service
            if self.nc:
                self.logger.debug("Sending device state %s for normally-closed output %s" % (not state, self))
                request_id = self.device.set_output_state(self.index, not state)
            else:
                request_id = self.device.set_output_state(self.index, state)

            if user:
                trigger = TriggerAudit.objects.model.create_from_user(user=user, state=state, request_id=request_id)
                OutputAudit.objects.model.create(trigger=trigger, output=self, request_id=request_id)

            # self._my_state = state      This is set in on_state_change
        except requests.exceptions.RequestException as e:  # catch all requests exception
            self.logger.exception(e)
        except Exception:
            self.logger.exception('')

    def on_state_change(self, state=None):
        from ios.consumers import IOConsumer

        try:
            # state is None when triggered by client (via receive_json>set_state_by_pk)
            # This is to send notification of current state, where client is out-of-sync and is setting to current state
            # which would normally not send a change-event (since nothing changed) and client will remain out-of-sync
            if state is None:
                self.logger.debug("on_state_change %s, state: %s (no change, just triggering notification)" % (self, state))
                state = self._my_state
            else:
                self.logger.debug("on_state_change %s, state: %s" % (self, state))
                if self.nc:
                    state = not state
                    self.logger.debug("on_state_change replacing device state to %s for normally-closed output %s" % (state, self))

                self._my_state = state  # calling self.state will cause the phidget to change again
                # if self.execution_limit and state:     #TODO: consider moving this to set_state(). OTOH self is saved here and not in set_state()
                #    self.logger.debug("Setting auto-off %s: %s ms" % (self, self.off_delay_ms))
                #    #self.off_delay_initiated_time = int(round(time.time() * 1000))          #current time in ms
                #    # This will make sure the app is always imported when
                #    # Django starts so that shared_task will use this app.
                #    from djhome.celery import app as celery_app
                #    #set_output_state.apply_async((self.pk, False, self.off_delay_initiated_time), eta=datetime.utcnow() + timedelta(milliseconds=self.off_delay_ms))
                #    result = set_output_state.apply_async((self.pk, False), eta=datetime.utcnow() + timedelta(milliseconds=self.off_delay_ms))
                #    self.task_id = result.task_id
                #    self.logger.debug("Set auto-off %s: %s ms (task_id=%s)" % (self, self.off_delay_ms, self.task_id))

                self.save()
            IOConsumer.send_io_changed(self)  # Update clients that output has changed

            # Group("binding.values").send({
            #     "text": json.dumps({
            #         "id": self.id,
            #         "state": self.statez
            #     })
            # })

        except Exception:
            self.logger.exception('on_state_change')


class InputToOutput(models.Model):
    objects = models.Manager()  # using a filtering-manager as the default will filter out results in the admin-site
    valid_objects = managers.InputToOutputValidManager()

    input = models.ForeignKey(Input, on_delete=models.CASCADE, related_name='output_assoc')
    output = models.ForeignKey(Output, on_delete=models.CASCADE, related_name='input_assoc')
    deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = (('input', 'output'),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def __str__(self):
        return "Input_to_Output (#%s): %s --> %s" % (self.id, self.input, self.output)

    def clean(self):
        self.logger.debug("Cleaning InputOutput")
        result = super().clean()
        self.logger.debug("Cleaned InputOutput: %s" % (result))
        return result

    def clean_fields(self, exclude=None):
        try:
            self.logger.debug("Cleaning InputOutput fields")
            result = super().clean_fields(exclude=exclude)
            self.logger.debug("Cleaned InputOutput fields: %s" % (result))
            return result
        except Exception:
            self.logger.exception('clean_fields')

    def save(self, **kwargs):
        self.logger.debug("Saving InputOutput: %s" % (kwargs))
        return super().save(**kwargs)


class TriggerAudit(models.Model):
    from schedules.models import Schedule, OnetimeSchedule

    objects = managers.TriggerAuditManager()

    TRIGGER_TYPE_INPUT = 1
    TRIGGER_TYPE_USER = 2
    TRIGGER_TYPE_SCHEDULE = 3
    TRIGGER_TYPE_ONETIMESCHEDULE = 4
    TRIGGER_TYPE_DELAYEDSCHEDULE = 5
    TRIGGER_TYPE_EMAIL = 6
    TRIGGER_TYPES = (
        (TRIGGER_TYPE_INPUT, 'Input'),
        (TRIGGER_TYPE_USER, 'User'),
        (TRIGGER_TYPE_SCHEDULE, 'Schedule'),
        (TRIGGER_TYPE_ONETIMESCHEDULE, 'OneTimeSchedule'),
        (TRIGGER_TYPE_DELAYEDSCHEDULE, 'DelayedSchedule'),
        (TRIGGER_TYPE_EMAIL, 'Email'),
    )

    type = models.IntegerField(verbose_name='type', blank=True, null=True, choices=TRIGGER_TYPES)

    input = models.ForeignKey(Input, verbose_name='input', null=True, on_delete=models.CASCADE,
                              related_name='input_triggeraudit_assoc')
    device = models.CharField(blank=True, max_length=255)
    index = models.IntegerField(blank=True, null=True)
    state = models.BooleanField(null=True, db_column='state')
    input_type = models.IntegerField(blank=True, null=True, verbose_name='Input type', choices=Input.INPUT_TYPES)

    user = models.ForeignKey(User, verbose_name='user', null=True, on_delete=models.CASCADE,
                             related_name='user_triggeraudit_assoc')
    username = models.CharField(verbose_name='username', blank=True, max_length=150)

    schedule = models.ForeignKey(Schedule, verbose_name='schedule', null=True, on_delete=models.CASCADE,
                                 related_name='schedule_triggeraudit_assoc')
    onetimeschedule = models.ForeignKey(OnetimeSchedule, verbose_name='onetime-Schedule', null=True,
                                        on_delete=models.CASCADE, related_name='onetimeschedule_triggeraudit_assoc')

    timestamp = models.DateTimeField(auto_now_add=True)
    request_id = models.CharField(blank=True, max_length=255)

    def __str__(self):
        return "TriggerAudit (#%s): %s, %s" % (self.id, self.type, self.timestamp)

    @classmethod
    def create_from_input(cls, input):
        return cls.objects.create(type=TriggerAudit.TRIGGER_TYPE_INPUT, input=input, device=input.device.description,
                                  index=input.index, input_type=input.input_type, state=input.state,
                                  request_id=getattr(local, 'request_id', ''))

    @classmethod
    def create_from_user(cls, user, state, request_id):
        return cls.objects.create(type=TriggerAudit.TRIGGER_TYPE_USER, user=user, username=user.username, state=state,
                                  request_id=request_id)

    @classmethod
    def create_from_schedule(cls, schedule):
        return cls.objects.create(type=TriggerAudit.TRIGGER_TYPE_SCHEDULE, schedule=schedule,
                                  request_id=getattr(local, 'request_id', ''))

    @classmethod
    def create_from_onetimeschedule(cls, onetimeschedule):
        return cls.objects.create(type=TriggerAudit.TRIGGER_TYPE_ONETIMESCHEDULE, onetimeschedule=onetimeschedule,
                                  request_id=getattr(local, 'request_id', ''))


class OutputAudit(models.Model):
    objects = managers.OutputAuditManager()

    output = models.ForeignKey(Output, null=True, on_delete=models.CASCADE, related_name='output_audit_assoc')
    state = models.BooleanField(null=True, db_column='state')
    target_position = models.IntegerField(blank=True, null=True, default=None)

    trigger = models.ForeignKey(TriggerAudit, verbose_name='trigger', null=True, on_delete=models.CASCADE,
                                related_name='triggeraudit_assoc')
    timestamp = models.DateTimeField(auto_now_add=True)
    request_id = models.CharField(blank=True, max_length=255)

    def __str__(self):
        return "OutputAudit (#%s): %s, %s [%s, %s]" % (
            self.id, self.output, self.timestamp, self.trigger, self.request_id)

    @classmethod
    def create(cls, trigger, output, request_id=None, target_position=None):
        from log_request_id import local
        if not request_id:
            request_id = getattr(local, 'request_id', '')
        return cls.objects.create(trigger=trigger, output=output, state=output.state, target_position=target_position,
                                  request_id=request_id)
