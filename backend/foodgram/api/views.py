from django.contrib.auth import password_validation
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import (
    viewsets,
    mixins,
    decorators,
    status,
    permissions,
)
from rest_framework.response import Response

from api.filters import IngredientFilter
from api.permissions import AuthenticatedOrAuthorOrReadOnly
from api.serializers import (
    AuthUserSerializer,
    AuthUserListSerializer,
    IngredientSerializer,
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
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'subscribe':
            return SubscribeSerializer
        if self.request.method == 'POST':
            return super().get_serializer_class()
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
            return Response(
                {'current_password': ['Неверно введен текущий пароль.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not new_password:
            return Response(
                {'new_password': ['Обязательное поле.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        errors = dict()
        try:
            password_validation.validate_password(
                password=new_password,
                user=request.user
            )
        except password_validation.ValidationError as err:
            errors['password'] = list(err.messages)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
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
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if author == request.user:
                return Response(
                    {'errors': 'Вы не можете подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscribe.objects.create(subscriber=request.user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data)
        if not subscribe_exists:
            return Response(
                {'errors': 'Вы не подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST
            )
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
    serializer_class = RecipeSerializer

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

    def get_serializer_class(self):
        if self.action in ['favorite', 'shopping_cart']:
            return RecipeFavoriteSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        instance.ingredients.all().delete()
        instance.delete()

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
        ingredients = shopping_carts.values_list(
            'recipe__ingredients__ingredient__name',
            ('recipe__ingredients__ingredient__measurement_unit__'
             'measurement_unit')
        ).annotate(Sum('recipe__ingredients__amount'))
        lines = []
        for ingredient in ingredients:
            lines.append(
                f'- {ingredient[0]} [{ingredient[1]}]: {ingredient[2]}\n'
            )
        response.writelines(lines)
        return response

    def favorite_and_shopping_cart(self, request, pk, model):
        recipe = get_object_or_404(Recipe, id=pk)
        instance = model.objects.filter(
            user=self.request.user,
            recipe=recipe
        )
        instance_exists = instance.exists()
        if request.method == 'POST':
            if instance_exists:
                return Response(
                    {'errors': 'Этот рецепт уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(
                user=self.request.user,
                recipe=recipe
            )
            serializer = self.get_serializer(recipe)
            return Response(serializer.data)
        if not instance_exists:
            return Response(
                {'errors': 'Этот рецепт не был добавлен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        methods=['post', 'delete'],
        detail=True,
        url_path='favorite'
    )
    def favorite(self, request, pk):
        return self.favorite_and_shopping_cart(request, pk, Favorite)

    @decorators.action(
        methods=['post', 'delete'],
        detail=True,
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        return self.favorite_and_shopping_cart(request, pk, ShoppingCart)
