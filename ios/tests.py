from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, APIClient
from rest_framework.authtoken.models import Token
from guardian.shortcuts import assign_perm, get_perms
from .models import Input, Output
from django.contrib.auth.models import User


class IOsTestCase(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', password='test', email='admin@mail.com')
        self.user1 = User.objects.create_user(username='user1', password='test')
        self.user2 = User.objects.create_user(username='user2', password='test')
        self.user3 = User.objects.create_user(username='user3', password='test')
        #print('Users: ', User.objects.all())
        self.obj0 = Input.objects.create(ph_sn=1, ph_index=0, input_type=Input.INPUT_TYPE_MAGNET, deleted=False, description='in 0')
        self.obj0.tags.add('Door')
        self.obj0.save()
        self.obj1 = Input.objects.create(ph_sn=1, ph_index=1, input_type=Input.INPUT_TYPE_MAGNET, deleted=False, description='in 1')
        self.obj1.tags.add('Door')
        self.obj1.save()
        assign_perm('change_input', self.user1, self.obj1)
        self.obj2 = Input.objects.create(ph_sn=1, ph_index=2, input_type=Input.INPUT_TYPE_MAGNET, deleted=False, description='in 2')
        self.obj2.tags.add('Door')
        self.obj2.save()
        assign_perm('view_input', self.user1, self.obj2)
        obj = Input.objects.create(ph_sn=1, ph_index=3, input_type=Input.INPUT_TYPE_MAGNET, deleted=False, description='in 3')
        obj.tags.add('Door')
        #obj.permissions.add('user3')
        obj.save()
        obj = Output.objects.create(ph_sn=1, ph_index=0, output_type=Output.OUTPUT_TYPE_REGULAR, deleted=False, description='out 0')
        obj.tags.add('Door')
        obj.save()
        obj = Output.objects.create(ph_sn=1, ph_index=1, output_type=Output.OUTPUT_TYPE_REGULAR, deleted=False, description='out 1')
        obj.tags.add('Door')
        #obj.permissions.add('user1')
        obj.save()
        obj = Output.objects.create(ph_sn=1, ph_index=2, output_type=Output.OUTPUT_TYPE_BLIND_UP, deleted=False, description='out 2')
        obj.tags.add('Door')
        #obj.permissions.add('user2')
        obj.save()
        obj = Output.objects.create(ph_sn=1, ph_index=3, output_type=Output.OUTPUT_TYPE_BLIND_DOWN, deleted=False, description='out 3')
        obj.tags.add('Door')
        #obj.permissions.add('user3')
        obj.save()
        #obj.save()
        #print('Tags: ', obj.tags.all())
        #print('Input: ', Input.objects.all())
        #outputs = models.ManyToManyField('Output', through='InputToOutput', related_name='inputs')
        #tags = TaggableModel

    def test_really(self):
        """Animals that can speak are correctly identified"""
        lion = Input.objects.get(ph_sn = 1, ph_index = 1)
        self.assertEqual(int(lion.ph_sn), 1)

    def test_drf(self):
        # Using the standard RequestFactory API to create a form POST request
        #factory = APIRequestFactory()
        #request = factory.get('/api/ios')
        #request.
        #request = factory.post('/api/ios', {'title': 'new idea'}, format='json')
        #request = factory.post('/api/ios', json.dumps({'title': 'new idea'}), content_type='application/json')

        print('perm0:', get_perms(self.user1, self.obj0))
        print('perm1:', get_perms(self.user1, self.obj1))
        print('obj0:', self.user1.has_perm('change_input', self.obj0))
        print('obj1:', self.user1.has_perm('change_input', self.obj1))


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
