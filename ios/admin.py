import pytz
from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter
from taggit.admin import TagAdmin
from taggit.models import Tag

from djhome import settings
from ios.models import Input, Output, InputToOutput, OutputAudit, TriggerAudit, Cue, CuedItem, Device

# @admin.register(InputType)
# class InputTypeAdmin(admin.ModelAdmin):
#     list_display = ('input_type', 'description', 'id')
#     ordering = ('id',)
#
# @admin.register(OutputType)
# class OutputTypeAdmin(admin.ModelAdmin):
#     list_display = ('output_type', 'description', 'id')
#     ordering = ('id',)


from django import forms
import logging
log = logging.getLogger(__name__)
# convert the errors to text
from django.utils.encoding import force_text


class InputForm(forms.ModelForm):

    class Meta:
        model = Input
        exclude = []

    def __init__(self, *args, **kwargs):
        log.debug('Created InputForm')
        super().__init__(*args, **kwargs)

    def is_valid(self):
        log.debug('running is_valid')
        log.info(force_text(self.errors))
        result = super().is_valid()
        log.debug('is_valid: %s' % result)
        return result


class InputToOutputForm(forms.ModelForm):

    class Meta:
        model = InputToOutput
        exclude = []

    def __init__(self, *args, **kwargs):
        log.debug('Created InputToOutputForm')
        super().__init__(*args, **kwargs)

    def _clean_fields(self):
        from django.forms.fields import Field, FileField
        from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
        for name, field in self.fields.items():
            # value_from_datadict() gets the data from the data dictionaries.
            # Each widget type knows how to retrieve its own data, because some
            # widgets split data over several HTML fields.
            if field.disabled:
                value = self.get_initial_for_field(field, name)
            else:
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, FileField):
                    initial = self.get_initial_for_field(field, name)
                    value = field.clean(value, initial)
                else:
                    value = field.clean(value)
                self.cleaned_data[name] = value
                if hasattr(self, 'clean_%s' % name):
                    value = getattr(self, 'clean_%s' % name)()
                    self.cleaned_data[name] = value
            except ValidationError as e:
                log.exception('_clean_fields')
                self.add_error(name, e)

    def add_error(self, field, error):
        log.debug('add_error: \'%s\': %s' % (field, error))
        super().add_error(field, error)

    def is_valid(self):
        #non_field_errors


        log.debug('running is_valid')
        log.info(force_text(self.errors))
        result = super().is_valid()
        log.debug('is_valid: %s' % result)
        return result


class InputToOutputInline(admin.TabularInline):
    model = InputToOutput
    extra = 1
    form = InputToOutputForm

    def XXXget_queryset(self, request):
        qs = InputToOutput.all_objects
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

@admin.register(Device)
class DeviceAdmin(GuardedModelAdmin):
    list_display = ('description', 'sn', 'host', 'deleted')

    def get_queryset(self, request):
        #return super(InputAdmin, self).get_queryset_also_deleted(request).prefetch_related('tags')
        qs = self.model._base_manager .get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs


@admin.register(Input)
class InputAdmin(GuardedModelAdmin):
    inlines = (InputToOutputInline, )
    list_display = ('description', 'device', 'index', 'input_type', 'deleted', 'tag_list')











    form = InputForm







    def get_queryset(self, request):
        #return super(InputAdmin, self).get_queryset_also_deleted(request).prefetch_related('tags')
        qs = self.model._base_manager .get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


@admin.register(Cue)
class CueAdmin(TagAdmin):
    class CuedItemInline(admin.StackedInline):
        model = CuedItem

    inlines = [CuedItemInline]


@admin.register(Output)
class OutputAdmin(GuardedModelAdmin):
    inlines = (InputToOutputInline, )

    list_display = ('description', 'device', 'index', 'output_type', 'deleted', 'tag_list', 'cue_list', '_my_state', 'default_state', 'execution_limit', 'started_time', 'current_position') # add task_id?, 'off_delay_initiated_time'

    def get_queryset(self, request):
        #return super(OutputAdmin, self).get_queryset_also_deleted(request).prefetch_related('tags')
        qs = self.model._base_manager .get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

    def cue_list(self, obj):
        return u", ".join(o.name for o in obj.cues.all())
    cue_list.short_description = 'Cues'

