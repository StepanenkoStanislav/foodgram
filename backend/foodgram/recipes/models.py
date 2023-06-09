from django.db import models

from users.models import AuthUser


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название',
        help_text='Введите название тэга'
    )
    color = models.CharField(
        max_length=7,
        unique=True,
        verbose_name='Цвет',
        help_text='Введите код цвета в HEX формате'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Ссылка',
        help_text='Введите ссылку для тэга'
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name[:30]


class MeasurementUnit(models.Model):
    measurement_unit = models.CharField(
        max_length=30,
        verbose_name='Ед. измерения',
        help_text='Введите единицу измерения',
        unique=True
    )

    class Meta:
        verbose_name = 'Ед. измерения'
        verbose_name_plural = 'Ед. измерения'

    def __str__(self):
        return self.measurement_unit


class Ingredient(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Название',
        help_text='Введите название'
    )
    measurement_unit = models.ForeignKey(
        MeasurementUnit,
        related_name='ingredients',
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Ед. измерения',
        help_text='Выберите единицу измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'], name='unique_ingredients')
        ]

    def __str__(self):
        return (f'{self.name[:20]} '
                f'[{self.measurement_unit.measurement_unit[:10]}]')


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент в рецепте',
        help_text='Добавьте ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        help_text='Введите количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'amount'],
                name='unique_recipeingredients'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient.name}: {self.amount} '
                f'{self.ingredient.measurement_unit.measurement_unit}')


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги',
        help_text='Введите тэги'
    )
    author = models.ForeignKey(
        AuthUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recipes',
        verbose_name='Автор',
        help_text='Укажите автора'
    )
    ingredients = models.ManyToManyField(
        RecipeIngredient,
        related_name='recipes',
        verbose_name='Ингредиенты',
        help_text='Укажите ингредиенты'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Введите название'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/images/',
        blank=True,
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Введите описание рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        help_text='Введите время приготовления (в минутах)'
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:30]


class Favorite(models.Model):
    user = models.ForeignKey(
        AuthUser,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        help_text='Укажите пользователя',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        help_text='Укажите рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorites')
        ]

    def __str__(self):
        return f'{self.user.username[:30]} -> {self.recipe.username[:30]}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        AuthUser,
        related_name='shopping_carts',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        help_text='Укажите пользователя',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_carts',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        help_text='Укажите рецепт'
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_carts')
        ]

    def __str__(self):
        return f'{self.user.username[:30]} -> {self.recipe.username[:30]}'


class Subscribe(models.Model):
    subscriber = models.ForeignKey(
        AuthUser,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        help_text='Укажите подписчика'
    )
    author = models.ForeignKey(
        AuthUser,
        related_name='subscribes',
        on_delete=models.CASCADE,
        verbose_name='Автор',
        help_text='Укажите автора'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'], name='unique_subscribes'
            )
        ]

    def __str__(self):
        return (f'{self.subscriber.username[:30]} -> '
                f'{self.author.username[:30]}')
