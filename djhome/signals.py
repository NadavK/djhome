from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging


# This code is triggered whenever a new user has been created and saved to the database
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        logger = logging.getLogger("djhome.create_auth_token")
        logger.debug('Creating token for user: %s' % instance)

        from rest_framework.authtoken.models import Token               #this func is loaded before models are loaded
        Token.objects.create(user=instance)
