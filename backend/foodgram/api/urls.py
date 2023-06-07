from django.urls import path, include
from rest_framework.routers import SimpleRouter

from api.views import (
    AuthUserViewSet,
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
)

router = SimpleRouter()
router.register('users', AuthUserViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns += router.urls
