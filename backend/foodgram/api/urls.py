from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('tags', views.TagViewSet, basename='tags')
router_v1.register('ingredient', views.IngredientAmountViewSet, basename='ingredient')
router_v1.register('recipes', views.RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router_v1.urls)),
]
