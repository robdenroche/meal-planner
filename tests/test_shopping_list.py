from mealplanner.models import load_meals
from mealplanner.shopping_list import (
    build_grouped_shopping_list,
    build_shopping_list,
)

from .fixtures import SAMPLE_YAML


def test_build_shopping_list_merges_duplicate_ingredients():
    meals = load_meals(SAMPLE_YAML)
    shopping_list = build_shopping_list(meals)

    cheese = next(item for item in shopping_list if item["ingredient"] == "cheese")
    assert sorted(cheese["meals"]) == ["Tacos", "Veggie Bowl"]

    names = [item["ingredient"] for item in shopping_list]
    assert names == sorted(names, key=str.lower)


def test_build_grouped_shopping_list_splits_ingredients_and_pantry_by_recipe():
    meals = load_meals(SAMPLE_YAML)

    shopping_list = build_grouped_shopping_list(meals)

    assert shopping_list == [
        {
            "section": "ingredients",
            "recipes": [
                {
                    "recipe": "Tacos",
                    "items": ["tortillas", "ground beef", "cheese"],
                },
                {
                    "recipe": "Veggie Bowl",
                    "items": ["rice", "beans", "cheese"],
                },
            ],
        },
        {
            "section": "pantry",
            "recipes": [
                {"recipe": "Tacos", "items": ["cumin", "salt"]},
                {"recipe": "Veggie Bowl", "items": ["olive oil"]},
            ],
        },
    ]
