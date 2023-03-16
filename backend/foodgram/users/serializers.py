from django.contrib.auth import get_user_model
from rest_framework import serializers
from api.serializers import RecipeGetSerializer


User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password'
        )


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.subscriber.filter(author=obj).exists()


class SubscribeSerializer(UserSerializer):
    recipes = RecipeGetSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields
        fields += ('recipes', 'recipes_count')


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=128, required=True, style={'input_type': 'password'})
    current_password = serializers.CharField(max_length=128, required=True, style={'input_type': 'password'})

    class Meta:
        fields = (
            'new_password', 'current_password'
        )
