from datetime import timedelta
from numbers import Number

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from guardian.shortcuts import get_objects_for_user
from oauth2_provider.contrib.rest_framework import OAuth2Authentication, TokenHasScope
from redis import Redis
from rest_framework import permissions, viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rq_scheduler import Scheduler
import logging

from djhome import settings
from djhome.permissions import IsAdminOrIsSelf
from ios.intents import IntentResponse, ExecuteResponsePayload, SyncResponsePayload, QueryResponsePayload
from .models import Input, Output, Server
from .serializers import InputSerializer, InputAdminSerializer, OutputSerializer, InputSimpleSerializer, \
    OutputSimpleSerializer, OutputAdminSerializer, TagWithEmojiSerializer, ServerSerializer


class ServerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows inputs to be viewed or edited.
    """
    queryset = Server.objects.all().order_by('id')
    serializer_class = ServerSerializer


class InputViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows inputs to be viewed or edited.
    """
    queryset = Input.objects.all().order_by('id')
    serializer_class = InputSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    # permission is never called!!!!!
    @action(methods=['post'], detail=False, permission_classes=[IsAdminOrIsSelf])
    def input(self, request):
        self.logger.debug('received input_changed: %s', request.data)
        index = request.data['index']
        state = request.data['state']
        user = self.request.user
        if 'server' in request.data:
            server_id = request.data['server']
            Input.objects.set_input_by_server_index(server_id, index, state, user)
        elif 'sn' in request.data:
            server_sn = request.data['sn']
            Input.objects.set_input_by_server_sn(server_sn, index, state, user)
        else:
            raise (Exception('missing "server" or "sn"'))
        return Response({'status': 'OK'})

    @action(methods=['get', 'post'], detail=True, permission_classes=[IsAdminOrIsSelf])
    def set_down(self, request, pk=None):
        meta = self.metadata_class()
        data = meta.determine_metadata(request, self)
        self.logger.debug('set_down DATAAAAAAAAAAAAAAAA: %s', data)

        input = self.get_object()
        self.logger.debug('set_down INPUTTTTTTTTTTTTTTTTTTT: %s', input)
        user = self.request.user
        input.on_state_change(True, user)
        return Response({'status': 'OK'})

    @action(methods=['get'], detail=True, permission_classes=[IsAdminOrIsSelf])
    def set_up(self, request, pk=None):
        input = self.get_object()
        self.logger.debug('set_up INPUTTTTTTTTTTTTTTTTTTT: %s', input)
        user = self.request.user
        input.on_state_change(False, user)
        return Response({'status': 'OK'})


class OutputViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows outputs to be viewed or edited.
    """
    queryset = Output.objects.all().order_by('id')
    serializer_class = OutputSerializer
    authentication_classes = [OAuth2Authentication, JWTAuthentication,
                              TokenAuthentication]  # , TokenAuthenticationQueryString]
    required_scopes = ['write']
    logger = logging.getLogger(__module__)

    def __init__(self, *args, **kwargs):
        # this never seems to get called.
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self.logger.info('************ OutputViewSet __init__ **********************************')

    @action(methods=['get'], detail=False, permission_classes=[IsAdminOrIsSelf])
    def defaults(self, request):
        """
        API: outputs/defaults/
        Used by Phidget-Server to obtain the default outputs (response is asynchronous)
        :return:
        """
        self.logger.debug('received request for get default outputs')
        # This will make sure the app is always imported when Django starts so that shared_task will use this app.
        # from djhome.celery import app as celery_app

        # TODO: Also need to do this at startup
        from ios.tasks import set_initial_phidget_outputs
        scheduler = Scheduler(connection=Redis())  # Get a scheduler for the "default" queue
        scheduler.enqueue_in(func=set_initial_phidget_outputs, time_delta=timedelta(seconds=5),
                             request_id=request.META.get(settings.LOG_REQUEST_ID_HEADER))
        # set_initial_phidget_outputs.apply_async((), countdown=5)
        return Response({'status': 'OK'})

    # Sent by client to request to change output state
    @action(methods=['get', 'post'], detail=False, permission_classes=[IsAdminOrIsSelf])
    def set_output(self, request):
        self.logger.debug('received set output request data: %s', request.data)
        # cue = request.data.get('cue')
        id = request.data.get('id')
        if id is None:
            return Response({'status': 'ID not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            self.handle_set(id, request.data['state'])
            return Response({'status': 'OK'})

    def get_outputs(self, id):
        '''
        :param id: can be a pk, a cue, or a list of both ids and cues
        :return:
        '''

        if isinstance(id, list):
            outputs = []
            ids = []
            for i in id:
                if isinstance(i, Number) or (isinstance(i, str) and i.isnumeric()):
                    ids.append(i)
                else:
                    outputs.append(self.get_outputs(i))  # maybe it's a cue?
            return Output.objects.filter(pk__in=ids).union(*outputs)  # for now, only deal with IDs, and not cues

        if isinstance(id, Number) or (isinstance(id, str) and id.isnumeric()):  # ids are numbers
            return [Output.objects.get(pk=id)]
        else:  # Maybe it's a cue and not an id?
            outputs = Output.objects.filter(cues__slug__iexact=id)
            if not outputs:
                outputs = Output.objects.filter(description__iexact=id)
                if not outputs:
                    self.logger.debug('No outputs found: %s', id)
                    return []
            # self.logger.debug('cuing outputs: %s', outputs)
            return outputs

    def handle_set(self, id, state, target_position=None):

        def set_state(output, state, user, target_position):
            if output.device_type == Output.DEVICE_TYPE_WINDOW:
                target_position = state
                state = True
            else:
                if state == 'on' or state == '100' or state == 100:
                    state = True
                elif state == 'off' or state == '0' or state == 0:
                    state = False
            return output.set_state(state, user=user, target_position=target_position)
            # self.logger.debug('Auditing...')        # this does func does not seem to be called...
            # OutputAudit.objects.create(output=output, state=state, user=self.request.user)         # Save audit of what initiated the output-change

        outputs = self.get_outputs(id)
        if not outputs:
            return False

        result = True
        for output in outputs:
            if not set_state(output, state, self.request.user, target_position):
                result = False
        return result

    # Sent by Google Assistant to change output state
    # @action(methods=['get', 'post'], detail=False, permission_classes=[IsAdminOrIsSelf])
    @action(methods=['post'], detail=False, permission_classes=[permissions.IsAuthenticated, TokenHasScope])
    def intents(self, request):
        self.logger.info('Received intent: %s', request.data)
        self.logger.info('Received intent from user: %s',
                         ','.join([request.user.username, request.user.first_name, request.user.last_name]).lower())
        try:
            requestId = request.data['requestId']
            inputs0 = request.data['inputs'][0]
            intents0 = inputs0['intent']
            if intents0 == 'action.devices.SYNC':
                response = IntentResponse(requestId, SyncResponsePayload())
                r = response.clean()
                self.logger.info('SYNC response: %s', r)
                return Response(r)
            elif intents0 == 'action.devices.EXECUTE':
                ids = []
                for device in inputs0['payload']['commands'][0]['devices']:
                    ids.append(device['id'])
                command = inputs0['payload']['commands'][0]['execution'][0]['command']
                state = None
                if command == 'action.devices.commands.OpenClose':
                    state = inputs0['payload']['commands'][0]['execution'][0]['params']['openPercent']
                elif command == 'action.devices.commands.OnOff':
                    state = inputs0['payload']['commands'][0]['execution'][0]['params']['on']
                elif command == 'action.devices.commands.StartStop':
                    state = inputs0['payload']['commands'][0]['execution'][0]['params']['start']
                else:
                    self.logger.error('Received unknown command: %s', command)

                if state is None:
                    result = False
                else:
                    result = True
                    # Don't perform actions for TEST users, used by google testers
                    if 'test' in ','.join(
                            [request.user.username, request.user.first_name, request.user.last_name]).lower():
                        self.logger.warn('IGNORING TEST INTENT')
                    else:
                        for id in ids:
                            if not self.handle_set(id, state):
                                result = False

                response = IntentResponse(
                    requestId,
                    ExecuteResponsePayload(ids, result))

                r = response.clean()
                self.logger.info('EXECUTE response: %s', r)
                return Response(r)
            elif intents0 == 'action.devices.QUERY':
                ids = []
                for device in inputs0['payload']['devices']:
                    ids.append(device['id'])

                outputs = self.get_outputs(ids)
                response = IntentResponse(
                    requestId,
                    QueryResponsePayload(outputs))

                r = response.clean()
                self.logger.info('QUERY response: %s', r)
                return Response(r)

            # self.logger.debug('received intents data: %s', request.data)
            # output, state = request.data['queryResult']['action'].split('_')
            # self.logger.debug('received intents: %s, %s', output, state)
            # self.handle_set(output, None, state)

            self.logger.warning('Received unhandled intent: %s', request.data)
            return Response({'status': 'OK'})
        except:
            self.logger.exception('Received bad intent: %s', request.data)
            raise

    # Sent by Phidget_Server to notify that output has changed
    @action(methods=['post'], detail=False, permission_classes=[IsAdminOrIsSelf])
    def output_changed(self, request):
        self.logger.debug('received output_changed notification: %s', request.data)
        try:
            output = Output.objects.get(server__sn=request.data['sn'], index=request.data['index'])
            output.on_state_change(request.data['state'])
        except Output.DoesNotExist:
            self.logger.warning('Output %s/%s not found' % (request.data['sn'], request.data['index']))
        except Exception as ex:
            self.logger.error(ex)

        return Response({'status': 'OK'})


@require_http_methods(["GET"])
def io(request):
    inputs = Input.objects.all()
    outputs = Output.objects.all()

    return render(request, "io.html", {
        'inputs': inputs,
        'outputs': outputs,
    })


# What is this used for?
# def inputs_by_tags(request, tags):
#     inputs = Input.objects.all(tags__in=tags)
#
#     # outputs = reversed(inputs.outputs.order_by('-timestamp')[:50])
#
#     return render(request, "inputs.html", {
#         'inputs': inputs,
#     })
#
#
# from .models import Output
#
#
# def index(request):
#     """
#     Root page view. Just shows a list of values currently available.
#     """
#     return render(request, "index.html", {
#         "output_message_values": Output.objects.order_by("id"),
#     })
#