@admin.register(TriggerAudit)
class TriggerAuditAdmin(GuardedModelAdmin):
    list_display = ('timestamp_seconds', 'type', 'input', 'input_type', 'state', 'user', 'schedule', 'onetimeschedule', 'request_id')
    #list_filter = ('type', 'input', 'input_type', 'user', 'schedule', 'onetimeschedule', 'output', )

    date_hierarchy = 'timestamp'
    list_filter = ('type', 'input', 'input_type', 'user', 'schedule', 'onetimeschedule')

    list_filter = (
        ('type', ChoiceDropdownFilter),
        ('input', RelatedDropdownFilter),
        ('input_type', ChoiceDropdownFilter),
        #('user', RelatedDropdownFilter),
        ('username', DropdownFilter),
        ('schedule', RelatedDropdownFilter),
        ('onetimeschedule', RelatedDropdownFilter),

        ## for ordinary fields
        #('a_charfield', DropdownFilter),
        ## for choice fields
        #('a_choicefield', ChoiceDropdownFilter),
        ## for related fields
        #('a_foreignkey_field', RelatedDropdownFilter),
    )

    #from django.utils import timezone
    #timezone.activate(tz)
    tz = pytz.timezone(settings.TIME_ZONE)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    #def has_delete_permission(self, request, obj=None):
    #    return False

    def timestamp_seconds(self, obj):
        return obj.timestamp.astimezone(self.tz).strftime("%d/%-m/%y %H:%M:%S")
    timestamp_seconds.admin_order_field = 'timestamp'
    timestamp_seconds.short_description = 'Time'


@admin.register(OutputAudit)
class OutputAuditAdmin(GuardedModelAdmin):
    list_display = ('timestamp_seconds', 'trigger__type', 'trigger__input', 'trigger__input_type', 'trigger__state', 'trigger__user', 'trigger__schedule', 'trigger__onetimeschedule', 'output', 'target_position', 'state', 'request_id')
    #list_filter = ('trigger_type', 'trigger_input', 'trigger_input_type', 'trigger_user', 'trigger_schedule', 'trigger_onetimeschedule', 'output', )

    date_hierarchy = 'timestamp'
    empty_value_display = '-'
    #list_filter = ('trigger_type', 'trigger_input', 'trigger_input_type', 'trigger_user', 'trigger_schedule', 'trigger_onetimeschedule', 'output', )

    list_filter = (
        ('trigger__type', ChoiceDropdownFilter),
        ('trigger__input', RelatedDropdownFilter),
        ('trigger__input_type', ChoiceDropdownFilter),
        #('trigger_user', RelatedDropdownFilter),
        ('trigger__username', DropdownFilter),
        ('trigger__schedule', RelatedDropdownFilter),
        ('trigger__onetimeschedule', RelatedDropdownFilter),
        ('output', RelatedDropdownFilter),

        ## for ordinary fields
        #('a_charfield', DropdownFilter),
        ## for choice fields
        #('a_choicefield', ChoiceDropdownFilter),
        ## for related fields
        #('a_foreignkey_field', RelatedDropdownFilter),
    )

    #from django.utils import timezone
    #timezone.activate(tz)
    tz = pytz.timezone(settings.TIME_ZONE)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    #def has_delete_permission(self, request, obj=None):
    #    return False

    def timestamp_seconds(self, obj):
        return obj.timestamp.astimezone(self.tz).strftime("%d/%-m/%y %H:%M:%S")
    timestamp_seconds.admin_order_field = 'timestamp'
    timestamp_seconds.short_description = 'Time'

    def trigger__type(self, obj):
        return obj.trigger.get_type_display() if obj.trigger.type else '-'
    trigger__type.admin_order_field = 'trigger__type'
    trigger__type.short_description = 'Type'

    def trigger__input(self, obj):
        return obj.trigger.input if obj.trigger.input else self.empty_value_display
    trigger__input.admin_order_field = 'trigger__input'
    trigger__input.short_description = 'Input'

    def trigger__state(self, obj):
        return obj.trigger.state
    trigger__state.admin_order_field = 'trigger__state'
    trigger__state.short_description = 'Input State'
    trigger__state.boolean = True
    trigger__state.empty_value_display = '-'

    def trigger__input_type(self, obj):
        return obj.trigger.get_input_type_display() if obj.trigger.input_type else '-'
    trigger__input_type.admin_order_field = 'trigger__input_type'
    trigger__input_type.short_description = 'Input Type'

    def trigger__user(self, obj):
        return obj.trigger.user if obj.trigger.user else self.empty_value_display
    trigger__user.admin_order_field = 'trigger__user'
    trigger__user.short_description = 'User'

    def trigger__schedule(self, obj):
        return obj.trigger.schedule if obj.trigger.schedule else self.empty_value_display
    trigger__schedule.admin_order_field = 'trigger__schedule'
    trigger__schedule.short_description = 'Schedule'

    def trigger__onetimeschedule(self, obj):
        return obj.trigger.onetimeschedule if obj.trigger.onetimeschedule else self.empty_value_display
    trigger__onetimeschedule.admin_order_field = 'trigger__onetimeschedule'
    trigger__onetimeschedule.short_description = 'OneTimeSchedule'

