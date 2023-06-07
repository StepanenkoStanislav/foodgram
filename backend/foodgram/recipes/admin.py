from django.contrib import admin

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


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(MeasurementUnit)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('measurement_unit',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    readonly_fields = ('favorite_count',)

    @admin.display(description='Добавлен в избранное')
    def favorite_count(self, recipe):
        return Favorite.objects.filter(recipe=recipe).count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscriber', 'author')
