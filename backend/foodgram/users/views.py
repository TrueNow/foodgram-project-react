from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from rest_framework import viewsets, decorators, response, mixins, status, exceptions
from django.urls import reverse
from . import serializers
from core import permissions

User = get_user_model()


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return serializers.UserSerializer
        elif self.action in ('subscriptions', 'subscribe'):
            return serializers.SubscribeSerializer
        elif self.action in ('set_password',):
            return serializers.ChangePasswordSerializer
        return serializers.SignUpSerializer

    def retrieve(self, request, *args, **kwargs):
        if self.request.user == self.get_object():
            return redirect(reverse('users:users-me'))
        return super().retrieve(request, *args, **kwargs)

    @decorators.action(
        methods=['get'], detail=False, url_path='me', url_name='me',
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        instance = self.request.user
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    @decorators.action(
        methods=['post'], detail=False, url_path='set_password', url_name='set_password',
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request, *args, **kwargs):
        instance = self.request.user
        serializer = self.get_serializer(self.request.data)
        serializer.is_valid(raise_exception=True)
        curr_password = serializer.validated_data.get('current_password')
        if not instance.check_password(curr_password):
            raise exceptions.ValidationError('Неверный пароль!')
        new_password = serializer.validated_data.get('new_password')
        instance.set_password(new_password)
        instance.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        methods=['get'], detail=False, url_path='subscriptions', url_name='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request, *args, **kwargs):
        instance = self.request.user
        subscriptions = instance.subscriber.all()
        subscribers = User.objects.filter(
            id__in=subscriptions.values('author'),
        )
        serializer = self.get_serializer(subscribers, many=True)
        return response.Response(serializer.data)

    @decorators.action(
        methods=['post', 'delete'], detail=True, url_path='subscribe', url_name='subscribe',
        permission_classes=[permissions.IsAuthenticated]
    )
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
