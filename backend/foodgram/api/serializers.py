from django.contrib.auth import password_validation
from django.contrib.auth.validators import UnicodeUsernameValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, exceptions

from recipes.models import (
    Favorite,
    Ingredient,
    MeasurementUnit,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscribe,
    Tag,
)
from users.models import AuthUser


class AuthUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=100,
        validators=[UnicodeUsernameValidator(
            message='Введите корректный логин, без цифр и знаков @/./+/-/_')]
    )
    email = serializers.EmailField(max_length=100)
    password = serializers.CharField(
        max_length=128, required=True, write_only=True)

    class Meta:
        model = AuthUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def validate_email(self, email):
        if AuthUser.objects.filter(email=email).exists():
            raise exceptions.ValidationError(f'Email {email} уже существует.')
        return email

    def validate_username(self, username):
        if AuthUser.objects.filter(username=username).exists():
            raise exceptions.ValidationError(
                f'Пользователь с ником {username} уже существует.')
        return username

    def create(self, validated_data):
        user = AuthUser(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        errors = dict()
        try:
            password_validation.validate_password(
                password=validated_data.get('password'),
                user=user
            )
        except password_validation.ValidationError as err:
            errors['password'] = list(err.messages)
            raise exceptions.ValidationError(errors)
        user.set_password(validated_data['password'])
        user.save()
        return user


class AuthUserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AuthUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, author):
        return (self.context['request'].user.is_authenticated
                and Subscribe.objects.filter(
                    subscriber=self.context['request'].user,
                    author=author
                ).exists())


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.SlugRelatedField(
        slug_field='measurement_unit', queryset=MeasurementUnit.objects.all())

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientListSerializer(serializers.ModelSerializer):
    id = IngredientSerializer()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = AuthUserListSerializer(read_only=True)
    ingredients = RecipeIngredientListSerializer(many=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, recipe):
        return (self.context['request'].user.is_authenticated
                and Favorite.objects.filter(
                    user=self.context['request'].user,
                    recipe=recipe
                ).exists())

    def get_is_in_shopping_cart(self, recipe):
        return (self.context['request'].user.is_authenticated
                and ShoppingCart.objects.filter(
                    user=self.context['request'].user,
                    recipe=recipe
                ).exists())

    def to_representation(self, instance):
        to_rep = super(RecipeListSerializer, self).to_representation(instance)
        for ingredient in to_rep.get('ingredients'):
            values = ingredient.pop('id')
            for name, value in values.items():
                ingredient[name] = value
            amount = ingredient.pop('amount')
            ingredient['amount'] = amount
        return to_rep


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate_cooking_time(self, time):
        if time <= 0:
            raise exceptions.ValidationError(
                'Время приготовления должно быть больше 0.')
        return time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise exceptions.ValidationError(
                'Этот список не может быть пустым.')
        return ingredients

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            current_ingredient, st = RecipeIngredient.objects.get_or_create(
                id=ingredient.get('id'), amount=ingredient.get('amount'))
            recipe.ingredients.add(current_ingredient)
        for tag in tags:
            recipe.tags.add(tag)
        return recipe

    def update(self, recipe, validated_data):
        if 'name' in validated_data:
            recipe.name = validated_data.get('name')
        if 'text' in validated_data:
            recipe.text = validated_data.get('text')
        if 'cooking_time' in validated_data:
            recipe.cooking_time = validated_data.get('cooking_time')
        if 'ingredients' in validated_data:
            recipe.ingredients.clear()
            for ingredient in validated_data.get('ingredients'):
                current_ingredient, _ = RecipeIngredient.objects.get_or_create(
                    id=ingredient.get('id'), amount=ingredient.get('amount'))
                recipe.ingredients.add(current_ingredient)
        if 'tags' in validated_data:
            recipe.tags.clear()
            for tag in validated_data.get('tags'):
                recipe.tags.add(tag)
        recipe.save()
        return recipe


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AuthUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, subscription):
        return Recipe.objects.filter(author=subscription).count()

    def get_recipes(self, subscription):
        recipes = Recipe.objects.filter(author=subscription)
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit')
        recipes_limit = (int(recipes_limit)
                         if recipes_limit and recipes_limit.isdigit()
                         else None)
        if recipes_limit and recipes_limit > 0:
            recipes = recipes[:recipes_limit]
        if recipes:
            serializer = RecipeFavoriteSerializer(recipes, many=True)
            return serializer.data
        return []

    def get_is_subscribed(self, author):
        return (self.context['request'].user.is_authenticated
                and Subscribe.objects.filter(
                    subscriber=self.context['request'].user,
                    author=author
                ).exists())
