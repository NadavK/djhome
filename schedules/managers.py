from django.db import models
import logging


class ScheduleManager(models.Manager):
    logger = logging.getLogger(__name__)

    def resubmit_all_schedules(self):
        '''
        Recalculates all schedules
        '''
        self.logger.info('Preparing next schedule for all schedules')

        for schedule in self.get_queryset().all():
            if schedule.valid:
                schedule.prepare_next_schedule()
            '''
            match = False
            from celery.app import app_or_default
            app = app_or_default()
            tasks_dict = app.control.inspect().scheduled()
            if tasks_dict:
                tasks = list(tasks_dict.values())[0]
                for task in tasks:
                    if task['request']['id'] == schedule.task_id:
                        logger.debug('Found existing task_id')
                        next_eta = schedule._prepare_next(now=0, just_testing=True)
                        logger.debug('etas: %s - %s' % (next_eta, task['eta']))
                        if task['eta'] == next_eta:
                            logger.debug('Found existing matching task_')
                            match = True
    
            if not match:
                schedule.prepare_next_schedule()
            '''


class OneTimeScheduleManager(models.Manager):
    logger = logging.getLogger(__name__)

    #def get_queryset(self):
    #    return super(OneTimeScheduleManager, self).get_queryset().filter(deleted=False).prefetch_related('outputs', 'tags')

    def is_onetime_active_for_datatime(self, output, date):     # should be "..._for_datetime"
        '''
        Return true if there are any active onetime schedules for the given output and date
        :param output:
        :param date:
        :return:
        '''
        self.logger.debug('Looking for active onetime schedules for output %s on %s', output, date)
        just_date = date.date()
        just_time = date.time()
        try:
            return self.get_queryset().filter(active=True, deleted=False, output=output, date=just_date, start__lte=just_time, end__gt=just_time).exists()
        except Exception as e:
            self.logger.exception('Looking for active onetime schedules for output %s on %s', output, date)

