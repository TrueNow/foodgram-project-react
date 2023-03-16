from django.urls import include, path
from . import views

auth_urlpatterns = [
    path('login', views.LoginView, name='login'),  # POST
    path('logout', views.LogoutView, name='logout'),  # POST
]

urlpatterns = [
    path('auth/token', include((auth_urlpatterns, 'users'), namespace='auth')),
]