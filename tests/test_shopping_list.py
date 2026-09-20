from mealplanner.models import load_meals
from mealplanner.shopping_list import build_shopping_list

from .fixtures import SAMPLE_YAML


def test_build_shopping_list_merges_duplicate_ingredients():
    meals = load_meals(SAMPLE_YAML)
    shopping_list = build_shopping_list(meals)

    cheese = next(item for item in shopping_list if item["ingredient"] == "cheese")
    assert sorted(cheese["meals"]) == ["Tacos", "Veggie Bowl"]

    names = [item["ingredient"] for item in shopping_list]
    assert names == sorted(names, key=str.lower)
