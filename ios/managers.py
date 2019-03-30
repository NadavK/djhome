from django.db import models
import logging


class InputManager(models.Manager):
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        return self.get_queryset_also_deleted().filter(deleted=False)

    def get_queryset_also_deleted(self):
        return super().get_queryset().prefetch_related('outputs', 'tags')

    # def phidget_sns(self):
    #     self.logger.debug('Getting SNS')
    #     sns = self.distinct('sn')
    #     self.logger.debug('Got SNs: ', sn)
    #     return sns

    # def inputs_to_outputs(self, ph_sn, ph_index):
    #     print('x1')
    #     #with apps.get_models()
    #     #input = super(InputManager, self).get(ph_sn=ph_sn, ph_index=ph_index)
    #     input = super(InputManager, self).get(ph_sn=124, ph_index=3)
    #     print(input)
    #     print('x2')
    #     outputs = input.outputs.all()
    #     print(outputs)
    #     return outputs
    #     print('x3')
    #     #print(apps.get_model('ios', 'Output').objects.all())
    #     #print(apps.get_model('ios', 'InputToOutput').objects.all())
    #     #return apps.get_model('ios', 'Output').objects.filter(input__ph_sn=ph_sn, input__ph_index=ph_index)

    def set_input_by_sn_index(self, ph_sn, ph_index, state):
        self.logger.debug('setting_input SN: %s, Index: %s, State: %s', ph_sn, ph_index, state)
        try:
            input = self.get(ph_sn=ph_sn, ph_index=ph_index)
            return input.on_state_change(state)
        except self.model.DoesNotExist:
            self.logger.warning('Input not found. Maybe input is deleted? SN: %s, Index: %s, State: %s ', ph_sn, ph_index, state)
        except Exception:
            self.logger.exception('Input SN: %s, Index: %s, State: %s', ph_sn, ph_index, state)

    def set_state(self, pk, state):
        self.logger.debug('setting_input pk: %s, State: %s', pk, state)
        try:
            input = self.get(pk=pk)

            # input = self.get_object(ph_sn=request.data['sn'], ph_index=request.data['index'])
            # ph_input_changed_helper(sender=self.__class__, ph_sn=input.ph_sn, ph_index=input.ph_index, state=True)       #calling signal sometimes causes phidget to fire all inputs and outputs
            input.on_state_change(state)
        except self.model.DoesNotExist:
            self.logger.error('Input not found. Maybe input is deleted? pk: %s, State: %s ', pk, state)
        except Exception:
            self.logger.warning('Input pk: %s, State: %s ', pk, state)


class OutputManager(models.Manager):
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        return self.get_queryset_also_deleted().filter(deleted=False)

    def get_queryset_also_deleted(self):
        return super(OutputManager, self).get_queryset().prefetch_related('toggle_off_output')

    def set_state_by_sn_index(self, ph_sn, ph_index, state):
        self.logger.debug('setting_output SN: %s, Index: %s, State: %s', ph_sn, ph_index, state)
        try:
            output = self.get(ph_sn=ph_sn, ph_index=ph_index)
            output.state = state
            return output
        except self.model.DoesNotExist:
            self.logger.error('Output not found. Maybe output is deleted? SN: %s, Index: %s, State: %s ', ph_sn, ph_index, state)
        except Exception :
            self.logger.exception('Output SN: %s, Index: %s, State: %s', ph_sn, ph_index, state)

    '''If task_id is passed, then state will only be set if task_id is still valid'''
    def set_state(self, pk, state, task_id='', target_position=None):
        self.logger.debug('set_state - pk: %s, State: %s, task_id: %s', pk, state, task_id)
        try:
            output = self.get(pk=pk)
            if task_id and task_id != output.task_id:
                self.logger.warning('set_state - Output task no longer valid for pk: %s', pk)
            elif output.deleted:
                self.logger.warning('set_state - Output pk %s is deleted', pk)
            else:
                output.set_state(state, target_position=target_position)
        except self.model.DoesNotExist:
            self.logger.error('set_state - Output not found. pk: %s, State: %s ', pk, state)
        except Exception:
            self.logger.exception('set_state - Output pk: %s, State: %s ', pk, state)


class InputToOutputManager(models.Manager):
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        return super(InputToOutputManager, self).get_queryset().filter(deleted=False)


class OutputAuditManager(models.Manager):
    logger = logging.getLogger(__name__)
