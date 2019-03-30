from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from ios.models import Input, Output, InputToOutput, OutputAudit

# @admin.register(InputType)
# class InputTypeAdmin(admin.ModelAdmin):
#     list_display = ('input_type', 'description', 'id')
#     ordering = ('id',)
#
# @admin.register(OutputType)
# class OutputTypeAdmin(admin.ModelAdmin):
#     list_display = ('output_type', 'description', 'id')
#     ordering = ('id',)

class InputToOutputInline(admin.TabularInline):
    model = InputToOutput
    extra = 5

@admin.register(Input)
class InputAdmin(GuardedModelAdmin):
    inlines = (InputToOutputInline, )

    list_display = ['description', 'ph_sn', 'ph_index', 'input_type', 'deleted', 'tag_list']

    def get_queryset(self, request):
        #return super(InputAdmin, self).get_queryset_also_deleted(request).prefetch_related('tags')
        qs = self.model._base_manager .get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


@admin.register(Output)
class OutputAdmin(GuardedModelAdmin):
    inlines = (InputToOutputInline, )

    list_display = ['description', 'ph_sn', 'ph_index', 'output_type', 'deleted', 'tag_list', '_my_state', 'default_state', 'execution_limit', 'started_time', 'current_position']# add task_id?, 'off_delay_initiated_time']

    def get_queryset(self, request):
        #return super(OutputAdmin, self).get_queryset_also_deleted(request).prefetch_related('tags')
        qs = self.model._base_manager .get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

@admin.register(OutputAudit)
class OutputAuditAudit(GuardedModelAdmin):
    #list_display = ['description', 'ph_sn', 'ph_index', 'output_type', 'deleted', 'tag_list', '_my_state', 'default_state', 'execution_limit', 'started_time', 'current_position']# add task_id?, 'off_delay_initiated_time']
    pass
