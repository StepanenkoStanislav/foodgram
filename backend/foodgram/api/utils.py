from recipes.models import RecipeIngredient


def create_and_add_ingredients_to_recipe(recipe, ingredients):
    for ingredient in ingredients:
        current_ingredient, _ = RecipeIngredient.objects.get_or_create(
            ingredient=ingredient.get('id'), amount=ingredient.get('amount'))
        recipe.ingredients.add(current_ingredient)
