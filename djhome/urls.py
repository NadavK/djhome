"""djhome URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import path
from rest_framework import routers, serializers, viewsets
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token
#from rest_framework.authtoken import views
from ios.views import InputViewSet, OutputViewSet, io, IOsView
from schedules.views import ScheduleViewSet, OnetimeScheduleViewSet
from schedules.views import times
from ios.views import index


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'inputs', InputViewSet)
router.register(r'outputs', OutputViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'onetimeschedules', OnetimeScheduleViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    # url(r'', index),
    # url(r'inputs/', inputs),
    url(r'api/times/', times),
    url(r'io/', io),
    path('admin/rq/', include('django_rq.urls')),
    url(r'admin/', admin.site.urls),
    url(r'api/api-ios/', IOsView.as_view(), name='ios_api'),
    # url(r'^api/times/', SchedulesView.as_view(), name='times'),
    url(r'api/', include(router.urls)),            #TODO: Why two /api ?
    # url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'api-token-auth/', obtain_jwt_token),
    url(r'api-token-refresh/', refresh_jwt_token),
    url(r'api-token-verify/', verify_jwt_token),
]
