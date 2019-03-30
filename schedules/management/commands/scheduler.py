import django_rq
from django_rq.management.commands import rqscheduler
from datetime import timedelta
import logging


# https://github.com/rq/rq-scheduler/issues/51#issuecomment-362352497
class Command(rqscheduler.Command):
    help = 'Starts the RQ worker, with custom start-up tasks'

    scheduler = django_rq.get_scheduler()
    log = logging.getLogger(__name__)

    def clear_scheduled_jobs(self):
        # Delete any existing jobs in the scheduler when the app starts up
        self.log.debug('Deleting scheduled jobs')
        for job in self.scheduler.get_jobs():
            self.log.debug('Deleting scheduled job %s', job)
            job.delete()

    def register_scheduled_jobs(self):
        # do your scheduling here
        from schedules.models import Schedule
        self.log.debug('Resubmitting schedules')

        #scheduler = Scheduler(connection=Redis())  # Get a scheduler for the "default" queue
        self.scheduler.enqueue_in(func=Schedule.objects.resubmit_all_schedules,
                                   time_delta=timedelta(seconds=5))

    def handle(self, *args, **kwargs):
        # This is necessary to prevent dupes
        self.clear_scheduled_jobs()
        self.register_scheduled_jobs()
        super(Command, self).handle(*args, **kwargs)
