from mealplanner.models import Meal, load_meals

from .fixtures import SAMPLE_YAML


def test_load_meals_parses_fields():
    meals = load_meals(SAMPLE_YAML)
    assert len(meals) == 2

    tacos = next(m for m in meals if m.name == "Tacos")
    assert tacos.recipe is None
    assert tacos.ingredients == ["tortillas", "ground beef", "cheese"]
    assert tacos.effort == "weeknight"
    assert tacos.protein == "beef/poultry"
    assert tacos.leftovers is True
    assert tacos.vegetarian is False


def test_load_meals_defaults_missing_fields():
    meals = load_meals("Mystery Meal:\n  ingredients:\n    - mystery\n")
    meal = meals[0]
    assert meal.effort is None
    assert meal.protein is None
    assert meal.leftovers is False
    assert meal.vegetarian is False
    assert meal.recipe is None
