from django.contrib.auth import get_user_model
from rest_framework import serializers
from api.serializers import RecipeAuthorSerializer


User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            # 'is_subscribed'
        )


class UserWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password'
        )


class SubscribeSerializer(serializers.ModelSerializer):
    recipes = RecipeAuthorSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = User
        fields = UserReadSerializer.Meta.fields
        fields += (
            #'subscriber',
            'recipes', 'recipes_count'
        )


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=128, required=True)
    current_password = serializers.CharField(max_length=128, required=True)

    class Meta:
        fields = (
            'new_password', 'current_password'
        )
