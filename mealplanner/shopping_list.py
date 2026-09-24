"""Aggregate ingredients from a set of meals into a shopping list."""

from __future__ import annotations

from .models import Meal


def build_shopping_list(meals: list[Meal]) -> list[dict]:
    """Merge ingredients case-insensitively, tracking meals for each item."""
    items: dict[str, dict] = {}
    for meal in meals:
        for ingredient in meal.ingredients:
            key = ingredient.strip().lower()
            if key not in items:
                items[key] = {"ingredient": ingredient.strip(), "meals": []}
            items[key]["meals"].append(meal.name)
    return sorted(items.values(), key=lambda item: item["ingredient"].lower())


def build_grouped_shopping_list(meals: list[Meal]) -> list[dict]:
    """Group ingredients and pantry items by recipe for display."""
    return [
        {
            "section": "ingredients",
            "recipes": _recipes_for_field(meals, "ingredients"),
        },
        {"section": "pantry", "recipes": _recipes_for_field(meals, "pantry")},
    ]


def _recipes_for_field(meals: list[Meal], field_name: str) -> list[dict]:
    recipes = []
    for meal in meals:
        items = [item.strip() for item in getattr(meal, field_name) if item.strip()]
        if items:
            recipes.append({"recipe": meal.name, "items": items})
    return recipes
