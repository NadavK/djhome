from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, APIClient
from rest_framework.authtoken.models import Token
from guardian.shortcuts import assign_perm, get_perms
from .models import Input, Output, InputToOutput
from django.contrib.auth.models import User


class IOsTestCase(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', password='test', email='admin@mail.com')
        self.user1 = User.objects.create_user(username='user1', password='test')
        self.user2 = User.objects.create_user(username='user2', password='test')
        self.user3 = User.objects.create_user(username='user3', password='test')
        #print('Users: ', User.objects.all())
        self.in0 = Input.objects.create(ph_sn=1, index=0, input_type=Input.INPUT_TYPE_MAGNET, deleted=False, description='in 0')
        self.in0.tags.add('Door')
        self.in0.save()
        self.in1 = Input.objects.create(ph_sn=1, index=1, input_type=Input.INPUT_TYPE_MAGNET, deleted=False, description='in 1')
        self.in1.tags.add('Door1')
        self.in1.save()
        assign_perm('change_input', self.user1, self.in1)
        self.in2 = Input.objects.create(ph_sn=1, index=2, input_type=Input.INPUT_TYPE_MAGNET, deleted=False, description='in 2')
        self.in2.tags.add('Door2')
        self.in2.save()
        assign_perm('view_input', self.user1, self.in2)
        self.in3 = Input.objects.create(ph_sn=1, index=3, input_type=Input.INPUT_TYPE_MAGNET, deleted=False, description='in 3')
        self.in3.tags.add('Door3')
        self.in3.save()
        self.out0 = Output.objects.create(ph_sn=1, index=0, output_type=Output.OUTPUT_TYPE_REGULAR, deleted=False, description='out 0')
        self.out0.tags.add('Door')
        self.out0.save()
        self.out1 = Output.objects.create(ph_sn=1, index=1, output_type=Output.OUTPUT_TYPE_ALARM, deleted=False, description='out 1')
        self.out1.tags.add('Door')
        #obj.permissions.add('user1')
        self.out1.save()
        self.out2 = Output.objects.create(ph_sn=1, index=2, output_type=Output.OUTPUT_TYPE_BLIND_UP, deleted=False, description='out 2')
        self.out2.tags.add('Door')
        #obj.permissions.add('user2')
        self.out2.save()
        self.out3 = Output.objects.create(ph_sn=1, index=3, output_type=Output.OUTPUT_TYPE_BLIND_DOWN, deleted=False, description='out 3')
        self.out3.tags.add('Door')
        #obj.permissions.add('user3')
        self.out3.save()
        #obj.save()
        #print('Tags: ', obj.tags.all())
        #print('Input: ', Input.objects.all())
        #outputs = models.ManyToManyField('Output', through='InputToOutput', related_name='inputs')
        #tags = TaggableModel

    def test_inputtooutputs(self):
        self.assertEqual(self.in0.outputs.count(), 0)
        self.in0.output_assoc.create(output=self.out0, deleted=False)
        self.in0.output_assoc.create(output=self.out1, deleted=False)
        self.in0.output_assoc.create(output=self.out2, deleted=True)
        self.in0.output_assoc.create(output=self.out3, deleted=False)
        self.assertEqual(self.in0.outputs.count(), 4)

        self.assertEqual(InputToOutput.objects.filter(input=self.in0, deleted=False).count(), 3)
        self.assertEqual(InputToOutput.objects.filter(input=self.in0, deleted=True).count(), 1)

        self.assertEqual(self.in0.outputs.filter(deleted=False).all().count(), 4)           # This filters outputs that are not deleted,
        self.assertEqual(InputToOutput.valid_objects.filter(input=self.in0).count(), 3)     # This filters i2o's that are not deleted

        with self.assertNumQueries(1):
            for i2o in InputToOutput.valid_objects.filter(input=self.in0):
                print('\t', i2o.output)

    def test_magnets(self):
        self.in0.output_assoc.create(output=self.out1, deleted=False)
        self.in1.output_assoc.create(output=self.out1, deleted=False)
        self.in2.output_assoc.create(output=self.out1, deleted=True)
        self.in3.output_assoc.create(output=self.out1, deleted=False)
        self.in0.state = True
        self.in0.save()
        self.in1.state = False
        self.in1.save()
        self.in2.state = True
        self.in2.save()
        self.in3.state = True
        self.in3.save()

        with self.assertNumQueries(1):
            self.assertTrue(InputToOutput.valid_objects.filter(output=self.out1, input__state=False).exists())
        self.in1.state = True
        self.in1.save()
        with self.assertNumQueries(1):
            self.assertFalse(InputToOutput.valid_objects.filter(output=self.out1, input__state=False).exists())



    def test_really(self):
        """Animals that can speak are correctly identified"""
        lion = Input.objects.get(ph_sn = 1, index = 1)
        self.assertEqual(int(lion.ph_sn), 1)

    def test_drf(self):
        # Using the standard RequestFactory API to create a form POST request
        #factory = APIRequestFactory()
        #request = factory.get('/api/ios')
        #request.
        #request = factory.post('/api/ios', {'title': 'new idea'}, format='json')
        #request = factory.post('/api/ios', json.dumps({'title': 'new idea'}), content_type='application/json')

        print('perm0:', get_perms(self.user1, self.in0))
        print('perm1:', get_perms(self.user1, self.in1))
        print('obj0:', self.user1.has_perm('change_input', self.in0))
        print('obj1:', self.user1.has_perm('change_input', self.in1))


        #BAD Get
        url = reverse('ios_api')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)       #status.HTTP_401_UNAUTHORIZED

        #User Get
        client = APIClient()
        client.login(username='user1', password='test')
        response = client.get(url, format='json')
        print('User1 response:', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #Admin Get
        client = APIClient()
        client.login(username='admin', password='test')
        response = client.get(url, format='json')
        print('Admin response:', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #data = {'name': 'DabApps'}
        #response = self.client.post(url, data, format='json')
        #self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        #self.assertEqual(Account.objects.count(), 1)
        #self.assertEqual(Account.objects.get().name, 'DabApps')


        # BAD Token
        token = Token.objects.get(user__username='admin')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Tokenx ' + token.key)
        response = client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Good Token
        token = Token.objects.get(user__username='admin')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
