from django.conf.urls import url
from django.urls import include


urlpatterns = [
    url(r'^auth/', include('djoser.urls.authtoken')),
]
