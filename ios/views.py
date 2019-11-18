from datetime import timedelta

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from guardian.shortcuts import get_objects_for_user
from redis import Redis
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action, authentication_classes
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rq_scheduler import Scheduler

from djhome import settings
from djhome.json_token_auth import JSONWebTokenAuthenticationQueryString, TokenAuthenticationQueryString
from djhome.permissions import IsAdminOrIsSelf
from .models import Input, Output
from .serializers import InputSerializer, InputAdminSerializer, OutputSerializer, InputSimpleSerializer, OutputSimpleSerializer, OutputAdminSerializer, TagSerializer
#from phidgets.signals import ph_input_changed_helper, ph_output_changed_helper
import logging


class InputViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows inputs to be viewed or edited.
    """
    queryset = Input.objects.all().order_by('id')
    serializer_class = InputSerializer

    def __init__(self, *args, **kwargs):
        super(InputViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    #@list_route(methods=['post'], serializer_class=InputSerializer)
    #def login(self, request):
    #    pass

    #@detail_route(renderer_classes=[renderers.StaticHTMLRenderer])
    #def highlight(self, request, *args, **kwargs):
    #    snippet = self.get_object()
    #    return Response(snippet.description)





    # permission is never called!!!!!
    @action(methods=['post'], detail=False, permission_classes=[IsAdminOrIsSelf])
    def input(self, request):
        self.logger.debug('received input_changed: %s', request.data)
        ph_sn = request.data['sn']
        ph_index = request.data['index']
        state = request.data['state']
        user = self.request.user
        Input.objects.set_input_by_sn_index(ph_sn, ph_index, state, user)
        return Response({'status': 'OK'})


    @action(methods=['get', 'post'], detail=True, permission_classes=[IsAdminOrIsSelf])
    def set_down(self, request, pk=None):
        meta = self.metadata_class()
        data = meta.determine_metadata(request, self)
        self.logger.debug('set_down DATAAAAAAAAAAAAAAAA: %s', data)

        input = self.get_object()
        self.logger.debug('set_down INPUTTTTTTTTTTTTTTTTTTT: %s', input)
        #ph_input_changed_helper(sender=self.__class__, ph_sn=input.ph_sn, ph_index=input.ph_index, state=True)       #calling signal sometimes causes phidget to fire all inputs and outputs
        user = self.request.user
        input.on_state_change(True, user)
        return Response({'status': 'OK'})

    @action(methods=['get'], detail=True, permission_classes=[IsAdminOrIsSelf])
    def set_up(self, request, pk=None):
        input = self.get_object()
        self.logger.debug('set_up INPUTTTTTTTTTTTTTTTTTTT: %s', input)
        #ph_input_changed_helper(sender=self.__class__, ph_sn=input.ph_sn, ph_index=input.ph_index, state=True)       #calling signal sometimes causes phidget to fire all inputs and outputs
        user = self.request.user
        input.on_state_change(False, user)
        return Response({'status': 'OK'})


class OutputViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows outputs to be viewed or edited.
    """
    queryset = Output.objects.all().order_by('id')
    serializer_class = OutputSerializer
    authentication_classes = (JSONWebTokenAuthentication, TokenAuthentication, TokenAuthenticationQueryString)

    def __init__(self, *args, **kwargs):
        # this never seems to get called.
        super(OutputViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self.logger.info('************ OutputViewSet __init__ **********************************')

    #@list_route(methods=['post'], url_path='recent')
    #def login(self, request):
    #    pass

    @action(methods=['get'], detail=False, permission_classes=[IsAdminOrIsSelf])
    def defaults(self, request):
        """
        API: outputs/defaults/
        Used by Phidget-Server to obtain the default outputs (response is asynchronous)
        :return:
        """
        self.logger.debug('received request for get default outputs')
        # This will make sure the app is always imported when Django starts so that shared_task will use this app.
        #from djhome.celery import app as celery_app

        #TODO: Also need to do this at startup
        from ios.tasks import set_initial_phidget_outputs
        scheduler = Scheduler(connection=Redis())  # Get a scheduler for the "default" queue
        scheduler.enqueue_in(func=set_initial_phidget_outputs, time_delta=timedelta(seconds=5), request_id=request.META.get(settings.LOG_REQUEST_ID_HEADER))
        #set_initial_phidget_outputs.apply_async((), countdown=5)
        return Response({'status': 'OK'})

    # Sent by client to request to change output state
    @action(methods=['get', 'post'], detail=False, permission_classes=[IsAdminOrIsSelf])
    def set_output(self, request):
        self.logger.debug('received set output request: %s', request.data)
        state = request.data['state']
        cue = request.data.get('cue')
        self.logger.debug('cue: %s', cue)
        if cue:
            if state == 'on':
                state = True
            elif state == 'off':
                state = False
            outputs = Output.objects.filter(cues__slug=cue)
            self.logger.debug('cueing outputs %s: %s', state, outputs)
            for output in outputs:
                output.set_state(state, user=self.request.user)
        else:
            ph_sn = request.data['sn']
            ph_index = request.data['index']
            Output.objects.set_state_by_sn_index(ph_sn, ph_index, state, self.request.user)

            #self.logger.debug('Auditing...')        # this does func does not seem to be called...
            #OutputAudit.objects.create(output=output, state=state, user=self.request.user)         # Save audit of what initiated the output-change

        return Response({'status': 'OK'})

    # Sent by Phidget_Server to notify that output has changed
    @action(methods=['post'], detail=False, permission_classes=[IsAdminOrIsSelf])
    def output_changed(self, request):
        self.logger.debug('received output_changed notification: %s', request.data)
        #data = json.loads(request.data)
        #print(data)
        try:
            #self.logger.info('received: ', request)
            output = Output.objects.get(ph_sn=request.data['sn'], ph_index=request.data['index'])
            # ph_output_changed_helper(sender=self.__class__, ph_sn=output.ph_sn, ph_index=output.ph_index, state=True)       #calling signal sometimes causes phidget to fire all inputs and outputs
            output.on_state_change(request.data['state'])
        except Output.DoesNotExist:
            self.logger.warning('Output %s/%s not found' % (request.data['sn'], request.data['index']))
        except Exception as ex:
            self.logger.error(ex)

        return Response({'status': 'OK'})

'''
@require_http_methods(["GET"])
def inputs_all(request):
    inputs = Input.objects.all()

    return render(request, "io.html", {
        'inputs': inputs,
})
'''

@require_http_methods(["GET"])
def io(request):
    inputs = Input.objects.all()
    outputs = Output.objects.all()

    return render(request, "io.html", {
        'inputs': inputs,
        'outputs': outputs,
})


#What is this used for?
def inputs_by_tags(request, tags):
    inputs = Input.objects.all(tags__in=tags)

    #outputs = reversed(inputs.outputs.order_by('-timestamp')[:50])

    return render(request, "inputs.html", {
        'inputs': inputs,
})

from django.shortcuts import render
from .models import Output

def index(request):
    """
    Root page view. Just shows a list of values currently available.
    """
    return render(request, "index.html", {
        "output_message_values": Output.objects.order_by("id"),
    })


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from taggit.models import Tag


class IOsView(APIView):
    """
    View to list all authorized inputs/outputs for this user.

    * Requires token authentication.
    """
    #authentication_classes = (authentication.TokenAuthentication,)
    #permission_classes = (permissions.IsAdminUser,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        """
        Return a list of all ios-objects and tags.
        """

        def add_tags(tags_set, new_tags):
            for tag in new_tags:
                tags_set.add(tag)

        user = self.request.user
        outputs = get_objects_for_user(user, ['ios.view_output', 'ios.change_output'], any_perm=True, with_superuser=True, accept_global_perms=False)

        outputs_serializer_class = OutputAdminSerializer if user.is_superuser else OutputSimpleSerializer
        #outputs_serializer=  OutputAdminSerializer(outputs, many=True, context={'request': request}) if user.is_superuser else OutputSimpleSerializer(outputs, many=True, context={'request': request})


        inputs = get_objects_for_user(user, ['ios.view_input', 'ios.change_input'], any_perm=True, with_superuser=True, accept_global_perms=False)
        inputs_serializer_class = InputAdminSerializer if user.is_superuser else InputSimpleSerializer
        inputs_serializer = inputs_serializer_class(inputs, many=True, context={'request': request})
        #inputs_serializer = InputSimpleSerializer(inputs, many=True, context={'request': request})

        #only return tags that exist in the filtered inputs & outputs
        tags = set()
        logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        for o in outputs:
            add_tags(tags, o.tags.all())
            from guardian.shortcuts import get_perms
            o.permissions = get_perms(user, o)
            #logger.debug('Permissions for %s: %s', o.pk, o.permissions)
        for i in inputs:
            add_tags(tags, i.tags.all())
        tags_serializer = TagSerializer(tags, many=True, context={'request': request})

        outputs_serializer = outputs_serializer_class(outputs, many=True, context={'request': request})
        all = {'tags': tags_serializer.data, 'outputs': outputs_serializer.data, 'inputs': inputs_serializer.data}
        return Response(all)