class IOsView(APIView):
    """
    View to list all authorized inputs/outputs for this user.

    * Requires token authentication.
    """
    # authentication_classes = (authentication.TokenAuthentication,)
    # permission_classes = (permissions.IsAdminUser,)
    permission_classes = (permissions.IsAuthenticated,)  # TokenHasScope)

    def get(self, request, format=None):
        """
        Return a list of all ios-objects and tags.
        """

        def add_tags(tags_set, new_tags):
            for tag in new_tags:
                tags_set.add(tag)

        user = self.request.user
        outputs = get_objects_for_user(user, ['ios.view_output', 'ios.change_output'], any_perm=True,
                                       with_superuser=True, accept_global_perms=False)

        outputs_serializer_class = OutputAdminSerializer if user.is_superuser else OutputSimpleSerializer
        # outputs_serializer=  OutputAdminSerializer(outputs, many=True, context={'request': request}) if user.is_superuser else OutputSimpleSerializer(outputs, many=True, context={'request': request})

        inputs = get_objects_for_user(user, ['ios.view_input', 'ios.change_input'], any_perm=True, with_superuser=True,
                                      accept_global_perms=False)
        inputs_serializer_class = InputAdminSerializer if user.is_superuser else InputSimpleSerializer
        inputs_serializer = inputs_serializer_class(inputs, many=True, context={'request': request})
        # inputs_serializer = InputSimpleSerializer(inputs, many=True, context={'request': request})

        # only return tags that exist in the filtered inputs & outputs
        tags = set()
        logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        for o in outputs:
            add_tags(tags, o.tags.all())
            from guardian.shortcuts import get_perms
            o.permissions = get_perms(user, o)
            # logger.debug('Permissions for %s: %s', o.pk, o.permissions)
        for i in inputs:
            add_tags(tags, i.tags.all())
        tags_serializer = TagWithEmojiSerializer(tags, many=True, context={'request': request})

        outputs_serializer = outputs_serializer_class(outputs, many=True, context={'request': request})
        all = {'tags': tags_serializer.data, 'outputs': outputs_serializer.data, 'inputs': inputs_serializer.data}
        return Response(all)


class IntentsView(APIView):
    """
    View to list all authorized inputs/outputs for this user.

    * Requires token authentication.
    """
    # authentication_classes = (authentication.TokenAuthentication,)
    # permission_classes = (permissions.IsAdminUser,)
    permission_classes = (permissions.IsAuthenticated,)  # TokenHasScope)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def get(self, request, format=None):
        """
        Return a list of all ios-objects and tags.
        """

        self.logger.debug('received intents data: %s', request.data)
        # # output, state = request.data['queryResult']['action'].split('_')
        # # self.logger.debug('received intents: %s, %s', output, state)
        # self.handle_action(output, None, state)

        return Response({'status': 'OK'})
