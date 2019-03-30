"""
WSGI config for djhome project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
from datetime import timedelta
import os
from django.core.wsgi import get_wsgi_application
from redis import Redis
from rq_scheduler import Scheduler


def load():
    import logging
    logger = logging.getLogger(__name__)
    logger.info('WSGI started')

    try:
        logger.debug('Clearing input states')
        from ios.models import Input
        Input.objects.all().update(state=None)



        # Send all default output states
        from ios.tasks import set_initial_phidget_outputs
        scheduler = Scheduler(connection=Redis())  # Get a scheduler for the "default" queue
        scheduler.enqueue_in(func=set_initial_phidget_outputs, time_delta=timedelta(seconds=5))



        #TODO: Need to ask Phidget to send current status for everything, so that UI can be updated
        #TODO: Need to send outputs with default inital state of true




        # This will make sure the app is always imported when Django starts so that shared_task will use this app.
        # from djhome.celery import app as celery_app
        # set_default_phidget_outputs.apply_async((), countdown=5)
        # async did not work, so calling synchronously
        #set_default_phidget_outputs()
    except Exception:
        logger.exception('WSGI loading failed')


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djhome.settings")
application = get_wsgi_application()
load()
