from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from .models import Schedule, OnetimeSchedule
from django import forms
from django.forms import Textarea, TextInput
from django.db import models
import dateutil.parser
import requests


class ScheduleAdminForm(forms.ModelForm):
    #def clean_time(self):
    #    # do something that validates your data
    #    return self.cleaned_data["time"]


    time = forms.CharField(max_length=6)#, widget=forms.Textarea(attrs={'rows':'1', 'cols': '5'}))

    class Meta:
        model = Schedule
        #fields = ('title', 'body')
        exclude = ('pk',)


@admin.register(Schedule)
class ScheduleAdmin(GuardedModelAdmin):
    #list_display = ['description', 'ph_sn', 'index', 'input_type', 'deleted', 'tag_list']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '6'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols': 60})},
    }
    save_as = True
    list_display = ('output_desc', 'turn_on_display', 'active', 'deleted', 'time', 'time_reference', 'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sha', 'but_only_secular_fri', 'description', 'eta')
    actions = ['make_active', 'make_inactive']
    #form = ScheduleAdminForm
    tasks = {}

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

        #from celery.app import app_or_default
        #app = app_or_default()
        #tasks_dict = app.control.inspect().scheduled()
        #if tasks_dict:
        #    self.tasks = list(tasks_dict.values())[0]

    def eta(self, obj):
        try:
            # url = 'http://localhost:5555/api/task/info/' + obj.task_id      #Celery Flower URL
            #return dateutil.parser.parse(requests.get(url).json()['eta']).strftime('%d/%m/%y %X')      Stopped working

            # Alternatives (but they return the entire list)
            # from celery.task.control import inspect
            # # inspect().scheduled()
            # inspect(['celery@djhome.prod']).scheduled()
            #
            # app.control.inspect(['celery@djhome.prod']).scheduled()
            #
            # # Doesn't work
            #print(obj.task_id)
            #print(app.control.inspect(['celery@djhome.prod']).query_task(['14608e64-6d11-47b1-b235-2d95931e6c9a']))
            #print(app.control.inspect(['celery@djhome-dev:']).query_task('14608e64-6d11-47b1-b235-2d95931e6c9a'))

            #from celery.app import app_or_default
            #app = app_or_default()
            #i = app.control.inspect()
            #print('active()')
            #print(i.active())

            #print(app.control.inspect(['celery@djhome-dev']).scheduled())
            #t = app.control.inspect(['celery@djhome-dev']).query_task([obj.task_id])
            #t = i.query_task([obj.task_id])        doesn't work...

            for task in self.tasks:
                if task['request']['id'] == obj.task_id:
                    return task['eta']
            return 'N/A'
        except Exception as e:
            print('ERROR getting schedule eta:', e)
            return 'N/A'

    def make_active(self, request, queryset):
        queryset.update(active=True)             # bulk operation doesn't run save(), nor emit pre_save or post_save signals
    make_active.short_description = "Activate selected schedules"

    def make_inactive(self, request, queryset):
        queryset.update(active=False)            # bulk operation doesn't run save(), nor emit pre_save or post_save signals
    make_inactive.short_description = "Deactivate selected schedules"


@admin.register(OnetimeSchedule)
class OnetimeScheduleAdmin(GuardedModelAdmin):
    save_as = True
    list_display = ('pk', 'output_desc', 'date', 'start', 'end', 'active', 'deleted')
