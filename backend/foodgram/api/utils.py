from recipes.models import RecipeIngredient


def create_and_add_ingredients_to_recipe(recipe, ingredients):
    recipe_ingredients = []
    for ingredient in ingredients:
        recipe_ingredients.append(
            RecipeIngredient(
                recipe_id=recipe.id,
                ingredient=ingredient.get('id'),
                amount=ingredient.get('amount')
            )
        )
    recipe_ingredients = RecipeIngredient.objects.bulk_create(
        recipe_ingredients)
    recipe.ingredients.add(*recipe_ingredients)
