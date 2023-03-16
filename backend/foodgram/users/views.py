from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, decorators, response, mixins, status, exceptions

from . import serializers
from .models import Subscription

User = get_user_model()


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    lookup_field = 'user_pk'

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return serializers.UserReadSerializer
        elif self.action in ('subscribtions', 'subscribe'):
            return serializers.SubscribeSerializer
        elif self.action in ('set_password',):
            return serializers.ChangePasswordSerializer
        else:
            return serializers.UserWriteSerializer

    @decorators.action(methods=['get'], detail=False, url_path='me', url_name='me')
    def me(self, request):
        instance = self.request.user
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    @decorators.action(methods=['post'], detail=False, url_path='set_password', url_name='set_password')
    def set_password(self, request):
        instance = self.request.user
        serializer = self.get_serializer(self.request.data)
        new_pass, curr_pass = serializer.data.get('new_password'), serializer.data.get('current_password')
        if not instance.check_password(curr_pass):
            raise exceptions.ValidationError('current_password is not correct')
        instance.set_password(new_pass)
        instance.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    # @decorators.action(methods=['get'], detail=False, url_path='subscribtions', url_name='subscribtions')
    # def subscribtions(self, request):
    #     instance = self.request.user
    #     subscribers = instance.following
    #     print(subscribers)
    #     serializer = self.get_serializer(subscribers, many=True)
    #     return response.Response(serializer.data)

    @decorators.action(methods=['post', 'delete'], detail=True, url_path='subscribe', url_name='subscribe')
    def subscribe(self, request, pk=None, **kwargs):
        instance = self.request.user
        author = get_object_or_404(User, pk=self.kwargs.get('user_pk'))
        subscription = Subscription.objects.filter(author=author, subscriber=instance)
        if self.request.method == 'POST':
            if subscription.exists():
                raise exceptions.ValidationError('Уже есть!')
            Subscription.objects.create(author=author, subscriber=instance)
            serializer = self.get_serializer(author)
            return response.Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            if not subscription.exists():
                raise exceptions.ValidationError('такого не существует! не могу удалить!')
            subscription.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
