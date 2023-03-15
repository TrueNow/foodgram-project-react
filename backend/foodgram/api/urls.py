from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router_v1 = DefaultRouter()
# router_v1.register('users', views.UserViewSet, basename='users')  # == GET/POST ... {id} == GET ... {me} == GET
# router_v1.register(r'users/(?P<user_id>\d+)/subscribe', views.SubscribesViewSet, basename='subscribes')  # POST/DELETE
router_v1.register('tags', views.TagViewSet, basename='tags')  # == GET ... {id} == GET
# router_v1.register('ingredient', views.IngredientViewSet, basename='tags')  # == GET ... {id} == GET
# router_v1.register('recipes', views.RecipeViewSet, basename='recipes')  # ALL
# router_v1.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart', views.ShoppingsViewSet, basename='shopping_cart')  # POST/DELETE
# router_v1.register(r'recipes/(?P<recipe_id>\d+)/favorite', views.FavoritesViewSet, basename='favorites')  # POST/DELETE

users_urlpatterns = [
    # path('set_password', views.SetPasswordView, name='download_shopping_cart'),  # POST
    # path('subscriptions', views.SubscriptionsView, name='subscriptions'),  # GET
]

auth_urlpatterns = [
    # path('login', views.LoginView, name='login'),  # POST
    # path('logout', views.LogoutView, name='logout'),  # POST
]


recipes_urlpatterns = [
    # path('download_shopping_cart', views.DownloadCartView, name='download_shopping_cart'),  # GET
]


urlpatterns = [
    path('users', include((users_urlpatterns, 'users'), namespace='users')),
    path('auth/token', include((auth_urlpatterns, 'users'), namespace='auth')),
    path('recipes', include((recipes_urlpatterns, 'recipes'), namespace='recipes')),
    path('', include(router_v1.urls)),
]
