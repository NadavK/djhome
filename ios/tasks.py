from __future__ import absolute_import, unicode_literals

from django_rq import job
from django.conf import settings
import datetime
import logging
import requests
from requests import Session


# NOTE: Only WARNING and higher logs are written. !@#@#! celery.


#@app.task()
from rq import get_current_job


@job
def set_initial_phidget_outputs():
    '''
    Sends all outputs to PhidgetServer
    '''
    logger = logging.getLogger(__name__)
    # prepare request_id
    from log_request_id import local
    from log_request_id.middleware import RequestIDMiddleware
    empty_request_id = not hasattr(local, 'request_id') or local.request_id is None
    if empty_request_id:
        local.request_id = RequestIDMiddleware()._generate_id()
    try:
        logger.warning('Calling PhidgetServer to set output states')
        #from rest_framework.authtoken.models import Token
        #token = Token.objects.get(user__username='phidget_server')
        from ios.models import Output
        for sn in Output.objects.filter(output_type=Output.OUTPUT_TYPE_REGULAR).values_list('ph_sn', flat=True).distinct():
            states_bytearray = bytearray(b' ' * 100)
            for index, default_state, state in Output.objects.filter(ph_sn=sn, output_type=Output.OUTPUT_TYPE_REGULAR).values_list('ph_index', 'default_state', '_my_state'):
                if int(index) > 99:      # some scripts (non-phidget outputs) use high index numbers
                    continue
                if default_state == Output.DEFAULT_STATE_TYPE_ON:
                    states_bytearray[index] = ord('1')
                elif default_state == Output.DEFAULT_STATE_TYPE_OFF:
                    states_bytearray[index] = ord('0')
                elif default_state == Output.DEFAULT_STATE_TYPE_RESTORE_LAST:
                    states_bytearray[index] = ord('*')
                else:
                    logger.warning('Unknown default state %s/%s: "%s"', sn, index, default_state)
            states = str(bytes(states_bytearray), 'UTF8').rstrip()
            url = settings.PHIDGET_SERVER_URL + 'default_outputs/' + sn
            logger.warning('Calling PhidgetServer: %s, output mask: "%s"', url, states)
            try:
                Session().post(url, json={'states': states}).raise_for_status()
            except Exception:
                logger.exception('Calling PhidgetServer')

            #requests.post(url, json={'callback_url': me, 'token': token.key, 'outputs': states}).raise_for_status()
    except requests.exceptions.RequestException as e:  # catch all requests exception
        logger.error(e)
        #logger.info('Retrying in 5 seconds')
        #set_outputs.apply_async((), countdown=5)
    except Exception as ex:
        logger.exception('')
        #logger.info('Retrying in 5 seconds')
        #set_outputs.apply_async((), countdown=5)

    if empty_request_id:
        delattr(local, 'request_id')


@job
def set_output_state(args):
    logger = logging.getLogger(__name__)
    logger.info('Output timed-execution')
    pk, state, target_position = args
    from ios.models import Output
    #Output.objects.set_statef(pk, state, initiated_time)
    Output.objects.set_state(pk, state, task_id=get_current_job().id, target_position=target_position)


@job
def set_output_state_from_schedule(args):
#def set_output_state_from_schedule(schedule_pk, schedule_type, state, target_position=None):
    logger = logging.getLogger(__name__)
    task_id = get_current_job().id
    logger.info('Scheduled-execution - set_output_state_from_schedule [task_id=%s]' % task_id)

    schedule_pk, schedule_type, state, target_position = args

    if not schedule_pk:
        logger.error('Scheduled pk is None [task_id=%s]' % task_id)
        return

    from schedules.models import Schedule, OnetimeSchedule
    try:
        # TODO: this can be done dynamically
        if schedule_type == Schedule.type:
            schedule = Schedule.objects.get(pk=schedule_pk)

            if OnetimeSchedule.objects.is_onetime_active_for_datatime(schedule.output, datetime.datetime.now()):
                logger.info('A OneTimeSchedule is active for this time: %s, %s', schedule, schedule.output)
                schedule.prepare_next_schedule(for_next_time=True)  # this will prepare the next schedule time
                return

        elif schedule_type == OnetimeSchedule.type:
            schedule = OnetimeSchedule.objects.get(pk=schedule_pk)
        else:
            logger.error("Unknown schedule type: %s" % schedule_type)
            return
    except Schedule.DoesNotExist:
        logger.error("Schedule id not found %s" % schedule_pk)
        return
    except OnetimeSchedule.DoesNotExist:
        logger.error("OnetimeSchedule id not found %s" % schedule_pk)
        return

    if schedule.task_id != task_id:
        logger.info('Schedule task is invalid: %s', schedule)
    else:
        if schedule.valid:
            from ios.models import Output
            Output.objects.set_state(schedule.output.pk, state, target_position=target_position)
        else:
            logger.info('Schedule is inactive/deleted: %s', schedule)
        schedule.prepare_next_schedule(for_next_time=True)     # this will prepare the next schedule time
