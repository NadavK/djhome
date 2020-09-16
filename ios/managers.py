from django.db import models
import logging

class DeviceManager(models.Manager):
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        return self.get_queryset_also_deleted().filter(deleted=False)

    def get_queryset_also_deleted(self):
        return super().get_queryset()

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

    # def inputs_to_outputs(self, ph_sn, index):
    #     print('x1')
    #     #with apps.get_models()
    #     #input = super(InputManager, self).get(ph_sn=ph_sn, index=index)
    #     input = super(InputManager, self).get(ph_sn=124, index=3)
    #     print(input)
    #     print('x2')
    #     outputs = input.outputs.all()
    #     print(outputs)
    #     return outputs
    #     print('x3')
    #     #print(apps.get_model('ios', 'Output').objects.all())
    #     #print(apps.get_model('ios', 'InputToOutput').objects.all())
    #     #return apps.get_model('ios', 'Output').objects.filter(input__ph_sn=ph_sn, input__ph_index=index)

    def set_input_by_device_sn(self, device_sn, index, state, user):
        self.logger.debug('setting_input Device sn: %s, Index: %s, State: %s (%s)', device_sn, index, state, user)
        try:
            input = self.get(device__sn=device_sn, index=index)
            input.on_state_change(state, user)
        except self.model.DoesNotExist:
            self.logger.warning('Input not found. Maybe input is deleted? Device sn: %s, Index: %s, State: %s ', device_sn, index, state)
        except Exception:
            self.logger.exception('Input Device sn: %s, Index: %s, State: %s, User: %s', device_sn, index, state, user)

    def set_input_by_device_index(self, device_id, index, state, user):
        self.logger.debug('setting_input Device id: %s, Index: %s, State: %s (%s)', device_id, index, state, user)
        try:
            input = self.get(device__id=device_id, index=index)
            input.on_state_change(state, user)
        except self.model.DoesNotExist:
            self.logger.warning('Input not found. Maybe input is deleted? Device id: %s, Index: %s, State: %s ', device_id, index, state)
        except Exception:
            self.logger.exception('Input Device id: %s, Index: %s, State: %s, User: %s', device_id, index, state, user)

    def set_state_by_pk(self, pk, state, user):
        self.logger.debug('setting_input pk: %s, State: %s (%s)', pk, state, user)
        try:
            input = self.get(pk=pk)

            # input = self.get_object(ph_sn=request.data['sn'], index=request.data['index'])
            # ph_input_changed_helper(sender=self.__class__, ph_sn=input.ph_sn, index=input.index, state=True)       #calling signal sometimes causes phidget to fire all inputs and outputs
            input.on_state_change(state, user)
        except self.model.DoesNotExist:
            self.logger.error('Input not found. Maybe input is deleted? pk: %s, State: %s ', pk, state)
        except Exception:
            self.logger.warning('Input pk: %s, State: %s, User: %s', pk, state, user)


class OutputManager(models.Manager):
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        return self.get_queryset_also_deleted().filter(deleted=False)

    def get_queryset_also_deleted(self):
        return super().get_queryset().prefetch_related('toggle_off_output')

    def set_state_by_device_index(self, device_id, index, state, user):
        self.logger.debug('setting_output Device: %s, Index: %s, State: %s', device_id, index, state)
        try:
            output = self.get(device__id=device_id, index=index)
            output.set_state(state, user=user)
            return output
        except self.model.DoesNotExist:
            self.logger.error('Output not found. Maybe output is deleted? Device: %s, Index: %s, State: %s ', device_id, index, state)
        except Exception :
            self.logger.exception('Output Device: %s, Index: %s, State: %s', device_id, index, state)

    '''If task_id is passed, then state will only be set if task_id is still valid'''
    def set_state_by_pk(self, pk, state, target_position=None, task_id='', user=None):
        self.logger.debug('set_state_by_pk - pk: %s, State: %s, target_position: %s, task_id: %s (%s)', pk, state, target_position, task_id, user)
        try:
            output = self.get(pk=pk)
            if task_id and task_id != output.task_id:
                self.logger.warning('set_state_by_pk - Task-ID incorrect for pk: %s (%s!=%s)', pk, task_id, output.task_id)
            else:
                if output.state == state:
                    # if output is not changed, on_state_change will not be triggered
                    # and this will leave out-of-sync-clients still out-of-sync
                    #output.on_state_change() - this failed with threading error
                    # Returning the object indicates that the state is  not changed
                    return output
                else:
                    output.set_state(state, target_position=target_position, user=user)
        except self.model.DoesNotExist:
            self.logger.error('set_state_by_pk - Output not found. pk: %s, State: %s ', pk, state)
        except Exception:
            self.logger.exception('set_state_by_pk - Output pk: %s, State: %s, User: %s ', pk, state, user)


class InputToOutputValidManager(models.Manager):
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False).select_related('output')
        #return super().get_queryset().filter(deleted=False).prefetch_related('output').select_related('output')


class TriggerAuditManager(models.Manager):
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        return super().get_queryset().exclude(input__pk=5)


class OutputAuditManager(models.Manager):
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        return super().get_queryset().exclude(trigger__input__pk=5).select_related('trigger')
