from django.contrib.auth import password_validation
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import (
    viewsets,
    mixins,
    decorators,
    status,
    exceptions,
    permissions,
)
from rest_framework.response import Response

from api.filters import IngredientFilter
from api.permissions import AuthenticatedOrAuthorOrReadOnly
from api.serializers import (
    AuthUserSerializer,
    AuthUserListSerializer,
    IngredientSerializer,
    RecipeListSerializer,
    RecipeSerializer,
    RecipeFavoriteSerializer,
    SubscribeSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscribe,
    Tag,
)
from users.models import AuthUser


class AuthUserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = AuthUser.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuthUserSerializer

    def get_permissions(self):
        if self.action in ['list', 'create']:
            return [permissions.AllowAny()]
        return super(AuthUserViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action == 'subscribe':
            return SubscribeSerializer
        if self.request.method == 'POST':
            return super(AuthUserViewSet, self).get_serializer_class()
        return AuthUserListSerializer

    @decorators.action(methods=['get'], detail=False, url_path='me')
    def retrieve_request_user(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @decorators.action(
        methods=['post'],
        detail=False,
        url_path='set_password',
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not request.user.check_password(current_password):
            raise exceptions.ValidationError(
                {'current_password': ['Неверно введен текущий пароль.']})
        if not new_password:
            raise exceptions.ValidationError(
                {'new_password': ['Обязательное поле.']})
        errors = dict()
        try:
            password_validation.validate_password(
                password=new_password,
                user=request.user
            )
        except password_validation.ValidationError as err:
            errors['password'] = list(err.messages)
            raise exceptions.ValidationError(errors)
        request.user.set_password(new_password)
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        methods=['get'],
        detail=False,
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions = AuthUser.objects.filter(
            username__in=Subscribe.objects.filter(
                subscriber=request.user).values_list('author__username'))
        serializer = SubscribeSerializer(
            subscriptions,
            many=True,
            context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @decorators.action(
        methods=['post', 'delete'],
        detail=True,
        url_path='subscribe',
        permission_classes=[AuthenticatedOrAuthorOrReadOnly]
    )
    def subscribe(self, request, pk):
        author = get_object_or_404(AuthUser, id=pk)
        subscribe = Subscribe.objects.filter(
            subscriber=request.user,
            author=author
        )
        subscribe_exists = subscribe.exists()
        if request.method == 'POST':
            if subscribe_exists:
                raise exceptions.ValidationError(
                    {'errors': 'Вы уже подписаны на этого автора.'})
            if author == request.user:
                raise exceptions.ValidationError(
                    {'errors': 'Вы не можете подписаться на самого себя.'})
            Subscribe.objects.create(subscriber=request.user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data)
        if not subscribe_exists:
            raise exceptions.ValidationError(
                {'errors': 'Вы не подписаны на этого автора.'})
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [IngredientFilter]
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [AuthenticatedOrAuthorOrReadOnly]
    serializer_class = RecipeListSerializer

    def filter_queryset(self, queryset):
        if self.action != 'list':
            return queryset
        if self.request.query_params.get('is_favorited') == '1':
            queryset = queryset.filter(
                favorites__in=Favorite.objects.filter(user=self.request.user))
        if self.request.query_params.get('is_in_shopping_cart') == '1':
            queryset = queryset.filter(
                shopping_carts__in=ShoppingCart.objects.filter(
                    user=self.request.user))
        if self.request.query_params.get('author'):
            author_id = self.request.query_params.get('author')
            author_id = int(author_id) if author_id.isdigit() else None
            if author_id:
                queryset = queryset.filter(author__id=author_id)
        if self.request.query_params.getlist('tags'):
            tags = self.request.query_params.getlist('tags')
            queryset = queryset.filter(tags__slug__in=tags)
        return queryset

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ['favorite', 'shopping_cart']:
            return RecipeFavoriteSerializer
        if self.request.method in ['POST', 'PATCH']:
            return RecipeSerializer
        return super(RecipeViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        recipe_serializer = RecipeListSerializer(
            recipe, context=self.get_serializer_context())
        return Response(
            recipe_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        recipe_serializer = RecipeListSerializer(
            recipe, context=self.get_serializer_context())
        return Response(recipe_serializer.data)

    @decorators.action(
        methods=['get'],
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = ('attachment; '
                                           'filename=shopping_cart.txt')
        shopping_carts = ShoppingCart.objects.filter(user=request.user)
        ingredients = dict()
        for shopping_cart in shopping_carts:
            for ingredient in shopping_cart.recipe.ingredients.all():
                ingredient_name = (f'{ingredient.id.name} '
                                   f'({ingredient.id.measurement_unit})')
                if ingredient_name not in ingredients:
                    ingredients[ingredient_name] = ingredient.amount
                else:
                    ingredients[ingredient_name] += ingredient.amount
        lines = []
        for name, amount in ingredients.items():
            lines.append(f'- {name}: {amount}\n')
        response.writelines(lines)
        return response

    @decorators.action(
        methods=['post', 'delete'],
        detail=True,
        url_path='favorite'
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite = Favorite.objects.filter(
            user=self.request.user,
            recipe=recipe
        )
        favorite_exists = favorite.exists()
        if request.method == 'POST':
            if favorite_exists:
                raise exceptions.ValidationError(
                    {'errors': 'Этот рецепт уже добавлен в избранное.'})
            Favorite.objects.create(
                user=self.request.user,
                recipe=recipe
            )
            serializer = self.get_serializer(recipe)
            return Response(serializer.data)
        if not favorite_exists:
            raise exceptions.ValidationError(
                {'errors': 'Этого рецепта нет в избранном.'})
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        methods=['post', 'delete'],
        detail=True,
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        shopping_cart = ShoppingCart.objects.filter(
            user=self.request.user,
            recipe=recipe
        )
        recipe_in_the_cart = shopping_cart.exists()
        if request.method == 'POST':
            if recipe_in_the_cart:
                raise exceptions.ValidationError(
                    {'errors': 'Этот рецепт уже добавлен в корзину.'})
            ShoppingCart.objects.create(
                user=self.request.user,
                recipe=recipe
            )
            serializer = self.get_serializer(recipe)
            return Response(serializer.data)
        if not recipe_in_the_cart:
            raise exceptions.ValidationError(
                {'errors': 'Этого рецепта нет в корзине.'})
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)