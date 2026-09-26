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
    """Group ingredients by recipe and combine pantry items for display."""
    return [
        {
            "section": "ingredients",
            "recipes": _recipes_for_field(meals, "ingredients"),
        },
        {"section": "pantry", "items": _unique_items(meals, "pantry")},
    ]


def _recipes_for_field(meals: list[Meal], field_name: str) -> list[dict]:
    recipes = []
    for meal in meals:
        items = [item.strip() for item in getattr(meal, field_name) if item.strip()]
        if items:
            recipes.append(
                {"recipe": meal.name, "recipe_url": meal.recipe, "items": items}
            )
    return recipes


def _unique_items(meals: list[Meal], field_name: str) -> list[str]:
    items = {}
    for meal in meals:
        for item in getattr(meal, field_name):
            item = item.strip()
            if item:
                items.setdefault(item.lower(), item)
    return sorted(items.values(), key=str.lower)
