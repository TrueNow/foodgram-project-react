from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'users'

router_v1 = DefaultRouter()
router_v1.register('users', views.UserViewSet, basename='users')

urlpatterns = [
    path('', include(router_v1.urls)),
    url(r'^auth/', include('djoser.urls.authtoken')),
]
