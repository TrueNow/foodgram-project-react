from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('users', views.UserViewSet, basename='users')
router_v1.register('tags', views.TagViewSet, basename='tags')
router_v1.register('ingredient', views.IngredientAmountViewSet, basename='ingredient')
router_v1.register('recipes', views.RecipeViewSet, basename='recipes')

auth_urlpatterns = [
    # path('login', views.LoginView, name='login'),  # POST
    # path('logout', views.LogoutView, name='logout'),  # POST
]

urlpatterns = [
    path('auth/token', include((auth_urlpatterns, 'users'), namespace='auth')),
    path('', include(router_v1.urls)),
]
