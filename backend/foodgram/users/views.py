from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from rest_framework import viewsets, decorators, response, mixins, status, exceptions
from django.urls import reverse
from . import serializers


User = get_user_model()


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return serializers.UserSerializer
        elif self.action in ('create',):
            return serializers.SignUpSerializer
        elif self.action in ('subscribtions', 'subscribe'):
            return serializers.SubscribeSerializer
        elif self.action in ('set_password',):
            return serializers.ChangePasswordSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if self.request.user == instance:
            return redirect(reverse('users:users-me'))
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        serializer = serializers.UserSerializer(user)
        headers = self.get_success_headers(serializer.data)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()

    @decorators.action(methods=['get'], detail=False, url_path='me', url_name='me')
    def me(self, request, *args, **kwargs):
        instance = self.request.user
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    @decorators.action(methods=['post'], detail=False, url_path='set_password', url_name='set_password')
    def set_password(self, request, *args, **kwargs):
        instance = self.request.user
        serializer = self.get_serializer(self.request.data)
        new_pass, curr_pass = serializer.data.get('new_password'), serializer.data.get('current_password')
        if not instance.check_password(curr_pass):
            raise exceptions.ValidationError('Неверный пароль!')
        instance.set_password(new_pass)
        instance.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(methods=['get'], detail=False, url_path='subscribtions', url_name='subscribtions')
    def subscribtions(self, request, *args, **kwargs):
        instance = self.get_object()
        subscribtions = instance.following.all()
        subscribers = User.objects.filter(
            id__in=subscribtions.values('author')
        )
        serializer = self.get_serializer(subscribers, many=True)
        return response.Response(serializer.data)

    @decorators.action(methods=['post', 'delete'], detail=True, url_path='subscribe', url_name='subscribe')
    def subscribe(self, request, *args, **kwargs):
        instance = self.request.user
        author = self.get_object()
        subscription = instance.subscriber.filter(author=author)
        if self.request.method == 'POST':
            if subscription.exists():
                raise exceptions.ValidationError('Уже есть!')
            instance.subscriber.create(author=author)
            serializer = serializers.SubscribeSerializer(author)
            headers = self.get_success_headers(serializer.data)
            return response.Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        if self.request.method == 'DELETE':
            if not subscription.exists():
                raise exceptions.ValidationError('Такого не существует! Не могу удалить!')
            subscription.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
