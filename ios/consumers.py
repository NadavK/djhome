import datetime
import json
import logging

from asgiref.sync import async_to_sync
from django.apps import apps
from channels.generic.websocket import JsonWebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model


class IOConsumer(JsonWebsocketConsumer):
    groups = ["broadcast"]          # django-channels automatically adds new connections to this (these) groups
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        self.logger.debug('Created ActionConsumer logger')
        self.input_model = None
        self.output_model = None

        super(IOConsumer, self).__init__(*args, **kwargs)

    def connect(self):
        # Cache models for quicker response
        self.logger.info('Caching Input model')
        self.input_model = apps.get_model('ios', 'Input')
        self.logger.info('Caching Output model')
        self.output_model = apps.get_model('ios', 'Output')

        self.accept()

    def receive_json(self, content, **kwargs):
        """ Receives an action from the user: either auth, or change state"""
        try:
            # Each websocket connection is expected to send an "auth" message, and we then set the user to the scope
            # Expected payload: {"stream": "auth", "token": "..."}
            if content['stream'] == 'auth':
                from rest_framework_simplejwt.tokens import AccessToken
                user = get_user_model().objects.get(id=AccessToken(content['token'])['user_id'])
                self.scope['user'] = user
                self.logger.info('User authenticated: %s' % user)
                self.send_json({'status': 'Authorization succeeded'})
                return
        except Exception:
            self.logger.exception('Auth exception. Closing connection.')
            self.send_json({'status': 'Authorization failed'})
            self.close(code=4010)

        try:
            # Change state for output object (input or output)
            # Expected payload: {"stream": "action", "payload": {"action": "update", "model": "ios.models.Output", "pk": "2", "data": {"state": true}}}
            user = self.scope.get('user')
            if user is None or not user.is_authenticated:
                self.logger.warning('Invalid user: ActionConsumer from %s (%s). Closing connection.' % (content, user))
                self.send_json({'status': 'Not authorized'})
                self.close(code=4010)
                return

            self.logger.info('ActionConsumer from %s (%s)' % (content, user))

            payload = content['payload']
            pk = payload['pk']
            state = payload['data']['state']
            model = payload['model']
            if model == 'ios.models.Input':
                #TODO: check user authorization
                self.input_model.objects.set_state_by_pk(pk, state, user=user)
            elif model == 'ios.models.Output':
                #TODO: check user authorization
                obj = self.output_model.objects.set_state_by_pk(pk, state, user=user)
                if obj:
                    self.logger.info('State not changed. Sending state notification to sync client')
                    self.send_json({'message': self.create_io_changed_msg(obj)})
            else:
                self.logger.error('ActionConsumer unknown model: %s' % model)

            self.send_json({'status': 'OK'})
        except Exception:
            self.logger.exception('Action exception')
            self.send_json({'status': 'Invalid'})

    def create_io_changed_msg(self, obj):
        # obj can be Input or Output - just need a pk
        msg = json.dumps(
            {"action": "update", "pk": obj.pk, "model": obj.__module__ + "." + obj.__class__.__name__, "state": obj.state,
             "stream": "action", "duh": str(datetime.datetime.now())})
        return msg

    def send_io_changed(self, obj):
        self.logger.info('Sending IO change notification')
        message = self.create_io_changed_msg(obj)
        try:
            async_to_sync(get_channel_layer().group_send)(
                self.groups[0],
                {
                    'type': 'broadcast_message',
                    'message': message
                }
            )
            self.logger.info('Sent IO change notification')
        except Exception:
            self.logger.exception('')

    def broadcast_message(self, event):
        # Send message to WebSocket
        self.send_json({
            'message': event['message']
        })
