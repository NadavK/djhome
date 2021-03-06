import asyncio
import datetime
import json
import logging
from django.apps import apps
from channels.generic.websocket import JsonWebsocketConsumer
from channels.layers import get_channel_layer


class IOConsumer(JsonWebsocketConsumer):
    groups = ["broadcast"]

    """ Needed custom Consumer because Input doesn't have status field, and Output has _my_state field """
    logger = logging.getLogger(__module__ + '.IOConsumer')

    def __init__(self, *args, **kwargs):
        #print("init:", args, kwargs)

        self.logger.debug('Created ActionConsumer logger')
        self.input_model = apps.get_model('ios', 'Input')
        self.logger.info('Caching Input model')
        self.output_model = apps.get_model('ios', 'Output')
        self.logger.info('Caching Output model')

        super(IOConsumer, self).__init__(*args, **kwargs)

    def connect(self):
        self.logger.info('channel connection')
        super().connect()

    def accept(self, subprotocol=None):
        super().accept(self.scope['jwt'])       # I don't know how to return multiple protocols

    def disconnect(self, close_code):
        pass

    def connection_groups(self, **kwargs):
        self.logger.info('channel connection group')
        #from pprint import pprint,pformat
        #self.logger.info(pformat(vars(kwargs['multiplexer'])))
        #for o in kwargs:
        #   self.logger.info(pformat(vars(0)))
        return ["action"]
        #return ["output-updates"]

    @classmethod
    def send_io_changed(cls, obj, state):
        try:
            cls.logger.info('Sending IO change notification')

            # obj can be Input or Output - just need a pk
            msg = json.dumps({"action": "update", "pk": obj.pk, "model": obj.__module__ + "." + obj.__class__.__name__, "state": state, "stream": "action", "duh":  str(datetime.datetime.now())})
            cls.logger.debug('**************send_io_changed message: %s' % msg)

            # Send message to broadcast group
            # don't ask...  https://stackoverflow.com/questions/50299749/signals-and-django-channels-chat-room
            loop = asyncio.get_event_loop()
            coroutine = get_channel_layer().group_send(
                'broadcast',
                {
                    'type': 'broadcast_message',
                    'message': msg
                }
            )
            asyncio.run_coroutine_threadsafe(coroutine, loop)
            #loop.run_until_complete(coroutine)
        except Exception:
            cls.logger.exception('')

    def broadcast_message(self, event):
        """ Receive message from room group """
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))

    def receive_json(self, content, **kwargs):
        """ Receives an action from the user to change state for output object (input or output)"""

        # Expected payload: {"stream":"action","payload":{"action":"update","model":"ios.models.Output","pk":"2","data":{"state":true}}}
        user = self.scope.get('user')
        if user is None or not user.is_authenticated:
            self.logger.warning('Invalid user: ActionConsumer from %s (%s)' % (content, user))
            self.send_json({'status': 'Not authorized'})
            return

        self.logger.info('ActionConsumer from %s (%s)' % (content, user))
        try:
            payload = content['payload']
            pk = payload['pk']
            state = payload['data']['state']
            model = payload['model']
            if model == 'ios.models.Output':
                #TODO: check user authorization
                self.output_model.objects.set_state_by_pk(pk, state, user=user)
            elif model == 'ios.models.Input':
                #TODO: check user authorization
                self.input_model.objects.set_state_by_pk(pk, state, user=user)
            else:
                self.logger.error('ActionConsumer unknown model: %s' % model)

            self.send_json({'status': 'OK'})
        except Exception:
            self.logger.exception('')
            self.send_json({'status': 'Invalid'})
