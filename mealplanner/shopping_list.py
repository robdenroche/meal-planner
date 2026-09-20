"""Aggregate ingredients from a set of meals into a shopping list."""

from __future__ import annotations

from .models import Meal


def build_shopping_list(meals: list[Meal]) -> list[dict]:
    """Merge ingredients across meals (case-insensitive), tracking which meals need each one."""
    items: dict[str, dict] = {}
    for meal in meals:
        for ingredient in meal.ingredients:
            key = ingredient.strip().lower()
            if key not in items:
                items[key] = {"ingredient": ingredient.strip(), "meals": []}
            items[key]["meals"].append(meal.name)
    return sorted(items.values(), key=lambda item: item["ingredient"].lower())
